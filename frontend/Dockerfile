# Frontend image — build the React app, then serve the static files with nginx.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# In the compose setup the frontend talks to the backend through nginx (/api),
# so we build with an empty API base (relative URLs).
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
