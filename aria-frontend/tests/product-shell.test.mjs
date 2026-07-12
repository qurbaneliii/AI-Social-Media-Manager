import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const occurrences = (source, needle) => source.split(needle).length - 1;

const primaryPages = [
  "app/dashboard/brand/page.tsx",
  "app/dashboard/brand-brain/page.tsx",
  "app/(dashboard)/posts/new/page.tsx",
  "app/(dashboard)/posts/page.tsx",
  "app/dashboard/approval/page.tsx",
  "app/(dashboard)/scheduler/page.tsx",
  "app/(dashboard)/analytics/page.tsx",
  "app/dashboard/settings/page.tsx"
];

test("both dashboard route groups delegate to the canonical ProductShell", () => {
  for (const layout of ["app/dashboard/layout.tsx", "app/(dashboard)/layout.tsx"]) {
    const source = read(layout);
    assert.match(source, /import \{ ProductShell \}/);
    assert.equal(occurrences(source, "<ProductShell>"), 1, `${layout} must render ProductShell once`);
  }
});

test("ProductShell owns one shell marker and one main landmark", () => {
  const source = read("components/layout/ProductShell.tsx");
  assert.equal(occurrences(source, 'data-testid="aria-product-shell"'), 1);
  assert.equal(occurrences(source, "<motion.main"), 1);
  assert.equal(occurrences(source, "<Sidebar"), 1);
  assert.equal(occurrences(source, "<TopBar"), 1);
  assert.equal(occurrences(source, "<MobileNav"), 1);
});

test("primary pages do not introduce nested main landmarks", () => {
  for (const page of primaryPages) {
    assert.equal(occurrences(read(page), "<main"), 0, `${page} must leave the main landmark to ProductShell`);
  }
});

test("all navigation surfaces derive from the canonical navigation module", () => {
  assert.match(read("components/dashboard/Sidebar.tsx"), /getNavigationSections/);
  assert.match(read("components/dashboard/MobileNav.tsx"), /getMobileNavigationItems/);
  assert.match(read("components/dashboard/TopBar.tsx"), /getCommandNavigationItems/);
});

test("legacy product routes redirect to canonical implemented destinations", () => {
  const redirects = new Map([
    ["app/dashboard/page.tsx", "/dashboard/brand"],
    ["app/dashboard/create/page.tsx", "/posts/new"],
    ["app/dashboard/content/page.tsx", "/posts"],
    ["app/dashboard/content-studio/page.tsx", "/posts/new"],
    ["app/dashboard/posts/page.tsx", "/posts"],
    ["app/dashboard/scheduler/page.tsx", "/scheduler"],
    ["app/dashboard/analytics/page.tsx", "/analytics"]
  ]);

  for (const [page, destination] of redirects) {
    const source = read(page);
    assert.match(source, /import \{ redirect \} from "next\/navigation"/);
    assert.ok(source.includes(`redirect("${destination}")`), `${page} must redirect to ${destination}`);
  }
});
