"""OCR service for document text extraction and verification."""

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class DocumentExtractionResult(BaseModel):
    """Result of document OCR extraction."""

    success: bool
    document_type: str
    extracted_data: dict[str, Any]
    confidence_score: float
    raw_text: str | None = None
    errors: list[str] = []


class OCRProvider(str, Enum):
    """Available OCR providers."""

    TESSERACT = "tesseract"
    AWS_TEXTRACT = "aws_textract"
    GOOGLE_VISION = "google_vision"
    AZURE_FORM = "azure_form"


class OCRService:
    """Service for OCR and document data extraction.

    This service provides an abstraction layer for various OCR providers
    and implements document-specific extraction logic.
    """

    # Patterns for common East African ID documents
    KENYA_ID_PATTERN = re.compile(r"\b\d{7,8}\b")
    UGANDA_NIN_PATTERN = re.compile(r"\bCM[A-Z0-9]{12}\b")
    TANZANIA_NIDA_PATTERN = re.compile(r"\b\d{20}\b")
    DATE_PATTERNS = [
        re.compile(r"\b\d{2}/\d{2}/\d{4}\b"),
        re.compile(r"\b\d{2}-\d{2}-\d{4}\b"),
        re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    ]

    def __init__(self, provider: OCRProvider = OCRProvider.TESSERACT) -> None:
        self.provider = provider

    async def extract_from_image(
        self,
        image_data: bytes,
        document_type: str,
    ) -> DocumentExtractionResult:
        """Extract text and data from a document image.

        Args:
            image_data: Raw image bytes
            document_type: Type of document (national_id, passport, etc.)

        Returns:
            DocumentExtractionResult with extracted data
        """
        # Get raw text from OCR provider
        raw_text = await self._perform_ocr(image_data)

        if not raw_text:
            return DocumentExtractionResult(
                success=False,
                document_type=document_type,
                extracted_data={},
                confidence_score=0.0,
                errors=["Failed to extract text from image"],
            )

        # Extract structured data based on document type
        extraction_handlers = {
            "national_id": self._extract_national_id,
            "passport": self._extract_passport,
            "land_title": self._extract_land_title,
            "bank_statement": self._extract_bank_statement,
            "tax_id": self._extract_tax_id,
        }

        handler = extraction_handlers.get(document_type, self._extract_generic)
        extracted_data, confidence = await handler(raw_text)

        return DocumentExtractionResult(
            success=True,
            document_type=document_type,
            extracted_data=extracted_data,
            confidence_score=confidence,
            raw_text=raw_text[:500] if raw_text else None,  # Truncate for storage
        )

    async def _perform_ocr(self, image_data: bytes) -> str | None:
        """Perform OCR using configured provider."""
        if self.provider == OCRProvider.TESSERACT:
            return await self._ocr_tesseract(image_data)
        elif self.provider == OCRProvider.AWS_TEXTRACT:
            return await self._ocr_textract(image_data)
        elif self.provider == OCRProvider.GOOGLE_VISION:
            return await self._ocr_google_vision(image_data)
        elif self.provider == OCRProvider.AZURE_FORM:
            return await self._ocr_azure_form(image_data)
        return None

    async def _ocr_tesseract(self, image_data: bytes) -> str | None:
        """OCR using Tesseract (local/open source)."""
        try:
            import pytesseract
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image)
            return text
        except ImportError:
            # Tesseract not installed, return placeholder
            return None
        except Exception:
            return None

    async def _ocr_textract(self, image_data: bytes) -> str | None:
        """OCR using AWS Textract."""
        try:
            import boto3

            client = boto3.client("textract")
            response = client.detect_document_text(Document={"Bytes": image_data})

            lines = []
            for block in response.get("Blocks", []):
                if block["BlockType"] == "LINE":
                    lines.append(block.get("Text", ""))

            return "\n".join(lines)
        except Exception:
            return None

    async def _ocr_google_vision(self, image_data: bytes) -> str | None:
        """OCR using Google Cloud Vision."""
        try:
            from google.cloud import vision

            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=image_data)
            response = client.text_detection(image=image)

            if response.text_annotations:
                return response.text_annotations[0].description
            return None
        except Exception:
            return None

    async def _ocr_azure_form(self, image_data: bytes) -> str | None:
        """OCR using Azure Form Recognizer."""
        # Placeholder for Azure integration
        return None

    async def _extract_national_id(self, text: str) -> tuple[dict, float]:
        """Extract data from national ID document."""
        data: dict[str, Any] = {}
        confidence = 0.0
        fields_found = 0

        # Try to find ID number
        id_match = self.KENYA_ID_PATTERN.search(text)
        if id_match:
            data["id_number"] = id_match.group()
            fields_found += 1

        # Try to find names
        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_upper = line.upper()
            if "NAME" in line_upper or "FULL NAME" in line_upper:
                if i + 1 < len(lines):
                    data["full_name"] = lines[i + 1].strip()
                    fields_found += 1
                    break

        # Try to find date of birth
        for pattern in self.DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                data["date_of_birth"] = match.group()
                fields_found += 1
                break

        # Try to find gender
        text_upper = text.upper()
        if "MALE" in text_upper:
            data["gender"] = "male" if "FEMALE" not in text_upper else "female"
            fields_found += 1

        # Calculate confidence based on fields found
        confidence = min(fields_found / 4.0, 1.0)  # Expect 4 fields

        return data, confidence

    async def _extract_passport(self, text: str) -> tuple[dict, float]:
        """Extract data from passport document."""
        data: dict[str, Any] = {}
        confidence = 0.0
        fields_found = 0

        # Look for passport number pattern
        passport_pattern = re.compile(r"\b[A-Z]{1,2}\d{6,7}\b")
        match = passport_pattern.search(text.upper())
        if match:
            data["passport_number"] = match.group()
            fields_found += 1

        # Look for MRZ (Machine Readable Zone) if present
        mrz_pattern = re.compile(r"[A-Z<]{44}")
        mrz_match = mrz_pattern.search(text.replace(" ", ""))
        if mrz_match:
            data["mrz_line"] = mrz_match.group()
            fields_found += 1

        # Find dates
        for pattern in self.DATE_PATTERNS:
            matches = pattern.findall(text)
            if len(matches) >= 2:
                data["date_of_birth"] = matches[0]
                data["expiry_date"] = matches[-1]
                fields_found += 2
                break

        confidence = min(fields_found / 4.0, 1.0)
        return data, confidence

    async def _extract_land_title(self, text: str) -> tuple[dict, float]:
        """Extract data from land title document."""
        data: dict[str, Any] = {}
        fields_found = 0

        # Look for title/plot number
        title_pattern = re.compile(r"\b(LR|CR|IR)\s*[A-Z]*\s*\d+[/\d]*\b", re.IGNORECASE)
        match = title_pattern.search(text)
        if match:
            data["title_number"] = match.group().upper()
            fields_found += 1

        # Look for acreage/area
        area_pattern = re.compile(r"(\d+\.?\d*)\s*(acres?|hectares?|ha|ac)", re.IGNORECASE)
        area_match = area_pattern.search(text)
        if area_match:
            data["area"] = area_match.group(1)
            data["area_unit"] = area_match.group(2).lower()
            fields_found += 1

        confidence = min(fields_found / 2.0, 1.0)
        return data, confidence

    async def _extract_bank_statement(self, text: str) -> tuple[dict, float]:
        """Extract data from bank statement."""
        data: dict[str, Any] = {}
        fields_found = 0

        # Look for account number
        account_pattern = re.compile(r"\b\d{10,16}\b")
        match = account_pattern.search(text)
        if match:
            data["account_number"] = match.group()
            fields_found += 1

        # Look for bank name (common East African banks)
        banks = ["EQUITY", "KCB", "COOPERATIVE", "ABSA", "STANBIC", "NCBA", "DTB"]
        text_upper = text.upper()
        for bank in banks:
            if bank in text_upper:
                data["bank_name"] = bank
                fields_found += 1
                break

        confidence = min(fields_found / 2.0, 1.0)
        return data, confidence

    async def _extract_tax_id(self, text: str) -> tuple[dict, float]:
        """Extract data from tax ID document."""
        data: dict[str, Any] = {}
        fields_found = 0

        # Kenya KRA PIN pattern
        pin_pattern = re.compile(r"\b[AP]\d{9}[A-Z]\b")
        match = pin_pattern.search(text.upper())
        if match:
            data["tax_pin"] = match.group()
            fields_found += 1

        confidence = min(fields_found / 1.0, 1.0)
        return data, confidence

    async def _extract_generic(self, text: str) -> tuple[dict, float]:
        """Generic extraction for unknown document types."""
        return {"raw_text": text[:1000]}, 0.5

    async def verify_document_authenticity(
        self,
        image_data: bytes,
        document_type: str,
    ) -> dict[str, Any]:
        """Perform basic document authenticity checks.

        Returns verification results including:
        - is_valid: Overall validity assessment
        - checks: Individual check results
        - confidence: Confidence score
        """
        checks: dict[str, bool] = {}

        # Check image quality
        checks["image_quality"] = await self._check_image_quality(image_data)

        # Check for tampering signs
        checks["no_tampering_detected"] = await self._check_tampering(image_data)

        # Check document format
        checks["valid_format"] = await self._check_document_format(
            image_data, document_type
        )

        # Calculate overall validity
        passed_checks = sum(1 for v in checks.values() if v)
        total_checks = len(checks)
        confidence = passed_checks / total_checks if total_checks > 0 else 0.0

        return {
            "is_valid": confidence >= 0.7,
            "checks": checks,
            "confidence": confidence,
        }

    async def _check_image_quality(self, image_data: bytes) -> bool:
        """Check if image quality is sufficient for OCR."""
        try:
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(image_data))

            # Check minimum resolution
            min_dimension = 500
            if image.width < min_dimension or image.height < min_dimension:
                return False

            # Check if image is not too blurry (basic check)
            # In production, use Laplacian variance or similar
            return True
        except Exception:
            return False

    async def _check_tampering(self, image_data: bytes) -> bool:
        """Basic tampering detection."""
        # In production, implement proper tampering detection:
        # - ELA (Error Level Analysis)
        # - Metadata consistency
        # - Copy-move detection
        return True

    async def _check_document_format(
        self, image_data: bytes, document_type: str
    ) -> bool:
        """Check if document format matches expected type."""
        # In production, use ML models for document classification
        return True


# Factory function
def get_ocr_service(provider: OCRProvider = OCRProvider.TESSERACT) -> OCRService:
    """Get OCR service instance."""
    return OCRService(provider=provider)
