import { LOCATOR_STRATEGY_ORDER } from "./types.js";

function buildCandidateFactories(descriptor) {
  return [
    {
      strategy: "role",
      available: Boolean(descriptor.role && descriptor.name),
      create: (root) => root.getByRole(descriptor.role, { name: descriptor.name })
    },
    {
      strategy: "label",
      available: Boolean(descriptor.label),
      create: (root) => root.getByLabel(descriptor.label)
    },
    {
      strategy: "text",
      available: Boolean(descriptor.text),
      create: (root) => root.getByText(descriptor.text)
    },
    {
      strategy: "testId",
      available: Boolean(descriptor.testId),
      create: (root) => root.getByTestId(descriptor.testId)
    },
    {
      strategy: "css",
      available: Boolean(descriptor.css),
      create: (root) => root.locator(descriptor.css)
    },
    {
      strategy: "xpath",
      available: Boolean(descriptor.xpath),
      create: (root) => root.locator(`xpath=${descriptor.xpath}`)
    }
  ].filter((entry) => entry.available);
}

export function buildLocatorPlan(descriptor) {
  const available = buildCandidateFactories(descriptor).map((entry) => entry.strategy);
  return LOCATOR_STRATEGY_ORDER.filter((strategy) => available.includes(strategy));
}

export function createBrowserAdapter(page) {
  async function resolveLocator(descriptor) {
    const roots = descriptor.scope ? [page.locator(descriptor.scope)] : [page];
    const factories = buildCandidateFactories(descriptor);

    for (const root of roots) {
      for (const entry of factories) {
        const candidate = entry.create(root).first();
        if ((await candidate.count()) > 0) {
          return {
            locator: candidate,
            strategy: entry.strategy
          };
        }
      }
    }

    throw new Error(`Unable to resolve locator for ${JSON.stringify(descriptor)}`);
  }

  async function gotoRequestPage(baseUrl, scenario) {
    await page.goto(`${baseUrl}/request.html?scenario=${scenario}`, {
      waitUntil: "domcontentloaded"
    });
  }

  async function click(descriptor) {
    const resolved = await resolveLocator(descriptor);
    await resolved.locator.click();
    return resolved.strategy;
  }

  async function selectOption(descriptor, value) {
    const resolved = await resolveLocator(descriptor);
    await resolved.locator.selectOption(value);
    return resolved.strategy;
  }

  async function check(descriptor) {
    const resolved = await resolveLocator(descriptor);
    await resolved.locator.check();
    return resolved.strategy;
  }

  async function waitFor(waitMs) {
    await page.waitForTimeout(waitMs);
  }

  async function screenshot(filePath) {
    await page.screenshot({ path: filePath, fullPage: true });
    return filePath;
  }

  async function extractControls() {
    return page
      .locator("main button, main select, main input, main [role='button']")
      .evaluateAll((elements) =>
        elements.map((element) => {
          const label =
            element.getAttribute("aria-label") ||
            element.labels?.[0]?.textContent?.trim() ||
            "";
          const text = element.textContent?.trim() || "";
          const role =
            element.getAttribute("role") ||
            (element.tagName === "BUTTON"
              ? "button"
              : element.tagName === "SELECT"
                ? "combobox"
                : element.type === "checkbox"
                  ? "checkbox"
                  : "input");
          return {
            role,
            label,
            text,
            disabled: Boolean(element.disabled || element.getAttribute("aria-disabled") === "true"),
            value: "value" in element ? String(element.value || "") : "",
            checked: "checked" in element ? Boolean(element.checked) : false
          };
        })
      );
  }

  return {
    buildLocatorPlan,
    gotoRequestPage,
    click,
    selectOption,
    check,
    waitFor,
    screenshot,
    extractControls
  };
}
