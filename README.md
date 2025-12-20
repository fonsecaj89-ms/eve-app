# EVE Online Trading Platform

A high-frequency trading and industry analytics platform for EVE Online, built with modern distributed systems architecture.

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.11) with async PostgreSQL, Neo4j graph database, and Redis caching
- **Frontend**: Vite + React + TypeScript
- **Databases**: 
  - PostgreSQL 15 (Fuzzwork SDE data)
  - Neo4j 5 (Route planning topology)
  - Redis 7 (ESI rate limiting & response caching)
- **Infrastructure**: Docker Compose orchestration
- **Tunnel**: Cloudflare Tunnel (REQUIRED for EVE SSO callbacks)

## 🚀 Quick Start

### Prerequisites

1. **EVE Developer Application**: Register at [EVE Developers Portal](https://developers.eveonline.com/)
2. **Fuzzwork SDE Dump**: Download from [Fuzzwork Downloads](https://www.fuzzwork.co.uk/dump/)
3. **Cloudflare Tunnel**: Set up at [Cloudflare Dashboard](https://dash.cloudflare.com/)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd eve-app
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your actual values
   ```

3. **Place Fuzzwork SDE dump**
   - Download the latest PostgreSQL dump from Fuzzwork
   - Place it in `backend/data/` directory

4. **Start all services**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - Frontend: https://eve-app.jf-nas.com
   - Backend API: http://localhost:8000
   - Neo4j Browser: http://localhost:7474

## 🔐 EVE SSO Authentication Flow

The application uses a critical proxy chain for EVE SSO callbacks:

```
EVE SSO → https://eve-app.jf-nas.com/callback 
       → Cloudflare Tunnel 
       → Vite Frontend (port 5173)
       → Proxy to Backend /auth/callback
       → Redis (session storage)
```

**Important**: The Cloudflare Tunnel is **mandatory**, not optional. Without it, EVE SSO callbacks cannot reach your application.

## 📋 Required Environment Variables

See `.env.example` for a complete list. Critical variables:

- `EVE_CLIENT_ID` - Your EVE application client ID
- `EVE_CLIENT_SECRET` - Your EVE application secret
- `EVE_CALLBACK_URL` - Must be `https://eve-app.jf-nas.com/callback`
- `CLOUDFLARE_TUNNEL_TOKEN` - Your tunnel token
- `SECRET_KEY` - Generate with `openssl rand -hex 32`

## 🗺️ Features

- **Market Analysis**: Real-time arbitrage detection across regions
- **Route Planning**: Security-weighted graph pathfinding via Neo4j
- **Contract Appraisal**: "Jita Split" methodology for accurate valuations
- **ESI Compliance**: Strict rate limiting with error budget management
- **Character Dashboard**: Wallet tracking, transaction history, skills

## 🛠️ Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Run Tests
```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test
```

## 📊 Database Seeding

### SDE Ingestion
```bash
docker-compose exec backend python -m app.scripts.ingest_sde
```

### Neo4j Graph Build
```bash
docker-compose exec backend python -m app.scripts.build_graph
```

## 🔍 Verification

Verify services are running correctly:

```bash
# Check PostgreSQL
docker-compose exec postgres psql -U eve_user -d eve_sde -c "SELECT COUNT(*) FROM invTypes;"

# Check Neo4j
docker-compose exec neo4j cypher-shell -u neo4j -p password "MATCH (n:SolarSystem) RETURN COUNT(n);"

# Check Redis
docker-compose exec redis redis-cli ping
```

## 📖 Documentation

- Implementation Plan: `.agent/implementation_plan.md`
- Task Tracking: `.agent/task.md`
- API Documentation: http://localhost:8000/docs (after starting backend)

## ⚠️ Important Notes

1. **Cloudflare Tunnel**: Not optional - required for EVE SSO
2. **SDE Data**: Must be placed in `backend/data/` before first run
3. **Vite Proxy**: The `/callback` route MUST proxy to backend for auth to work
4. **ESI Rate Limits**: Built-in error budget management to avoid HTTP 420 bans

## 🤝 Contributing

This project follows Clean Code principles and SOLID architecture patterns. Please maintain:
- Type hints in Python
- TypeScript strict mode in frontend
- Comprehensive error handling
- ESI compliance at all times

## 📝 License

[Your License Here]

## 🔗 Links

- [EVE Online Developer Portal](https://developers.eveonline.com/)
- [ESI Documentation](https://esi.evetech.net/ui/)
- [Fuzzwork SDE](https://www.fuzzwork.co.uk/dump/)
