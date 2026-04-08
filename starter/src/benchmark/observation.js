import { mkdir } from "node:fs/promises";
import path from "node:path";

export async function captureObservation(page, adapter, { screenshotDir, stepId }) {
  await mkdir(screenshotDir, { recursive: true });
  const screenshotPath = path.join(screenshotDir, `${stepId}.png`);
  await adapter.screenshot(screenshotPath);

  const url = page.url();
  const title = await page.title();
  const headings = await page
    .locator("h1, h2")
    .evaluateAll((elements) => elements.map((element) => element.textContent?.trim() || "").filter(Boolean));
  const banners = await page
    .locator("[role='alert'], [data-status-banner]")
    .evaluateAll((elements) => elements.map((element) => element.textContent?.trim() || "").filter(Boolean));
  const domEvidence = await page
    .locator("main")
    .innerText()
    .then((text) => text.replace(/\s+/g, " ").trim().slice(0, 500))
    .catch(() => "");
  const controls = await adapter.extractControls();

  return {
    url,
    title,
    headings,
    banners,
    domEvidence,
    screenshotPath,
    controls
  };
}
