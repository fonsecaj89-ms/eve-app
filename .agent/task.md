# EVE Online Trading Platform - Implementation Tasks

## Phase 1: Infrastructure & Environment Setup
- [ ] Create Docker Compose configuration with all services (postgres, neo4j, redis, backend, frontend, cloudflare tunnel)
- [ ] Set up `.env.example` with all required environment variables
- [ ] Create `.gitignore` for secrets and generated files
- [ ] Configure network topology and service dependencies
- [ ] Set up health checks for all services

## Phase 2: Database & Data Layer
- [ ] Design PostgreSQL schema mappings for SDE data
  - [ ] Create SQLModel models for invTypes
  - [ ] Create SQLModel models for mapSolarSystems
  - [ ] Create SQLModel models for staStations
  - [ ] Create SQLModel models for industryActivityMaterials
  - [ ] Create SQLModel models for invMarketGroups
- [ ] Implement SDE ingestion script (`init_db.sh` and Python ingestion)
- [ ] Set up database connection pooling and session management
- [ ] Create repository layer for data access

## Phase 3: Neo4j Graph Database
- [ ] Design Neo4j graph schema (SolarSystem nodes, GATE relationships)
- [ ] Create ETL script to load topology from Postgres to Neo4j
- [ ] Implement weighted pathfinding with security-based weights
- [ ] Create RouteService for route calculations
- [ ] Test pathfinding with various security profiles

## Phase 4: ESI Client & Rate Limiting
- [ ] Implement Redis-backed Token Bucket algorithm
- [ ] Create ESIClient class with error budget management
- [ ] Implement HTTP 420 lockdown mechanism
- [ ] Add OAuth token refresh logic
- [ ] Create error handling and retry logic
- [ ] Test rate limiting under load

## Phase 5: Backend Core Services
- [ ] Set up FastAPI application structure
- [ ] Implement dependency injection (get_db, get_graph, get_cache)
- [ ] Create MarketService with profit calculations
  - [ ] Implement broker fee calculations
  - [ ] Implement sales tax calculations
  - [ ] Integrate character skills from ESI
- [ ] Create ContractService with appraisal logic
- [ ] Implement UniverseService for item/station resolution

## Phase 6: Backend API Endpoints
- [ ] Create authentication router (OAuth2 flow)
- [ ] Create market router
  - [ ] GET /market/orders endpoint
  - [ ] GET /market/arbitrage endpoint
  - [ ] Background task for market cache updates
- [ ] Create contracts router with appraisal endpoint
- [ ] Create character router (wallet, skills)
- [ ] Create universe router (search, resolve)
- [ ] Create routing router (calculate routes)

## Phase 7: Frontend Infrastructure
- [ ] Initialize Vite + React + TypeScript project
- [ ] Configure Vite for Docker + Cloudflare Tunnel HMR
- [ ] Set up React Router
- [ ] Configure TanStack Query (React Query)
- [ ] Set up Zustand for state management
- [ ] Create base CSS with design tokens

## Phase 8: Frontend Authentication
- [ ] Create AuthContext and useAuth hook
- [ ] Implement OAuth callback handling
- [ ] Create protected route wrapper
- [ ] Build Login page component
- [ ] Add session persistence

## Phase 9: Frontend UI Components
- [ ] Create MainLayout with navigation
- [ ] Build Dashboard view
  - [ ] Wallet balance display
  - [ ] PLEX ticker
  - [ ] Recharts wallet history
- [ ] Build Market View
  - [ ] TanStack Table with virtualization
  - [ ] Filter bar component
  - [ ] Item autocomplete search
- [ ] Build Route View with security visualization
- [ ] Build Contracts View with card layout

## Phase 10: Integration & Testing
- [ ] Test complete authentication flow
- [ ] Test market data fetching and display
- [ ] Test route calculation with Neo4j
- [ ] Test contract appraisal logic
- [ ] Verify ESI rate limiting under load
- [ ] Test HMR over Cloudflare Tunnel

## Phase 11: Documentation & Deployment
- [ ] Create README with setup instructions
- [ ] Document API endpoints
- [ ] Create deployment guide
- [ ] Add environment variable documentation
- [ ] Create troubleshooting guide
