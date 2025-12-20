# EVE Online Trading Platform - Project Documentation

This directory contains the planning and task tracking artifacts for the EVE Online high-frequency trading platform.

## Files

- **`implementation_plan.md`**: Comprehensive architectural implementation plan based on the detailed specification document
- **`task.md`**: Granular task checklist broken down into 11 phases

## Project Overview

A distributed systems application for EVE Online market analysis featuring:
- **Backend**: FastAPI with PostgreSQL (SDE data), Neo4j (graph routing), Redis (rate limiting)
- **Frontend**: React + Vite with HMR over Cloudflare Tunnel
- **ESI Integration**: Strict compliance with HTTP 420 error limiting via Redis-backed circuit breaker
- **Core Features**: Market arbitrage, contract appraisal, weighted pathfinding, profit calculations

## Next Steps (When Resuming)

1. Review `implementation_plan.md` for detailed architecture
2. Obtain EVE Developer credentials (ESI_CLIENT_ID, ESI_SECRET_KEY)
3. Download Fuzzwork SDE PostgreSQL dump
4. Begin Phase 1: Infrastructure setup (Docker Compose configuration)

## Status

**Current Phase**: Planning Complete
**Next**: Infrastructure Setup (pending user approval and prerequisites)
