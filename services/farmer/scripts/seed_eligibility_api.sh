#!/bin/bash
# Seed eligibility schemes and rules for Kenyan agricultural programs via the API
# Usage: bash seed_eligibility_api.sh [BASE_URL]
# Default: http://farmer.213.32.19.116.sslip.io/api/v1/eligibility

BASE_URL="${1:-http://farmer.213.32.19.116.sslip.io/api/v1/eligibility}"
TENANT="00000000-0000-0000-0000-000000000001"
SUCCESS=0
FAIL=0
SKIP=0

create_scheme() {
  local name="$1"
  local json="$2"
  echo -n "  Creating scheme: $name ... "
  response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schemes" \
    -H "Content-Type: application/json" \
    -d "$json" 2>&1)
  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')
  if [ "$http_code" = "201" ]; then
    SCHEME_ID=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
    echo "OK (id=$SCHEME_ID)"
    SUCCESS=$((SUCCESS + 1))
  elif [ "$http_code" = "409" ]; then
    echo "SKIPPED (already exists)"
    SKIP=$((SKIP + 1))
    SCHEME_ID=""
  else
    echo "FAILED ($http_code)"
    echo "  $body" | head -3
    FAIL=$((FAIL + 1))
    SCHEME_ID=""
  fi
}

activate_scheme() {
  local scheme_id="$1"
  local name="$2"
  if [ -z "$scheme_id" ]; then return; fi
  echo -n "  Activating: $name ... "
  response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/schemes/$scheme_id/activate" \
    -H "Content-Type: application/json" 2>&1)
  http_code=$(echo "$response" | tail -1)
  if [ "$http_code" = "200" ]; then
    echo "OK"
  else
    body=$(echo "$response" | sed '$d')
    echo "FAILED ($http_code)"
    echo "  $body" | head -3
  fi
}

create_rule() {
  local name="$1"
  local json="$2"
  local scheme_id="$3"
  if [ -z "$scheme_id" ]; then return; fi
  echo -n "    Rule: $name ... "
  response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/rules" \
    -H "Content-Type: application/json" \
    -d "$json" 2>&1)
  http_code=$(echo "$response" | tail -1)
  if [ "$http_code" = "201" ]; then
    echo "OK"
    SUCCESS=$((SUCCESS + 1))
  else
    body=$(echo "$response" | sed '$d')
    echo "FAILED ($http_code)"
    echo "  $body" | head -3
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Seeding Eligibility Schemes ==="
echo "API: $BASE_URL"
echo ""

# =====================================================================
# 1. AGRICULTURAL INPUT SUBSIDY
# =====================================================================
echo "--- Scheme 1: Agricultural Input Subsidy ---"
create_scheme "Agricultural Input Subsidy" '{
  "tenant_id": "'"$TENANT"'",
  "name": "Agricultural Input Subsidy",
  "code": "AIS-2026",
  "description": "Government subsidy program for certified seeds and fertilizers. Provides e-vouchers redeemable at certified agro-dealers.",
  "scheme_type": "subsidy",
  "max_beneficiaries": 10000,
  "budget_amount": 150000000,
  "benefit_type": "voucher",
  "benefit_amount": 15000,
  "benefit_description": "E-voucher redeemable at certified agro-dealers for seeds and fertilizers",
  "application_deadline": "2026-06-30T23:59:59",
  "auto_approve_enabled": true,
  "min_score_for_auto_approve": 70.0,
  "max_risk_for_auto_approve": "medium",
  "waitlist_enabled": true,
  "waitlist_capacity": 2000
}'
AIS_ID="$SCHEME_ID"

if [ -n "$AIS_ID" ]; then
  create_rule "Farm Registration" '{
    "scheme_id": "'"$AIS_ID"'",
    "name": "Active Farm Registration",
    "description": "Farmer must have at least one registered farm",
    "field_type": "farm",
    "field_name": "farm_count",
    "operator": "greater_than_or_equal",
    "value": "1",
    "value_type": "number",
    "is_mandatory": true,
    "weight": 1.0,
    "priority": 1,
    "pass_message": "Farm registration is complete",
    "fail_message": "You need at least one registered farm"
  }' "$AIS_ID"

  create_rule "Minimum Land Size" '{
    "scheme_id": "'"$AIS_ID"'",
    "name": "Minimum Land Size",
    "description": "Farm must be at least 0.5 acres",
    "field_type": "farm",
    "field_name": "total_acreage",
    "operator": "greater_than_or_equal",
    "value": "0.5",
    "value_type": "number",
    "is_mandatory": true,
    "weight": 1.5,
    "priority": 2,
    "pass_message": "Farm size meets minimum requirement",
    "fail_message": "Farm must be at least 0.5 acres"
  }' "$AIS_ID"

  create_rule "KYC Verification" '{
    "scheme_id": "'"$AIS_ID"'",
    "name": "KYC Verification",
    "description": "Farmer must have completed KYC",
    "field_type": "kyc",
    "field_name": "kyc_status",
    "operator": "equals",
    "value": "approved",
    "value_type": "string",
    "is_mandatory": false,
    "weight": 2.0,
    "priority": 3,
    "pass_message": "KYC verification completed",
    "fail_message": "Complete your KYC verification to improve your score"
  }' "$AIS_ID"

  activate_scheme "$AIS_ID" "Agricultural Input Subsidy"
fi
echo ""

# =====================================================================
# 2. CROP INSURANCE PROGRAM
# =====================================================================
echo "--- Scheme 2: Crop Insurance Program ---"
create_scheme "Crop Insurance Program" '{
  "tenant_id": "'"$TENANT"'",
  "name": "Crop Insurance Program",
  "code": "CIP-2026",
  "description": "Weather-indexed crop insurance for smallholder farmers. Covers losses from drought, floods, and pest outbreaks.",
  "scheme_type": "insurance",
  "max_beneficiaries": 5000,
  "budget_amount": 250000000,
  "benefit_type": "service",
  "benefit_amount": 50000,
  "benefit_description": "Crop insurance coverage up to KES 50,000 per season",
  "application_deadline": "2026-04-30T23:59:59",
  "auto_approve_enabled": false,
  "waitlist_enabled": true,
  "waitlist_capacity": 1000
}'
CIP_ID="$SCHEME_ID"

if [ -n "$CIP_ID" ]; then
  create_rule "Farm Registration" '{
    "scheme_id": "'"$CIP_ID"'",
    "name": "Active Farm Registration",
    "description": "Farmer must have at least one registered farm",
    "field_type": "farm",
    "field_name": "farm_count",
    "operator": "greater_than_or_equal",
    "value": "1",
    "value_type": "number",
    "is_mandatory": true,
    "weight": 1.0,
    "priority": 1,
    "pass_message": "Farm registration is complete",
    "fail_message": "You need at least one registered farm"
  }' "$CIP_ID"

  create_rule "Minimum Acreage" '{
    "scheme_id": "'"$CIP_ID"'",
    "name": "Minimum Cultivable Acreage",
    "description": "Must have at least 1 acre under cultivation",
    "field_type": "farm",
    "field_name": "total_acreage",
    "operator": "greater_than_or_equal",
    "value": "1.0",
    "value_type": "number",
    "is_mandatory": true,
    "weight": 1.5,
    "priority": 2,
    "pass_message": "Cultivable acreage meets requirement",
    "fail_message": "Must have at least 1 acre under cultivation"
  }' "$CIP_ID"

  activate_scheme "$CIP_ID" "Crop Insurance Program"
fi
echo ""

# =====================================================================
# 3. FARM MECHANIZATION LOAN
# =====================================================================
echo "--- Scheme 3: Farm Mechanization Loan ---"
create_scheme "Farm Mechanization Loan" '{
  "tenant_id": "'"$TENANT"'",
  "name": "Farm Mechanization Loan",
  "code": "FML-2026",
  "description": "Low-interest loans for farm equipment purchase including tractors, irrigation systems, and post-harvest processing equipment.",
  "scheme_type": "loan",
  "max_beneficiaries": 1000,
  "budget_amount": 500000000,
  "benefit_type": "cash",
  "benefit_amount": 500000,
  "benefit_description": "Loan up to KES 500,000 at 4% interest rate with 3-year repayment",
  "application_deadline": "2026-12-31T23:59:59",
  "auto_approve_enabled": false,
  "waitlist_enabled": true,
  "waitlist_capacity": 500
}'
FML_ID="$SCHEME_ID"

if [ -n "$FML_ID" ]; then
  create_rule "Farm Registration" '{
    "scheme_id": "'"$FML_ID"'",
    "name": "Active Farm Registration",
    "description": "Farmer must have a registered farm",
    "field_type": "farm",
    "field_name": "farm_count",
    "operator": "greater_than_or_equal",
    "value": "1",
    "value_type": "number",
    "is_mandatory": true,
    "weight": 1.0,
    "priority": 1,
    "pass_message": "Farm registration confirmed",
    "fail_message": "Register your farm to apply"
  }' "$FML_ID"

  create_rule "Minimum Land Size" '{
    "scheme_id": "'"$FML_ID"'",
    "name": "Minimum Land Size",
    "description": "Farm must be at least 2 acres for mechanization loans",
    "field_type": "farm",
    "field_name": "total_acreage",
    "operator": "greater_than_or_equal",
    "value": "2.0",
    "value_type": "number",
    "is_mandatory": true,
    "weight": 2.0,
    "priority": 2,
    "pass_message": "Farm size meets minimum for mechanization",
    "fail_message": "Farm must be at least 2 acres for this loan"
  }' "$FML_ID"

  create_rule "KYC Required" '{
    "scheme_id": "'"$FML_ID"'",
    "name": "KYC Verification",
    "description": "Full KYC verification required for loans",
    "field_type": "kyc",
    "field_name": "kyc_status",
    "operator": "equals",
    "value": "approved",
    "value_type": "string",
    "is_mandatory": false,
    "weight": 2.5,
    "priority": 3,
    "pass_message": "KYC verification completed",
    "fail_message": "Complete KYC verification to apply for loans"
  }' "$FML_ID"

  activate_scheme "$FML_ID" "Farm Mechanization Loan"
fi
echo ""

# =====================================================================
# Summary
# =====================================================================
echo "=== Seeding Complete ==="
echo "  Created: $SUCCESS"
echo "  Skipped: $SKIP"
echo "  Failed:  $FAIL"
