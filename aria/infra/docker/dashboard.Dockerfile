# FILE: infra/docker/dashboard.Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY apps/dashboard/package.json /app/package.json
RUN npm install
COPY apps/dashboard /app
EXPOSE 3000
CMD ["npm", "run", "dev"]
