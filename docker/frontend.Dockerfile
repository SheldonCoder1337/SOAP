# Development

FROM node:22.10.0 AS development
WORKDIR /app

COPY ./web/package*.json ./
RUN npm install --registry http://registry.npmmirror.com --verbose --force

COPY ./web .
EXPOSE 5173

# Production

FROM node:22.10.0 AS build-stage
WORKDIR /app

COPY ./web/package*.json ./
RUN npm install --registry https://registry.npmmirror.com --force

COPY ./web .
RUN npm run build

FROM nginx:alpine AS production
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY ./docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./docker/nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
