import "reflect-metadata";
import { NestFactory } from "@nestjs/core";
import { FastifyAdapter, NestFastifyApplication } from "@nestjs/platform-fastify";
import { AppModule } from "./app.module.js";
import { ErrorEnvelopeFilter } from "./common/filters/error-envelope.filter.js";
import { env } from "./config/env.js";

async function bootstrap() {
  const app = await NestFactory.create<NestFastifyApplication>(AppModule, new FastifyAdapter());
  app.useGlobalFilters(new ErrorEnvelopeFilter());
  await app.listen({ port: env.apiPort, host: "0.0.0.0" });
}

bootstrap();
