import { Injectable } from "@nestjs/common";
import Redis from "ioredis";
import { env } from "../../config/env.js";

export enum CacheTTLClass {
  SHORT = 300,
  MEDIUM = 3600,
  LONG = 86400
}

@Injectable()
export class RedisService {
  private readonly client = new Redis(env.redisUrl);

  async setJson<T>(key: string, value: T, ttl: CacheTTLClass): Promise<void> {
    await this.client.set(key, JSON.stringify(value), "EX", ttl);
  }

  async getJson<T>(key: string): Promise<T | null> {
    const value = await this.client.get(key);
    return value ? (JSON.parse(value) as T) : null;
  }

  async setIdempotency(key: string, payload: object): Promise<void> {
    await this.setJson(`idempotency:${key}`, payload, CacheTTLClass.MEDIUM);
  }

  async getIdempotency<T>(key: string): Promise<T | null> {
    return this.getJson<T>(`idempotency:${key}`);
  }
}
