# Frontend Next.js de DRIFT con salida standalone (next.config.js: output: "standalone").
FROM node:22-alpine AS dependencias
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:22-alpine AS construccion
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=dependencias /app/node_modules ./node_modules
COPY . .
# Las variables NEXT_PUBLIC_* se fijan en el build: llega como build arg desde el compose.
ARG NEXT_PUBLIC_DRIFT_API_URL=/api
ENV NEXT_PUBLIC_DRIFT_API_URL=$NEXT_PUBLIC_DRIFT_API_URL
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=construccion /app/.next/standalone ./
COPY --from=construccion /app/.next/static ./.next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
