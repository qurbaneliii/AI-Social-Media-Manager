import { describe, expect, it } from "vitest";
import { GenericContainer, StartedTestContainer } from "testcontainers";

describe("API integration", () => {
  let postgres: StartedTestContainer;

  it("starts postgres container for endpoint integration", async () => {
    postgres = await new GenericContainer("postgres:15")
      .withEnvironment({ POSTGRES_PASSWORD: "postgres", POSTGRES_DB: "aria" })
      .withExposedPorts(5432)
      .start();

    expect(postgres.getMappedPort(5432)).toBeGreaterThan(0);

    await postgres.stop();
  }, 120000);
});
