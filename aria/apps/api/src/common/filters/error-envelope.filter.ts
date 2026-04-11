import { ArgumentsHost, Catch, ExceptionFilter, HttpException, HttpStatus } from "@nestjs/common";
import { randomUUID } from "node:crypto";
import type { FastifyReply, FastifyRequest } from "fastify";
import type { ErrorEnvelope } from "../types/error-envelope.js";

@Catch()
export class ErrorEnvelopeFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const reply = ctx.getResponse<FastifyReply>();
    const request = ctx.getRequest<FastifyRequest>();

    const status = exception instanceof HttpException ? exception.getStatus() : HttpStatus.INTERNAL_SERVER_ERROR;
    const message = exception instanceof HttpException ? exception.message : "Internal server error";

    const envelope: ErrorEnvelope = {
      error: {
        code: this.mapCode(status),
        message,
        details: {
          method: request.method,
          path: request.url
        },
        trace_id: randomUUID(),
        retryable: status === 503 || status === 429
      }
    };

    reply.status(status).send(envelope);
  }

  private mapCode(status: number): string {
    if (status === 400) return "validation_error";
    if (status === 401) return "unauthorized";
    if (status === 403) return "forbidden";
    if (status === 404) return "not_found";
    if (status === 409) return "conflict";
    if (status === 429) return "rate_limited";
    if (status === 503) return "transient_upstream";
    return "internal_error";
  }
}
