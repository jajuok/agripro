# AgriScheme Pro - Implementation Plan

## Overview

This document outlines a phased implementation approach for AgriScheme Pro, a comprehensive Farm Management Information System (FMIS). The plan is structured to deliver value incrementally while managing technical complexity and risk.

**Last Updated:** 2026-02-19
**Current Version:** v0.2.0

---

## Implementation Status Summary

| Phase | Name | Status | Completion |
|-------|------|--------|------------|
| 1 | Foundation & Core Infrastructure | **DONE** | 100% |
| 2 | Farmer Onboarding & KYC | **DONE** | 100% |
| 3 | Core Operational Features | **PARTIAL** | ~35% |
| 4 | Financial & Compliance Tools | NOT STARTED | 0% |
| 5 | Advanced Technology Integrations | **PARTIAL** | ~15% |
| 6 | Supply Chain & Stakeholder Management | NOT STARTED | 0% |
| 7 | Communication & Engagement | **PARTIAL** | ~40% |
| 8 | Platform Administration & Go-Live | NOT STARTED | 0% |
| **NEW** | Back Office Management Portal | NOT STARTED | 0% |

---

## Phase 1: Foundation & Core Infrastructure - COMPLETE

### 1.1 Technical Foundation - COMPLETE

**Objective:** Establish the cloud-native platform foundation and core services.

#### What Was Built:

1. **Cloud Infrastructure** - COMPLETE
   - Self-hosted PaaS on OVHcloud VPS (Ubuntu 22.04 LTS) via Coolify
   - Traefik v2.10 reverse proxy with automatic SSL (sslip.io domains)
   - Nginx API gateway on port 8888 routing `/api/v1/*` to 15+ services
   - Docker-based containerization for all services
   - Prometheus + Grafana monitoring stack

2. **Core Services Architecture** - COMPLETE
   - 16 microservices scaffolded and deployed (FastAPI + SQLAlchemy 2.0)
   - Nginx API gateway with rate limiting and auth-aware routing
   - Kafka 7.5.0 message broker with Zookeeper for event-driven architecture
   - Redis 7 caching layer (separate DB slots per service, 0-13)
   - PostgreSQL 16 (single instance, 15 separate databases for service isolation)

3. **Security Foundation** - COMPLETE
   - JWT-based authentication with refresh token rotation
   - TLS via Traefik automatic certificates
   - Audit logging infrastructure (immutable audit_logs table)
   - Login attempt tracking for brute-force protection

4. **Development Environment** - COMPLETE
   - Docker Compose for local development (all-in-one)
   - Coolify deployment guides documented
   - CI/CD via GitHub webhooks for auto-deployment on push
   - E2E testing with Maestro (12 flows, ~86 assertions)

#### Deployed Services:
| Service | Port | Status | Business Logic |
|---------|------|--------|----------------|
| auth-service | 8000 | FUNCTIONAL | Full auth, RBAC, 2FA |
| farmer-service | 8000 | FUNCTIONAL | Farmers, farms, KYC, eligibility, crop planning |
| task-service | 8000 | FUNCTIONAL | Task CRUD, comments, stats |
| notification-service | 8000 | FUNCTIONAL | Multi-channel notifications |
| gis-service | 8000 | FUNCTIONAL | Geocoding, boundaries, area calc |
| farm-service | 8000 | STUB | Health check only |
| financial-service | 8000 | STUB | Health check only |
| market-service | 8000 | STUB | Health check only |
| inventory-service | 8000 | STUB | Health check only |
| livestock-service | 8000 | STUB | Health check only |
| compliance-service | 8000 | STUB | Health check only |
| traceability-service | 8000 | STUB | Health check only |
| ai-service | 8000 | STUB | Health check only |
| iot-service | 8000 | STUB | Health check only |
| integration-service | 8000 | STUB | Health check only |

---

### 1.2 User Management & Access Control - COMPLETE

**Objective:** Implement multi-tenant user management with RBAC.

#### What Was Built:

1. **Authentication Service** - COMPLETE
   - Dual auth: email/password + phone/PIN (farmer-friendly)
   - TOTP-based 2FA (setup, enable, disable, status)
   - Password reset flow (request + confirm)
   - Token lifecycle: access tokens, refresh tokens, revocation
   - Session management with concurrent login support
   - Brute-force protection via login attempt tracking

2. **Authorization Service** - COMPLETE
   - Role-Based Access Control (RBAC) with roles + permissions tables
   - Admin API: create/list/delete roles, create/list permissions
   - Role-permission assignment and revocation
   - User-role assignment and revocation
   - Superuser dependency protection

3. **Multi-Tenancy** - PARTIAL
   - Tenant ID field on all major entities (hardcoded: `00000000-0000-0000-0000-000000000001`)
   - Database-level service isolation (separate DB per service)
   - Cross-tenant support designed but not yet multi-tenant operational

4. **Audit & Compliance** - COMPLETE
   - Immutable `audit_logs` table with IP, user-agent tracking
   - `login_attempts` tracking table
   - All admin actions audit-logged
   - `refresh_tokens` and `password_reset_tokens` tracked

#### Database Tables (Auth Service):
`users`, `roles`, `user_roles`, `permissions`, `role_permissions`, `refresh_tokens`, `password_reset_tokens`, `login_attempts`, `audit_logs`

#### API Endpoints (18 total):
- `POST /register`, `POST /register/phone` - Registration
- `POST /login`, `POST /login/phone` - Authentication
- `POST /refresh`, `POST /logout` - Token management
- `POST /2fa/setup`, `POST /2fa/enable`, `POST /2fa/disable`, `GET /2fa/status` - 2FA
- `POST /password/reset-request`, `POST /password/reset-confirm`, `POST /password/change` - Password
- `GET /users/me`, `PATCH /users/me`, `GET /users`, `GET /users/{id}` - User management
- Admin RBAC endpoints (roles, permissions, user-role assignment)

---

## Phase 2: Farmer Onboarding & KYC Module - COMPLETE

### 2.1 Registration & Identity Verification - COMPLETE

**Objective:** Build comprehensive KYC system with biometric and document verification.

#### What Was Built:

1. **Biometric Capture Service** - COMPLETE
   - Fingerprint capture endpoint with quality scoring
   - Facial recognition capture endpoint
   - Biometric verification endpoint
   - Biometric records retrieval per farmer
   - Deduplication support via `biometric_data` table

2. **Document Verification Service** - COMPLETE
   - Document upload with type classification (national_id, passport, land_title, etc.)
   - Document verification endpoint (admin)
   - OCR extraction support
   - Document number tracking

3. **KYC Workflow Engine** - COMPLETE
   - Multi-step workflow: Personal Info -> Documents -> Bank Info -> Review
   - `POST /kyc/{farmer_id}/start` - Initiate KYC
   - `POST /kyc/{farmer_id}/step/complete` - Complete individual steps
   - `POST /kyc/{farmer_id}/submit` - Submit for review
   - `POST /kyc/{farmer_id}/review` - Admin approve/reject
   - `GET /kyc/review-queue` - Manual review queue
   - `POST /kyc/{farmer_id}/review/assign` - Assign reviewer

4. **External Verification** - COMPLETE (API ready, integrations pending)
   - `POST /kyc/{farmer_id}/verify/external` - Run external verifications
   - `GET /kyc/{farmer_id}/verify/status` - Check verification status
   - `external_verifications` table for ID, credit, sanctions checks
   - Actual external service integrations (IPRS, credit bureaus) pending

#### Database Tables:
`documents`, `biometric_data`, `kyc_applications`, `kyc_review_queue`, `external_verifications`

#### Mobile Screens (5):
- `/kyc` - KYC dashboard with progress tracking
- `/kyc/personal-info` - Name, ID, DOB, gender, phone, address
- `/kyc/documents` - Document upload per type
- `/kyc/bank-info` - Bank name, account number, holder name
- `/kyc/submit` - Final review and submission

#### E2E Tests: `kyc.yaml` - 29 assertions

---

### 2.2 Farm Profile Registration - COMPLETE

**Objective:** Capture comprehensive farm data with validation.

#### What Was Built:

1. **Farm Location Service** - COMPLETE
   - GPS coordinate capture (native + web geolocation)
   - GIS reverse geocoding (county/sub-county/ward lookup)
   - Coordinate validation (Kenya boundary check)
   - GIS polygon validation and area calculation
   - Geofencing (point-in-boundary check)
   - Polygon overlap detection and simplification

2. **Land & Asset Documentation** - COMPLETE
   - 6-step registration wizard: Location -> Boundary -> Land Details -> Soil & Water -> Documents -> Review
   - Document upload for land ownership proof
   - Equipment/asset registration via `farm_assets` table
   - Photo documentation support
   - Farm boundary as GeoJSON polygon

3. **Soil & Water Profile** - COMPLETE
   - Soil type, pH, nutrient tracking via `soil_test_reports` table
   - Water source documentation
   - Irrigation type classification
   - Soil test report upload

4. **Crop History** - COMPLETE
   - `crop_records` table for previous crop data
   - `field_visits` table for extension officer verification
   - Historical yield capture

#### Database Tables:
`farmers`, `farm_profiles`, `farm_documents`, `farm_assets`, `crop_records`, `soil_test_reports`, `field_visits`

#### API Endpoints:
- Farmer CRUD: `POST/GET/PATCH /farmers`, `GET /farmers/by-user/{userId}`
- Farm CRUD: `POST/GET/PATCH /farms`, `GET /farms/farmer/{farmerId}`
- Farm Registration: `POST /farm-registration/start`, boundary, land details, soil/water, documents, assets, crops, soil tests, complete

#### Mobile Screens (8):
- `/(tabs)/farms` - Farm list with stats
- `/farms/add` - 6-step registration wizard
- `/farms/[id]` - Farm detail with tabs
- `/farms/[id]/boundary` - Map boundary editor
- `/farms/[id]/land-details` - Edit land info
- `/farms/[id]/soil-water` - Edit soil/water
- `/farms/[id]/crops` - Manage crops
- `/farms/[id]/documents` - Upload/view documents

#### E2E Tests: `farms.yaml` - 5 assertions

---

### 2.3 Eligibility Assessment Engine - COMPLETE

**Objective:** Automated eligibility screening with risk scoring.

#### What Was Built:

1. **Rules Engine** - COMPLETE
   - Configurable eligibility schemes (create, list, get, update, activate)
   - Rule groups with AND/OR logic
   - Individual rules with operators (gt, lt, eq, gte, lte, in, not_in, between, contains)
   - Rule fields: `field_name`, `operator`, `value`, `weight`
   - Multi-scheme support per tenant

2. **Credit Integration** - COMPLETE (API ready)
   - `credit_bureau_providers` configuration table
   - `POST /eligibility/credit-checks` - Request credit check
   - `GET /eligibility/farmers/{id}/credit-checks` - Credit history
   - Credit scoring integration ready (external connections pending)

3. **Risk Scoring Model** - COMPLETE
   - `risk_factors` table for configurable risk scoring
   - `risk_assessments` table with multi-factor scores
   - `GET /eligibility/farmers/{id}/risk-assessment` - Current risk
   - `GET /eligibility/farmers/{id}/risk-history` - Risk history

4. **Workflow Automation** - COMPLETE
   - `POST /eligibility/assessments` - Run automated assessment
   - `POST /eligibility/assessments/{id}/decision` - Manual decision
   - `GET /eligibility/review-queue` - Manual review queue
   - `GET /eligibility/schemes/{id}/waitlist` - Waitlist management
   - `POST /eligibility/assessments/batch` - Batch assessment
   - `eligibility_notifications` table for status change notifications

#### Database Tables:
`eligibility_schemes`, `eligibility_rule_groups`, `eligibility_rules`, `eligibility_assessments`, `credit_bureau_providers`, `credit_checks`, `risk_factors`, `risk_assessments`, `eligibility_review_queue`, `scheme_waitlists`, `eligibility_notifications`

#### Seed Data:
3 seeded schemes with 8 rules: Agricultural Input Subsidy (AIS-2026), Crop Insurance Program (CIP-2026), Farm Mechanization Loan (FML-2026)

#### Mobile Screens (2):
- `/eligibility` - Scheme list with stats, assessment status
- `/eligibility/[id]` - Scheme detail, "Check My Eligibility" button, results

#### E2E Tests: `eligibility.yaml` - 7 assertions

---

## Phase 3: Core Operational Features - PARTIALLY COMPLETE

### 3.1 Crop & Season Planning - COMPLETE

**Objective:** Comprehensive crop lifecycle management tools.

#### What Was Built:

1. **Crop Calendar Service** - COMPLETE
   - `crop_calendar_templates` - Regional/crop-specific growth stage templates
   - Template CRUD + recommendations by region/season/crop
   - Growth stage tracking with stage advancement
   - Activity scheduling engine
   - Alert system (activity_reminder, activity_overdue, weather_warning, planting_window, etc.)
   - Dashboard endpoint aggregating active plans, overdue activities, alerts

2. **Input Planning** - COMPLETE
   - `input_requirements` table (seeds, fertilizer, pesticide, herbicide, fungicide)
   - QR code verification for certified seeds
   - Input calculator endpoint (`GET /crop-planning/calculate-inputs`)
   - Procurement status tracking (planned -> ordered -> received -> applied)
   - Cost tracking (estimated vs actual)

3. **Irrigation Management** - COMPLETE
   - `irrigation_schedules` table with method types (drip, sprinkler, furrow, etc.)
   - Auto-generation from template (`POST /plans/{id}/irrigation/generate`)
   - Soil moisture tracking (before/after)
   - Weather context integration (rainfall, temperature, evapotranspiration)
   - Deficit irrigation support

#### Database Tables:
`crop_calendar_templates`, `crop_plans`, `planned_activities`, `input_requirements`, `irrigation_schedules`, `crop_plan_alerts`

#### API Endpoints (40+ total):
- Templates: CRUD, recommend
- Plans: CRUD, activate, advance-stage, complete, statistics
- Activities: CRUD, complete, skip, upcoming
- Inputs: CRUD, verify-qr, calculate
- Irrigation: CRUD, generate, complete
- Alerts: list, mark-read, dismiss
- Dashboard: aggregated stats

#### Mobile Screens (8):
- `/crop-planning` - Dashboard with stats, upcoming activities, plan list
- `/crop-planning/create` - 4-step wizard (Farm & Crop -> Template -> Details -> Review)
- `/crop-planning/alerts` - Alert list with severity colors
- `/crop-planning/[id]` - Plan detail with tabs
- `/crop-planning/[id]/activities` - Activity list
- `/crop-planning/[id]/activity-complete` - Complete activity with notes/photos/GPS
- `/crop-planning/[id]/inputs` - Input requirements list
- `/crop-planning/[id]/irrigation` - Irrigation schedule

#### E2E Tests: `crop_planning.yaml` - 5 assertions

---

### 3.2 Livestock Management - NOT STARTED

**Objective:** Individual animal tracking and health management.

**Service:** `livestock-service` - STUB (health check only)

#### Remaining Work:
- Animal registry (identification, profiles, herd structure, transfers)
- Health management (vaccination, treatment, vet visits, disease reporting, quarantine)
- Breeding & production (breeding cycles, heat detection, milk/eggs/weight tracking, feeding programs)
- Mobile screens for livestock management

---

### 3.3 Task & Workforce Management - PARTIALLY COMPLETE

**Objective:** Field task assignment and labor tracking.

#### What Was Built:

1. **Task Management** - COMPLETE
   - Task CRUD with priorities (1-10) and due dates
   - Status management: pending -> in_progress -> completed -> cancelled
   - Categories: maintenance, administrative, equipment, infrastructure, inspection, livestock, etc.
   - Recurrence support (daily, weekly, biweekly, monthly, quarterly, yearly)
   - Comments system with task-level threads
   - Statistics aggregation (total, pending, completed, overdue, by category)
   - Soft delete support

#### Database Tables (Task Service):
`tasks`, `task_comments`

#### API Endpoints (10):
- `GET/POST /tasks` - List/create tasks
- `GET/PATCH/DELETE /tasks/{id}` - Task CRUD
- `POST /tasks/{id}/complete` - Mark complete
- `GET /tasks/stats` - Statistics
- `GET/POST /tasks/{id}/comments` - Comments

#### Mobile Screens (3):
- `/(tabs)/tasks` - Unified task list (crop activities + standalone tasks), sectioned by Overdue/Today/Upcoming
- `/tasks/create` - Create new task
- `/tasks/[taskId]` - Task detail

#### E2E Tests: `tasks.yaml` - 5 assertions

#### Remaining Work:
- Worker assignment (assign tasks to specific workers/farmers)
- GPS proof of completion
- Photo verification
- Labor management (attendance, time logging, productivity metrics)
- Payroll integration (hours to pay calculation)
- Seasonal labor planning

---

### 3.4 Inventory & Input Management - NOT STARTED

**Objective:** Complete inventory tracking for all farm inputs and outputs.

**Service:** `inventory-service` - STUB (health check only)

#### Remaining Work:
- Multi-category inventory tracking (seeds, fertilizers, pesticides, fuel, equipment, produce)
- Barcode/QR scanning
- Stock level monitoring
- Low stock alerts, expiry warnings, reorder automation
- Inventory valuation, usage analytics, waste/loss reporting

---

## Phase 4: Financial & Compliance Tools - NOT STARTED

### 4.1 Farm Accounting
**Service:** `financial-service` - STUB
- Transaction management, payroll, financial reporting all pending

### 4.2 Subsidy & Scheme Disbursement
- Voucher system, direct benefit transfer, fraud detection, grievance management all pending

### 4.3 Compliance & Audit Reporting
**Service:** `compliance-service` - STUB
- Report templates, automation, audit trail all pending

### 4.4 E-Commerce & Direct Sales
- Storefront, order management, payments, CRM all pending

---

## Phase 5: Advanced Technology Integrations - PARTIALLY COMPLETE

### 5.1 Precision Agriculture & GIS - PARTIALLY COMPLETE

#### What Was Built:
- GIS Service with 7 endpoints: reverse-geocode, validate-coordinates, validate-polygon, calculate-area, point-in-boundary, check-overlap, simplify-polygon
- Kenya administrative boundary lookup (county, sub-county, ward)
- Integrated into farm registration flow

#### Remaining Work:
- Satellite imagery integration (Sentinel-2, Landsat)
- NDVI analysis and mapping
- Field boundary detection from imagery
- Variable rate application maps
- Map visualization layer with offline tiles

### 5.2 AI-Powered Analytics - NOT STARTED
**Service:** `ai-service` - STUB

### 5.3 IoT Sensor Integration - NOT STARTED
**Service:** `iot-service` - STUB

### 5.4 Offline Functionality - PARTIALLY COMPLETE

#### What Was Built:
- PWA with service worker (Workbox)
- TWA (Trusted Web Activity) Android APK (~913KB)
- Offline sync queue in farm store (`pendingUploads` mechanism)
- Asset caching via Workbox

#### Remaining Work:
- Full offline database (IndexedDB/SQLite)
- Bi-directional sync engine with conflict resolution
- Offline map tiles
- USSD fallback for feature phones

---

## Phase 6: Supply Chain & Stakeholder Management - NOT STARTED

### 6.1 Market Linkage & Trading
**Service:** `market-service` - STUB
- Mobile market screen exists with MOCK DATA only (hardcoded prices for Maize, Wheat, Beans, Potatoes)

### 6.2 Traceability & Transparency
**Service:** `traceability-service` - STUB

### 6.3 Financial Services Integration
- Lender integration, loan management, insurance module all pending

---

## Phase 7: Communication & Engagement - PARTIALLY COMPLETE

### 7.1 Multi-Channel Communication - PARTIALLY COMPLETE

#### What Was Built:
- **Notification Service** - COMPLETE
  - In-app notifications (list, unread count, mark read, mark all read)
  - Template system with variable substitution
  - Multi-channel design: in-app, SMS, push, email
  - Web push subscription support (VAPID protocol)
  - Delivery status tracking (pending, sent, delivered, failed, skipped)
  - Notification preferences per user (channel toggles, category toggles, quiet hours)
  - Cost tracking per delivery
  - Bulk notification creation

#### Database Tables (Notification Service):
`notifications`, `notification_templates`, `notification_preferences`, `delivery_logs`

#### API Endpoints (9):
- `GET/POST /notifications` - List/create
- `POST /notifications/bulk` - Bulk create
- `GET /notifications/unread-count` - Badge count
- `PATCH /notifications/{id}/read` - Mark read
- `POST /notifications/mark-all-read` - Mark all
- `GET/PUT /preferences` - Notification preferences
- `POST /preferences/push-subscription` - Web push

#### Mobile Screen:
- `/notifications` - Full notification center with pull-to-refresh, infinite scroll, mark all read

#### E2E Tests: `notifications.yaml` - 8 assertions

#### Remaining Work:
- SMS gateway integration (Africa's Talking, Twilio)
- Email service integration
- WhatsApp Business API integration
- IVR system
- Push notification delivery (FCM/APNS)

### 7.2 Extension Services Support - NOT STARTED
### 7.3 Feedback & Grievance Management - NOT STARTED

---

## Phase 8: Platform Administration & Go-Live - NOT STARTED

### 8.1 Scheme Configuration - NOT STARTED
### 8.2 Data Management & Analytics - NOT STARTED
### 8.3 Integration Hub - PARTIALLY COMPLETE (Nginx gateway operational)

---

## Mobile App Feature Summary

### Fully Functional Screens (Real API):
| Screen | Route | E2E Tests |
|--------|-------|-----------|
| Login (Phone + PIN) | `/(auth)/login` | 7 assertions |
| Registration | `/(auth)/register` | in auth flow |
| Home Dashboard | `/(tabs)/home` | 5 assertions |
| Farms List | `/(tabs)/farms` | 5 assertions |
| Tasks (Unified) | `/(tabs)/tasks` | 5 assertions |
| Profile | `/(tabs)/profile` | 6 assertions |
| Farm Registration (6-step) | `/farms/add` | in farms flow |
| Farm Detail (tabbed) | `/farms/[id]/*` | in farms flow |
| KYC Workflow (4-step) | `/kyc/*` | 29 assertions |
| Crop Planning Dashboard | `/crop-planning` | 5 assertions |
| Create Crop Plan (4-step) | `/crop-planning/create` | - |
| Plan Detail + Activities | `/crop-planning/[id]/*` | - |
| Eligibility Schemes | `/eligibility` | 7 assertions |
| Eligibility Detail | `/eligibility/[id]` | in eligibility flow |
| Notifications | `/notifications` | 8 assertions |
| Reports | `/reports` | 7 assertions |
| Support & FAQ | `/support` | 4 assertions |
| Navigation (5 tabs) | all tabs | 6 assertions |

### Stub/Mock Screens:
| Screen | Route | Status |
|--------|-------|--------|
| Market Prices | `/(tabs)/market` | MOCK DATA (hardcoded) |
| Payment Methods | `/profile/payments` | STUB |
| Notification Preferences | `/profile/notifications` | STUB |
| Legal/Terms | `/legal` | STUB |

### State Management (Zustand):
- **Auth Store** - User session, tokens, auto-refresh (persisted to SecureStore)
- **Farm Store** - Farms list, registration draft, pending uploads (persisted to AsyncStorage)
- **Crop Planning Store** - Plans, activities, templates, alerts (partially persisted)
- **Task Store** - Tasks, comments, stats (not persisted)
- **KYC Store** - KYC status and progress (not persisted)

### E2E Test Suite:
- **Framework:** Maestro (Detox incompatible with TWA)
- **Total Flows:** 12
- **Total Assertions:** ~86
- **Runner:** `maestro test apps/mobile/e2e/maestro/regression.yaml`

---

## Deployment Architecture

```
                    ┌─────────────────────────┐
                    │    OVHcloud VPS (Ubuntu) │
                    │       213.32.19.116      │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                   │
    ┌─────────┴───────┐ ┌──────┴──────┐ ┌─────────┴────────┐
    │  Traefik (SSL)  │ │ Nginx :8888 │ │   Caddy (PWA)    │
    │  *.sslip.io     │ │ API Gateway │ │ app.*.sslip.io   │
    └─────────┬───────┘ └──────┬──────┘ └──────────────────┘
              │                │
    ┌─────────┴───────────────┴───────────────┐
    │         Docker Services (15+)            │
    ├──────────┬──────────┬──────────┬────────┤
    │  auth    │ farmer   │  task    │ notif  │
    │  gis     │ market   │ financi  │ live   │
    │  invent  │ comply   │ trace    │ ai     │
    │  iot     │ integr   │ farm     │        │
    └──────────┴──────────┴──────────┴────────┘
              │                │
    ┌─────────┴──────┐ ┌──────┴──────┐
    │ PostgreSQL 16  │ │   Redis 7   │
    │ (15 databases) │ │ (14 slots)  │
    └────────────────┘ └─────────────┘
              │
    ┌─────────┴──────┐
    │  Kafka 7.5.0   │
    │ + Zookeeper    │
    └────────────────┘
```

**Mobile Delivery:**
- PWA served via Caddy at `https://app.213.32.19.116.sslip.io`
- TWA APK (~913KB) wraps PWA in Android app shell
- APK: `apps/mobile/twa/app/build/outputs/apk/release/app-release.apk`

---

## NEW: Phase 9 - Back Office Management Portal

### Overview

A comprehensive web-based administration portal for scheme administrators, operations staff, extension officers, and finance teams to manage all aspects of the AgriScheme Pro platform. This portal sits alongside the farmer-facing mobile app and provides the operational backbone for program management.

### Architecture Decision

**Technology Stack:**
- **Frontend:** Next.js 14+ (App Router) with TypeScript
- **UI Library:** shadcn/ui + Tailwind CSS (consistent, accessible components)
- **State Management:** TanStack Query (server state) + Zustand (client state)
- **Charts/Analytics:** Recharts or Tremor
- **Tables:** TanStack Table (sorting, filtering, pagination)
- **Maps:** Leaflet/MapLibre for GIS visualization
- **Auth:** Same JWT tokens from auth-service, role-based route guards
- **Deployment:** Static export or Node.js on Coolify, same Traefik routing

**Location:** `apps/backoffice/`

### 9.1 Authentication & Role-Based Access

**Objective:** Secure admin login with role-based dashboards.

#### Features:
1. **Admin Login**
   - Email/password authentication (reuses auth-service)
   - 2FA enforcement for admin accounts
   - Session timeout and idle detection
   - Audit trail for all admin actions

2. **Role-Based Dashboards**
   - **Super Admin** - Full platform access, system configuration
   - **Scheme Administrator** - Scheme management, eligibility, disbursement
   - **Operations Manager** - Farmer oversight, KYC review, farm verification
   - **Extension Officer** - Farmer visits, crop advisory, field verification
   - **Finance Officer** - Payments, disbursements, financial reports
   - **Support Agent** - Grievance handling, farmer support
   - **Auditor** - Read-only access to all data, audit reports

3. **Permission Management**
   - Role CRUD (leveraging existing auth-service admin API)
   - Permission assignment UI
   - User-role management interface
   - Activity log viewer

#### API Dependencies: Auth service admin endpoints (already built)

---

### 9.2 Dashboard & Analytics

**Objective:** Real-time operational dashboards with KPI tracking.

#### Features:

1. **Executive Dashboard**
   - Total registered farmers (with registration trend chart)
   - Total farms and total hectares under management
   - KYC completion funnel (started -> personal_info -> documents -> bank_info -> submitted -> verified)
   - Active schemes count and total beneficiaries
   - Active crop plans and upcoming harvest timeline
   - Task completion rates
   - Regional heatmap of farmer registrations

2. **Scheme Performance Dashboard**
   - Per-scheme: applications, assessments, approvals, rejections, waitlisted
   - Budget utilization (allocated vs disbursed)
   - Eligibility score distribution (histogram)
   - Risk level breakdown (pie chart)
   - Geographic distribution of beneficiaries

3. **Operational Metrics**
   - KYC review queue depth and average processing time
   - Eligibility review queue depth
   - Pending farm verifications
   - Overdue tasks count
   - Notification delivery success rates
   - System health (service uptime, API response times)

4. **Farmer Activity Timeline**
   - Registration events
   - KYC progress
   - Farm registrations
   - Crop plan creation/completion
   - Eligibility assessments
   - Task completions

#### API Dependencies: Aggregation endpoints needed across farmer, task, notification services

---

### 9.3 Farmer Management

**Objective:** Complete farmer lifecycle management for administrators.

#### Features:

1. **Farmer Directory**
   - Searchable, filterable table of all farmers
   - Filters: county, sub-county, KYC status, registration date, scheme enrollment
   - Quick view: name, phone, location, KYC status, farm count, scheme status
   - Export to CSV/Excel
   - Bulk actions (send notification, assign to scheme)

2. **Farmer Detail View**
   - Profile overview (personal info, contact, registration date)
   - KYC status with step-by-step completion detail
   - Uploaded documents with verification controls
   - Biometric records status
   - Farm profiles linked to this farmer
   - Eligibility assessments and scheme enrollments
   - Crop plans (active, completed, draft)
   - Task history
   - Notification history
   - Activity timeline (all events)
   - Admin notes/comments

3. **Farmer Actions**
   - Edit farmer profile
   - Override KYC status (with audit log)
   - Trigger external verification
   - Send direct notification
   - Assign to scheme
   - Suspend/reactivate account
   - Merge duplicate farmer records

#### API Dependencies: Farmer service endpoints (already built), new admin-specific aggregation endpoints

---

### 9.4 KYC Review & Verification

**Objective:** Streamlined KYC review workflow for operations staff.

#### Features:

1. **Review Queue Dashboard**
   - Pending reviews count with aging indicators
   - Review queue table (farmer name, submitted date, assigned reviewer, priority)
   - Auto-assignment to available reviewers
   - Priority scoring (wait time, scheme deadline proximity)

2. **KYC Review Interface**
   - Side-by-side: farmer info + uploaded documents
   - Document viewer with zoom, rotate, fullscreen
   - Verification checklist per document type
   - National ID cross-reference display
   - Biometric record display
   - External verification results (ID, credit, sanctions)
   - Approve/reject per step with reason codes
   - Overall approve/reject/request-more-info

3. **Verification Management**
   - External verification status dashboard
   - Failed verification retry
   - Manual override with justification
   - Batch verification triggers

4. **KYC Analytics**
   - Average review time
   - Approval/rejection rates
   - Common rejection reasons
   - Reviewer productivity metrics
   - Bottleneck identification

#### API Dependencies: KYC endpoints (already built), review queue endpoints (already built)

---

### 9.5 Farm Oversight & GIS

**Objective:** Geographic farm management and verification.

#### Features:

1. **Farm Map View**
   - Interactive map showing all registered farms
   - Color-coded by: verification status, crop type, scheme enrollment
   - Cluster view for dense areas
   - Click farm polygon to view details
   - Overlap detection highlighting

2. **Farm Directory**
   - Searchable table of all farms
   - Filters: county, crop type, acreage range, verification status, ownership type
   - Quick stats: total farms, total hectares, verified vs pending

3. **Farm Verification Workflow**
   - Pending verification queue
   - Satellite imagery overlay for boundary verification
   - Compare declared vs measured acreage
   - Field visit assignment and scheduling
   - Verification approve/reject with notes

4. **Land Analytics**
   - Total cultivable land by region
   - Crop distribution map
   - Soil type distribution
   - Irrigation coverage
   - Land ownership type breakdown

#### API Dependencies: Farm endpoints + GIS service (already built)

---

### 9.6 Eligibility & Scheme Management

**Objective:** Full scheme lifecycle management for administrators.

#### Features:

1. **Scheme Management**
   - Create new scheme (wizard: basic info -> eligibility rules -> budget -> activation)
   - Edit scheme details, rules, budget
   - Activate/deactivate schemes
   - Clone existing scheme as template
   - Scheme calendar view (application windows, deadlines)

2. **Eligibility Rules Builder**
   - Visual rule builder (drag-and-drop rule groups)
   - Rule conditions: field, operator, value, weight
   - AND/OR rule group logic
   - Test rules against sample farmer data
   - Rule simulation (how many farmers would qualify)

3. **Assessment Management**
   - Assessment results table (farmer, scheme, score, risk, decision)
   - Filters: scheme, decision, risk level, score range
   - Manual review queue for borderline cases
   - Override assessment decision with justification
   - Batch assessment trigger

4. **Waitlist Management**
   - Waitlist view per scheme (position, score, status)
   - Offer management (offer, accept, decline, expire)
   - Automatic progression when slots open
   - Waitlist analytics

5. **Scheme Reporting**
   - Beneficiary list per scheme
   - Geographic distribution of beneficiaries
   - Budget vs actual spend
   - Scheme performance over time
   - Compliance reporting

#### API Dependencies: Eligibility endpoints (already built)

---

### 9.7 Crop Planning Oversight

**Objective:** Monitor and support farmer crop planning activities.

#### Features:

1. **Crop Planning Dashboard**
   - Active plans by crop type (bar chart)
   - Seasonal planting timeline
   - Overdue activities across all farmers
   - Template usage statistics

2. **Template Management**
   - Create/edit crop calendar templates
   - Define growth stages with activities
   - Set regional recommendations
   - Input requirements per template
   - Irrigation schedules per template
   - Template activation/deactivation

3. **Crop Plan Monitor**
   - All active plans table (farmer, crop, farm, status, progress)
   - Plan detail view (activities, inputs, irrigation)
   - Alert management (view, resolve, escalate)
   - Overdue activity escalation

4. **Advisory Content**
   - Crop-specific advisory notes
   - Weather-based recommendations
   - Pest/disease alerts by region
   - Best practice guides

#### API Dependencies: Crop planning endpoints (already built)

---

### 9.8 Task & Workforce Management

**Objective:** Assign and monitor field tasks across the workforce.

#### Features:

1. **Task Board**
   - Kanban view: Pending -> In Progress -> Completed
   - Calendar view of all tasks
   - Filter by: assignee, category, priority, farm, date range
   - Bulk task creation and assignment

2. **Task Analytics**
   - Completion rates by worker/team
   - Average time to completion
   - Overdue trends
   - Category distribution

3. **Workforce Directory** (future)
   - Worker profiles
   - Assignment history
   - Productivity scores
   - Availability calendar

#### API Dependencies: Task service (already built)

---

### 9.9 Notification Management

**Objective:** Manage communications across all channels.

#### Features:

1. **Notification Center**
   - Send notifications: individual, bulk, or broadcast
   - Template management (create, edit, preview with variables)
   - Schedule future notifications
   - Channel selection (in-app, SMS, push, email)

2. **Delivery Monitoring**
   - Delivery logs table (status, channel, cost, timestamp)
   - Delivery success rates by channel
   - Failed delivery retry
   - Cost reporting

3. **Campaign Management** (future)
   - Targeted campaigns by farmer segment
   - A/B testing support
   - Campaign analytics

#### API Dependencies: Notification service (already built)

---

### 9.10 Reports & Data Export

**Objective:** Comprehensive reporting for all stakeholders.

#### Features:

1. **Standard Reports**
   - Farmer registration report (by period, region, status)
   - KYC completion report
   - Farm verification report
   - Scheme enrollment report
   - Crop planning summary
   - Task completion report
   - Notification delivery report

2. **Custom Report Builder**
   - Select data source (farmers, farms, schemes, tasks, etc.)
   - Choose columns and filters
   - Grouping and aggregation
   - Chart visualization
   - Save as template

3. **Export Capabilities**
   - CSV, Excel, PDF export
   - Scheduled report generation
   - Email distribution lists
   - API access for external BI tools

4. **Audit Reports**
   - User activity audit trail
   - Data change log
   - Permission change history
   - Login/access reports

#### API Dependencies: New aggregation endpoints, auth audit logs (already built)

---

### 9.11 System Configuration

**Objective:** Platform-level configuration for super admins.

#### Features:

1. **Tenant Management**
   - Create/manage tenants
   - Tenant-specific settings
   - Feature flags per tenant

2. **System Settings**
   - Default notification preferences
   - KYC workflow configuration (required steps, document types)
   - Eligibility rule defaults
   - API rate limits

3. **Integration Management**
   - External service connection status
   - API key management
   - Webhook configuration
   - Integration health monitoring

4. **System Health**
   - Service status dashboard (all 15 microservices)
   - Database connection status
   - Redis/Kafka health
   - API response time monitoring
   - Error rate tracking

#### API Dependencies: New system admin endpoints needed

---

### Back Office Implementation Phases

| Phase | Modules | Priority | Estimated Effort |
|-------|---------|----------|------------------|
| **BO-1** | Auth + Dashboard + Farmer Directory | HIGH | Foundation |
| **BO-2** | KYC Review + Farm Oversight (Map) | HIGH | Core operations |
| **BO-3** | Eligibility & Scheme Management | HIGH | Scheme admin |
| **BO-4** | Crop Planning Oversight + Templates | MEDIUM | Farm support |
| **BO-5** | Task Management + Notifications | MEDIUM | Operations |
| **BO-6** | Reports & Data Export | MEDIUM | Analytics |
| **BO-7** | System Config + Audit | LOW | Platform admin |

**Recommended Start:** BO-1 (Auth + Dashboard + Farmers), since it provides immediate operational value and most API endpoints already exist.

---

## Technical Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                │
├──────────────┬──────────────┬──────────────┬──────────────┬────────┤
│  Farmer App  │  Back Office │Extension App │ E-Commerce   │  USSD  │
│  (TWA/PWA)   │  (Next.js)   │   (Future)   │   (Future)   │(Future)│
│   BUILT      │  PLANNED     │              │              │        │
└──────────────┴──────────────┴──────────────┴──────────────┴────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │         API Gateway           │
                    │  Nginx :8888 + Traefik (SSL)  │
                    │           BUILT               │
                    └───────────────┬───────────────┘
                                    │
┌───────────────────────────────────┴───────────────────────────────────┐
│                     Service Layer (Docker/Coolify)                     │
├─────────────┬─────────────┬─────────────┬─────────────┬──────────────┤
│    Auth     │   Farmer    │    Task     │Notification │     GIS      │
│   BUILT     │   BUILT     │   BUILT     │   BUILT     │    BUILT     │
├─────────────┼─────────────┼─────────────┼─────────────┼──────────────┤
│  Inventory  │  Livestock  │  Financial  │  Compliance │  Traceability│
│   STUB      │   STUB      │   STUB      │   STUB      │    STUB      │
├─────────────┼─────────────┼─────────────┼─────────────┼──────────────┤
│     AI      │     IoT     │   Market    │    Farm     │  Integration │
│   STUB      │   STUB      │   STUB      │   STUB      │    STUB      │
└─────────────┴─────────────┴─────────────┴─────────────┴──────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
       ┌──────┴──────┐       ┌──────┴──────┐       ┌──────┴──────┐
       │ PostgreSQL  │       │    Redis    │       │    Kafka    │
       │     16      │       │      7      │       │   7.5.0     │
       │   BUILT     │       │   BUILT     │       │   BUILT     │
       └─────────────┘       └─────────────┘       └─────────────┘
```

---

## External Integrations Map

| Category | Systems | Priority | Status |
|----------|---------|----------|--------|
| Identity | National ID (IPRS), NIN registries | P1 | API ready, integration pending |
| Financial | Core banking, Mobile money (M-Pesa), Payment gateways | P1 | NOT STARTED |
| Government | Subsidy portals, Land registries, Tax systems | P1 | NOT STARTED |
| Credit | Credit Reference Bureaus | P1 | API ready, integration pending |
| Satellite | Sentinel Hub, Landsat, Planet | P2 | NOT STARTED |
| Weather | OpenWeather, AccuWeather, Local met offices | P2 | NOT STARTED |
| IoT | ThingsBoard, AWS IoT, Azure IoT | P2 | NOT STARTED |
| SMS | Africa's Talking, Twilio | P1 | NOT STARTED |
| ERP | SAP, Oracle, Microsoft Dynamics | P3 | NOT STARTED |

---

## Risk Considerations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Biometric vendor lock-in | High | Abstract biometric layer, evaluate multiple vendors |
| Government API instability | High | Implement robust retry logic, caching, fallback procedures |
| Offline sync conflicts | Medium | Design clear conflict resolution rules, user notification |
| IoT device diversity | Medium | Build abstraction layer, support major protocols |
| Data privacy regulations | High | Privacy-by-design, consent management, regional compliance |
| Internet connectivity | High | Offline-first architecture, USSD fallback |
| Farmer digital literacy | Medium | Simple UI/UX, local language support, training programs |
| Fraud attempts | High | Multi-layer verification, anomaly detection, audit trails |

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Farmer registration completion rate | > 90% | Measuring |
| System uptime | 99.9% | Operational |
| API response time (p95) | < 500ms | Measuring |
| Offline sync success rate | > 99% | Basic queue built |
| Fraud detection rate | > 95% | Rules engine built |
| User satisfaction (NPS) | > 40 | Not yet measured |
| Mobile app crash rate | < 0.1% | TWA stable |
| E2E test pass rate | 100% | 12/12 flows passing |
| KYC processing time | < 48hrs | Queue built, measuring |

---

## Phase Dependencies

```
Phase 1 (Foundation) ──── DONE
         │
         v
Phase 2 (KYC/Farms) ──── DONE
         │
         ├──> Phase 3 (Operations) ──── 35% done
         │         │
         │         ├──> Phase 9 (Back Office) ──── NEW, can start now
         │         │
         │         └──> Phase 4 (Financial) ──── depends on 3.3, 3.4
         │
         ├──> Phase 5 (Advanced Tech) ──── 15% done
         │
         └──> Phase 7 (Communication) ──── 40% done

Phase 4 + 5 + 6 ──> Phase 8 (Admin & Go-Live)
```

---

## Recommended Next Steps

### Immediate Priority (can start now):
1. **Phase 9 / BO-1: Back Office Portal** - Auth + Dashboard + Farmer Management
   - Most backend APIs already exist
   - Provides immediate operational value for scheme administrators
   - Unblocks KYC review workflow (currently no UI for reviewers)

2. **Phase 9 / BO-2: KYC Review Interface**
   - Critical for operational readiness
   - Backend review queue already built

3. **Phase 9 / BO-3: Eligibility Scheme Management**
   - Backend fully built, needs admin UI for scheme configuration

### Medium Priority:
4. **Phase 3.3: Complete Task Management** - Worker assignment, GPS verification
5. **Phase 7.1: SMS/Push Integration** - Connect notification service to delivery channels
6. **Phase 6.1: Market Prices** - Wire market screen to real data

### Lower Priority (future phases):
7. **Phase 3.2: Livestock Management** - New service implementation
8. **Phase 3.4: Inventory Management** - New service implementation
9. **Phase 4: Financial Services** - Significant new development
10. **Phase 5: Advanced Tech** - AI, IoT, satellite integrations
