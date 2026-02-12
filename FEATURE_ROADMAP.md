# AgriScheme Pro - Feature Development Roadmap

**Version:** 2.1.0
**Last Updated:** 2026-02-12
**Status:** Active Development

---

## Current Implementation Status

### Fully Implemented Features

#### 1. Authentication & User Management
- **Service:** Auth Service (23 endpoints, 8 models, 3 migrations)
- **Backend:** Complete
- **Mobile:** Complete
- **Status:** Production-ready
- **Features:**
  - Email & phone-based registration (with PIN)
  - Login/logout with JWT tokens
  - Token refresh mechanism
  - Password reset with token expiration
  - TOTP two-factor authentication (setup, enable, disable, verify)
  - Role-based access control (RBAC) with granular permissions
  - Admin role & permission management
  - User-role assignment
  - Login attempt tracking with account lockout (brute force protection)
  - Audit logging for all security actions
  - Multi-tenant support
  - IP tracking and user agent logging
- **API Endpoints:**
  - POST `/auth/register`, `/auth/register/phone`, `/auth/login`, `/auth/login/phone`
  - POST `/auth/refresh`, `/auth/logout`
  - POST `/auth/2fa/setup`, `/auth/2fa/enable`, `/auth/2fa/disable`, GET `/auth/2fa/status`
  - POST `/auth/password/reset-request`, `/auth/password/reset-confirm`, `/auth/password/change`
  - GET `/users/me`, PATCH `/users/me`, GET `/users`, GET `/users/{user_id}`
  - POST `/admin/roles`, GET `/admin/roles`, GET/DELETE `/admin/roles/{role_id}`
  - POST/GET `/admin/permissions`
  - POST/DELETE `/admin/roles/{role_id}/permissions[/{permission_id}]`
  - POST/DELETE/GET `/admin/users/{user_id}/roles[/{role_id}]`
  - GET `/admin/users/{user_id}/permissions`

#### 2. Farmer Profile Management
- **Service:** Farmer Service
- **Backend:** Complete
- **Mobile:** Complete
- **Status:** Production-ready
- **Features:**
  - Farmer profile creation and editing
  - Profile viewing with KYC status filtering
  - Link farmer to auth user account
  - Pagination and search
- **API Endpoints:**
  - POST `/farmers`, GET `/farmers`, GET `/farmers/{farmer_id}`
  - GET `/farmers/by-user/{user_id}`, PATCH `/farmers/{farmer_id}`

#### 3. Farm Registration Workflow
- **Service:** Farmer Service (20+ endpoints)
- **Backend:** Complete
- **Mobile:** Complete (8-screen wizard)
- **Status:** Production-ready
- **Features:**
  - Multi-step registration state machine (8 steps: LOCATION to COMPLETE)
  - GPS location capture with reverse geocoding
  - Farm boundary mapping (polygon drawing with validation)
  - Land details (size, ownership, use type)
  - Document upload (title deed, lease, etc.)
  - Soil test report management
  - Crop history tracking
  - Farm asset tracking (equipment, vehicles, infrastructure, storage)
  - Field visit scheduling with GPS check-in and location verification
  - Review and submit workflow
  - Soft delete support
- **Mobile Screens:**
  - `/farms/add` - Start registration
  - `/farms/[id]/index` - Farm location
  - `/farms/[id]/boundary` - Boundary mapping
  - `/farms/[id]/land-details` - Land information
  - `/farms/[id]/documents` - Document upload
  - `/farms/[id]/soil-water` - Soil & water details
  - `/farms/[id]/crops` - Crop history
  - `/farms/[id]/review` - Final review

#### 4. KYC (Know Your Customer)
- **Service:** Farmer Service (15+ endpoints)
- **Backend:** Complete
- **Mobile:** Complete (5-screen wizard)
- **Status:** Production-ready
- **Features:**
  - Full KYC workflow state machine (PENDING, IN_REVIEW, APPROVED, REJECTED, EXPIRED)
  - Personal information collection
  - National ID / passport document upload with OCR extraction
  - Bank information capture
  - Biometric capture and verification with quality scoring
  - External verification integration
  - Document verification with OCR
  - KYC review queue management
  - Admin approval/rejection interface
  - Verification comments
- **API Endpoints:**
  - POST `/kyc/{farmer_id}/start`, GET `/kyc/{farmer_id}/status`
  - POST `/kyc/{farmer_id}/step/complete`
  - Biometric capture & verification endpoints
  - Document verification with OCR
  - External verification integration
  - KYC review queue management
- **Mobile Screens:**
  - `/kyc/index` - KYC status dashboard
  - `/kyc/personal-info` - Personal information form
  - `/kyc/documents` - Document upload
  - `/kyc/bank-info` - Banking details
  - `/kyc/submit` - Review & submit

#### 5. Eligibility Assessment
- **Service:** Farmer Service
- **Backend:** Complete
- **Mobile:** Complete
- **Status:** Production-ready
- **Features:**
  - Program eligibility checking with rule-based scoring
  - Risk scoring for credit decisions
  - Multiple program support
  - Eligibility history
  - Credit assessment engine
- **API Endpoints:**
  - GET `/eligibility`, POST `/eligibility/check`, GET `/eligibility/{id}`

#### 6. Document Management
- **Service:** Farmer Service
- **Backend:** Complete
- **Mobile:** Integrated in farm registration and KYC
- **Status:** Production-ready
- **Features:**
  - Document upload (images, PDFs) with GPS metadata
  - Document categorization (NATIONAL_ID, PASSPORT, LAND_TITLE, etc.)
  - Document verification status tracking
  - Storage service integration
- **API Endpoints:**
  - POST `/documents`, GET `/documents/{farm_id}`, DELETE `/documents/{doc_id}`

#### 7. GIS Services
- **Service:** GIS Service (8 endpoints, standalone computation)
- **Backend:** Complete
- **Mobile:** Integrated in farm registration
- **Status:** Production-ready
- **Features:**
  - Reverse geocoding (coordinates to county/sub-county/ward)
  - Kenya boundary validation (checks coordinates against Kenya GIS boundary)
  - GeoJSON polygon validation and normalization
  - Geodetic area calculation (acres, hectares, sq meters)
  - Point-in-polygon with distance to nearest edge
  - Boundary overlap detection with area/percentage
  - Polygon self-intersection checking
  - Douglas-Peucker polygon simplification
  - Buffer boundary generation
- **API Endpoints:**
  - POST `/reverse-geocode`, `/validate-coordinates`, `/validate-polygon`
  - POST `/calculate-area`, `/point-in-boundary`, `/check-overlap`
  - POST `/simplify-polygon`, `/buffer-boundary`

#### 8. Crop Planning System
- **Service:** Farmer Service (30+ endpoints, 6 models)
- **Backend:** Complete
- **Mobile:** Complete (9 screens + 4 components)
- **Status:** Production-ready
- **Features:**
  - Crop calendar templates with regional variations
  - Crop plan lifecycle (Draft, Active, Completed, Archived)
  - Growth stage tracking (Germination, Vegetative, Flowering, Harvest)
  - Planned activity management (13 activity types, auto-generation from templates)
  - Activity completion with GPS verification and photo documentation
  - Input requirement calculation (seed, fertilizer, pesticide)
  - QR code verification for certified inputs
  - Procurement status and cost tracking
  - Irrigation scheduling (7 methods: drip, sprinkler, furrow, etc.)
  - Auto-generation based on crop needs with soil moisture tracking
  - Crop plan alerts (activity reminders, overdue, weather, planting windows, harvest)
  - Dashboard with plan overview, upcoming/overdue activities, cost summaries
  - Plan statistics
- **API Endpoints:**
  - Templates: GET/POST `/crop-planning/templates`, GET/PATCH `/crop-planning/templates/{id}`, GET `/crop-planning/templates/recommend`
  - Plans: GET/POST `/crop-planning/plans`, GET/PATCH/DELETE `/crop-planning/plans/{id}`
  - Plan actions: POST `/crop-planning/plans/{id}/activate`, `/advance-stage`, `/complete`
  - GET `/crop-planning/plans/{id}/statistics`
  - Activities: GET/POST `/crop-planning/plans/{id}/activities`, GET/PATCH `/crop-planning/activities/{id}`
  - POST `/crop-planning/activities/{id}/complete`, `/skip`
  - GET `/crop-planning/activities/upcoming`
  - Inputs: GET/POST `/crop-planning/plans/{id}/inputs`, GET/PATCH `/crop-planning/inputs/{id}`
  - POST `/crop-planning/inputs/{id}/verify-qr`, GET `/crop-planning/calculate-inputs`
  - Irrigation: GET/POST `/crop-planning/plans/{id}/irrigation`, POST `/crop-planning/plans/{id}/irrigation/generate`
  - GET/PATCH `/crop-planning/irrigation/{id}`, POST `/crop-planning/irrigation/{id}/complete`
  - Alerts: GET `/crop-planning/alerts`, POST `/crop-planning/alerts/{id}/read`, `/dismiss`
  - Dashboard: GET `/crop-planning/dashboard`
- **Mobile Screens:**
  - `/crop-planning/index` - Dashboard with active plans
  - `/crop-planning/create` - New plan wizard
  - `/crop-planning/[id]/index` - Plan details
  - `/crop-planning/[id]/activities` - Activity list
  - `/crop-planning/[id]/activity-complete` - Activity completion form
  - `/crop-planning/[id]/inputs` - Input management
  - `/crop-planning/[id]/irrigation` - Irrigation schedule
  - `/crop-planning/alerts` - Alerts view
- **Mobile Components:**
  - GrowthStageTimeline, PlanCard, StatusBadge, ActivityCard

#### 9. Task Management
- **Service:** Task Service (9 endpoints, 2 models, 1 migration)
- **Backend:** Complete
- **Mobile:** Complete (integrated in Tasks tab)
- **Status:** Production-ready
- **Features:**
  - Task CRUD with soft delete
  - Task filtering by farmer, status, category, priority range
  - Task categories (MAINTENANCE, ADMINISTRATIVE, EQUIPMENT, INFRASTRUCTURE, PROCUREMENT, INSPECTION, LIVESTOCK, GENERAL, OTHER)
  - Priority levels (1-10 scale)
  - Status workflow (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)
  - Recurrence support (NONE, DAILY, WEEKLY, BIWEEKLY, MONTHLY, QUARTERLY, YEARLY)
  - Task comments for collaboration
  - Task statistics (counts by status/category)
  - Due date and completion tracking
  - Worker assignment
- **API Endpoints:**
  - GET `/tasks`, POST `/tasks`, GET `/tasks/stats`
  - GET `/tasks/{task_id}`, PATCH `/tasks/{task_id}`, DELETE `/tasks/{task_id}`
  - POST `/tasks/{task_id}/comments`, GET `/tasks/{task_id}/comments`

#### 10. CI/CD & Deployment
- **Status:** Complete
- **Features:**
  - GitHub Actions CI (lint, test, build for backend + mobile)
  - Docker image builds (auth, farmer services)
  - Auto-deploy workflow via Coolify API (detects changed services, deploys in parallel)
  - Manual dispatch with explicit service list
  - Coolify-based deployment (15 services containerized)
  - Nginx API gateway routing
  - TWA (Trusted Web Activity) APK project
  - PWA deployment workflow

---

### Mobile App Infrastructure
- **Framework:** Expo / React Native with Expo Router (file-based routing)
- **Navigation:** 5-tab layout (Home, Farms, Market, Tasks, Profile)
- **State:** Zustand stores (auth, farmer)
- **API:** Axios client with interceptors for auth tokens and service routing
- **Modes:** Unified gateway, production individual services, or development direct ports
- **Platforms:** Android APK (native + TWA), iOS, Web/PWA
- **Components:** Button, Input, StepIndicator, PhotoCapture, BoundaryMap + crop planning components
- **Admin:** Next.js web-admin app (scaffolded with Tailwind, minimal implementation)

---

## Not Yet Implemented (Stub Services)

All 11 services below are identical stubs: a FastAPI app with only `GET /` and `GET /health` endpoints, no routers, no models, no database, no business logic.

### HIGH Priority

#### Market Service
- **Container:** 10.0.1.36
- **Mobile:** Empty tab placeholder
- **Priority:** HIGH
- **Effort:** 3-4 weeks
- **Planned Features:**
  - Crop price listings and price history/trends
  - Produce listings (create, manage, search)
  - Buyer/seller matching and connections
  - Location-based market matching
  - Market news and demand information
  - External market price API integration
- **Planned Mobile Screens:**
  - `/market/prices` - Current market prices
  - `/market/listings` - My produce listings
  - `/market/create-listing` - List produce for sale
  - `/market/buyers` - Find buyers
  - `/market/trends` - Price trends/charts

#### Notification Service
- **Container:** 10.0.1.57
- **Mobile:** No integration
- **Priority:** HIGH
- **Effort:** 2-3 weeks
- **Planned Features:**
  - Push notifications (Firebase Cloud Messaging)
  - SMS notifications (Africa's Talking or Twilio)
  - Email notifications (SendGrid or AWS SES)
  - In-app notification center
  - Notification preferences per user
  - Notification history and read status
  - Multi-channel delivery with queue (Redis/RabbitMQ)
  - Integration points: crop planning alerts, KYC updates, market price alerts, payment confirmations
- **Planned Mobile Screens:**
  - `/notifications` - Notification center
  - `/profile/notifications` - Notification preferences

#### Financial Service
- **Container:** 10.0.1.42
- **Priority:** HIGH
- **Effort:** 4-5 weeks
- **Planned Features:**
  - Income/expense recording and categorization
  - Transaction history
  - Financial reports and summaries
  - M-Pesa integration (STK Push, callbacks)
  - Loan application workflow
  - Credit scoring integration
  - Subsidy tracking and disbursement
  - Transaction encryption and PIN/biometric confirmation
  - Audit logging
- **Planned Mobile Screens:**
  - `/financial/dashboard` - Financial overview
  - `/financial/transactions` - Transaction history
  - `/financial/income` - Record income
  - `/financial/expense` - Record expense
  - `/financial/reports` - Financial reports
  - `/financial/loans` - Loan applications

### MEDIUM Priority

#### Inventory Service
- **Container:** 10.0.1.29
- **Priority:** MEDIUM
- **Effort:** 2-3 weeks
- **Planned Features:**
  - Input stock management (seeds, fertilizer, pesticides)
  - Harvested produce tracking
  - Farm equipment registry
  - Stock level tracking with low stock alerts
  - Usage recording and reorder management
  - Integration with crop planning (input procurement) and market service (produce listings)
- **Planned Mobile Screens:**
  - `/inventory` - Dashboard
  - `/inventory/inputs` - Input stock
  - `/inventory/produce` - Harvested produce
  - `/inventory/equipment` - Farm equipment
  - `/inventory/add` - Add inventory item

#### Livestock Service
- **Container:** 10.0.1.33
- **Priority:** MEDIUM
- **Effort:** 3-4 weeks
- **Planned Features:**
  - Animal registration and records
  - Health records and veterinary tracking
  - Breeding records and lineage
  - Feed management
  - Vaccination scheduling
  - Production tracking (milk, eggs, etc.)
  - Integration with inventory (feed stock), financial (sales), notifications (vaccination reminders)
- **Planned Mobile Screens:**
  - `/livestock` - Dashboard
  - `/livestock/animals` - Animal list
  - `/livestock/[id]` - Animal details
  - `/livestock/health` - Health records
  - `/livestock/breeding` - Breeding records
  - `/livestock/production` - Production tracking

#### Traceability Service
- **Container:** 10.0.1.31
- **Priority:** MEDIUM
- **Effort:** 3-4 weeks
- **Planned Features:**
  - QR code generation for produce batches
  - Batch tracking through supply chain
  - Supply chain event logging
  - Certification tracking (GlobalGAP, organic, etc.)
  - Product journey history
  - Consumer-facing traceability API
- **Planned Mobile Screens:**
  - `/traceability` - Batch management
  - `/traceability/create` - Create batch with QR code

#### Compliance Service
- **Container:** 10.0.1.59
- **Priority:** MEDIUM
- **Effort:** 3-4 weeks
- **Planned Features:**
  - Regulatory compliance tracking
  - Certification management
  - Audit trail
  - Report generation
  - Deadline reminders
  - Documentation repository
- **Planned Mobile Screens:**
  - `/compliance` - Certifications dashboard
  - `/compliance/documents` - Compliance docs

#### Integration Service
- **Container:** 10.0.1.39
- **Priority:** MEDIUM
- **Effort:** Variable
- **Planned Features:**
  - Payment gateway integrations (M-Pesa, bank transfer)
  - Weather API integration
  - Government systems integration
  - Third-party data source connectors
  - Webhook management
  - External API adapters

### LOW Priority

#### AI Service
- **Container:** 10.0.1.58
- **Priority:** LOW
- **Effort:** Variable (requires ML expertise)
- **Planned Features:**
  - Crop disease detection (image classification)
  - Yield prediction (regression models)
  - Optimal planting time recommendations (time series + weather)
  - Pest identification (image classification)
  - Soil health assessment
  - Weather-based recommendations
- **Planned Mobile Screens:**
  - `/ai/disease-detection` - Photo-based diagnosis
  - `/ai/recommendations` - AI recommendations

#### IoT Service
- **Container:** 10.0.1.40
- **Priority:** LOW
- **Effort:** 3-4 weeks (requires hardware partnerships)
- **Planned Features:**
  - Device registration and management
  - Time-series sensor data ingestion
  - Soil moisture monitoring
  - Weather station integration
  - Data aggregation and alert rules engine
  - Real-time data visualization
  - Communication protocols (MQTT, HTTP)
- **Planned Mobile Screens:**
  - `/iot` - Device dashboard
  - Real-time sensor readings
  - Historical charts
  - Alert configuration

#### Farm Service
- **Container:** 10.0.1.43
- **Priority:** LOW
- **Effort:** 2-3 weeks
- **Note:** Significant overlap with farm management in Farmer Service. Needs scope clarification or merging.
- **Planned Features:**
  - Farm operations management
  - Asset management (machinery, buildings)
  - Maintenance scheduling
  - Farm analytics
  - Resource allocation

---

## Infrastructure Improvements Pending

### High Priority
1. **HTTPS/SSL Certificate** (1-2 days) - Currently using HTTP only on port 8888
2. **Push Notifications** (1 week) - Firebase Cloud Messaging setup
3. **Offline Mode Support** (2-3 weeks) - Local SQLite, data sync, conflict resolution
4. **API Documentation** (1 week) - Swagger UI for all services, OpenAPI specs

### Medium Priority
5. **Redis Caching Layer** (1 week) - Cache frequently accessed data, session storage
6. **Rate Limiting** (3-4 days) - Per-user/IP limits, abuse protection
7. **Monitoring Dashboard** (2 weeks) - Prometheus metrics, Grafana dashboards
8. **Centralized Logging** (1 week) - ELK stack or similar, log aggregation

### Lower Priority
9. **Service Discovery** (2 weeks) - Replace hardcoded container IPs with Consul or similar
10. **Horizontal Scaling** (2 weeks) - Load balancer, multiple instances, connection pooling
11. **Message Queue** (2 weeks) - RabbitMQ or Kafka for async processing
12. **GraphQL API** (3-4 weeks) - Optional layer on top of REST for mobile optimization

---

## Mobile App Enhancements Pending

### UX Improvements
1. Dark mode theme support
2. Multi-language (Swahili, English)
3. Onboarding flow for first-time users
4. Help/FAQ section
5. Improved offline indicators

### Authentication
6. Biometric login (Fingerprint/Face ID)
7. Remember me / stay logged in
8. Social login (Google, Facebook) - optional

### Features
9. QR code scanner (traceability, input verification)
10. Camera improvements for document capture
11. Maps optimization (faster boundary drawing)
12. Charts/graphs for data visualization
13. Export reports (PDF/Excel)

---

## Technical Debt

1. Hardcoded container IPs in Nginx gateway
2. No service discovery mechanism
3. No HTTPS (HTTP on port 8888)
4. No rate limiting
5. No request caching
6. Test coverage gaps (only auth service has tests)
7. Web admin app is scaffolded but minimal
8. Task service recurrence support exists in model but auto-generation not implemented
9. API response format inconsistency across services

---

## Summary

| Category | Count | Details |
|----------|-------|---------|
| **Backend services implemented** | 4 | Auth (23 endpoints), Farmer (40+), GIS (8), Task (9) |
| **Backend services stub** | 11 | Market, Notification, Financial, Inventory, Livestock, Traceability, Compliance, Integration, AI, IoT, Farm |
| **Total backend endpoints** | ~80+ | Across 4 implemented services |
| **Mobile screens implemented** | ~30 | Auth, farms, KYC, crop planning, eligibility, tasks, profile |
| **Mobile screens pending** | ~25 | Market, financial, livestock, inventory, notifications, traceability, compliance, AI, IoT |
| **Database migrations** | 12 | Auth (3), Farmer (7), Task (1), GIS (in-memory) |

**What's built:** Complete farmer onboarding pipeline (register, KYC, farm registration, eligibility), full crop planning system with mobile UI, task management, and GIS services.

**Biggest gaps:** Market service, notification service, and financial service are the highest-priority missing pieces that would complete the core farmer experience.

---

**Document Maintained By:** AgriScheme Pro Development Team
**Next Review:** 2026-03-12
