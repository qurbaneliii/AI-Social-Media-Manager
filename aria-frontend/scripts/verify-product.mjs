import { chromium } from "playwright-core";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const baseUrl = process.env.ARIA_BROWSER_BASE_URL ?? "http://127.0.0.1:3200";
const outputRoot = path.resolve("../docs/product/screenshots/after");
const executablePath = process.env.ARIA_BROWSER_EXECUTABLE ?? "C:/Program Files/Google/Chrome/Application/chrome.exe";
const routes = [
  ["overview", "/dashboard/brand"],
  ["brand-brain", "/dashboard/brand-brain"],
  ["create", "/posts/new"],
  ["content", "/posts"],
  ["approval", "/dashboard/approval"],
  ["calendar", "/scheduler"],
  ["insights", "/analytics"],
  ["settings", "/dashboard/settings"]
];
const viewports = [
  ["desktop", 1440, 900],
  ["desktop", 1280, 800],
  ["tablet", 1024, 768],
  ["tablet", 768, 1024],
  ["mobile", 390, 844],
  ["mobile", 360, 800]
];
const routeFilter = new Set((process.env.ARIA_VERIFY_ROUTES ?? "").split(",").filter(Boolean));
const selectedRoutes = routeFilter.size ? routes.filter(([name]) => routeFilter.has(name)) : routes;
const selectedViewports = process.env.ARIA_VERIFY_QUICK === "true" ? [viewports[0]] : viewports;

const browser = await chromium.launch({ executablePath, headless: true });
const results = [];
try {
  for (const theme of ["light", "dark"]) {
    for (const [category, width, height] of selectedViewports) {
      for (const [name, route] of selectedRoutes) {
        const context = await browser.newContext({ viewport: { width, height }, colorScheme: theme });
        await context.addInitScript(({ selectedTheme }) => {
          localStorage.setItem("theme", selectedTheme);
          localStorage.setItem("isPreview", "true");
          localStorage.setItem("token", "preview-token-static-mode");
          localStorage.setItem("aria_token", "preview-token-static-mode");
          localStorage.setItem("aria_role", "brand_manager");
          localStorage.setItem("aria_company_id", "preview-company-id");
          localStorage.setItem("aria_workspace_id", "preview-workspace-id");
          localStorage.setItem("user", JSON.stringify({ id: "preview-user", email: "preview@aria.local", name: "Preview User", role: "brand_manager" }));
        }, { selectedTheme: theme });
        const page = await context.newPage();
        const consoleErrors = [];
        const pageErrors = [];
        const failedRequests = [];
        page.on("console", (message) => {
          if (message.type() === "error") consoleErrors.push(`${message.text()} @ ${message.location().url || "unknown"}`);
        });
        page.on("pageerror", (error) => pageErrors.push(error.message));
        page.on("requestfailed", (request) => failedRequests.push(`${request.method()} ${request.url()} ${request.failure()?.errorText ?? "failed"}`));
        const response = await page.goto(`${baseUrl}${route}`, { waitUntil: "networkidle", timeout: 30_000 });
        await page.waitForTimeout(250);
        const state = await page.evaluate(() => ({
          title: document.querySelector("h1")?.textContent?.trim() ?? "",
          bodyLength: document.body.innerText.trim().length,
          shellMarkers: document.querySelectorAll('[data-testid="aria-product-shell"]').length,
          mainLandmarks: document.querySelectorAll("main").length,
          horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
          errorOverlay: Boolean(document.querySelector("[data-nextjs-dialog], nextjs-portal"))
        }));
        const screenshot = path.join(outputRoot, theme, category, `${name}-${width}x${height}.png`);
        await mkdir(path.dirname(screenshot), { recursive: true });
        await page.screenshot({ path: screenshot, fullPage: false });
        results.push({
          theme,
          viewport: `${width}x${height}`,
          route,
          name,
          status: response?.status() ?? null,
          ...state,
          consoleErrors,
          pageErrors,
          failedRequests,
          screenshot: path.relative(path.resolve(".."), screenshot).replaceAll("\\", "/")
        });
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}

await writeFile(path.join(outputRoot, "verification.json"), `${JSON.stringify(results, null, 2)}\n`, "utf8");
const failures = results.filter((result) =>
  result.status !== 200 ||
  result.bodyLength === 0 ||
  result.shellMarkers !== 1 ||
  result.mainLandmarks !== 1 ||
  result.horizontalOverflow ||
  result.errorOverlay ||
  result.consoleErrors.length ||
  result.pageErrors.length ||
  result.failedRequests.length
);
console.log(JSON.stringify({ checks: results.length, failures: failures.length, failureDetails: failures }, null, 2));
process.exitCode = failures.length ? 1 : 0;
