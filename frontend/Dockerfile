FROM node:20-alpine

WORKDIR /app

# Arguments
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

COPY package.json .
RUN npm install

COPY . .

EXPOSE 5173

# Bind to 0.0.0.0 to ensure visibility from host/Cloudflare tunnel
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
