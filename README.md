# GeoTrack — Last-Mile Logistics Platform

A last-mile delivery system for a transport and distribution operator. It covers the full lifecycle of a shipment: the **client** requests a pickup by email, the **administrator** accepts it and imports the orders, the **warehouse** validates the goods on arrival, and the **driver** picks up, delivers, and closes their route — every state traced, from a web panel and a mobile app.

I designed and built the entire system as its only engineer — backend, web panel, mobile app, infrastructure — and then acted as my own security engineer: threat modeling, control design, vulnerability scanning, remediation, and re-testing.

**Stack:** Python · FastAPI · PostgreSQL · React 19 + TypeScript · React Native (Expo) · Docker · Nginx · GitHub Actions

---

## 1. What it does

GeoTrack coordinates three roles around a single order:

| Role | Works in | Responsibilities |
| --- | --- | --- |
| **Administrator** | Web panel | Accepts requests (Excel), groups by zone, assigns routes, resolves incident reports, dispatches roadside assistance, reviews KPIs and settlements. |
| **Warehouse** | Web panel | Builds pickup routes, performs manual intake of collected goods (flagging shortages), manages returns. |
| **Driver** | Mobile app | Receives the assigned route, optimizes stop order from current location, collects with photos, delivers with proof of delivery, reports failures and breakdowns. |

### Order pipeline

```
Request (email + Excel)
      │  admin ACCEPTS
      ▼
TO_PICK_UP ──────────────► warehouse builds pickup route
      │                        │  driver collects (photos)
      │                        ▼
      │                    PICKED_UP ──► warehouse performs MANUAL INTAKE
      │                                     │  shortage → FLAGGED
      ▼                                     ▼  complete → READY_TO_SHIP
(background geocoding)                         │  admin groups by ZONE and dispatches
                                               ▼
                                          ASSIGNED ──► driver optimizes ──► EN_ROUTE
                                                                              │
                                                                  delivery ◄──┤
                                                          DELIVERED / FAILED  │
                                                                              ▼
                                                                        end-of-day close
```

A `FAILED` order can be **rescheduled** (back to `READY_TO_SHIP`) or **cancelled**.

### Design decisions worth calling out

- **Custom routing, not a paid API.** Stop order is computed with a nearest-neighbour algorithm over Haversine distance, calculated **from the driver's live position**. No dependency on Google Directions — lower cost, no rate limits, and full control over the heuristic.
- **Geocoding with graceful degradation.** Google Geocoding when an API key is present, Nominatim/OSM as a free fallback, backed by an address cache so the same address is never billed twice.
- **Roadside assistance with a deliberate authority split.** A driver reporting a breakdown pauses their own route. The admin can *dispatch help* but **cannot resume the route** — only the driver can. This is a separation-of-duties decision, not a UI limitation: the person with ground truth about vehicle safety is the only one who can declare it safe to continue.
- **Navigation is delegated.** Turn-by-turn is deep-linked out to Google Maps or Waze per stop rather than reimplemented.

---

## 2. Architecture

```
geotrack/
├── backend/    REST API — FastAPI + PostgreSQL + SQLAlchemy/Alembic   (dockerized)
├── frontend/   Admin & warehouse web panel — React 19 + Vite + Tailwind (Nginx, dockerized)
├── mobile/     Driver app — Expo SDK 52 + React Native + TypeScript    (not dockerized)
└── docker-compose.yml
```

| Layer | Technologies |
| --- | --- |
| **Backend** | FastAPI · SQLAlchemy · Alembic · PostgreSQL · JWT (Argon2) · geopy |
| **Frontend** | React 19 · Vite · Tailwind CSS 4 · React Router · Recharts · Google Maps / Leaflet |
| **Mobile** | Expo SDK 52 · React Native · TypeScript · expo-router · React Query · react-native-maps |
| **Infra** | Docker Compose · Nginx reverse proxy · GitHub Actions CI |

**The browser never talks to the API directly.** Nginx (port `8080`) serves the SPA and proxies `/api`, `/media` and `/socket.io` to the backend. Everything is same-origin: no CORS configuration to get wrong, and no hardcoded `localhost` baked into the production bundle.

### Design system

The web panel is built on **frontend-geotrack**, an in-house component library (12 components: `Button`, `Card`, `StatCard`, `EstadoBadge`, `Modal`, `PageHeader`, `Input`, `PasswordInput`, `Badge`, `Logo`, `Skeleton`, `SkeletonStat`) with 120 design tokens. Components are configured through props rather than loose utility classes, so visual language stays consistent as the panel grows. `EstadoBadge` in particular takes an order state code and derives its own colour, which keeps status rendering identical everywhere it appears.

---

## 3. Security

Security was designed in from the start rather than bolted on. This section documents the threat model, the controls, and the vulnerability work I ran against my own code.

### Threat model

| Threat | Why it matters here | Control |
| --- | --- | --- |
| Unauthorized access to shipment data | Routes, client addresses and settlement figures are commercially sensitive | JWT authentication + RBAC across three roles |
| Credential compromise | Drivers use the app on personal devices in the field | Argon2 password hashing; tokens stored via `expo-secure-store`, never in plain storage |
| Privilege escalation between roles | A driver reaching admin endpoints could reassign or cancel deliveries | Role checks enforced server-side on every protected endpoint |
| Injection through user-supplied input | Endpoints accept free-text search, addresses, and imported Excel data | Parameterized queries throughout; schema validation at the API boundary |
| Insider misuse by legitimate users | An authenticated user can reassign, reschedule or cancel orders | Audit logging over every state transition |
| API key abuse | Google Maps/Geocoding keys are billable | Keys restricted by referrer and by API, with quota caps |

### Access control

- **JWT bearer authentication** with role-based access control across `admin`, `warehouse` and `driver`.
- **Separation of duties** enforced in the domain logic, not just the UI — the breakdown/resume split described above is the clearest example.
- **Least privilege**: each role's endpoints expose only the operations that role needs.

### Cryptography

- **Passwords:** Argon2 — chosen over bcrypt for its memory-hardness against GPU-accelerated cracking.
- **In transit:** TLS terminated at the reverse proxy.
- **Mobile token storage:** `expo-secure-store` (Keychain / Keystore), not `AsyncStorage`.
- **Secrets:** injected through environment variables, never committed. `.env` is gitignored.

### Audit logging

Every state transition on an order writes an audit record capturing actor, action, target and timestamp. This makes it possible to reconstruct who changed what and when, and to surface patterns — such as a single account cancelling an unusual number of deliveries — that no single request would reveal.

### Vulnerability management

Testing was **manual** — no automated scanners. I reviewed endpoints, application flows and code by hand against the OWASP Top 10, classified what I found, fixed it, and re-tested to confirm the fix held. Automating this in CI is on the roadmap (see Known gaps).

**Finding — real-time fleet positions exposed on the public landing page**

| | |
| --- | --- |
| **Severity** | High |
| **Category** | Broken Access Control · Insecure Design (OWASP 1 and 6) |
| **Where** | Public landing page, no authentication required |

The landing page fronts several portals, and it carried a live map of vehicles moving along their routes. It was there as an engagement feature — the product showing off what it does — and it worked exactly as intended.

That was the problem. The map served **real positions of loaded delivery vehicles to anyone on the internet**, with no login. A continuously updating feed of where cargo is, refreshed as it moves, is reconnaissance for targeted theft. No authorization check was missing in the technical sense: the feature was designed to be public, and the design itself was the vulnerability.

**Remediation:** the public map now runs on **simulated data**. It still demonstrates what the platform does, so the marketing value is intact, but real vehicle positions are served only inside the authenticated portals, to the roles that operate them.

**Verified:** ✅ Re-tested — the public endpoint no longer returns live fleet data.

> This one did not come from reading code or running a tool. It came from asking who benefits from this data being visible, and noticing that the answer included people the operator would not want looking. A scanner cannot flag "this feature works as designed and that is the issue."

### OWASP Top 10 coverage (2025)

Tested and addressed **8 of 10** categories:

| # | Category | Status |
| --- | --- | --- |
| 1 | Broken Access Control | ✅ Tested — both findings above fall here |
| 2 | Security Misconfiguration | ✅ Tested |
| 3 | Software Supply Chain Failures | ❌ Not covered — no dependency scanning in place |
| 4 | Cryptographic Failures | ✅ Tested — Argon2, TLS, secure token storage |
| 5 | Injection | ✅ Tested — parameterized queries, boundary validation |
| 6 | Insecure Design | ✅ Tested — separation of duties in the assistance flow |
| 7 | Authentication Failures | ✅ Tested — JWT lifetime, password handling |
| 8 | Software & Data Integrity Failures | ❌ Not covered |
| 9 | Logging & Alerting Failures | ✅ Tested — audit trail over state transitions |
| 10 | Mishandling of Exceptional Conditions | ✅ Tested — error responses reveal no internals |

Categories 3 and 8 are untested. Both need tooling I have not wired in yet — dependency and artifact scanning — rather than analysis I skipped.

### Known gaps

Stated plainly, because a security document that claims completeness isn't credible:

- **No automated test suite.** Verification is currently build- and typecheck-based (below). This is the largest gap.
- **All security testing is manual.** It does not re-run on every change, so a regression could reach `main` unnoticed.
- **No dependency or artifact scanning**, which is why OWASP categories 3 and 8 are untested.
- **No centralized log aggregation.** Audit records live in the database; shipping them to a SIEM would make anomaly detection continuous rather than manual.
- **Nothing is wired into CI yet.** GitHub Actions already runs build and quality checks; adding dependency scanning and SAST there is the obvious next step.
- **Authorization is enforced per-handler.** A policy middleware would make it structurally impossible to forget a check on a new endpoint.

---

## 4. Requirements

| To run… | You need |
| --- | --- |
| Backend + web panel | **Docker Desktop** (Compose v2). Python and Node run inside the containers. |
| Database | Included (`db` container, PostgreSQL 15), or bring your own via `DATABASE_URL`. |
| Mobile app (development) | **Node 18+**, **Expo Go** on the phone, PC and phone on the same WiFi. |
| Mobile app (native maps, background location) | An Expo **dev build** (`eas build`) — Expo Go does not support native maps. |
| Google Maps / Geocoding (optional) | A Google Cloud project with billing enabled + restricted API keys. |
| Email intake (optional) | An IMAP/SMTP mailbox (on Gmail, an app password). |

---

## 5. Setup

### 5.1 Clone and configure

```bash
git clone https://github.com/SebastianUC202120472/Geotrack.git
cd Geotrack
cp .env.example .env    # then fill in your own values
```

| Group | Variables | Notes |
| --- | --- | --- |
| **Database** | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` | Host is `db` (the Compose service name), **not** `localhost`. |
| **Auth / JWT** | `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Generate a strong key: `python -c "import secrets; print(secrets.token_hex(32))"` |
| **Initial admin** | `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Created on first boot if absent. **Set both to your own values — there are no defaults, by design.** |
| **Panel maps** | `VITE_GOOGLE_MAPS_KEY` | Empty = OpenStreetMap (free). With key = Google Maps. |
| **Backend geocoding** | `GOOGLE_GEOCODING_KEY` | Empty = Nominatim/OSM (free, less precise). With key = Google. |
| **Email (optional)** | `MAIL_ENABLED`, `MAIL_*`, `IMAP_*`, `SMTP_*` | With `MAIL_ENABLED=false` the inbox is inactive and everything else works. |

> **Never commit `.env`.** It is gitignored. Restrict your Google keys by referrer and API, and set quota caps — an unrestricted billable key in a public repo is the fastest way to lose a Google Cloud account.

### 5.2 Database options

- **Local (default):** leave `DATABASE_URL` pointing at `db`. The container runs PostgreSQL 15 with a persistent volume.
- **Remote (Supabase or similar):** replace `DATABASE_URL` with your provider's connection string, e.g.

  ```
  DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-...pooler.supabase.com:5432/postgres?sslmode=require
  ```

  URL-encode special characters in the password (`@` becomes `%40`).

The schema is created on boot (`create_all`) and the initial admin is seeded. Alembic migrations are versioned for environments already managed with Alembic.

### 5.3 Run

```bash
docker compose up --build
```

| Service | URL |
| --- | --- |
| Web panel | http://localhost:8080 |
| API + Swagger | http://localhost:8000/docs |

Sign in with the admin credentials you set in `.env`.

### 5.4 Google keys (optional)

Everything works without Google — the panel falls back to OSM and geocoding to Nominatim. To enable Google:

1. In Google Cloud Console: create a project, enable billing, and enable **Maps JavaScript API** (panel), **Geocoding API** (backend), and **Maps SDK for Android/iOS** (mobile).
2. Create keys and **restrict them** — HTTP referrers for the panel, specific API plus a quota cap for geocoding.
3. Set each key and rebuild:
   - Panel → `VITE_GOOGLE_MAPS_KEY` → `docker compose up -d --build frontend`
   - Backend → `GOOGLE_GEOCODING_KEY` → `docker compose up -d --build backend`
   - Mobile → `EXPO_PUBLIC_GOOGLE_MAPS_KEY` in `mobile/.env` (applied at `eas build`)

### 5.5 Driver mobile app

```bash
cd mobile
npm install
npx expo install --check          # align native versions with the SDK
# Create mobile/.env with your machine's LAN IP (not localhost):
#   EXPO_PUBLIC_API_URL=http://192.168.x.x:8000/api
npx expo start -c                 # scan the QR with Expo Go, same WiFi
```

Native maps and background location require a dev build: `eas build --platform android`. See `mobile/README.md`.

---

## 6. Common commands

| Task | Command |
| --- | --- |
| Bring everything up | `docker compose up --build` |
| Run detached | `docker compose up -d --build` |
| Rebuild panel only | `docker compose up -d --build --no-deps frontend` |
| Rebuild backend only | `docker compose up -d --build backend` |
| Follow logs | `docker compose logs -f backend` |
| Stop | `docker compose down` |
| Stop and wipe local DB | `docker compose down -v` |
| Run the mobile app | `cd mobile && npx expo start -c` |

The panel is a static build served by Nginx, so web changes require rebuilding its image. The backend only needs rebuilding when dependencies, endpoints or tables change.

**Verification before calling anything done** (no automated test suite yet — see Known gaps):

```bash
cd frontend && npm run build && npm run lint          # Frontend
docker compose run --rm backend python -c "import app.main"   # Backend imports
cd mobile && npx tsc --noEmit                          # Mobile typecheck
```

---

## 7. End-to-end walkthrough

1. **Request.** A client emails an Excel of orders. It lands in the panel **Inbox**.
2. **Accept (admin).** The admin opens the thread and accepts it by uploading the Excel → orders are created as `TO_PICK_UP` and geocoded in the background.
3. **Build pickup route (warehouse).** Requests are assigned to a driver and vehicle.
4. **Collect (driver).** The driver opens the pickup route, optimizes from their location, and registers receipt with photos → `PICKED_UP`.
5. **Manual intake (warehouse).** The warehouse reviews the photo gallery, flags shortages (→ `FLAGGED`) and confirms; the rest move to `READY_TO_SHIP`.
6. **Dispatch (admin).** In zone grouping, the admin picks a district and creates a delivery route → `ASSIGNED`.
7. **Deliver (driver).** The driver optimizes the route, navigates stop by stop, and marks `DELIVERED` with proof of delivery or `FAILED` with a reason.
8. **Reports and assistance.** The admin resolves reports and reschedules or cancels failures. On a breakdown, the driver reports it (route pauses), the admin dispatches help, and the driver resumes.
9. **End of day.** With no stops pending, the driver closes the route.

Throughout, the panel surfaces a KPI dashboard, live fleet tracking, per-order traceability, and client settlements.

> **Testing the driver flow without the app:** until a dev build exists, the driver side can be exercised through the `/api/conductor/*` endpoints (login → manifest → optimize → mark delivered/failed → report → assistance → resume). Everything reflects in the panel. See Swagger at http://localhost:8000/docs.

---

## 8. Git workflow

The repository follows **Gitflow**: `main` (production) ← `develop` (integration) ← `feature/*` branches. Features merge into `develop` with `--no-ff` to preserve branch topology; `develop` is promoted to `main` per release. 480+ commits to date, with build and quality checks running in GitHub Actions.

---

Built by **Sebastián Urteaga Castañeda** — [LinkedIn](https://www.linkedin.com/in/sebastian-urteaga/)