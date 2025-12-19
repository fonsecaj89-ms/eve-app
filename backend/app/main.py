from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.logger import configure_logging
import structlog
import time

# Configure structured logging
configure_logging()
logger = structlog.get_logger()

app = FastAPI(title="EVE Online Trading Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import images, auth, market, router as routing_router, contracts
app.include_router(images.router)
app.include_router(auth.router)
app.include_router(market.router)
app.include_router(routing_router.router)
app.include_router(contracts.router)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=process_time,
        esi_request_id=response.headers.get("x-esi-request-id"), # Capture ESI ID if present/passed
    )
    return response

@app.get("/")
async def root():
    return {"message": "EVE Trading Backend Online"}

@app.get("/health")
async def health():
    return {"status": "ok"}
