"""Database models."""

from app.models.crop_planning import (
    CropCalendarTemplate,
    CropPlan,
    CropPlanAlert,
    InputRequirement,
    IrrigationSchedule,
    PlannedActivity,
)
from app.models.eligibility import (
    CreditBureauProvider,
    CreditCheck,
    EligibilityAssessment,
    EligibilityNotification,
    EligibilityReviewQueue,
    EligibilityRule,
    EligibilityRuleGroup,
    EligibilityScheme,
    RiskAssessment,
    RiskFactor,
    SchemeWaitlist,
)
from app.models.farmer import (
    BiometricData,
    CropRecord,
    Document,
    ExternalVerification,
    FarmAsset,
    FarmDocument,
    Farmer,
    FarmProfile,
    FieldVisit,
    KYCApplication,
    KYCReviewQueue,
    SoilTestReport,
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
    # Crop Planning models
    "CropCalendarTemplate",
    "CropPlan",
    "PlannedActivity",
    "InputRequirement",
    "IrrigationSchedule",
    "CropPlanAlert",
]
