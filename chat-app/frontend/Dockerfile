FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
RUN apk add --no-cache curl
COPY . .
EXPOSE 5173

# Script para garantir que node_modules existe antes de iniciar
CMD ["sh", "-c", "npm install && npm run dev -- --host 0.0.0.0 --port 5173"]
