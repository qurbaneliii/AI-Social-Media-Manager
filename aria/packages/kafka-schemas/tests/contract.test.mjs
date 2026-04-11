import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import Ajv from "ajv/dist/2020.js";

const eventsDir = path.resolve("./events");
const ajv = new Ajv({ strict: false, allErrors: true });

function load(file) {
  return JSON.parse(fs.readFileSync(path.join(eventsDir, file), "utf-8"));
}

describe("Kafka event schema contracts", () => {
  it("validates media.uploaded.v1 schema structure", () => {
    const schema = load("media.uploaded.v1.schema.json");
    const valid = ajv.validateSchema(schema);
    expect(valid).toBe(true);
  });

  it("validates module.result.ready.v1 schema structure", () => {
    const schema = load("module.result.ready.v1.schema.json");
    const valid = ajv.validateSchema(schema);
    expect(valid).toBe(true);
  });
});
