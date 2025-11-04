FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Gera Prisma Client dentro do container (DATABASE_URL fake apenas para build)
RUN DATABASE_URL="mongodb://placeholder:27017/chatdb" npx prisma generate
EXPOSE 3000