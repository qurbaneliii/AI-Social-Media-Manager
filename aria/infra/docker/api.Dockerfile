# FILE: infra/docker/api.Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY apps/api/package.json /app/package.json
RUN npm install
COPY apps/api /app
EXPOSE 4000
CMD ["npm", "run", "dev"]
