FROM node:22-alpine AS build
WORKDIR /app
ENV NG_CLI_ANALYTICS=false
COPY package*.json ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist/downgrade-game/browser /usr/share/nginx/html
EXPOSE 80
