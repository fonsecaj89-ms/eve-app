FROM node:20-alpine

WORKDIR /app

# Arguments
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Arguments moved after install to prevent cache invalidation
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

EXPOSE 5173

# Bind to 0.0.0.0 to ensure visibility from host/Cloudflare tunnel
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
