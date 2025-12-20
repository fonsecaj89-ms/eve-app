# EVE Online Trading Platform - Implementation Plan

Based on the comprehensive architectural specification provided, this plan outlines the systematic implementation of a high-frequency trading and industry analytics platform for EVE Online.

## User Review Required

> [!IMPORTANT]
> **EVE Developer Application Registration**
> Before proceeding, you must register an application at [EVE Developers Portal](https://developers.eveonline.com/) and obtain:
> - `ESI_CLIENT_ID`
> - `ESI_SECRET_KEY`
> - Configure callback URL to match your deployment (local: `http://localhost:8000/auth/callback`)
> - Register ALL required scopes listed in Table 2 of the specification

> [!IMPORTANT]
> **Fuzzwork SDE Database Dump**
> The implementation requires the Fuzzwork PostgreSQL conversion of the EVE SDE. You need to:
> 1. Download the latest dump from [Fuzzwork Downloads](https://www.fuzzwork.co.uk/dump/)
> 2. Place the `.sql` or `.dump` file in `backend/data/` directory
> 3. Confirm the filename for the ingestion script configuration

> [!WARNING]
> **Cloudflare Tunnel Token**
> For HMR to function correctly over HTTPS, you need a Cloudflare Tunnel token. Options:
> 1. Create a free Cloudflare account and set up a tunnel
> 2. Skip tunnel setup for local-only development (HMR will work on localhost)
> 3. Provide existing tunnel token if available

## Proposed Changes

### Infrastructure Layer

#### [NEW] [docker-compose.yml](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/docker-compose.yml)

Complete Docker Compose orchestration defining 6 services:

- **postgres-sde**: PostgreSQL 15 with Fuzzwork SDE data, health checks via `pg_isready`
- **neo4j-topology**: Neo4j 5 Community for graph-based route planning
- **redis-cache**: Redis Alpine for ESI rate limiting and response caching
- **backend-api**: Python 3.11 + FastAPI application server
- **frontend-ui**: Node 18 + Vite development server with HMR configuration
- **tunnel** (optional): Cloudflare tunnel for secure public access

All services connected via custom bridge network `eve-net` with named volumes for persistence.

---

#### [NEW] [.env.example](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/.env.example)

Environment variable template covering:
- Database credentials (Postgres, Neo4j, Redis)
- ESI OAuth configuration (Client ID, Secret, Scopes)
- Frontend URL for OAuth callbacks
- Cloudflare tunnel token (optional)
- Application-specific settings (tax rates, default skills)

---

#### [NEW] [.gitignore](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/.gitignore)

Excludes sensitive data, generated files, and Docker volumes:
- `.env` (secrets)
- `backend/data/*.dump`, `backend/data/*.sql` (SDE dumps)
- `postgres_data/`, `neo4j_data/`, `redis_data/` (Docker volumes)
- Standard Python and Node exclusions

---

### Backend - Data Layer

#### [NEW] [backend/app/database.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/database.py)

Database connection setup using SQLModel with async PostgreSQL support:
- SQLAlchemy async engine configuration
- Session factory with dependency injection
- Connection pooling (pool_size=20, max_overflow=40)
- `get_db()` FastAPI dependency

---

#### [NEW] [backend/app/models/sde.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/models/sde.py)

SQLModel ORM mappings for Fuzzwork SDE schema (read-only reference data):

**`InvType`**: Maps `invTypes` table
- Primary key: `type_id`
- Fields: `type_name`, `volume`, `portion_size`, `market_group_id`
- Handles legacy camelCase column names via `Field(sa_column_kwargs)`

**`MapSolarSystem`**: Maps `mapSolarSystems` table
- Primary key: `solar_system_id`
- Fields: `solar_system_name`, `security`, `region_id`
- Relationship to `Region` model

**`StaStation`**: Maps `staStations` table
- Primary key: `station_id`
- Fields: `station_name`, `solar_system_id`, `reprocessing_efficiency`

**`IndustryActivityMaterial`**: Maps `industryActivityMaterials` table
- Composite key: `type_id`, `activity_id`, `material_type_id`
- Fields: `quantity` for blueprint calculations

**`InvMarketGroup`**: Maps `invMarketGroups` table
- Primary key: `market_group_id`
- Fields: `market_group_name`, `parent_group_id`
- Self-referential relationship for tree structure

---

#### [NEW] [backend/app/scripts/ingest_sde.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/scripts/ingest_sde.py)

SDE ingestion orchestrator:
1. Checks if `invTypes` table exists and is populated
2. If empty, executes `pg_restore` using Fuzzwork dump
3. Validates critical tables post-ingestion
4. Logs progress and errors

Designed to run as Docker init container or manual script.

---

### Backend - Graph Database

#### [NEW] [backend/app/graph.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/graph.py)

Neo4j driver configuration:
- Async driver initialization
- `get_graph()` FastAPI dependency for session injection
- Connection health checks

---

#### [NEW] [backend/app/scripts/build_graph.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/scripts/build_graph.py)

ETL pipeline: Postgres SDE → Neo4j topology graph

1. **Extract**: Query `mapSolarSystems` and `mapSolarSystemJumps` from Postgres
2. **Transform**: Convert to Cypher `CREATE` statements
3. **Load**: Batch insert using `UNWIND` for performance
   - Create `:SolarSystem` nodes with properties (id, name, security)
   - Create `:GATE` relationships (bidirectional for gameplay accuracy)
4. **Index**: Create index on `SolarSystem(id)` for fast lookups

Expected runtime: ~30 seconds for ~8,000 systems + ~10,000 gates

---

#### [NEW] [backend/app/services/route_service.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/services/route_service.py)

Route calculation service implementing weighted Dijkstra:

**`calculate_route(start_id, end_id, security_preference)`**:
- Uses Neo4j APOC or GDS library
- Applies weight function based on destination security status:
  - High Sec (≥0.5): Weight = 1
  - Low Sec (0.1-0.4): Weight = 50
  - Null Sec (≤0.0): Weight = 1000
- Returns: `RouteResult` with waypoints, total jumps, and risk score

**Cypher Query Structure**:
```cypher
MATCH (start:SolarSystem {id: $start_id}), (end:SolarSystem {id: $end_id})
CALL apoc.algo.dijkstra(start, end, 'GATE', 'risk_weight')
YIELD path, weight
RETURN [node IN nodes(path) | node.name] AS waypoints, weight AS risk_score
```

---

### Backend - ESI Integration

#### [NEW] [backend/app/clients/esi_client.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/clients/esi_client.py)

ESI HTTP client with strict compliance mechanisms:

**Core Features**:
- **Error Budget Manager**: Tracks error count in Redis (`esi:error_count`)
- **Lockdown Logic**:
  - Green (< 50 errors): Normal operation
  - Yellow (50-90 errors): Exponential backoff + jitter
  - Red (≥ 90 errors): Raises `ESILockdownException`, blocks requests
- **HTTP 420 Handler**: Sets global lock (`esi:global_lock`) on 420 response
- **Token Refresh**: Automatic OAuth token refresh on 403
- **Cache Respect**: Honors `Expires` and `Cache-Control` headers via Redis

**Request Flow**:
1. Check global lock and error budget
2. Check Redis cache for cached response
3. Execute HTTP request via `httpx.AsyncClient`
4. Parse ESI-specific headers (`X-ESI-Error-Limit-Remain`, `X-ESI-Error-Limit-Reset`)
5. Update Redis error counters
6. Cache response if appropriate
7. Return data or raise exception

---

#### [NEW] [backend/app/clients/token_manager.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/clients/token_manager.py)

OAuth token lifecycle management:
- Stores access/refresh tokens in Redis (keyed by character ID)
- Automatically refreshes tokens 5 minutes before expiration
- Thread-safe token retrieval
- Implements OAuth2 Authorization Code flow

---

### Backend - Business Logic

#### [NEW] [backend/app/services/market_service.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/services/market_service.py)

Market analysis with accurate profit calculations:

**`calculate_net_profit(buy_price, sell_price, character_skills)`**:
- Implements formula from specification Section 6.2
- Fetches character skills via ESI (`esi-skills.read_skills.v1`)
- Calculates effective tax rate:
  - Base: 8%, reduced by Accounting skill (11% per level)
- Calculates effective broker fee:
  - Base: 3%, reduced by Broker Relations (0.3% per level) and standings
- Returns: `ProfitCalculation` with gross, fees, net, and ROI

**`fetch_market_orders(region_id, type_id)`**:
- Retrieves orders from ESI with pagination support
- Parses `X-Pages` header for multi-page fetches
- Uses `asyncio.gather()` for concurrent page fetching
- Filters orders by duration (≥ 1 day remaining)
- Caches results in Redis with TTL from ESI headers

---

#### [NEW] [backend/app/services/contract_service.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/services/contract_service.py)

Contract appraisal using "Jita Split" methodology:

**`appraise_contract(contract_id)`**:
1. Fetch contract items via ESI
2. Resolve all `type_id` values to `InvType` models
3. Query Jita (The Forge, Region 10000002) market stats
4. Calculate "Jita Split" for each item: `(min_sell + max_buy) / 2`
5. Sum total estimated value
6. Compare against contract asking price
7. Return: `ContractAppraisal` with value breakdown, profit %, and top 5 items

---

#### [NEW] [backend/app/services/universe_service.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/services/universe_service.py)

Item and location resolution service:

**`search_items(query, limit=20)`**:
- Performs `ILIKE` search on `invTypes.type_name`
- Returns: `[{label: str, value: int}]` format for autocomplete

**`resolve_station(station_id)`**:
- Queries `staStations` table for NPC stations
- Falls back to ESI for player structures (requires `esi-search.search_structures.v1`)
- Caches results in Redis (stations don't change frequently)

**`get_item_details(type_id)`**:
- Fetches full `InvType` with volume, market group, etc.
- Used for freight calculations and UI display

---

### Backend - API Endpoints

#### [NEW] [backend/app/routers/auth.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/routers/auth.py)

OAuth2 authentication flow:

**`GET /auth/login`**: Redirects to EVE SSO with scopes
**`GET /auth/callback`**: Handles OAuth callback
- Exchanges code for access/refresh tokens
- Validates JWT using EVE's JWKS (requires `python-jose[cryptography]`)
- Fetches character info from EVE SSO
- Stores tokens in Redis
- Creates session cookie
- Redirects to frontend

**`POST /auth/logout`**: Clears session and Redis tokens

---

#### [NEW] [backend/app/routers/market.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/routers/market.py)

Market data endpoints:

**`GET /market/orders`**: Fetch orders for region/type
- Query params: `region_id`, `type_id`, `order_type` (buy/sell)
- Returns: Paginated list of market orders

**`GET /market/arbitrage`**: Calculate arbitrage opportunities
- Query params: `region_a`, `region_b`, `min_volume`, `min_profit_percent`
- Logic: Find items where `region_b.buy > region_a.sell`
- Returns: Sorted list by profit (descending)

**`POST /market/cache/update`**: Background task to cache all market data
- Fetches orders for configured regions (The Forge, Domain, Heimatar)
- Respects ESI rate limits via `ESIClient`
- Updates Postgres `MarketOrder` table via bulk upsert

---

#### [NEW] [backend/app/routers/contracts.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/routers/contracts.py)

Contract analysis:

**`GET /contracts/public`**: List public contracts in region
**`GET /contracts/appraise/{contract_id}`**: Appraise contract value
- Uses `ContractService.appraise_contract()`
- Returns: Estimated value, profit %, item breakdown

---

#### [NEW] [backend/app/routers/character.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/routers/character.py)

Character data:

**`GET /character/wallet`**: Fetch wallet balance (requires `esi-wallet.read_character_wallet.v1`)
**`GET /character/skills`**: Fetch skills (requires `esi-skills.read_skills.v1`)
**`GET /character/transactions`**: Fetch transaction history

---

#### [NEW] [backend/app/routers/universe.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/routers/universe.py)

Universe data:

**`GET /universe/search/items`**: Autocomplete search
- Query param: `q` (search term)
- Returns: `[{label, value}]` for React Select

**`GET /universe/resolve/station/{station_id}`**: Resolve station name
**`GET /universe/item/{type_id}`**: Get item details

---

#### [NEW] [backend/app/routers/routing.py](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/app/routers/routing.py)

Route calculation:

**`POST /routing/calculate`**: Calculate route between systems
- Request body: `{start_id, end_id, security_preference}`
- Uses `RouteService.calculate_route()`
- Returns: `{waypoints: string[], jumps: int, risk_score: int}`

---

### Frontend - Infrastructure

#### [NEW] [frontend/vite.config.ts](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/vite.config.ts)

Vite configuration optimized for Docker + Cloudflare Tunnel:

```typescript
server: {
  host: '0.0.0.0',  // Allow external container access
  port: 5173,
  hmr: {
    protocol: 'wss',  // WebSocket Secure for tunnel
    host: process.env.VITE_HMR_HOST,  // Tunnel URL
    clientPort: 443  // HTTPS port
  },
  watch: {
    usePolling: true  // Required for Windows/WSL2
  }
}
```

Proxy configuration:
- `/api/*` → `http://backend:8000/api/*`

---

#### [NEW] [frontend/package.json](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/package.json)

Dependencies:
- **Core**: `react`, `react-dom`, `react-router-dom`
- **State**: `@tanstack/react-query`, `zustand`
- **UI**: `@tanstack/react-table`, `recharts`, `react-select`
- **HTTP**: `axios`
- **Validation**: `zod`
- **Dev**: `vite`, `typescript`, `@vitejs/plugin-react`

---

#### [NEW] [frontend/src/index.css](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/src/index.css)

Design system with CSS custom properties:

**Color Tokens**:
- `--color-primary`: EVE-themed blues
- `--color-success`, `--color-warning`, `--color-danger`: Semantic colors
- `--color-highsec`, `--color-lowsec`, `--color-nullsec`: Security status colors

**Typography**:
- Base font: Inter (Google Fonts)
- Monospace: JetBrains Mono for numbers/IDs

**Components**:
- Card styles with glassmorphism
- Table virtualization utilities
- Animation keyframes for loaders

---

### Frontend - Authentication

#### [NEW] [frontend/src/contexts/AuthContext.tsx](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/src/contexts/AuthContext.tsx)

Authentication state management:

**Context Value**:
```typescript
{
  session: CharacterSession | null,
  isAuthenticated: boolean,
  login: () => void,  // Redirects to /auth/login
  logout: () => void  // Calls /auth/logout
}
```

**Logic**:
- Checks session on mount via `/auth/session` endpoint
- Persists auth state across page reloads
- Provides `useAuth()` hook for components

---

#### [NEW] [frontend/src/components/ProtectedRoute.tsx](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/src/components/ProtectedRoute.tsx)

Route guard:
- Checks `useAuth().isAuthenticated`
- Redirects to `/login` if unauthenticated
- Preserves intended destination in `?redirect=` query param

---

### Frontend - UI Components

#### [NEW] [frontend/src/components/MainLayout.tsx](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/src/components/MainLayout.tsx)

Application shell:
- Top navigation bar with character avatar and wallet balance
- Sidebar with links (Dashboard, Market, Contracts, Routes)
- Logout button
- `<Outlet />` for nested routes

---

#### [NEW] [frontend/src/pages/Dashboard.tsx](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/src/pages/Dashboard.tsx)

Dashboard view:
- Wallet balance (large, prominent)
- PLEX ticker (real-time Jita price)
- Recharts line chart: Wallet balance over last 30 days
- Quick stats: Total transactions, Net profit this week

Uses React Query to fetch `/character/wallet` and `/character/transactions`

---

#### [NEW] [frontend/src/pages/Market.tsx](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/src/pages/Market.tsx)

Market analysis view:

**Filter Bar**:
- Region selector (dropdown)
- Item search (autocomplete via `/universe/search/items`)
- Min spread % (number input)
- Min volume (number input)

**Data Grid** (TanStack Table):
- Columns: Item, Buy Price, Sell Price, Spread %, Volume, Profit/Unit
- Virtual scrolling for 10,000+ rows
- Sortable columns
- Row click → Show route to best opportunity

---

#### [NEW] [frontend/src/pages/Routes.tsx](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/src/pages/Routes.tsx)

Route visualization:

**Input Form**:
- Start system (autocomplete)
- End system (autocomplete)
- Security preference (radio: Safest / Shortest / Custom)

**Route Display**:
- Horizontal stepper UI
- Each system node colored by security:
  - Green: High Sec
  - Orange: Low Sec
  - Red: Null Sec
- Warning icons on known choke points
- Total jumps and risk score displayed

---

#### [NEW] [frontend/src/pages/Contracts.tsx](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/frontend/src/pages/Contracts.tsx)

Contract browser:

**Filter Bar**:
- Region selector
- Contract type filter (Item Exchange, Auction, Courier)
- Min profit % filter

**Contract Cards**:
- Card header: Contract title and type icon
- Card body: Ask price vs. appraised value
- Profit margin badge (color-coded)
- Click to expand: Shows item breakdown list

Uses infinite scroll via React Query for pagination

---

### Backend - Dependencies

#### [NEW] [backend/requirements.txt](file:///c:/Users/fonse/Nextcloud4/Documents/Código/Personal%20Projects/eve-app/backend/requirements.txt)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlmodel==0.0.14
asyncpg==0.29.0
redis==5.0.1
neo4j==5.14.0
httpx==0.25.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
pandas==2.1.3
```

---

## Verification Plan

### Automated Tests

1. **SDE Ingestion Verification**:
   ```bash
   docker-compose exec backend python -m app.scripts.ingest_sde
   docker-compose exec postgres psql -U eve_user -d eve_sde -c "SELECT COUNT(*) FROM invTypes;"
   ```
   Expected: ~15,000 rows

2. **Neo4j Graph Build**:
   ```bash
   docker-compose exec backend python -m app.scripts.build_graph
   docker-compose exec neo4j cypher-shell -u neo4j -p password "MATCH (n:SolarSystem) RETURN COUNT(n);"
   ```
   Expected: ~8,000 nodes

3. **ESI Rate Limiting Test**:
   ```bash
   docker-compose exec backend python -c "
   from app.clients.esi_client import ESIClient
   import redis
   r = redis.from_url('redis://redis:6379')
   client = ESIClient(r)
   for i in range(100):
       client.get('/markets/10000002/orders/')
   "
   ```
   Expected: Yellow state triggered at 50 errors, lockdown at 90

4. **Route Calculation Test**:
   ```bash
   curl http://localhost:8000/routing/calculate \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"start_id": 30000142, "end_id": 30002187, "security_preference": "safest"}'
   ```
   Expected: JSON with waypoints avoiding null sec

5. **Frontend Build**:
   ```bash
   docker-compose exec frontend npm run build
   ```
   Expected: No TypeScript errors, dist/ folder created

### Manual Verification

1. **OAuth Flow**: Navigate to `http://localhost:5173`, click Login, verify redirect to EVE SSO, authorize, verify redirect back with session
2. **Market View**: Select "The Forge", search for "Tritanium", verify orders display
3. **Route View**: Enter "Jita" to "Amarr", select "Safest", verify route avoids low/null sec
4. **Contracts**: Filter by profit > 15%, verify appraisals match Jita prices
5. **HMR (if using tunnel)**: Edit a React component, verify hot reload without full page refresh
