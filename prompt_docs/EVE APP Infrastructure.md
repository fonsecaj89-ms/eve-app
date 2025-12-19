# Infrastructure & Project Setup Prompt

Context:

You are an expert DevOps and System Architect. We are building a containerized EVE Online Trading & Routing application using FastAPI (Backend), React (Frontend), Neo4j (Graph DB), PostgreSQL (Relational DB), and Redis (Cache).

Goal:

Initialize the project structure, Docker configuration, and logging infrastructure.

## 1. Project Structure & Environment

Create the following folder structure:

```
eve-app/
├── backend/
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── package.json
│   └── .env.example
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 2. Git & Environment Security

- **`.gitignore`**: Generate a standard Python, Node, and Docker gitignore. Explicitly ignore `.env`, `*.log`, `__pycache__`, `node_modules`, and local database volume folders.
    
- **`.env` Files**: Create a root-level `.env` file strategy. Since Docker Compose sometimes fails to propagate env vars to build contexts, you must configure the `docker-compose.yml` and `Dockerfile`s to explicitly accept `ARG` and `ENV` values for:
    
    - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
        
    - `NEO4J_AUTH`
        
    - `REDIS_HOST`, `REDIS_PORT`
        
    - `EVE_CLIENT_ID`, `EVE_CLIENT_SECRET`, `EVE_CALLBACK_URL`
        
    - `CLOUDFLARE_TUNNEL_TOKEN`
        

## 3. Docker Configuration

Create a `docker-compose.yml` that orchestrates:

1. **Backend (FastAPI):**
    
    - Expose port `8000`.
        
    - Depends on Postgres, Neo4j, Redis.
        
    - Mount `./backend:/app` for development.
        
2. **Frontend (React/Vite):**
    
    - **Crucial:** The development server must bind to host `0.0.0.0` (not localhost) to ensure the Cloudflare tunnel works correctly with the local network IP.
        
    - Map internal port `5173` (or default Vite port) to host port `7777`.
        
    - Environment variable `VITE_API_URL` must point to the backend.
        
3. **PostgreSQL:** Persist data to a volume. Use latest stable Alpine image.
    
4. **Neo4j:** Persist data to a volume. Enable APOC plugins if necessary for graph algorithms.
    
5. **Redis:** Alpine image. Persistence enabled (AOF).
    

**Important:** Ensure `Dockerfile`s for both Backend and Frontend explicitly declare `ARG` variables at the top and assign them to `ENV` variables so the build process has access to necessary configuration.

## 4. Logging Infrastructure

Implement a robust, centralized logging configuration for both services:

- **Backend:** JSON-structured logs including timestamp, service name, log level, and message. Ensure logs capture ESI request IDs and rate limit headers for debugging.
    
- **Frontend:** A custom logger utility that can send critical errors to the backend (optional) or format console output for readability during dev.
    

## 5. Documentation

- Update `README.md` with a "Getting Started" section detailed enough that a fresh clone can run `docker-compose up --build` and have a working stack. Include instructions on how to populate the `.env` file.