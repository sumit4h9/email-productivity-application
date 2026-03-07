FROM node:20-alpine

# Add needed libs and build tools for lightningcss
RUN apk add --no-cache libc6-compat python3 make g++

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps && npm rebuild lightningcss || true

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]