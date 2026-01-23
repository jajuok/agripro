"""Database models."""

from app.models.farmer import (
    Farmer,
    FarmProfile,
    Document,
    BiometricData,
    KYCApplication,
    ExternalVerification,
    KYCReviewQueue,
    FarmDocument,
    FarmAsset,
    CropRecord,
    SoilTestReport,
    FieldVisit,
)
from app.models.eligibility import (
    EligibilityScheme,
    EligibilityRuleGroup,
    EligibilityRule,
    EligibilityAssessment,
    CreditBureauProvider,
    CreditCheck,
    RiskFactor,
    RiskAssessment,
    EligibilityReviewQueue,
    SchemeWaitlist,
    EligibilityNotification,
)

__all__ = [
    # Farmer models
    "Farmer",
    "FarmProfile",
    "Document",
    "BiometricData",
    "KYCApplication",
    "ExternalVerification",
    "KYCReviewQueue",
    "FarmDocument",
    "FarmAsset",
    "CropRecord",
    "SoilTestReport",
    "FieldVisit",
    # Eligibility models
    "EligibilityScheme",
    "EligibilityRuleGroup",
    "EligibilityRule",
    "EligibilityAssessment",
    "CreditBureauProvider",
    "CreditCheck",
    "RiskFactor",
    "RiskAssessment",
    "EligibilityReviewQueue",
    "SchemeWaitlist",
    "EligibilityNotification",
]
