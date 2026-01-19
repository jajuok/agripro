"""KYC verification API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.kyc import (
    AssignReviewRequest,
    BiometricCaptureRequest,
    BiometricCaptureResult,
    CompleteStepRequest,
    DocumentVerificationResult,
    ExternalVerificationResult,
    KYCReviewRequest,
    KYCStatusResponse,
    KYCStep,
    ReviewQueueItem,
    StartKYCRequest,
)
from app.services.biometric_service import BiometricService, FingerPosition
from app.services.document_service import DocumentService
from app.services.external_verification_service import ExternalVerificationService
from app.services.kyc_workflow_service import KYCWorkflowService
from app.services.ocr_service import get_ocr_service
from app.services.storage_service import get_storage_service

router = APIRouter()


# KYC Application Management
@router.post("/{farmer_id}/start", response_model=KYCStatusResponse)
async def start_kyc_application(
    farmer_id: UUID,
    request: StartKYCRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> KYCStatusResponse:
    """Start a new KYC application for a farmer."""
    workflow = KYCWorkflowService(db)

    req = request or StartKYCRequest()
    await workflow.start_kyc_application(
        farmer_id=farmer_id,
        required_documents=req.required_documents,
        required_biometrics=req.required_biometrics,
    )
    await db.commit()

    status_response = await workflow.get_workflow_status(farmer_id)
    if not status_response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")

    return _convert_workflow_status(status_response)


@router.get("/{farmer_id}/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> KYCStatusResponse:
    """Get KYC verification status for a farmer."""
    workflow = KYCWorkflowService(db)
    status_response = await workflow.get_workflow_status(farmer_id)

    if not status_response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")

    return _convert_workflow_status(status_response)


@router.post("/{farmer_id}/step/complete", response_model=KYCStatusResponse)
async def complete_kyc_step(
    farmer_id: UUID,
    request: CompleteStepRequest,
    db: AsyncSession = Depends(get_db),
) -> KYCStatusResponse:
    """Complete a KYC step and advance to the next."""
    workflow = KYCWorkflowService(db)

    try:
        status_response = await workflow.complete_step(
            farmer_id=farmer_id,
            step=KYCStep(request.step.value),
            data=request.data,
        )
        await db.commit()
        return _convert_workflow_status(status_response)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{farmer_id}/submit", response_model=KYCStatusResponse)
async def submit_for_kyc_review(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> KYCStatusResponse:
    """Submit farmer profile for KYC review."""
    workflow = KYCWorkflowService(db)

    try:
        status_response = await workflow.submit_for_review(farmer_id)
        await db.commit()
        return _convert_workflow_status(status_response)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{farmer_id}/review", response_model=KYCStatusResponse)
async def review_kyc(
    farmer_id: UUID,
    review: KYCReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> KYCStatusResponse:
    """Review and approve/reject KYC (admin only)."""
    workflow = KYCWorkflowService(db)

    try:
        status_response = await workflow.process_review_decision(
            farmer_id=farmer_id,
            decision=review.action,
            reviewer_id=review.reviewer_id,
            notes=review.notes,
            rejection_reason=review.rejection_reason,
        )
        await db.commit()
        return _convert_workflow_status(status_response)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Document Management
@router.post("/{farmer_id}/documents", response_model=DocumentVerificationResult)
async def upload_document(
    farmer_id: UUID,
    file: Annotated[UploadFile, File()],
    document_type: Annotated[str, Form()],
    document_number: Annotated[str | None, Form()] = None,
    db: AsyncSession = Depends(get_db),
) -> DocumentVerificationResult:
    """Upload a KYC document."""
    doc_service = DocumentService(db)
    workflow = KYCWorkflowService(db)
    storage = get_storage_service()
    ocr = get_ocr_service()

    # Upload to storage
    upload_result = await storage.upload_file(
        file=file,
        folder="kyc_documents",
        farmer_id=farmer_id,
        encrypt=True,
    )

    # Save document record
    doc = await doc_service.upload_document(
        farmer_id=farmer_id,
        document_type=document_type,
        file=file,
        document_number=document_number,
    )

    # Record in workflow
    await workflow.record_document_submission(
        farmer_id=farmer_id,
        document_type=document_type,
        document_id=doc.id,
    )

    # Attempt OCR extraction
    extracted_data = None
    confidence = None
    try:
        await file.seek(0)
        image_data = await file.read()
        extraction = await ocr.extract_from_image(image_data, document_type)
        if extraction.success:
            extracted_data = extraction.extracted_data
            confidence = extraction.confidence_score
    except Exception:
        pass  # OCR is optional

    await db.commit()

    return DocumentVerificationResult(
        document_id=doc.id,
        document_type=document_type,
        is_verified=False,  # Documents need manual verification
        extracted_data=extracted_data,
        confidence_score=confidence,
    )


@router.post("/{farmer_id}/documents/{document_id}/verify")
async def verify_document(
    farmer_id: UUID,
    document_id: UUID,
    verified: bool = True,
    notes: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify a document (admin only)."""
    doc_service = DocumentService(db)

    doc = await doc_service.get_document(document_id)
    if not doc or doc.farmer_id != farmer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Update verification status
    # In a full implementation, update the Document model
    await db.commit()

    return {"document_id": str(document_id), "verified": verified, "notes": notes}


# Biometric Management
@router.post("/{farmer_id}/biometrics/fingerprint", response_model=BiometricCaptureResult)
async def capture_fingerprint(
    farmer_id: UUID,
    template: Annotated[UploadFile, File(description="Fingerprint template file")],
    finger: str = Query(..., description="Finger position (e.g., right_index)"),
    capture_device: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> BiometricCaptureResult:
    """Capture fingerprint biometric."""
    bio_service = BiometricService(db)
    workflow = KYCWorkflowService(db)

    # Read template data
    template_data = await template.read()

    # Validate finger position
    try:
        finger_position = FingerPosition(finger)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid finger position. Valid options: {[f.value for f in FingerPosition]}",
        )

    result = await bio_service.capture_fingerprint(
        farmer_id=farmer_id,
        finger_position=finger_position,
        template_data=template_data,
        capture_device=capture_device,
    )

    if result.success:
        await workflow.record_biometric_capture(
            farmer_id=farmer_id,
            biometric_type=f"fingerprint_{finger}",
        )
        await db.commit()

    return BiometricCaptureResult(
        success=result.success,
        biometric_id=result.biometric_id,
        biometric_type=result.biometric_type,
        quality_score=result.quality_score,
        is_duplicate=result.is_duplicate,
        duplicate_farmer_id=result.duplicate_farmer_id,
        errors=result.errors,
    )


@router.post("/{farmer_id}/biometrics/face", response_model=BiometricCaptureResult)
async def capture_face(
    farmer_id: UUID,
    image: Annotated[UploadFile, File(description="Face image")],
    capture_device: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> BiometricCaptureResult:
    """Capture facial biometric."""
    bio_service = BiometricService(db)
    workflow = KYCWorkflowService(db)

    image_data = await image.read()

    result = await bio_service.capture_face(
        farmer_id=farmer_id,
        image_data=image_data,
        capture_device=capture_device,
    )

    if result.success:
        await workflow.record_biometric_capture(
            farmer_id=farmer_id,
            biometric_type="face",
        )
        await db.commit()

    return BiometricCaptureResult(
        success=result.success,
        biometric_id=result.biometric_id,
        biometric_type=result.biometric_type,
        quality_score=result.quality_score,
        is_duplicate=result.is_duplicate,
        duplicate_farmer_id=result.duplicate_farmer_id,
        errors=result.errors,
    )


@router.post("/{farmer_id}/biometrics/verify")
async def verify_biometric(
    farmer_id: UUID,
    biometric_type: str,
    template: Annotated[UploadFile, File()],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify farmer using biometric."""
    bio_service = BiometricService(db)

    template_data = await template.read()

    if biometric_type.startswith("fingerprint"):
        result = await bio_service.verify_fingerprint(farmer_id, template_data)
    elif biometric_type == "face":
        result = await bio_service.verify_face(farmer_id, template_data)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid biometric type",
        )

    return {
        "match": result.match,
        "confidence": result.confidence,
        "farmer_id": str(result.farmer_id) if result.farmer_id else None,
    }


@router.get("/{farmer_id}/biometrics")
async def get_biometrics(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get all biometric records for a farmer."""
    bio_service = BiometricService(db)
    return await bio_service.get_farmer_biometrics(farmer_id)


# External Verification
@router.post("/{farmer_id}/verify/external", response_model=list[ExternalVerificationResult])
async def run_external_verifications(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ExternalVerificationResult]:
    """Run all external verifications for a farmer."""
    ext_service = ExternalVerificationService(db)

    try:
        results = await ext_service.run_all_verifications(farmer_id)
        await db.commit()

        return [
            ExternalVerificationResult(
                success=r.success,
                verification_type=name,
                is_verified=r.is_verified,
                match_score=r.match_score,
                data=r.data,
                error=r.error,
            )
            for name, r in results.items()
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{farmer_id}/verify/status")
async def get_verification_status(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get status of all external verifications."""
    ext_service = ExternalVerificationService(db)
    return await ext_service.get_verification_status(farmer_id)


# Review Queue Management
@router.get("/review-queue", response_model=list[ReviewQueueItem])
async def get_review_queue(
    queue_status: str = Query("pending", description="Filter by status"),
    assigned_to: UUID | None = None,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ReviewQueueItem]:
    """Get KYC applications in the review queue."""
    workflow = KYCWorkflowService(db)
    items = await workflow.get_review_queue(
        status=queue_status,
        assigned_to=assigned_to,
        limit=limit,
    )

    return [
        ReviewQueueItem(
            queue_id=UUID(item["queue_id"]),
            farmer_id=UUID(item["farmer_id"]),
            farmer_name=item["farmer_name"],
            priority=item["priority"],
            reason=item["reason"],
            queued_at=item["queued_at"],
            assigned_to=UUID(item["assigned_to"]) if item["assigned_to"] else None,
            status=queue_status,
        )
        for item in items
    ]


@router.post("/{farmer_id}/review/assign")
async def assign_review(
    farmer_id: UUID,
    request: AssignReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Assign a KYC review to a reviewer."""
    workflow = KYCWorkflowService(db)
    await workflow.assign_review(farmer_id, request.reviewer_id)
    await db.commit()
    return {"assigned": True, "farmer_id": str(farmer_id), "reviewer_id": str(request.reviewer_id)}


# Helper function to convert workflow status
def _convert_workflow_status(ws) -> KYCStatusResponse:
    """Convert workflow status to response schema."""
    from app.schemas.kyc import BiometricCapture, DocumentSubmission, ExternalVerificationStatus

    # Convert documents
    doc_submissions = []
    if ws.steps.get("documents"):
        submitted = ws.steps["documents"].get("submitted", [])
        required = ws.steps["documents"].get("required_types", [])
        for doc_type in required:
            doc_submissions.append(
                DocumentSubmission(
                    document_type=doc_type,
                    is_submitted=doc_type in submitted,
                    is_verified=False,
                )
            )

    # Convert biometrics
    bio_captures = []
    if ws.steps.get("biometrics"):
        captured = ws.steps["biometrics"].get("captured", [])
        required = ws.steps["biometrics"].get("required_types", [])
        for bio_type in required:
            bio_captures.append(
                BiometricCapture(
                    biometric_type=bio_type,
                    is_captured=bio_type in captured,
                    is_verified=False,
                )
            )

    # Convert verifications
    ext_verifications = [
        ExternalVerificationStatus(
            verification_type=v["type"],
            provider="",
            status=v["status"],
            is_verified=v["is_verified"],
        )
        for v in ws.external_verifications
    ]

    return KYCStatusResponse(
        farmer_id=ws.farmer_id,
        current_step=ws.current_step,
        overall_status=ws.overall_status,
        progress_percentage=ws.progress_percentage,
        personal_info_complete=ws.steps.get("personal_info", {}).get("complete", False),
        documents_complete=ws.steps.get("documents", {}).get("complete", False),
        biometrics_complete=ws.steps.get("biometrics", {}).get("complete", False),
        bank_info_complete=ws.steps.get("bank_info", {}).get("complete", False),
        required_documents=ws.steps.get("documents", {}).get("required_types", []),
        documents_submitted=doc_submissions,
        missing_documents=ws.missing_documents,
        required_biometrics=ws.steps.get("biometrics", {}).get("required_types", []),
        biometrics_captured=bio_captures,
        missing_biometrics=ws.missing_biometrics,
        external_verifications=ext_verifications,
        in_review_queue=ws.in_review_queue,
        submitted_at=ws.submitted_at,
    )
