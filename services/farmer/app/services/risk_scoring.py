"""Risk Scoring Service for Eligibility Assessment."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.eligibility import (
    CreditCheck,
    RiskAssessment,
    RiskFactor,
    RiskLevel,
)
from app.models.farmer import Farmer, FarmProfile, CropRecord
from app.schemas.eligibility import RiskFactorScore, RiskAssessmentResponse


class RiskScoringService:
    """Service for calculating risk scores for farmers."""

    # Risk level thresholds (higher score = higher risk)
    RISK_THRESHOLDS = {
        RiskLevel.LOW: (0, 25),
        RiskLevel.MEDIUM: (25, 50),
        RiskLevel.HIGH: (50, 75),
        RiskLevel.VERY_HIGH: (75, 100),
    }

    # Default weights for risk categories
    DEFAULT_CATEGORY_WEIGHTS = {
        "credit": 0.35,
        "performance": 0.25,
        "external": 0.20,
        "fraud": 0.20,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_risk_factors(self, tenant_id: uuid.UUID) -> list[RiskFactor]:
        """Get all active risk factors for a tenant."""
        query = (
            select(RiskFactor)
            .where(RiskFactor.tenant_id == tenant_id)
            .where(RiskFactor.is_active == True)
            .order_by(RiskFactor.category, RiskFactor.name)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def calculate_risk_score(
        self,
        farmer: Farmer,
        farm: FarmProfile | None = None,
        credit_check: CreditCheck | None = None,
        assessment_id: uuid.UUID | None = None,
        external_data: dict | None = None,
    ) -> RiskAssessment:
        """
        Calculate comprehensive risk score for a farmer.

        Returns a RiskAssessment with detailed breakdown.
        """
        factor_scores: list[RiskFactorScore] = []
        category_scores: dict[str, float] = {}

        # Calculate Credit Risk
        credit_risk, credit_factors = self._calculate_credit_risk(credit_check)
        factor_scores.extend(credit_factors)
        category_scores["credit"] = credit_risk

        # Calculate Performance Risk (based on historical data)
        performance_risk, performance_factors = await self._calculate_performance_risk(
            farmer, farm
        )
        factor_scores.extend(performance_factors)
        category_scores["performance"] = performance_risk

        # Calculate External Risk (weather, market, etc.)
        external_risk, external_factors = self._calculate_external_risk(
            farm, external_data
        )
        factor_scores.extend(external_factors)
        category_scores["external"] = external_risk

        # Calculate Fraud Risk
        fraud_risk, fraud_factors, fraud_indicators = self._calculate_fraud_risk(
            farmer, farm, credit_check
        )
        factor_scores.extend(fraud_factors)
        category_scores["fraud"] = fraud_risk

        # Calculate weighted total risk score
        total_risk_score = self._calculate_weighted_total(category_scores)

        # Determine risk level
        risk_level = self._get_risk_level(total_risk_score)

        # Generate risk flags and recommendations
        risk_flags = self._generate_risk_flags(category_scores, factor_scores)
        recommendations = self._generate_recommendations(risk_level, risk_flags)

        # Create risk assessment record
        risk_assessment = RiskAssessment(
            farmer_id=farmer.id,
            assessment_id=assessment_id,
            total_risk_score=total_risk_score,
            risk_level=risk_level.value,
            confidence_score=self._calculate_confidence(factor_scores),
            credit_risk_score=credit_risk,
            performance_risk_score=performance_risk,
            external_risk_score=external_risk,
            fraud_risk_score=fraud_risk,
            factor_scores={
                f.factor_code: {
                    "raw": f.raw_value,
                    "normalized": f.normalized_score,
                    "weight": f.weight,
                    "weighted": f.weighted_score,
                }
                for f in factor_scores
            },
            fraud_indicators=fraud_indicators if fraud_indicators else None,
            risk_flags=risk_flags if risk_flags else None,
            recommendations=recommendations if recommendations else None,
            model_version="1.0.0",
            model_type="rule_based",
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        )

        self.db.add(risk_assessment)
        await self.db.flush()

        return risk_assessment

    def _calculate_credit_risk(
        self, credit_check: CreditCheck | None
    ) -> tuple[float, list[RiskFactorScore]]:
        """Calculate credit-based risk score."""
        factors: list[RiskFactorScore] = []

        if not credit_check or credit_check.credit_score is None:
            # No credit data - assign moderate risk
            return 50.0, [
                RiskFactorScore(
                    factor_code="credit_data_missing",
                    factor_name="Credit Data Missing",
                    raw_value=None,
                    normalized_score=50.0,
                    weight=1.0,
                    weighted_score=50.0,
                    category="credit",
                )
            ]

        # Credit Score Factor (inversed - higher score = lower risk)
        credit_score = credit_check.credit_score
        if credit_score >= 750:
            credit_score_risk = 10
        elif credit_score >= 700:
            credit_score_risk = 25
        elif credit_score >= 650:
            credit_score_risk = 40
        elif credit_score >= 550:
            credit_score_risk = 60
        else:
            credit_score_risk = 80

        factors.append(
            RiskFactorScore(
                factor_code="credit_score",
                factor_name="Credit Score",
                raw_value=credit_score,
                normalized_score=credit_score_risk,
                weight=0.4,
                weighted_score=credit_score_risk * 0.4,
                category="credit",
            )
        )

        # Defaults Factor
        defaults_count = credit_check.defaults_count or 0
        if defaults_count == 0:
            defaults_risk = 0
        elif defaults_count == 1:
            defaults_risk = 50
        else:
            defaults_risk = 90

        factors.append(
            RiskFactorScore(
                factor_code="defaults",
                factor_name="Payment Defaults",
                raw_value=defaults_count,
                normalized_score=defaults_risk,
                weight=0.3,
                weighted_score=defaults_risk * 0.3,
                category="credit",
            )
        )

        # Debt-to-Income Factor
        dti = credit_check.debt_to_income_ratio or 0
        if dti < 20:
            dti_risk = 10
        elif dti < 35:
            dti_risk = 25
        elif dti < 50:
            dti_risk = 50
        elif dti < 70:
            dti_risk = 75
        else:
            dti_risk = 90

        factors.append(
            RiskFactorScore(
                factor_code="debt_to_income",
                factor_name="Debt-to-Income Ratio",
                raw_value=dti,
                normalized_score=dti_risk,
                weight=0.3,
                weighted_score=dti_risk * 0.3,
                category="credit",
            )
        )

        # Calculate category total
        total_credit_risk = sum(f.weighted_score for f in factors)
        return total_credit_risk, factors

    async def _calculate_performance_risk(
        self, farmer: Farmer, farm: FarmProfile | None
    ) -> tuple[float, list[RiskFactorScore]]:
        """Calculate performance-based risk from historical data."""
        factors: list[RiskFactorScore] = []

        # Check KYC status
        kyc_status = farmer.kyc_status
        if kyc_status == "approved":
            kyc_risk = 0
        elif kyc_status == "pending":
            kyc_risk = 40
        elif kyc_status == "in_review":
            kyc_risk = 30
        else:
            kyc_risk = 80

        factors.append(
            RiskFactorScore(
                factor_code="kyc_status",
                factor_name="KYC Verification Status",
                raw_value=kyc_status,
                normalized_score=kyc_risk,
                weight=0.3,
                weighted_score=kyc_risk * 0.3,
                category="performance",
            )
        )

        # Farm verification status
        if farm:
            farm_verified_risk = 10 if farm.is_verified else 50
            factors.append(
                RiskFactorScore(
                    factor_code="farm_verified",
                    factor_name="Farm Verification",
                    raw_value=farm.is_verified,
                    normalized_score=farm_verified_risk,
                    weight=0.3,
                    weighted_score=farm_verified_risk * 0.3,
                    category="performance",
                )
            )

            # Crop history - check for historical yields
            crop_records = await self._get_crop_records(farm.id)
            if crop_records:
                # Calculate yield performance
                yield_performance = self._calculate_yield_performance(crop_records)
                factors.append(
                    RiskFactorScore(
                        factor_code="yield_history",
                        factor_name="Historical Yield Performance",
                        raw_value=yield_performance,
                        normalized_score=max(0, 100 - yield_performance),
                        weight=0.4,
                        weighted_score=max(0, 100 - yield_performance) * 0.4,
                        category="performance",
                    )
                )
            else:
                factors.append(
                    RiskFactorScore(
                        factor_code="no_crop_history",
                        factor_name="No Crop History",
                        raw_value=None,
                        normalized_score=40,
                        weight=0.4,
                        weighted_score=40 * 0.4,
                        category="performance",
                    )
                )
        else:
            factors.append(
                RiskFactorScore(
                    factor_code="no_farm_data",
                    factor_name="No Farm Data",
                    raw_value=None,
                    normalized_score=60,
                    weight=0.7,
                    weighted_score=60 * 0.7,
                    category="performance",
                )
            )

        total_performance_risk = sum(f.weighted_score for f in factors)
        return total_performance_risk, factors

    async def _get_crop_records(self, farm_id: uuid.UUID) -> list[CropRecord]:
        """Get crop records for a farm."""
        query = (
            select(CropRecord)
            .where(CropRecord.farm_id == farm_id)
            .order_by(CropRecord.year.desc())
            .limit(5)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _calculate_yield_performance(self, crop_records: list[CropRecord]) -> float:
        """Calculate yield performance percentage."""
        if not crop_records:
            return 50.0

        performance_scores = []
        for record in crop_records:
            if record.expected_yield_kg and record.actual_yield_kg:
                performance = (record.actual_yield_kg / record.expected_yield_kg) * 100
                performance_scores.append(min(performance, 150))  # Cap at 150%

        if performance_scores:
            return sum(performance_scores) / len(performance_scores)
        return 50.0

    def _calculate_external_risk(
        self, farm: FarmProfile | None, external_data: dict | None
    ) -> tuple[float, list[RiskFactorScore]]:
        """Calculate external risk factors (weather, market, etc.)."""
        factors: list[RiskFactorScore] = []
        external_data = external_data or {}

        # Weather risk (would integrate with weather service)
        weather_risk = external_data.get("weather_risk", 30)
        factors.append(
            RiskFactorScore(
                factor_code="weather_risk",
                factor_name="Weather/Climate Risk",
                raw_value=weather_risk,
                normalized_score=weather_risk,
                weight=0.4,
                weighted_score=weather_risk * 0.4,
                category="external",
            )
        )

        # Market risk (would integrate with market service)
        market_risk = external_data.get("market_risk", 25)
        factors.append(
            RiskFactorScore(
                factor_code="market_risk",
                factor_name="Market Price Risk",
                raw_value=market_risk,
                normalized_score=market_risk,
                weight=0.3,
                weighted_score=market_risk * 0.3,
                category="external",
            )
        )

        # Location risk
        if farm:
            # This would be based on historical data for the region
            location_risk = external_data.get("location_risk", 20)
        else:
            location_risk = 40

        factors.append(
            RiskFactorScore(
                factor_code="location_risk",
                factor_name="Geographic/Regional Risk",
                raw_value=location_risk,
                normalized_score=location_risk,
                weight=0.3,
                weighted_score=location_risk * 0.3,
                category="external",
            )
        )

        total_external_risk = sum(f.weighted_score for f in factors)
        return total_external_risk, factors

    def _calculate_fraud_risk(
        self,
        farmer: Farmer,
        farm: FarmProfile | None,
        credit_check: CreditCheck | None,
    ) -> tuple[float, list[RiskFactorScore], list[str]]:
        """Calculate fraud risk indicators."""
        factors: list[RiskFactorScore] = []
        fraud_indicators: list[str] = []

        # Check for identity verification
        identity_risk = 0
        if not farmer.national_id:
            identity_risk += 40
            fraud_indicators.append("Missing national ID")

        if farmer.kyc_status != "approved":
            identity_risk += 20

        factors.append(
            RiskFactorScore(
                factor_code="identity_verification",
                factor_name="Identity Verification",
                raw_value=farmer.national_id is not None,
                normalized_score=identity_risk,
                weight=0.4,
                weighted_score=identity_risk * 0.4,
                category="fraud",
            )
        )

        # Check for data consistency
        consistency_risk = 0
        if farm:
            # Check if farm location matches farmer location
            if farm.county and farmer.county and farm.county != farmer.county:
                # Different counties might be valid, but flag it
                if not self._are_counties_adjacent(farm.county, farmer.county):
                    consistency_risk += 30
                    fraud_indicators.append("Farm location far from farmer residence")

            # Check for unusually large land claims
            if farm.total_acreage and farm.total_acreage > 100:
                consistency_risk += 20
                fraud_indicators.append("Unusually large land claim")

        factors.append(
            RiskFactorScore(
                factor_code="data_consistency",
                factor_name="Data Consistency",
                raw_value=None,
                normalized_score=consistency_risk,
                weight=0.3,
                weighted_score=consistency_risk * 0.3,
                category="fraud",
            )
        )

        # Check for duplicate patterns (simplified)
        duplicate_risk = 0  # Would check against database
        factors.append(
            RiskFactorScore(
                factor_code="duplicate_check",
                factor_name="Duplicate Detection",
                raw_value=None,
                normalized_score=duplicate_risk,
                weight=0.3,
                weighted_score=duplicate_risk * 0.3,
                category="fraud",
            )
        )

        total_fraud_risk = sum(f.weighted_score for f in factors)
        return total_fraud_risk, factors, fraud_indicators

    def _are_counties_adjacent(self, county1: str, county2: str) -> bool:
        """Check if two counties are adjacent (simplified)."""
        # This would use actual geographic data
        # For now, return True to avoid false positives
        return True

    def _calculate_weighted_total(self, category_scores: dict[str, float]) -> float:
        """Calculate weighted total risk score."""
        total = 0.0
        for category, score in category_scores.items():
            weight = self.DEFAULT_CATEGORY_WEIGHTS.get(category, 0.25)
            total += score * weight
        return min(100, max(0, total))

    def _get_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score."""
        for level, (min_score, max_score) in self.RISK_THRESHOLDS.items():
            if min_score <= score < max_score:
                return level
        return RiskLevel.VERY_HIGH

    def _calculate_confidence(self, factors: list[RiskFactorScore]) -> float:
        """Calculate confidence score based on data availability."""
        # Check how many factors have actual data
        factors_with_data = sum(1 for f in factors if f.raw_value is not None)
        total_factors = len(factors)

        if total_factors == 0:
            return 0.0

        return (factors_with_data / total_factors) * 100

    def _generate_risk_flags(
        self, category_scores: dict[str, float], factors: list[RiskFactorScore]
    ) -> list[str]:
        """Generate risk flags for high-risk areas."""
        flags = []

        # Category-level flags
        for category, score in category_scores.items():
            if score >= 60:
                flags.append(f"High {category} risk ({score:.1f})")

        # Factor-level flags
        for factor in factors:
            if factor.normalized_score >= 70:
                flags.append(f"High risk: {factor.factor_name}")

        return flags

    def _generate_recommendations(
        self, risk_level: RiskLevel, risk_flags: list[str]
    ) -> list[str]:
        """Generate recommendations based on risk assessment."""
        recommendations = []

        if risk_level == RiskLevel.LOW:
            recommendations.append("Suitable for standard processing")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Consider additional verification")
            recommendations.append("Monitor initial disbursements")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Requires manual review")
            recommendations.append("Request additional documentation")
            recommendations.append("Consider reduced benefit amount")
        else:  # VERY_HIGH
            recommendations.append("High-risk case - escalate for review")
            recommendations.append("Verify all documentation thoroughly")
            recommendations.append("Consider rejection or waitlisting")

        return recommendations

    async def get_recent_risk_assessment(
        self, farmer_id: uuid.UUID, max_age_days: int = 30
    ) -> RiskAssessment | None:
        """Get the most recent valid risk assessment."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        query = (
            select(RiskAssessment)
            .where(RiskAssessment.farmer_id == farmer_id)
            .where(RiskAssessment.assessed_at >= cutoff_date)
            .order_by(RiskAssessment.assessed_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_farmer_risk_history(
        self, farmer_id: uuid.UUID, limit: int = 10
    ) -> list[RiskAssessment]:
        """Get risk assessment history for a farmer."""
        query = (
            select(RiskAssessment)
            .where(RiskAssessment.farmer_id == farmer_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
