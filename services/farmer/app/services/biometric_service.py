"""Biometric capture and verification service."""

import hashlib
import secrets
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import BiometricData


class BiometricType(str, Enum):
    """Types of biometric data."""

    FINGERPRINT = "fingerprint"
    FACE = "face"
    VOICE = "voice"


class FingerPosition(str, Enum):
    """Finger positions for fingerprint capture."""

    RIGHT_THUMB = "right_thumb"
    RIGHT_INDEX = "right_index"
    RIGHT_MIDDLE = "right_middle"
    RIGHT_RING = "right_ring"
    LEFT_THUMB = "left_thumb"
    LEFT_INDEX = "left_index"
    LEFT_MIDDLE = "left_middle"
    LEFT_RING = "left_ring"


class BiometricCaptureResult(BaseModel):
    """Result of biometric capture operation."""

    success: bool
    biometric_id: UUID | None = None
    biometric_type: str
    quality_score: float
    is_duplicate: bool = False
    duplicate_farmer_id: UUID | None = None
    errors: list[str] = []


class BiometricVerifyResult(BaseModel):
    """Result of biometric verification."""

    match: bool
    confidence: float
    farmer_id: UUID | None = None


class LivenessCheckResult(BaseModel):
    """Result of liveness detection."""

    is_live: bool
    confidence: float
    method: str


class BiometricService:
    """Service for biometric capture, storage, and verification.

    This service provides abstraction for various biometric SDKs and
    implements deduplication, liveness detection, and quality scoring.
    """

    # Minimum quality thresholds
    MIN_FINGERPRINT_QUALITY = 40.0  # NFIQ score threshold
    MIN_FACE_QUALITY = 0.7
    MIN_LIVENESS_CONFIDENCE = 0.8

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def capture_fingerprint(
        self,
        farmer_id: UUID,
        finger_position: FingerPosition,
        template_data: bytes,
        image_data: bytes | None = None,
        capture_device: str | None = None,
        capture_location: dict | None = None,
    ) -> BiometricCaptureResult:
        """Capture and store fingerprint biometric.

        Args:
            farmer_id: The farmer's UUID
            finger_position: Which finger was captured
            template_data: The fingerprint template (ISO/ANSI format)
            image_data: Optional raw fingerprint image
            capture_device: Device identifier used for capture
            capture_location: GPS coordinates of capture

        Returns:
            BiometricCaptureResult with status and any errors
        """
        errors: list[str] = []

        # Check quality
        quality_score = await self._assess_fingerprint_quality(template_data)
        if quality_score < self.MIN_FINGERPRINT_QUALITY:
            return BiometricCaptureResult(
                success=False,
                biometric_type=BiometricType.FINGERPRINT,
                quality_score=quality_score,
                errors=[
                    f"Quality score {quality_score:.1f} below minimum {self.MIN_FINGERPRINT_QUALITY}"
                ],
            )

        # Check for duplicates across all farmers
        duplicate_check = await self._check_fingerprint_duplicate(
            template_data, exclude_farmer_id=farmer_id
        )
        if duplicate_check["is_duplicate"]:
            return BiometricCaptureResult(
                success=False,
                biometric_type=BiometricType.FINGERPRINT,
                quality_score=quality_score,
                is_duplicate=True,
                duplicate_farmer_id=duplicate_check.get("farmer_id"),
                errors=["Duplicate fingerprint detected"],
            )

        # Generate secure template hash for storage
        template_hash = self._generate_template_hash(template_data)

        # Store biometric data
        biometric = BiometricData(
            farmer_id=farmer_id,
            biometric_type=f"{BiometricType.FINGERPRINT}_{finger_position.value}",
            template_hash=template_hash,
            quality_score=quality_score,
            capture_device=capture_device,
            capture_location=capture_location,
            is_primary=finger_position == FingerPosition.RIGHT_INDEX,
        )
        self.db.add(biometric)
        await self.db.flush()

        return BiometricCaptureResult(
            success=True,
            biometric_id=biometric.id,
            biometric_type=BiometricType.FINGERPRINT,
            quality_score=quality_score,
        )

    async def capture_face(
        self,
        farmer_id: UUID,
        image_data: bytes,
        capture_device: str | None = None,
        capture_location: dict | None = None,
    ) -> BiometricCaptureResult:
        """Capture and store facial biometric.

        Args:
            farmer_id: The farmer's UUID
            image_data: The face image
            capture_device: Device identifier
            capture_location: GPS coordinates

        Returns:
            BiometricCaptureResult with status
        """
        errors: list[str] = []

        # Perform liveness detection
        liveness = await self.check_face_liveness(image_data)
        if not liveness.is_live:
            return BiometricCaptureResult(
                success=False,
                biometric_type=BiometricType.FACE,
                quality_score=0.0,
                errors=["Liveness check failed - possible spoofing detected"],
            )

        # Assess quality
        quality_score = await self._assess_face_quality(image_data)
        if quality_score < self.MIN_FACE_QUALITY:
            return BiometricCaptureResult(
                success=False,
                biometric_type=BiometricType.FACE,
                quality_score=quality_score,
                errors=[f"Face quality {quality_score:.2f} below minimum {self.MIN_FACE_QUALITY}"],
            )

        # Generate face template/embedding
        template_data = await self._generate_face_template(image_data)

        # Check for duplicates
        duplicate_check = await self._check_face_duplicate(
            template_data, exclude_farmer_id=farmer_id
        )
        if duplicate_check["is_duplicate"]:
            return BiometricCaptureResult(
                success=False,
                biometric_type=BiometricType.FACE,
                quality_score=quality_score,
                is_duplicate=True,
                duplicate_farmer_id=duplicate_check.get("farmer_id"),
                errors=["Duplicate face detected"],
            )

        # Store
        template_hash = self._generate_template_hash(template_data)
        biometric = BiometricData(
            farmer_id=farmer_id,
            biometric_type=BiometricType.FACE,
            template_hash=template_hash,
            quality_score=quality_score,
            capture_device=capture_device,
            capture_location=capture_location,
            is_primary=True,
        )
        self.db.add(biometric)
        await self.db.flush()

        return BiometricCaptureResult(
            success=True,
            biometric_id=biometric.id,
            biometric_type=BiometricType.FACE,
            quality_score=quality_score,
        )

    async def verify_fingerprint(
        self,
        farmer_id: UUID,
        template_data: bytes,
    ) -> BiometricVerifyResult:
        """Verify a fingerprint against stored template.

        Args:
            farmer_id: The farmer to verify against
            template_data: The fingerprint template to verify

        Returns:
            BiometricVerifyResult with match status
        """
        # Get stored fingerprint templates for this farmer
        result = await self.db.execute(
            select(BiometricData).where(
                BiometricData.farmer_id == farmer_id,
                BiometricData.biometric_type.like(f"{BiometricType.FINGERPRINT}%"),
                BiometricData.is_verified == True,
            )
        )
        stored_biometrics = result.scalars().all()

        if not stored_biometrics:
            return BiometricVerifyResult(match=False, confidence=0.0)

        # Compare against each stored template
        # In production, use actual biometric matching SDK
        for stored in stored_biometrics:
            match_result = await self._compare_fingerprints(template_data, stored.template_hash)
            if match_result["match"]:
                return BiometricVerifyResult(
                    match=True,
                    confidence=match_result["confidence"],
                    farmer_id=farmer_id,
                )

        return BiometricVerifyResult(match=False, confidence=0.0)

    async def verify_face(
        self,
        farmer_id: UUID,
        image_data: bytes,
    ) -> BiometricVerifyResult:
        """Verify a face against stored template."""
        # Check liveness first
        liveness = await self.check_face_liveness(image_data)
        if not liveness.is_live:
            return BiometricVerifyResult(match=False, confidence=0.0)

        # Get stored face template
        result = await self.db.execute(
            select(BiometricData).where(
                BiometricData.farmer_id == farmer_id,
                BiometricData.biometric_type == BiometricType.FACE,
                BiometricData.is_verified == True,
            )
        )
        stored = result.scalar_one_or_none()

        if not stored:
            return BiometricVerifyResult(match=False, confidence=0.0)

        # Generate template from image and compare
        template_data = await self._generate_face_template(image_data)
        match_result = await self._compare_faces(template_data, stored.template_hash)

        return BiometricVerifyResult(
            match=match_result["match"],
            confidence=match_result["confidence"],
            farmer_id=farmer_id if match_result["match"] else None,
        )

    async def identify_by_fingerprint(
        self,
        template_data: bytes,
    ) -> BiometricVerifyResult:
        """Identify a farmer by fingerprint (1:N matching).

        Searches all stored fingerprints to find a match.
        """
        # In production, use specialized 1:N matching service
        # This is a simplified implementation
        result = await self.db.execute(
            select(BiometricData).where(
                BiometricData.biometric_type.like(f"{BiometricType.FINGERPRINT}%"),
                BiometricData.is_verified == True,
            )
        )
        all_biometrics = result.scalars().all()

        for stored in all_biometrics:
            match_result = await self._compare_fingerprints(template_data, stored.template_hash)
            if match_result["match"]:
                return BiometricVerifyResult(
                    match=True,
                    confidence=match_result["confidence"],
                    farmer_id=stored.farmer_id,
                )

        return BiometricVerifyResult(match=False, confidence=0.0)

    async def check_face_liveness(self, image_data: bytes) -> LivenessCheckResult:
        """Check if face image is from a live person.

        Detects:
        - Photo attacks (printed photos)
        - Video replay attacks
        - 3D mask attacks
        """
        # In production, integrate with liveness detection SDK
        # This is a placeholder implementation

        # Perform basic checks
        checks_passed = 0
        total_checks = 3

        # Check 1: Image has sufficient variation (not a flat photo)
        # Check 2: Face has natural texture
        # Check 3: No screen artifacts detected

        # Placeholder: assume live for now
        checks_passed = 3

        confidence = checks_passed / total_checks
        return LivenessCheckResult(
            is_live=confidence >= self.MIN_LIVENESS_CONFIDENCE,
            confidence=confidence,
            method="passive_liveness",
        )

    async def get_farmer_biometrics(self, farmer_id: UUID) -> list[dict]:
        """Get all biometric records for a farmer."""
        result = await self.db.execute(
            select(BiometricData).where(BiometricData.farmer_id == farmer_id)
        )
        biometrics = result.scalars().all()

        return [
            {
                "id": str(b.id),
                "type": b.biometric_type,
                "quality_score": b.quality_score,
                "is_verified": b.is_verified,
                "is_primary": b.is_primary,
                "capture_device": b.capture_device,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in biometrics
        ]

    async def mark_biometric_verified(
        self,
        biometric_id: UUID,
        verified: bool = True,
    ) -> bool:
        """Mark a biometric record as verified."""
        result = await self.db.execute(
            select(BiometricData).where(BiometricData.id == biometric_id)
        )
        biometric = result.scalar_one_or_none()
        if not biometric:
            return False

        biometric.is_verified = verified
        return True

    # Private helper methods

    def _generate_template_hash(self, template_data: bytes) -> str:
        """Generate a secure hash of biometric template.

        In production, this would encrypt the template before hashing.
        """
        salt = secrets.token_bytes(16)
        return hashlib.sha256(salt + template_data).hexdigest()

    async def _assess_fingerprint_quality(self, template_data: bytes) -> float:
        """Assess fingerprint quality using NFIQ or similar."""
        # In production, use NIST NFIQ 2.0 or SDK-specific quality assessment
        # Placeholder: return good quality
        return 75.0

    async def _assess_face_quality(self, image_data: bytes) -> float:
        """Assess face image quality."""
        # In production, check:
        # - Face detection confidence
        # - Pose angle
        # - Lighting conditions
        # - Focus/blur
        # - Occlusion
        return 0.85

    async def _generate_face_template(self, image_data: bytes) -> bytes:
        """Generate face embedding/template from image."""
        # In production, use face recognition SDK (e.g., AWS Rekognition, Face++)
        # Return a placeholder template
        return hashlib.sha256(image_data).digest()

    async def _check_fingerprint_duplicate(
        self,
        template_data: bytes,
        exclude_farmer_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Check if fingerprint exists in database (deduplication)."""
        # In production, use biometric matching for 1:N search
        # Placeholder: no duplicates
        return {"is_duplicate": False, "farmer_id": None}

    async def _check_face_duplicate(
        self,
        template_data: bytes,
        exclude_farmer_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Check if face exists in database (deduplication)."""
        # In production, use face matching for 1:N search
        return {"is_duplicate": False, "farmer_id": None}

    async def _compare_fingerprints(
        self,
        template1: bytes,
        template2_hash: str,
    ) -> dict[str, Any]:
        """Compare two fingerprint templates."""
        # In production, use biometric matching SDK
        # Placeholder
        return {"match": False, "confidence": 0.0}

    async def _compare_faces(
        self,
        template1: bytes,
        template2_hash: str,
    ) -> dict[str, Any]:
        """Compare two face templates."""
        # In production, use face matching SDK
        return {"match": False, "confidence": 0.0}
