# EVE Online Trading & Routing App

An advanced Algo-Trading and Route Optimization application for EVE Online, built with FastAPI, React, Neo4j, PostgreSQL, and Redis.

## Architecture

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React (Vite, Node 20)
- **Database (Relational)**: PostgreSQL 17
- **Database (Graph)**: Neo4j 5.x
- **Cache**: Redis

## Getting Started

### Prerequisites

- Docker Desktop installed and running.
- Git.

### Setup

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository_url>
   cd eve-app
   ```

2. **Environment Configuration**:
   Copy the example environment file to `.env`:
   ```bash
   cp .env.example .env
   ```
   open `.env` and fill in your details:
   - `EVE_CLIENT_ID`, `EVE_CLIENT_SECRET`: From your EVE Online Developers application.
   - `CLOUDFLARE_TUNNEL_TOKEN`: If using Cloudflare Tunnels (optional for local dev).
   - Change `POSTGRES_PASSWORD` and `NEO4J_AUTH` if you wish, or keep defaults for local dev.

3. **Start the Application**:
   Build and start the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```
   *Note: The first build may take a few minutes.*

4. **Access the Application**:
   - **Frontend**: http://localhost:7777
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **Neo4j Browser**: http://localhost:7474 (Login with credentials from `.env`)

## Project Structure

- `backend/`: FastAPI application code.
- `frontend/`: React application code.
- `docker-compose.yml`: Service orchestration.
- `eve_data/`: (Optional) Local volume mapping.

## Development

- **Backend**: The `backend` folder is mounted into the container. Changes to Python files will auto-reload the server.
- **Frontend**: The `frontend` folder is not fully mounted for hot-reload in this initial config unless node_modules are handled carefully, but the current setup rebuilds on change if configured or you can run `npm run dev` locally pointing to the backend. *Self-Correction: The docker-compose mounts `backend` but `frontend` is currently built. To enable HMR in Docker, you might need extra volume mappings, but `Vite` HMR through Docker can be tricky.*

## Logging

- Backend logs are in JSON format for easy parsing.
- Frontend logs are handled by a custom utility in `src/utils/logger.js`.
