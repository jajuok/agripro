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
from app.models.crop_planning import (
    CropCalendarTemplate,
    CropPlan,
    PlannedActivity,
    InputRequirement,
    IrrigationSchedule,
    CropPlanAlert,
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
