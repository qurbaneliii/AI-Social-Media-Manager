FROM node:20-bullseye-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npx prisma generate

EXPOSE 3000

CMD ["sh", "-c", "npx prisma migrate deploy && npm run dev -- --hostname 0.0.0.0 --port 3000"]
