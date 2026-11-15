# 1) Valida os mapas do Tiled com o validador do downgrade-tools (contexto extra "tools").
#    Fase com erro quebra o build e nao entra no jogo.
FROM python:3.12-slim AS fases
WORKDIR /v
ENV PYTHONIOENCODING=utf-8
COPY --from=tools app ./app
COPY public/assets ./assets
RUN python -m app.validar assets/fases && touch /v/fases-ok

# 2) Build do Angular + Phaser
FROM node:22-alpine AS build
WORKDIR /app
ENV NG_CLI_ANALYTICS=false
COPY --from=fases /v/fases-ok /tmp/fases-ok
COPY package*.json ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

# 3) Nginx servindo o build
FROM nginx:1.27-alpine
COPY --from=build /app/dist/downgrade-game/browser /usr/share/nginx/html
EXPOSE 80
