FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# gcc and libpq-dev are often needed for psychopg2 (postgres)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Arguments (propagated to ENV)
ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_DB
ARG NEO4J_AUTH
ARG REDIS_HOST
ARG REDIS_PORT
ARG EVE_CLIENT_ID
ARG EVE_CLIENT_SECRET
ARG EVE_CALLBACK_URL

ENV POSTGRES_USER=$POSTGRES_USER \
    POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    POSTGRES_DB=$POSTGRES_DB \
    NEO4J_AUTH=$NEO4J_AUTH \
    REDIS_HOST=$REDIS_HOST \
    REDIS_PORT=$REDIS_PORT \
    EVE_CLIENT_ID=$EVE_CLIENT_ID \
    EVE_CLIENT_SECRET=$EVE_CLIENT_SECRET \
    EVE_CALLBACK_URL=$EVE_CALLBACK_URL \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
