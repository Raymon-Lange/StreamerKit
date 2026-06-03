# StreamerKit Platform Roadmap
## Phases 1–3: API, Deployment, Dashboard

Version: 1.0
Status: Planning

---

# Overview

StreamerKit has evolved beyond a collection of fantasy baseball scripts.

The project already contains:

- ESPN league integration
- Team hitter evaluation
- Team pitcher evaluation
- Free agent analysis
- SP streamer recommendations
- Recent drops analysis
- Roster optimization
- Pitcher start evaluation
- Weekly scoring reports

The next objective is transforming StreamerKit into a self-hosted web application running in the FireHive platform ecosystem.

The initial release will focus on:

1. API Layer
2. Deployment Platform
3. Web Dashboard

Email automation and chatbot capabilities will be implemented in later phases.

---

# Phase 1 — API Layer

## Objective

Expose existing StreamerKit functionality through REST APIs.

## Deliverables

- GET /health
- GET /api/dashboard
- GET /api/streamers
- GET /api/recent-drops
- GET /api/roster-optimizer
- GET /api/pitcher-starts
- GET /api/weekly-scores

## Success Criteria

- Existing scripts continue working
- API endpoints return JSON
- No duplicated logic
- Swagger/OpenAPI documentation available

---

# Phase 2 — Deployment

## Objective

Deploy StreamerKit as a production service within the FireHive homelab platform.

## Target Environment

Initial deployment:

- docker-host.lab

Future option:

- streamerkit.lab

## Deployment Flow

Git Push
→ Build Docker Image
→ Push GHCR
→ SSH Deploy
→ Docker Compose Pull
→ Docker Compose Up

## Success Criteria

- Docker container runs successfully
- Environment variables load correctly
- Health endpoint responds
- GitHub deployment is automated
- Service survives restart

---

# Phase 3 — Dashboard

## Objective

Provide a web interface for StreamerKit.

## Dashboard Pages

### 1. Daily Brief

- Top streamer
- Top waiver target
- Recent drop recommendation
- Lineup recommendation
- Weekly matchup status

### 2. Streamers

- Today's streamers
- Tier ranking
- Matchup information
- Pickup recommendation

### 3. Recent Drops

- Dropped players
- Claim priority
- Recommendation notes

### 4. Roster Optimizer

- Suggested lineup swaps
- Bench upgrades
- Confidence score
- Reasoning

### 5. Weekly Scores

- Current matchup
- League rankings
- Team score
- Median score
- Top-half / bottom-half status

## Frontend

Preferred:

- React
- TypeScript
- Tailwind

## Success Criteria

- All five pages functional
- Data loads from API
- Mobile layout works
- Dashboard deploys with StreamerKit
- Can be used as the daily fantasy homepage

---

# End State

StreamerKit
- Fantasy analysis engine
- FastAPI service layer
- Docker deployment
- GitHub Actions CI/CD
- Web dashboard
