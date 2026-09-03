FROM node:20-bookworm-slim

WORKDIR /app

ENV NODE_ENV=production

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3108

CMD ["npm", "start"]