"""KYC Workflow Engine - orchestrates the complete KYC process."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.farmer import (
    BiometricData,
    Document,
    ExternalVerification,
    Farmer,
    KYCApplication,
    KYCReviewQueue,
    KYCStatus,
)


class KYCStep(str, Enum):
    """KYC workflow steps."""

    PERSONAL_INFO = "personal_info"
    DOCUMENTS = "documents"
    BIOMETRICS = "biometrics"
    BANK_INFO = "bank_info"
    EXTERNAL_VERIFICATION = "external_verification"
    REVIEW = "review"
    COMPLETE = "complete"


class KYCWorkflowStatus(BaseModel):
    """Current status of KYC workflow."""

    farmer_id: UUID
    current_step: str
    overall_status: str
    progress_percentage: int

    # Step status
    steps: dict[str, dict[str, Any]]

    # Requirements
    missing_documents: list[str]
    missing_biometrics: list[str]

    # Verification results
    external_verifications: list[dict]

    # Review info
    in_review_queue: bool
    submitted_at: datetime | None = None
    estimated_completion: datetime | None = None


class KYCWorkflowService:
    """Service for managing the complete KYC workflow.

    This service orchestrates:
    1. Step-by-step registration wizard
    2. Document collection and verification
    3. Biometric capture and deduplication
    4. External verification (ID, credit, sanctions)
    5. Manual review queue management
    6. Auto-approval for qualifying farmers
    """

    # Default requirements
    DEFAULT_REQUIRED_DOCUMENTS = ["national_id"]
    DEFAULT_REQUIRED_BIOMETRICS = ["fingerprint_right_index", "face"]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def start_kyc_application(
        self,
        farmer_id: UUID,
        required_documents: list[str] | None = None,
        required_biometrics: list[str] | None = None,
    ) -> KYCApplication:
        """Start a new KYC application for a farmer.

        Args:
            farmer_id: The farmer's UUID
            required_documents: List of required document types
            required_biometrics: List of required biometric types

        Returns:
            The created KYC application
        """
        # Check if application already exists
        existing = await self._get_application(farmer_id)
        if existing:
            return existing

        # Create new application
        application = KYCApplication(
            farmer_id=farmer_id,
            current_step=KYCStep.PERSONAL_INFO.value,
            required_documents={
                doc: False for doc in (required_documents or self.DEFAULT_REQUIRED_DOCUMENTS)
            },
            submitted_documents={},
            required_biometrics=required_biometrics or self.DEFAULT_REQUIRED_BIOMETRICS,
            captured_biometrics=[],
        )
        self.db.add(application)
        await self.db.flush()
        return application

    async def get_workflow_status(self, farmer_id: UUID) -> KYCWorkflowStatus | None:
        """Get the current KYC workflow status for a farmer."""
        application = await self._get_application(farmer_id)
        if not application:
            return None

        farmer = await self._get_farmer_with_relations(farmer_id)
        if not farmer:
            return None

        # Calculate progress
        steps_completed = sum([
            application.personal_info_complete,
            application.documents_complete,
            application.biometrics_complete,
            application.bank_info_complete,
        ])
        progress = int((steps_completed / 4) * 100)

        # Get missing requirements
        missing_docs = self._get_missing_documents(application, farmer)
        missing_bio = self._get_missing_biometrics(application, farmer)

        # Get external verifications
        verifications = await self._get_external_verifications(farmer_id)

        # Check if in review queue
        in_review = await self._is_in_review_queue(farmer_id)

        return KYCWorkflowStatus(
            farmer_id=farmer_id,
            current_step=application.current_step,
            overall_status=farmer.kyc_status,
            progress_percentage=progress,
            steps={
                KYCStep.PERSONAL_INFO.value: {
                    "complete": application.personal_info_complete,
                    "required": True,
                },
                KYCStep.DOCUMENTS.value: {
                    "complete": application.documents_complete,
                    "required": True,
                    "submitted": list(application.submitted_documents.keys()) if application.submitted_documents else [],
                    "required_types": list(application.required_documents.keys()) if application.required_documents else [],
                },
                KYCStep.BIOMETRICS.value: {
                    "complete": application.biometrics_complete,
                    "required": True,
                    "captured": application.captured_biometrics or [],
                    "required_types": application.required_biometrics or [],
                },
                KYCStep.BANK_INFO.value: {
                    "complete": application.bank_info_complete,
                    "required": False,  # Optional for some schemes
                },
                KYCStep.REVIEW.value: {
                    "complete": farmer.kyc_status == KYCStatus.APPROVED.value,
                    "status": farmer.kyc_status,
                },
            },
            missing_documents=missing_docs,
            missing_biometrics=missing_bio,
            external_verifications=[
                {
                    "type": v.verification_type,
                    "status": v.status,
                    "is_verified": v.is_verified,
                }
                for v in verifications
            ],
            in_review_queue=in_review,
            submitted_at=application.submitted_at,
            estimated_completion=self._estimate_completion(application),
        )

    async def complete_step(
        self,
        farmer_id: UUID,
        step: KYCStep,
        data: dict[str, Any] | None = None,
    ) -> KYCWorkflowStatus:
        """Mark a KYC step as complete and advance to next step.

        Args:
            farmer_id: The farmer's UUID
            step: The step being completed
            data: Optional data associated with step completion

        Returns:
            Updated workflow status
        """
        application = await self._get_application(farmer_id)
        if not application:
            raise ValueError("KYC application not found")

        farmer = await self._get_farmer_with_relations(farmer_id)
        if not farmer:
            raise ValueError("Farmer not found")

        # Mark step complete
        if step == KYCStep.PERSONAL_INFO:
            application.personal_info_complete = True
            application.current_step = KYCStep.DOCUMENTS.value

        elif step == KYCStep.DOCUMENTS:
            # Verify all required documents are submitted
            missing = self._get_missing_documents(application, farmer)
            if missing:
                raise ValueError(f"Missing required documents: {', '.join(missing)}")
            application.documents_complete = True
            application.current_step = KYCStep.BIOMETRICS.value

        elif step == KYCStep.BIOMETRICS:
            # Verify all required biometrics are captured
            missing = self._get_missing_biometrics(application, farmer)
            if missing:
                raise ValueError(f"Missing required biometrics: {', '.join(missing)}")
            application.biometrics_complete = True
            application.current_step = KYCStep.BANK_INFO.value

        elif step == KYCStep.BANK_INFO:
            application.bank_info_complete = True
            application.current_step = KYCStep.EXTERNAL_VERIFICATION.value
            # Trigger external verifications
            await self._trigger_external_verifications(farmer_id)

        return await self.get_workflow_status(farmer_id)  # type: ignore

    async def submit_for_review(self, farmer_id: UUID) -> KYCWorkflowStatus:
        """Submit the KYC application for review.

        This will either:
        1. Auto-approve if all verifications pass
        2. Add to manual review queue if manual review is needed
        """
        application = await self._get_application(farmer_id)
        if not application:
            raise ValueError("KYC application not found")

        farmer = await self._get_farmer_with_relations(farmer_id)
        if not farmer:
            raise ValueError("Farmer not found")

        # Check all requirements are met
        if not application.personal_info_complete:
            raise ValueError("Personal information incomplete")
        if not application.documents_complete:
            raise ValueError("Documents incomplete")
        if not application.biometrics_complete:
            raise ValueError("Biometrics incomplete")

        # Update application
        application.submitted_at = datetime.now(timezone.utc)
        application.current_step = KYCStep.REVIEW.value
        farmer.kyc_status = KYCStatus.IN_REVIEW.value

        # Check if auto-approval is possible
        can_auto_approve, reasons = await self._check_auto_approval(farmer_id)

        if can_auto_approve:
            # Auto-approve
            farmer.kyc_status = KYCStatus.APPROVED.value
            farmer.kyc_verified_at = datetime.now(timezone.utc)
            application.current_step = KYCStep.COMPLETE.value
        else:
            # Add to manual review queue
            await self._add_to_review_queue(farmer_id, reasons)

        return await self.get_workflow_status(farmer_id)  # type: ignore

    async def process_review_decision(
        self,
        farmer_id: UUID,
        decision: str,  # "approve" or "reject"
        reviewer_id: UUID,
        notes: str | None = None,
        rejection_reason: str | None = None,
    ) -> KYCWorkflowStatus:
        """Process a review decision for a KYC application."""
        application = await self._get_application(farmer_id)
        if not application:
            raise ValueError("KYC application not found")

        farmer = await self._get_farmer_with_relations(farmer_id)
        if not farmer:
            raise ValueError("Farmer not found")

        # Update application
        application.reviewed_at = datetime.now(timezone.utc)
        application.reviewer_id = reviewer_id
        application.review_notes = notes

        if decision == "approve":
            farmer.kyc_status = KYCStatus.APPROVED.value
            farmer.kyc_verified_at = datetime.now(timezone.utc)
            farmer.kyc_verified_by = reviewer_id
            application.current_step = KYCStep.COMPLETE.value
        elif decision == "reject":
            farmer.kyc_status = KYCStatus.REJECTED.value
            application.rejection_reason = rejection_reason

        # Remove from review queue
        await self._remove_from_review_queue(farmer_id, decision)

        return await self.get_workflow_status(farmer_id)  # type: ignore

    async def record_document_submission(
        self,
        farmer_id: UUID,
        document_type: str,
        document_id: UUID,
    ) -> None:
        """Record that a document has been submitted."""
        application = await self._get_application(farmer_id)
        if not application:
            return

        if application.submitted_documents is None:
            application.submitted_documents = {}

        application.submitted_documents[document_type] = str(document_id)

        # Check if all required documents are now submitted
        if application.required_documents:
            all_submitted = all(
                doc_type in application.submitted_documents
                for doc_type in application.required_documents.keys()
            )
            if all_submitted:
                application.documents_complete = True

    async def record_biometric_capture(
        self,
        farmer_id: UUID,
        biometric_type: str,
    ) -> None:
        """Record that a biometric has been captured."""
        application = await self._get_application(farmer_id)
        if not application:
            return

        if application.captured_biometrics is None:
            application.captured_biometrics = []

        if biometric_type not in application.captured_biometrics:
            application.captured_biometrics.append(biometric_type)

        # Check if all required biometrics are now captured
        if application.required_biometrics:
            all_captured = all(
                bio_type in application.captured_biometrics
                for bio_type in application.required_biometrics
            )
            if all_captured:
                application.biometrics_complete = True

    async def get_review_queue(
        self,
        status: str = "pending",
        assigned_to: UUID | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Get KYC applications in the review queue."""
        query = select(KYCReviewQueue).where(KYCReviewQueue.status == status)

        if assigned_to:
            query = query.where(KYCReviewQueue.assigned_to == assigned_to)

        query = query.order_by(KYCReviewQueue.priority, KYCReviewQueue.queued_at)
        query = query.limit(limit)

        result = await self.db.execute(query)
        queue_items = result.scalars().all()

        items = []
        for item in queue_items:
            farmer = await self._get_farmer_with_relations(item.farmer_id)
            if farmer:
                items.append({
                    "queue_id": str(item.id),
                    "farmer_id": str(item.farmer_id),
                    "farmer_name": f"{farmer.first_name} {farmer.last_name}",
                    "priority": item.priority,
                    "reason": item.reason,
                    "queued_at": item.queued_at.isoformat() if item.queued_at else None,
                    "assigned_to": str(item.assigned_to) if item.assigned_to else None,
                })

        return items

    async def assign_review(
        self,
        farmer_id: UUID,
        reviewer_id: UUID,
    ) -> None:
        """Assign a KYC review to a specific reviewer."""
        result = await self.db.execute(
            select(KYCReviewQueue).where(
                KYCReviewQueue.farmer_id == farmer_id,
                KYCReviewQueue.status == "pending",
            )
        )
        queue_item = result.scalar_one_or_none()
        if queue_item:
            queue_item.assigned_to = reviewer_id
            queue_item.assigned_at = datetime.now(timezone.utc)
            queue_item.status = "in_progress"

    # Private helper methods

    async def _get_application(self, farmer_id: UUID) -> KYCApplication | None:
        """Get KYC application for a farmer."""
        result = await self.db.execute(
            select(KYCApplication).where(KYCApplication.farmer_id == farmer_id)
        )
        return result.scalar_one_or_none()

    async def _get_farmer_with_relations(self, farmer_id: UUID) -> Farmer | None:
        """Get farmer with documents and biometrics loaded."""
        result = await self.db.execute(
            select(Farmer)
            .options(
                selectinload(Farmer.documents),
                selectinload(Farmer.biometrics),
            )
            .where(Farmer.id == farmer_id)
        )
        return result.scalar_one_or_none()

    def _get_missing_documents(
        self, application: KYCApplication, farmer: Farmer
    ) -> list[str]:
        """Get list of missing required documents."""
        if not application.required_documents:
            return []

        submitted_types = {d.document_type for d in farmer.documents}
        return [
            doc_type
            for doc_type in application.required_documents.keys()
            if doc_type not in submitted_types
        ]

    def _get_missing_biometrics(
        self, application: KYCApplication, farmer: Farmer
    ) -> list[str]:
        """Get list of missing required biometrics."""
        if not application.required_biometrics:
            return []

        captured_types = {b.biometric_type for b in farmer.biometrics if b.is_verified}
        return [
            bio_type
            for bio_type in application.required_biometrics
            if bio_type not in captured_types
        ]

    async def _get_external_verifications(
        self, farmer_id: UUID
    ) -> list[ExternalVerification]:
        """Get all external verifications for a farmer."""
        result = await self.db.execute(
            select(ExternalVerification).where(
                ExternalVerification.farmer_id == farmer_id
            )
        )
        return list(result.scalars().all())

    async def _is_in_review_queue(self, farmer_id: UUID) -> bool:
        """Check if farmer is in the review queue."""
        result = await self.db.execute(
            select(KYCReviewQueue).where(
                KYCReviewQueue.farmer_id == farmer_id,
                KYCReviewQueue.status.in_(["pending", "in_progress"]),
            )
        )
        return result.scalar_one_or_none() is not None

    def _estimate_completion(self, application: KYCApplication) -> datetime | None:
        """Estimate when KYC review will be completed."""
        if application.submitted_at:
            # Estimate 2 business days for review
            return application.submitted_at + timedelta(days=2)
        return None

    async def _trigger_external_verifications(self, farmer_id: UUID) -> None:
        """Trigger external verification checks."""
        farmer = await self._get_farmer_with_relations(farmer_id)
        if not farmer:
            return

        # Queue ID verification
        if farmer.national_id:
            await self._create_verification_request(
                farmer_id=farmer_id,
                verification_type="id_iprs",
                provider="IPRS",
                request_data={"national_id": farmer.national_id},
            )

        # Queue credit check (if bank info provided)
        if farmer.national_id:
            await self._create_verification_request(
                farmer_id=farmer_id,
                verification_type="credit_bureau",
                provider="TransUnion",
                request_data={"national_id": farmer.national_id},
            )

        # Queue sanctions screening
        await self._create_verification_request(
            farmer_id=farmer_id,
            verification_type="sanctions",
            provider="WorldCheck",
            request_data={
                "name": f"{farmer.first_name} {farmer.last_name}",
                "national_id": farmer.national_id,
            },
        )

    async def _create_verification_request(
        self,
        farmer_id: UUID,
        verification_type: str,
        provider: str,
        request_data: dict,
    ) -> ExternalVerification:
        """Create an external verification request."""
        verification = ExternalVerification(
            farmer_id=farmer_id,
            verification_type=verification_type,
            provider=provider,
            request_data=request_data,
            status="pending",
        )
        self.db.add(verification)
        await self.db.flush()
        return verification

    async def _check_auto_approval(self, farmer_id: UUID) -> tuple[bool, list[str]]:
        """Check if farmer can be auto-approved.

        Returns (can_auto_approve, reasons_for_manual_review)
        """
        reasons = []

        # Check external verifications
        verifications = await self._get_external_verifications(farmer_id)

        # Check ID verification
        id_verified = any(
            v.verification_type == "id_iprs" and v.is_verified
            for v in verifications
        )
        if not id_verified:
            reasons.append("ID verification pending or failed")

        # Check sanctions
        sanctions_clear = any(
            v.verification_type == "sanctions" and v.is_verified
            for v in verifications
        )
        if not sanctions_clear:
            reasons.append("Sanctions check pending or flagged")

        # Check document verification
        farmer = await self._get_farmer_with_relations(farmer_id)
        if farmer:
            unverified_docs = [d for d in farmer.documents if not d.is_verified]
            if unverified_docs:
                reasons.append("Documents pending verification")

        can_auto_approve = len(reasons) == 0
        return can_auto_approve, reasons

    async def _add_to_review_queue(
        self, farmer_id: UUID, reasons: list[str]
    ) -> KYCReviewQueue:
        """Add farmer to manual review queue."""
        # Calculate priority based on reasons
        priority = 5  # Default medium priority
        if "Sanctions" in str(reasons):
            priority = 1  # High priority for sanctions flags

        queue_item = KYCReviewQueue(
            farmer_id=farmer_id,
            priority=priority,
            reason="; ".join(reasons),
        )
        self.db.add(queue_item)
        await self.db.flush()
        return queue_item

    async def _remove_from_review_queue(
        self, farmer_id: UUID, decision: str
    ) -> None:
        """Remove farmer from review queue after decision."""
        result = await self.db.execute(
            select(KYCReviewQueue).where(
                KYCReviewQueue.farmer_id == farmer_id,
                KYCReviewQueue.status.in_(["pending", "in_progress"]),
            )
        )
        queue_item = result.scalar_one_or_none()
        if queue_item:
            queue_item.status = "completed"
            queue_item.decision = decision
            queue_item.completed_at = datetime.now(timezone.utc)
