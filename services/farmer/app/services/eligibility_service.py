"""Main Eligibility Assessment Service."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.eligibility import (
    AssessmentStatus,
    EligibilityAssessment,
    EligibilityNotification,
    EligibilityReviewQueue,
    EligibilityRule,
    EligibilityRuleGroup,
    EligibilityScheme,
    RiskLevel,
    SchemeStatus,
    SchemeWaitlist,
    WorkflowDecision,
)
from app.models.farmer import Farmer, FarmProfile
from app.schemas.eligibility import (
    AssessmentDecisionRequest,
    CreditCheckRequest,
    EligibilityAssessmentRequest,
    EligibilityRuleCreate,
    EligibilityRuleGroupCreate,
    EligibilitySchemeCreate,
    EligibilitySchemeUpdate,
    SchemeEligibilitySummary,
)
from app.services.credit_service import CreditBureauService
from app.services.risk_scoring import RiskScoringService
from app.services.rules_engine import RulesEngine


class EligibilityService:
    """Main service for eligibility assessment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rules_engine = RulesEngine(db)
        self.credit_service = CreditBureauService(db)
        self.risk_service = RiskScoringService(db)

    # =========================================================================
    # Scheme Management
    # =========================================================================

    async def create_scheme(self, data: EligibilitySchemeCreate) -> EligibilityScheme:
        """Create a new eligibility scheme."""
        scheme = EligibilityScheme(
            tenant_id=data.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            scheme_type=data.scheme_type,
            start_date=data.start_date,
            end_date=data.end_date,
            application_deadline=data.application_deadline,
            max_beneficiaries=data.max_beneficiaries,
            budget_amount=data.budget_amount,
            benefit_type=data.benefit_type,
            benefit_amount=data.benefit_amount,
            benefit_description=data.benefit_description,
            auto_approve_enabled=data.auto_approve_enabled,
            min_score_for_auto_approve=data.min_score_for_auto_approve,
            max_risk_for_auto_approve=data.max_risk_for_auto_approve.value
            if data.max_risk_for_auto_approve
            else None,
            waitlist_enabled=data.waitlist_enabled,
            waitlist_capacity=data.waitlist_capacity,
        )
        self.db.add(scheme)
        await self.db.flush()
        return scheme

    async def get_scheme(self, scheme_id: uuid.UUID) -> EligibilityScheme | None:
        """Get a scheme by ID."""
        query = (
            select(EligibilityScheme)
            .options(
                selectinload(EligibilityScheme.rules),
                selectinload(EligibilityScheme.rule_groups).selectinload(
                    EligibilityRuleGroup.rules
                ),
            )
            .where(EligibilityScheme.id == scheme_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_scheme_by_code(self, code: str) -> EligibilityScheme | None:
        """Get a scheme by code."""
        query = select(EligibilityScheme).where(EligibilityScheme.code == code)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_schemes(
        self,
        tenant_id: uuid.UUID,
        status: SchemeStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[EligibilityScheme], int]:
        """List schemes with pagination."""
        query = select(EligibilityScheme).where(EligibilityScheme.tenant_id == tenant_id)

        if status:
            query = query.where(EligibilityScheme.status == status.value)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(EligibilityScheme.created_at.desc())

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_scheme(
        self, scheme_id: uuid.UUID, data: EligibilitySchemeUpdate
    ) -> EligibilityScheme | None:
        """Update a scheme."""
        scheme = await self.get_scheme(scheme_id)
        if not scheme:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(scheme, field):
                if field == "max_risk_for_auto_approve" and value:
                    value = value.value
                setattr(scheme, field, value)

        await self.db.commit()
        await self.db.refresh(scheme)
        return scheme

    async def activate_scheme(self, scheme_id: uuid.UUID) -> EligibilityScheme | None:
        """Activate a scheme."""
        scheme = await self.get_scheme(scheme_id)
        if scheme:
            scheme.status = SchemeStatus.ACTIVE.value
            await self.db.commit()
            await self.db.refresh(scheme)
        return scheme

    # =========================================================================
    # Rule Management
    # =========================================================================

    async def create_rule(self, data: EligibilityRuleCreate) -> EligibilityRule:
        """Create a new eligibility rule."""
        rule = EligibilityRule(
            scheme_id=data.scheme_id,
            rule_group_id=data.rule_group_id,
            name=data.name,
            description=data.description,
            field_type=data.field_type.value,
            field_name=data.field_name,
            field_path=data.field_path,
            operator=data.operator.value,
            value=data.value,
            value_type=data.value_type,
            is_mandatory=data.is_mandatory,
            is_exclusion=data.is_exclusion,
            weight=data.weight,
            priority=data.priority,
            pass_message=data.pass_message,
            fail_message=data.fail_message,
        )
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def create_rule_group(self, data: EligibilityRuleGroupCreate) -> EligibilityRuleGroup:
        """Create a new rule group."""
        group = EligibilityRuleGroup(
            scheme_id=data.scheme_id,
            name=data.name,
            description=data.description,
            logic_operator=data.logic_operator,
            priority=data.priority,
            is_mandatory=data.is_mandatory,
            weight=data.weight,
        )
        self.db.add(group)
        await self.db.flush()
        return group

    async def get_scheme_rules(self, scheme_id: uuid.UUID) -> list[EligibilityRule]:
        """Get all rules for a scheme."""
        return await self.rules_engine.get_scheme_rules(scheme_id)

    # =========================================================================
    # Eligibility Assessment
    # =========================================================================

    async def assess_eligibility(
        self,
        request: EligibilityAssessmentRequest,
        tenant_id: uuid.UUID,
    ) -> EligibilityAssessment:
        """
        Perform full eligibility assessment for a farmer.

        This orchestrates:
        1. Rule evaluation
        2. Credit check
        3. Risk scoring
        4. Workflow decision
        """
        # Get farmer and farm
        farmer = await self._get_farmer(request.farmer_id)
        if not farmer:
            raise ValueError(f"Farmer not found: {request.farmer_id}")

        farm = None
        if request.farm_id:
            farm = await self._get_farm(request.farm_id)

        # Get scheme
        scheme = await self.get_scheme(request.scheme_id)
        if not scheme:
            raise ValueError(f"Scheme not found: {request.scheme_id}")

        # Check if scheme is active and accepting applications
        if scheme.status != SchemeStatus.ACTIVE.value:
            raise ValueError(f"Scheme is not active: {scheme.status}")

        # Compare datetimes, handling both timezone-aware and naive
        if scheme.application_deadline:
            now = datetime.now(UTC)
            deadline = scheme.application_deadline
            # If deadline is naive, make it UTC-aware
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=UTC)
            if deadline < now:
                raise ValueError("Application deadline has passed")

        # Check for existing pending assessment
        existing = await self._get_existing_assessment(request.farmer_id, request.scheme_id)
        if existing and existing.status not in [
            AssessmentStatus.EXPIRED.value,
            AssessmentStatus.REJECTED.value,
        ]:
            return existing

        # Create assessment record
        assessment = EligibilityAssessment(
            farmer_id=request.farmer_id,
            scheme_id=request.scheme_id,
            farm_id=request.farm_id,
            status=AssessmentStatus.IN_PROGRESS.value,
            assessment_date=datetime.now(UTC),
        )
        self.db.add(assessment)
        await self.db.flush()

        try:
            # Step 1: Credit Check
            credit_data = {}
            credit_check = await self.credit_service.get_recent_credit_check(request.farmer_id)
            if not credit_check:
                credit_check = await self.credit_service.request_credit_check(
                    CreditCheckRequest(
                        farmer_id=request.farmer_id,
                        assessment_id=assessment.id,
                    ),
                    farmer,
                    tenant_id,
                )
            credit_data = self.credit_service.get_credit_data_for_rules(credit_check)
            assessment.credit_score = credit_check.credit_score if credit_check else None

            # Step 2: Rule Evaluation
            (
                rule_results,
                eligibility_score,
                mandatory_passed,
            ) = await self.rules_engine.evaluate_rule_groups(
                farmer=farmer,
                scheme_id=request.scheme_id,
                farm=farm,
                credit_data=credit_data,
            )

            assessment.eligibility_score = eligibility_score
            assessment.rules_passed = sum(1 for r in rule_results if r.passed)
            assessment.rules_failed = sum(1 for r in rule_results if not r.passed)
            assessment.mandatory_rules_passed = mandatory_passed
            assessment.rule_results = [r.model_dump(mode="json") for r in rule_results]

            # Step 3: Risk Scoring
            risk_assessment = await self.risk_service.calculate_risk_score(
                farmer=farmer,
                farm=farm,
                credit_check=credit_check,
                assessment_id=assessment.id,
            )
            assessment.risk_score = risk_assessment.total_risk_score
            assessment.risk_level = risk_assessment.risk_level

            # Step 4: Determine Status and Workflow Decision
            status, decision = self._determine_assessment_outcome(
                scheme=scheme,
                eligibility_score=eligibility_score,
                mandatory_passed=mandatory_passed,
                risk_level=RiskLevel(risk_assessment.risk_level),
            )

            assessment.status = status.value
            assessment.workflow_decision = decision.value
            assessment.valid_until = datetime.now(UTC) + timedelta(days=90)

            # Step 5: Handle workflow decision
            await self._handle_workflow_decision(assessment, scheme, decision)

            await self.db.commit()
            await self.db.refresh(assessment)

            # Send notification
            await self._send_assessment_notification(assessment, farmer)

            return assessment

        except Exception as e:
            assessment.status = AssessmentStatus.PENDING.value
            assessment.notes = f"Assessment error: {str(e)}"
            await self.db.commit()
            raise

    def _determine_assessment_outcome(
        self,
        scheme: EligibilityScheme,
        eligibility_score: float,
        mandatory_passed: bool,
        risk_level: RiskLevel,
    ) -> tuple[AssessmentStatus, WorkflowDecision]:
        """Determine assessment outcome based on scores and rules."""
        # If mandatory rules failed, not eligible
        if not mandatory_passed:
            return AssessmentStatus.NOT_ELIGIBLE, WorkflowDecision.AUTO_REJECT

        # Check for auto-approval conditions
        if scheme.auto_approve_enabled:
            min_score = scheme.min_score_for_auto_approve or 70
            max_risk = (
                RiskLevel(scheme.max_risk_for_auto_approve)
                if scheme.max_risk_for_auto_approve
                else RiskLevel.MEDIUM
            )

            risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.VERY_HIGH]
            risk_acceptable = risk_order.index(risk_level) <= risk_order.index(max_risk)

            if eligibility_score >= min_score and risk_acceptable:
                # Check capacity
                if scheme.max_beneficiaries:
                    if scheme.current_beneficiaries < scheme.max_beneficiaries:
                        return AssessmentStatus.APPROVED, WorkflowDecision.AUTO_APPROVE
                    elif scheme.waitlist_enabled:
                        return AssessmentStatus.WAITLISTED, WorkflowDecision.WAITLIST
                    else:
                        return AssessmentStatus.NOT_ELIGIBLE, WorkflowDecision.AUTO_REJECT
                else:
                    return AssessmentStatus.APPROVED, WorkflowDecision.AUTO_APPROVE

        # High risk requires manual review
        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            return AssessmentStatus.ELIGIBLE, WorkflowDecision.MANUAL_REVIEW

        # Otherwise eligible, pending review
        return AssessmentStatus.ELIGIBLE, WorkflowDecision.MANUAL_REVIEW

    async def _handle_workflow_decision(
        self,
        assessment: EligibilityAssessment,
        scheme: EligibilityScheme,
        decision: WorkflowDecision,
    ) -> None:
        """Handle the workflow decision."""
        if decision == WorkflowDecision.AUTO_APPROVE:
            assessment.final_decision = "approved"
            assessment.decision_date = datetime.now(UTC)
            assessment.decision_reason = "Auto-approved based on eligibility criteria"
            scheme.current_beneficiaries += 1

        elif decision == WorkflowDecision.AUTO_REJECT:
            assessment.final_decision = "rejected"
            assessment.decision_date = datetime.now(UTC)
            assessment.decision_reason = "Did not meet mandatory eligibility criteria"

        elif decision == WorkflowDecision.WAITLIST:
            # Add to waitlist
            await self._add_to_waitlist(assessment, scheme)

        elif decision == WorkflowDecision.MANUAL_REVIEW:
            # Add to review queue
            await self._add_to_review_queue(assessment)

    async def _add_to_waitlist(
        self, assessment: EligibilityAssessment, scheme: EligibilityScheme
    ) -> SchemeWaitlist:
        """Add assessment to scheme waitlist."""
        # Get current waitlist position
        count_query = select(func.count()).where(
            and_(
                SchemeWaitlist.scheme_id == scheme.id,
                SchemeWaitlist.status == "waiting",
            )
        )
        result = await self.db.execute(count_query)
        current_count = result.scalar() or 0

        waitlist_entry = SchemeWaitlist(
            scheme_id=scheme.id,
            farmer_id=assessment.farmer_id,
            assessment_id=assessment.id,
            position=current_count + 1,
            original_position=current_count + 1,
            eligibility_score=assessment.eligibility_score or 0,
            risk_score=assessment.risk_score,
        )
        self.db.add(waitlist_entry)

        assessment.waitlist_position = current_count + 1
        assessment.waitlisted_at = datetime.now(UTC)

        await self.db.flush()
        return waitlist_entry

    async def _add_to_review_queue(
        self, assessment: EligibilityAssessment
    ) -> EligibilityReviewQueue:
        """Add assessment to manual review queue."""
        # Determine priority based on risk and score
        risk_level = assessment.risk_level
        if risk_level == RiskLevel.VERY_HIGH.value:
            priority = 1
            reason = "Very high risk - requires urgent review"
        elif risk_level == RiskLevel.HIGH.value:
            priority = 2
            reason = "High risk - requires review"
        else:
            priority = 5
            reason = "Standard review required"

        queue_entry = EligibilityReviewQueue(
            assessment_id=assessment.id,
            priority=priority,
            queue_reason=reason,
            queue_category="standard_review",
            sla_due_at=datetime.now(UTC) + timedelta(days=3),
        )
        self.db.add(queue_entry)
        await self.db.flush()
        return queue_entry

    async def _send_assessment_notification(
        self, assessment: EligibilityAssessment, farmer: Farmer
    ) -> None:
        """Send notification about assessment status."""
        status_messages = {
            AssessmentStatus.APPROVED.value: "Congratulations! Your application has been approved.",
            AssessmentStatus.ELIGIBLE.value: "Your eligibility has been confirmed. Your application is under review.",
            AssessmentStatus.NOT_ELIGIBLE.value: "Unfortunately, you do not meet the eligibility criteria.",
            AssessmentStatus.WAITLISTED.value: f"You have been added to the waitlist at position {assessment.waitlist_position}.",
        }

        message = status_messages.get(
            assessment.status,
            "Your eligibility assessment is being processed.",
        )

        notification = EligibilityNotification(
            farmer_id=farmer.id,
            assessment_id=assessment.id,
            notification_type="status_change",
            title="Eligibility Assessment Update",
            message=message,
            channels=["in_app", "sms"],
        )
        self.db.add(notification)

    # =========================================================================
    # Manual Review
    # =========================================================================

    async def make_decision(
        self,
        assessment_id: uuid.UUID,
        decision_request: AssessmentDecisionRequest,
        reviewer_id: uuid.UUID,
    ) -> EligibilityAssessment:
        """Make manual decision on an assessment."""
        assessment = await self.get_assessment(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment not found: {assessment_id}")

        assessment.final_decision = decision_request.decision
        assessment.decision_reason = decision_request.reason
        assessment.decision_date = datetime.now(UTC)
        assessment.decided_by = reviewer_id
        assessment.notes = decision_request.notes

        if decision_request.decision == "approved":
            assessment.status = AssessmentStatus.APPROVED.value
            # Update scheme beneficiary count
            scheme = await self.get_scheme(assessment.scheme_id)
            if scheme:
                scheme.current_beneficiaries += 1
        else:
            assessment.status = AssessmentStatus.REJECTED.value

        # Update review queue
        await self._complete_review_queue_item(
            assessment_id, decision_request.decision, reviewer_id
        )

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def _complete_review_queue_item(
        self, assessment_id: uuid.UUID, decision: str, reviewer_id: uuid.UUID
    ) -> None:
        """Mark review queue item as completed."""
        query = select(EligibilityReviewQueue).where(
            EligibilityReviewQueue.assessment_id == assessment_id
        )
        result = await self.db.execute(query)
        queue_item = result.scalars().first()

        if queue_item:
            queue_item.status = "completed"
            queue_item.decision = decision
            queue_item.completed_at = datetime.now(UTC)
            queue_item.assigned_to = reviewer_id

    # =========================================================================
    # Queries
    # =========================================================================

    async def get_assessment(self, assessment_id: uuid.UUID) -> EligibilityAssessment | None:
        """Get an assessment by ID."""
        query = select(EligibilityAssessment).where(EligibilityAssessment.id == assessment_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def _get_existing_assessment(
        self, farmer_id: uuid.UUID, scheme_id: uuid.UUID
    ) -> EligibilityAssessment | None:
        """Get existing non-expired assessment."""
        query = (
            select(EligibilityAssessment)
            .where(
                and_(
                    EligibilityAssessment.farmer_id == farmer_id,
                    EligibilityAssessment.scheme_id == scheme_id,
                )
            )
            .order_by(EligibilityAssessment.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_farmer_assessments(
        self, farmer_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[EligibilityAssessment], int]:
        """List assessments for a farmer."""
        query = select(EligibilityAssessment).where(EligibilityAssessment.farmer_id == farmer_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(EligibilityAssessment.created_at.desc())

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def list_scheme_assessments(
        self,
        scheme_id: uuid.UUID,
        status: AssessmentStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[EligibilityAssessment], int]:
        """List assessments for a scheme."""
        query = select(EligibilityAssessment).where(EligibilityAssessment.scheme_id == scheme_id)

        if status:
            query = query.where(EligibilityAssessment.status == status.value)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(EligibilityAssessment.created_at.desc())

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_review_queue(
        self,
        status: str = "pending",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[EligibilityReviewQueue], int]:
        """Get manual review queue."""
        query = select(EligibilityReviewQueue).where(EligibilityReviewQueue.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(
            EligibilityReviewQueue.priority,
            EligibilityReviewQueue.queued_at,
        )

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_scheme_waitlist(
        self, scheme_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[SchemeWaitlist], int]:
        """Get waitlist for a scheme."""
        query = select(SchemeWaitlist).where(
            and_(
                SchemeWaitlist.scheme_id == scheme_id,
                SchemeWaitlist.status == "waiting",
            )
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(SchemeWaitlist.position)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _get_farmer(self, farmer_id: uuid.UUID) -> Farmer | None:
        """Get farmer by ID."""
        query = select(Farmer).where(Farmer.id == farmer_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def _get_farm(self, farm_id: uuid.UUID) -> FarmProfile | None:
        """Get farm by ID."""
        query = select(FarmProfile).where(FarmProfile.id == farm_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    # =========================================================================
    # Analytics
    # =========================================================================

    async def get_scheme_summary(self, scheme_id: uuid.UUID) -> SchemeEligibilitySummary:
        """Get eligibility summary for a scheme."""
        scheme = await self.get_scheme(scheme_id)
        if not scheme:
            raise ValueError(f"Scheme not found: {scheme_id}")

        # Count by status
        status_counts = {}
        for status in AssessmentStatus:
            count_query = select(func.count()).where(
                and_(
                    EligibilityAssessment.scheme_id == scheme_id,
                    EligibilityAssessment.status == status.value,
                )
            )
            result = await self.db.execute(count_query)
            status_counts[status.value] = result.scalar() or 0

        # Calculate averages
        avg_query = select(
            func.avg(EligibilityAssessment.eligibility_score),
            func.avg(EligibilityAssessment.risk_score),
        ).where(EligibilityAssessment.scheme_id == scheme_id)
        result = await self.db.execute(avg_query)
        avg_row = result.first()

        return SchemeEligibilitySummary(
            scheme_id=scheme_id,
            scheme_name=scheme.name,
            total_assessments=sum(status_counts.values()),
            eligible_count=status_counts.get(AssessmentStatus.ELIGIBLE.value, 0),
            not_eligible_count=status_counts.get(AssessmentStatus.NOT_ELIGIBLE.value, 0),
            approved_count=status_counts.get(AssessmentStatus.APPROVED.value, 0),
            rejected_count=status_counts.get(AssessmentStatus.REJECTED.value, 0),
            pending_review_count=status_counts.get(AssessmentStatus.IN_PROGRESS.value, 0),
            waitlisted_count=status_counts.get(AssessmentStatus.WAITLISTED.value, 0),
            average_eligibility_score=avg_row[0] if avg_row else None,
            average_risk_score=avg_row[1] if avg_row else None,
        )
