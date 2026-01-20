"""Tests for KYC workflow service."""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer, KYCApplication, KYCReviewQueue
from app.services.kyc_workflow_service import KYCStep, KYCWorkflowService


@pytest.mark.asyncio
class TestKYCWorkflowService:
    """Test cases for KYC workflow service."""

    async def test_start_kyc_application(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test starting a new KYC application."""
        workflow = KYCWorkflowService(db_session)

        kyc_app = await workflow.start_kyc_application(
            farmer_id=test_farmer.id,
            required_documents=["national_id", "land_title"],
            required_biometrics=["fingerprint_right_index", "face"],
        )

        assert kyc_app is not None
        assert kyc_app.farmer_id == test_farmer.id
        assert kyc_app.current_step == "personal_info"
        assert kyc_app.personal_info_complete is False
        assert kyc_app.documents_complete is False
        assert kyc_app.biometrics_complete is False

    async def test_get_workflow_status(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test getting workflow status."""
        workflow = KYCWorkflowService(db_session)

        # Start KYC first
        await workflow.start_kyc_application(farmer_id=test_farmer.id)
        await db_session.commit()

        # Get status
        status = await workflow.get_workflow_status(test_farmer.id)

        assert status is not None
        assert status.farmer_id == test_farmer.id
        assert status.current_step == "personal_info"
        assert status.overall_status == "pending"
        assert 0 <= status.progress_percentage <= 100

    async def test_complete_personal_info_step(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test completing the personal info step."""
        workflow = KYCWorkflowService(db_session)

        # Start KYC
        await workflow.start_kyc_application(farmer_id=test_farmer.id)
        await db_session.commit()

        # Complete personal info step
        status = await workflow.complete_step(
            farmer_id=test_farmer.id,
            step=KYCStep.PERSONAL_INFO,
            data={"verified": True},
        )

        assert status.steps["personal_info"]["complete"] is True
        assert status.current_step == "documents"

    async def test_record_document_submission(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test recording a document submission."""
        workflow = KYCWorkflowService(db_session)

        # Start KYC with required documents
        await workflow.start_kyc_application(
            farmer_id=test_farmer.id,
            required_documents=["national_id"],
        )
        await db_session.commit()

        # Complete personal info first
        await workflow.complete_step(
            farmer_id=test_farmer.id,
            step=KYCStep.PERSONAL_INFO,
        )
        await db_session.commit()

        # Record document submission
        doc_id = uuid.uuid4()
        await workflow.record_document_submission(
            farmer_id=test_farmer.id,
            document_type="national_id",
            document_id=doc_id,
        )
        await db_session.commit()

        # Check status
        status = await workflow.get_workflow_status(test_farmer.id)
        assert "national_id" in status.steps["documents"]["submitted"]

    async def test_record_biometric_capture(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test recording a biometric capture."""
        workflow = KYCWorkflowService(db_session)

        # Start KYC with required biometrics
        await workflow.start_kyc_application(
            farmer_id=test_farmer.id,
            required_biometrics=["fingerprint_right_index"],
        )
        await db_session.commit()

        # Record biometric capture
        await workflow.record_biometric_capture(
            farmer_id=test_farmer.id,
            biometric_type="fingerprint_right_index",
        )
        await db_session.commit()

        # Check status
        status = await workflow.get_workflow_status(test_farmer.id)
        assert "fingerprint_right_index" in status.steps["biometrics"]["captured"]

    async def test_submit_for_review(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test submitting application for review."""
        workflow = KYCWorkflowService(db_session)

        # Start KYC with minimal requirements
        await workflow.start_kyc_application(
            farmer_id=test_farmer.id,
            required_documents=[],
            required_biometrics=[],
        )
        await db_session.commit()

        # Complete all steps
        await workflow.complete_step(
            farmer_id=test_farmer.id,
            step=KYCStep.PERSONAL_INFO,
        )
        await workflow.complete_step(
            farmer_id=test_farmer.id,
            step=KYCStep.DOCUMENTS,
        )
        await workflow.complete_step(
            farmer_id=test_farmer.id,
            step=KYCStep.BIOMETRICS,
        )
        await workflow.complete_step(
            farmer_id=test_farmer.id,
            step=KYCStep.BANK_INFO,
        )
        await db_session.commit()

        # Submit for review
        status = await workflow.submit_for_review(test_farmer.id)

        assert status.overall_status in ["in_review", "approved"]
        assert status.submitted_at is not None

    async def test_process_review_decision_approve(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test approving a KYC application."""
        workflow = KYCWorkflowService(db_session)

        # Start and complete KYC
        await workflow.start_kyc_application(
            farmer_id=test_farmer.id,
            required_documents=[],
            required_biometrics=[],
        )
        for step in [
            KYCStep.PERSONAL_INFO,
            KYCStep.DOCUMENTS,
            KYCStep.BIOMETRICS,
            KYCStep.BANK_INFO,
        ]:
            await workflow.complete_step(farmer_id=test_farmer.id, step=step)
        await db_session.commit()

        # Submit for review
        await workflow.submit_for_review(test_farmer.id)
        await db_session.commit()

        # Process approval
        reviewer_id = uuid.uuid4()
        status = await workflow.process_review_decision(
            farmer_id=test_farmer.id,
            decision="approve",
            reviewer_id=reviewer_id,
            notes="All documents verified",
        )

        assert status.overall_status == "approved"

    async def test_process_review_decision_reject(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test rejecting a KYC application."""
        workflow = KYCWorkflowService(db_session)

        # Start and complete KYC
        await workflow.start_kyc_application(
            farmer_id=test_farmer.id,
            required_documents=[],
            required_biometrics=[],
        )
        for step in [
            KYCStep.PERSONAL_INFO,
            KYCStep.DOCUMENTS,
            KYCStep.BIOMETRICS,
            KYCStep.BANK_INFO,
        ]:
            await workflow.complete_step(farmer_id=test_farmer.id, step=step)
        await db_session.commit()

        # Submit for review
        await workflow.submit_for_review(test_farmer.id)
        await db_session.commit()

        # Process rejection
        reviewer_id = uuid.uuid4()
        status = await workflow.process_review_decision(
            farmer_id=test_farmer.id,
            decision="reject",
            reviewer_id=reviewer_id,
            rejection_reason="Invalid documents",
        )

        assert status.overall_status == "rejected"

    async def test_get_review_queue(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test getting the review queue."""
        workflow = KYCWorkflowService(db_session)

        # Add farmer to review queue
        queue_entry = KYCReviewQueue(
            farmer_id=test_farmer.id,
            priority=3,
            reason="Manual review required",
            status="pending",
        )
        db_session.add(queue_entry)
        await db_session.commit()

        # Get queue
        items = await workflow.get_review_queue(status="pending", limit=10)

        assert len(items) >= 1
        assert any(item["farmer_id"] == str(test_farmer.id) for item in items)

    async def test_assign_review(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test assigning a review to a reviewer."""
        workflow = KYCWorkflowService(db_session)

        # Add farmer to review queue
        queue_entry = KYCReviewQueue(
            farmer_id=test_farmer.id,
            priority=3,
            reason="Manual review required",
            status="pending",
        )
        db_session.add(queue_entry)
        await db_session.commit()

        # Assign review
        reviewer_id = uuid.uuid4()
        await workflow.assign_review(test_farmer.id, reviewer_id)
        await db_session.commit()

        # Verify assignment
        await db_session.refresh(queue_entry)
        assert queue_entry.assigned_to == reviewer_id
        assert queue_entry.status == "in_progress"

    async def test_workflow_status_not_found(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting status for non-existent farmer."""
        workflow = KYCWorkflowService(db_session)

        status = await workflow.get_workflow_status(uuid.uuid4())
        assert status is None

    async def test_cannot_complete_step_without_requirements(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test that steps cannot be completed without meeting requirements."""
        workflow = KYCWorkflowService(db_session)

        # Start KYC with required documents
        await workflow.start_kyc_application(
            farmer_id=test_farmer.id,
            required_documents=["national_id"],
        )
        await db_session.commit()

        # Complete personal info first
        await workflow.complete_step(
            farmer_id=test_farmer.id,
            step=KYCStep.PERSONAL_INFO,
        )
        await db_session.commit()

        # Try to complete documents step without submitting required documents
        with pytest.raises(ValueError, match="Missing required documents"):
            await workflow.complete_step(
                farmer_id=test_farmer.id,
                step=KYCStep.DOCUMENTS,
            )

    async def test_missing_documents_tracking(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test tracking of missing documents."""
        workflow = KYCWorkflowService(db_session)

        # Start KYC with required documents
        await workflow.start_kyc_application(
            farmer_id=test_farmer.id,
            required_documents=["national_id", "land_title"],
        )
        await db_session.commit()

        # Get status
        status = await workflow.get_workflow_status(test_farmer.id)

        # Should have 2 missing documents
        assert len(status.missing_documents) == 2
        assert "national_id" in status.missing_documents
        assert "land_title" in status.missing_documents

    async def test_missing_biometrics_tracking(
        self, db_session: AsyncSession, test_farmer: Farmer
    ) -> None:
        """Test tracking of missing biometrics."""
        workflow = KYCWorkflowService(db_session)

        # Start KYC with required biometrics
        await workflow.start_kyc_application(
            farmer_id=test_farmer.id,
            required_biometrics=["fingerprint_right_index", "face"],
        )
        await db_session.commit()

        # Get status
        status = await workflow.get_workflow_status(test_farmer.id)

        # Should have 2 missing biometrics
        assert len(status.missing_biometrics) == 2
        assert "fingerprint_right_index" in status.missing_biometrics
        assert "face" in status.missing_biometrics
