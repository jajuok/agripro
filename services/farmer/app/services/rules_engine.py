"""Rules Engine Service for Eligibility Assessment."""

import json
import re
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.eligibility import (
    EligibilityRule,
    EligibilityRuleGroup,
    EligibilityScheme,
    RuleOperator,
    RuleFieldType,
)
from app.models.farmer import Farmer, FarmProfile, CropRecord
from app.schemas.eligibility import RuleEvaluationResult


class RulesEngine:
    """Configurable rules engine for eligibility evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_scheme_rules(
        self, scheme_id: UUID, active_only: bool = True
    ) -> list[EligibilityRule]:
        """Get all rules for a scheme."""
        query = select(EligibilityRule).where(EligibilityRule.scheme_id == scheme_id)
        if active_only:
            query = query.where(EligibilityRule.is_active == True)
        query = query.order_by(EligibilityRule.priority)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_scheme_rule_groups(
        self, scheme_id: UUID, active_only: bool = True
    ) -> list[EligibilityRuleGroup]:
        """Get all rule groups for a scheme with their rules."""
        query = (
            select(EligibilityRuleGroup)
            .options(selectinload(EligibilityRuleGroup.rules))
            .where(EligibilityRuleGroup.scheme_id == scheme_id)
        )
        if active_only:
            query = query.where(EligibilityRuleGroup.is_active == True)
        query = query.order_by(EligibilityRuleGroup.priority)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def evaluate_farmer(
        self,
        farmer: Farmer,
        scheme_id: UUID,
        farm: FarmProfile | None = None,
        credit_data: dict | None = None,
        additional_data: dict | None = None,
    ) -> tuple[list[RuleEvaluationResult], float, bool]:
        """
        Evaluate a farmer against all scheme rules.

        Returns:
            tuple: (rule_results, eligibility_score, mandatory_rules_passed)
        """
        # Get all rules for the scheme
        rules = await self.get_scheme_rules(scheme_id)

        if not rules:
            return [], 100.0, True

        # Build data context for evaluation
        context = self._build_evaluation_context(farmer, farm, credit_data, additional_data)

        # Evaluate each rule
        results: list[RuleEvaluationResult] = []
        total_weight = 0.0
        weighted_score = 0.0
        mandatory_passed = True

        for rule in rules:
            result = self._evaluate_rule(rule, context)
            results.append(result)

            # Update scoring
            total_weight += rule.weight
            if result.passed:
                weighted_score += rule.weight * 100
            elif rule.is_mandatory:
                mandatory_passed = False

        # Calculate final eligibility score
        eligibility_score = (weighted_score / total_weight) if total_weight > 0 else 0.0

        return results, eligibility_score, mandatory_passed

    async def evaluate_rule_groups(
        self,
        farmer: Farmer,
        scheme_id: UUID,
        farm: FarmProfile | None = None,
        credit_data: dict | None = None,
        additional_data: dict | None = None,
    ) -> tuple[list[RuleEvaluationResult], float, bool]:
        """
        Evaluate rules organized by groups with AND/OR logic.

        Returns:
            tuple: (rule_results, eligibility_score, mandatory_rules_passed)
        """
        rule_groups = await self.get_scheme_rule_groups(scheme_id)

        if not rule_groups:
            # Fall back to ungrouped rules
            return await self.evaluate_farmer(farmer, scheme_id, farm, credit_data, additional_data)

        context = self._build_evaluation_context(farmer, farm, credit_data, additional_data)

        all_results: list[RuleEvaluationResult] = []
        total_weight = 0.0
        weighted_score = 0.0
        mandatory_passed = True

        for group in rule_groups:
            group_results = []
            for rule in group.rules:
                if not rule.is_active:
                    continue
                result = self._evaluate_rule(rule, context)
                group_results.append(result)
                all_results.append(result)

            # Evaluate group based on logic operator
            if group.logic_operator.upper() == "AND":
                group_passed = all(r.passed for r in group_results) if group_results else True
            else:  # OR
                group_passed = any(r.passed for r in group_results) if group_results else True

            # Update scoring
            total_weight += group.weight
            if group_passed:
                weighted_score += group.weight * 100
            elif group.is_mandatory:
                mandatory_passed = False

        eligibility_score = (weighted_score / total_weight) if total_weight > 0 else 0.0

        return all_results, eligibility_score, mandatory_passed

    def _build_evaluation_context(
        self,
        farmer: Farmer,
        farm: FarmProfile | None = None,
        credit_data: dict | None = None,
        additional_data: dict | None = None,
    ) -> dict[str, Any]:
        """Build the data context for rule evaluation."""
        context = {
            "farmer": {
                "id": str(farmer.id),
                "first_name": farmer.first_name,
                "last_name": farmer.last_name,
                "gender": farmer.gender,
                "date_of_birth": farmer.date_of_birth,
                "national_id": farmer.national_id,
                "phone_number": farmer.phone_number,
                "email": farmer.email,
                "county": farmer.county,
                "sub_county": farmer.sub_county,
                "ward": farmer.ward,
                "village": farmer.village,
                "is_active": farmer.is_active,
            },
            "kyc": {
                "status": farmer.kyc_status,
                "verified_at": farmer.kyc_verified_at,
                "has_bank_account": bool(farmer.bank_account),
                "has_mobile_money": bool(farmer.mobile_money_number),
            },
            "location": {
                "county": farmer.county,
                "sub_county": farmer.sub_county,
                "ward": farmer.ward,
            },
            "credit": credit_data or {},
            "custom": additional_data or {},
        }

        # Add farm data if available
        if farm:
            context["farm"] = {
                "id": str(farm.id),
                "name": farm.name,
                "total_acreage": farm.total_acreage,
                "cultivable_acreage": farm.cultivable_acreage,
                "ownership_type": farm.ownership_type,
                "latitude": farm.latitude,
                "longitude": farm.longitude,
                "county": farm.county,
                "sub_county": farm.sub_county,
                "soil_type": farm.soil_type,
                "soil_ph": farm.soil_ph,
                "water_source": farm.water_source,
                "irrigation_type": farm.irrigation_type,
                "has_year_round_water": farm.has_year_round_water,
                "is_verified": farm.is_verified,
                "registration_complete": farm.registration_complete,
            }
            context["location"]["latitude"] = farm.latitude
            context["location"]["longitude"] = farm.longitude
        else:
            context["farm"] = {}

        return context

    def _evaluate_rule(
        self, rule: EligibilityRule, context: dict[str, Any]
    ) -> RuleEvaluationResult:
        """Evaluate a single rule against the context."""
        # Get the actual value from context
        actual_value = self._get_value_from_context(
            context, rule.field_type, rule.field_name, rule.field_path
        )

        # Parse the expected value
        expected_value = self._parse_value(rule.value, rule.value_type)

        # Evaluate the comparison
        passed = self._compare_values(actual_value, expected_value, rule.operator)

        # Handle exclusion rules (if match = exclude)
        if rule.is_exclusion:
            passed = not passed

        # Determine message
        if passed:
            message = rule.pass_message or f"Rule '{rule.name}' passed"
        else:
            message = rule.fail_message or f"Rule '{rule.name}' failed"

        return RuleEvaluationResult(
            rule_id=rule.id,
            rule_name=rule.name,
            passed=passed,
            actual_value=str(actual_value) if actual_value is not None else None,
            expected_value=str(expected_value) if expected_value is not None else None,
            message=message,
            is_mandatory=rule.is_mandatory,
            weight=rule.weight,
        )

    def _get_value_from_context(
        self,
        context: dict[str, Any],
        field_type: str,
        field_name: str,
        field_path: str | None = None,
    ) -> Any:
        """Extract a value from the evaluation context."""
        # Get the section based on field type
        section = context.get(field_type.lower(), {})

        if not section:
            return None

        # If field_path is provided, use it for nested access
        if field_path:
            return self._get_nested_value(section, field_path)

        # Otherwise use direct field name
        return section.get(field_name)

    def _get_nested_value(self, data: dict, path: str) -> Any:
        """Get a nested value using dot notation path."""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                idx = int(key)
                value = value[idx] if idx < len(value) else None
            else:
                return None
            if value is None:
                return None
        return value

    def _parse_value(self, value: str | None, value_type: str) -> Any:
        """Parse the rule value based on its type."""
        if value is None:
            return None

        try:
            if value_type == "number":
                return float(value)
            elif value_type == "integer":
                return int(value)
            elif value_type == "boolean":
                return value.lower() in ("true", "1", "yes")
            elif value_type == "array":
                return json.loads(value)
            elif value_type == "date":
                return datetime.fromisoformat(value)
            elif value_type == "json":
                return json.loads(value)
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            return value

    def _compare_values(
        self, actual: Any, expected: Any, operator: str
    ) -> bool:
        """Compare two values using the specified operator."""
        op = operator.lower()

        # Handle null checks first
        if op == "is_null":
            return actual is None
        if op == "is_not_null":
            return actual is not None

        # If actual is None and we're not doing null check, rule fails
        if actual is None:
            return False

        try:
            if op == "equals":
                return self._normalize_for_comparison(actual) == self._normalize_for_comparison(expected)
            elif op == "not_equals":
                return self._normalize_for_comparison(actual) != self._normalize_for_comparison(expected)
            elif op == "greater_than":
                return float(actual) > float(expected)
            elif op == "greater_than_or_equal":
                return float(actual) >= float(expected)
            elif op == "less_than":
                return float(actual) < float(expected)
            elif op == "less_than_or_equal":
                return float(actual) <= float(expected)
            elif op == "in_list":
                expected_list = expected if isinstance(expected, list) else [expected]
                return self._normalize_for_comparison(actual) in [
                    self._normalize_for_comparison(e) for e in expected_list
                ]
            elif op == "not_in_list":
                expected_list = expected if isinstance(expected, list) else [expected]
                return self._normalize_for_comparison(actual) not in [
                    self._normalize_for_comparison(e) for e in expected_list
                ]
            elif op == "contains":
                return str(expected).lower() in str(actual).lower()
            elif op == "not_contains":
                return str(expected).lower() not in str(actual).lower()
            elif op == "between":
                if isinstance(expected, list) and len(expected) == 2:
                    return float(expected[0]) <= float(actual) <= float(expected[1])
                return False
            elif op == "regex_match":
                return bool(re.match(str(expected), str(actual), re.IGNORECASE))
            else:
                return False
        except (ValueError, TypeError):
            return False

    def _normalize_for_comparison(self, value: Any) -> Any:
        """Normalize values for comparison."""
        if isinstance(value, str):
            return value.lower().strip()
        return value


# =============================================================================
# Rule Builder Helper Functions
# =============================================================================


def create_land_size_rule(
    scheme_id: UUID,
    min_acreage: float | None = None,
    max_acreage: float | None = None,
    is_mandatory: bool = True,
) -> dict:
    """Helper to create a land size eligibility rule."""
    if min_acreage is not None and max_acreage is not None:
        return {
            "scheme_id": scheme_id,
            "name": f"Land Size ({min_acreage}-{max_acreage} acres)",
            "description": f"Farm must be between {min_acreage} and {max_acreage} acres",
            "field_type": RuleFieldType.FARM.value,
            "field_name": "total_acreage",
            "operator": RuleOperator.BETWEEN.value,
            "value": json.dumps([min_acreage, max_acreage]),
            "value_type": "array",
            "is_mandatory": is_mandatory,
            "fail_message": f"Farm size must be between {min_acreage} and {max_acreage} acres",
        }
    elif min_acreage is not None:
        return {
            "scheme_id": scheme_id,
            "name": f"Minimum Land Size ({min_acreage} acres)",
            "description": f"Farm must be at least {min_acreage} acres",
            "field_type": RuleFieldType.FARM.value,
            "field_name": "total_acreage",
            "operator": RuleOperator.GREATER_THAN_OR_EQUAL.value,
            "value": str(min_acreage),
            "value_type": "number",
            "is_mandatory": is_mandatory,
            "fail_message": f"Farm size must be at least {min_acreage} acres",
        }
    else:
        return {
            "scheme_id": scheme_id,
            "name": f"Maximum Land Size ({max_acreage} acres)",
            "description": f"Farm must be at most {max_acreage} acres",
            "field_type": RuleFieldType.FARM.value,
            "field_name": "total_acreage",
            "operator": RuleOperator.LESS_THAN_OR_EQUAL.value,
            "value": str(max_acreage),
            "value_type": "number",
            "is_mandatory": is_mandatory,
            "fail_message": f"Farm size must be at most {max_acreage} acres",
        }


def create_kyc_status_rule(
    scheme_id: UUID,
    required_status: str = "approved",
    is_mandatory: bool = True,
) -> dict:
    """Helper to create a KYC status eligibility rule."""
    return {
        "scheme_id": scheme_id,
        "name": "KYC Verification Required",
        "description": f"Farmer must have KYC status: {required_status}",
        "field_type": RuleFieldType.KYC.value,
        "field_name": "status",
        "operator": RuleOperator.EQUALS.value,
        "value": required_status,
        "value_type": "string",
        "is_mandatory": is_mandatory,
        "fail_message": "KYC verification is required",
    }


def create_location_rule(
    scheme_id: UUID,
    allowed_counties: list[str],
    is_mandatory: bool = True,
) -> dict:
    """Helper to create a location eligibility rule."""
    return {
        "scheme_id": scheme_id,
        "name": "Eligible Counties",
        "description": f"Farm must be in: {', '.join(allowed_counties)}",
        "field_type": RuleFieldType.LOCATION.value,
        "field_name": "county",
        "operator": RuleOperator.IN_LIST.value,
        "value": json.dumps(allowed_counties),
        "value_type": "array",
        "is_mandatory": is_mandatory,
        "fail_message": f"Farm must be located in one of: {', '.join(allowed_counties)}",
    }


def create_credit_score_rule(
    scheme_id: UUID,
    min_score: int,
    is_mandatory: bool = False,
    weight: float = 1.0,
) -> dict:
    """Helper to create a credit score eligibility rule."""
    return {
        "scheme_id": scheme_id,
        "name": f"Minimum Credit Score ({min_score})",
        "description": f"Credit score must be at least {min_score}",
        "field_type": RuleFieldType.CREDIT.value,
        "field_name": "credit_score",
        "operator": RuleOperator.GREATER_THAN_OR_EQUAL.value,
        "value": str(min_score),
        "value_type": "number",
        "is_mandatory": is_mandatory,
        "weight": weight,
        "fail_message": f"Credit score must be at least {min_score}",
    }
