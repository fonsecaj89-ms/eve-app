# Part 1: Backend Development Prompt

**Context:** You are a Senior Python Backend Developer specializing in High-Frequency Trading systems and Data Engineering. You are building the backend for the EVE App.

**Tech Stack:**

- **Framework:** FastAPI
    
- **Databases:** PostgreSQL (SQLModel/SQLAlchemy), Neo4j (Graph logic), Redis (Caching).
    
- **Language:** Python 3.11+ (Strict PEP 8, Type Hints).
    
- **Architecture:** SOLID Principles, Clean Architecture.
    

**Task:** Develop the complete backend logic with the following modules:

## 1. Database & Infrastructure Layer

- **Postgres:**
    
    - Store static EVE SDE data (Regions, Stations, Items).
        
    - Store persistent user data (Settings, Saved Routes).
        
    - **Visual Asset Store (Crucial):** Create a table `ImageCache` to store binary image data (`bytea` or `LargeBinary`) retrieved from EVE Image Server.
        
        - Columns: `id` (primary key), `resource_type` (type, character, corporation, alliance), `resource_id` (integer), `variant` (icon, portrait, logo), `blob_data` (binary), `last_updated`.
            
        - Index on `(resource_type, resource_id, variant)`.
            
- **Neo4j:** Store the EVE Universe topology (Solar Systems, Gates, Jumps) for routing algorithms.
    
- **Redis:**
    
    - Cache Market Data (TTL 30 mins).
        
    - Cache Public Contracts (TTL 30 days or expiration).
        
    - **Lockdown Mechanism:** Store a key `ESI_GLOBAL_LOCKDOWN` with a TTL.
        

## 2. Data Ingestion (Fuzzwork & SDE)

Create a robust script (`scripts/ingest_data.py`) to:

1. Create the script to download the latest "Translquility" SQL dump from `https://www.fuzzwork.co.uk/dump/`. Store it in eve_data located in the root of the project. Note: I already have the latest dump in eve_data.
    
2. Open the file and Parse and ingest strictly necessary tables (Items, Map data) into PostgreSQL.

3. **Graph Construction:** Read map data and populate Neo4j nodes (Systems) and relationships (Stargates). Ensure edges have weights (distance/security status) for routing.

    

## 3. ESI Client (The "Violent" Rate Limiter)

Create a wrapper around the EVE ESI API that is paranoid about bans:

- **Token Bucket:** Implement a local token bucket respecting the `X-ESI-Error-Limit-Remain` header.
    
- **Global Lockdown:** Before ANY request, check Redis for `ESI_GLOBAL_LOCKDOWN`. If exists, raise `429 Too Many Requests` immediately.
    
- **Error Handling:**
    
    - If **ONE** 4xx/5xx error occurs:
        
        1. Log the error with high severity.
            
        2. Sleep for 30 seconds.
            
        3. Set `ESI_GLOBAL_LOCKDOWN` in Redis for 1 minute.
            
- **Pagination:** Handle `X-Pages`. Add a **2-second delay** between page fetches.
    
- **Region Loop:** Add a **5-second delay** between processing different regions.
    

## 4. Domain Modules

### A. Authentication

- Implement EVE SSO. Scopes: Use strictly the list provided in resources.
    
- Session: On login, store the session in Redis.
    

### B. Visual Asset Caching Service

- **Objective:** Prevent client-side connections to `images.evetech.net` to save tokens and bandwidth.
    
- **Endpoint:** `GET /api/images/{resource_type}/{resource_id}`
    
    - `resource_type` enum: `type` (items/ships), `character`, `corporation`, `alliance`.
        
    - Query param: `?size=64` (default).
        
- **Logic:**
    
    1. Check Postgres `ImageCache` for the specific ID and Type.
        
    2. **Cache Hit:** Return the binary data directly with correct Content-Type.
        
    3. **Cache Miss:**
        
        - Download from `https://images.evetech.net/{resource_type}/{resource_id}/{variant}`.
            
        - Save binary to Postgres `ImageCache`.
            
        - Return binary to client.
            
- **Variants:**
    
    - For `type`: use `icon`.
        
    - For `character`: use `portrait`.
        
    - For `corporation`/`alliance`: use `logo`.
        

### C. Market Engine

- **Scanning Logic:**
    
    - _Station Scan:_ Fetch orders for current station. Cache for 30 mins. Calculate top 30 trades.
        
    - _Region Scan:_ Iterate all markets in the region (using the delay logic).
        
    - _Global Scan:_ **DO NOT** call ESI. Query PostgreSQL/Redis snapshot data only. Return top 50 trades.
        
- **Profit Algorithm:** Sort by Profit %. Input: Buy/Sell Station, Item, Tax Rate.
    

### D. Routing Engine (Neo4j)

- **Algorithm:** Implement A* or Dijkstra in Neo4j (using APOC or Graph Data Science lib).
    
- **Safety Check:**
    
    - Fetch recent kills (zKillboard API or ESI Killmails).
        
    - **Smartbomb Avoidance:** If a system has high kills within a short timeframe, flag as "Critical Risk" and increase edge weight significantly.
        

### E. Contracts

- Endpoint: `/api/contracts`
    
- Fetch public contracts. Cache aggressively.
    
- **Valuation:** Calculate breakdown of items inside. Compare vs Jita split.
    

## 5. Coding Standards

- Use Pydantic for all request/response schemas.
    
- Add Docstrings to every function (Google Style).
    
- **Logging:** Every ESI interaction must be logged: `[ESI] Method: GET | URL: ... | Status: 200 | Limit-Remain: 99`.
    

**Resources:**

- EVE Client ID: `5e0952c68665441aae27846cb735138e`
    
- Redis IP: `redis` (docker hostname)
    
- Tunnel Port: `7777`