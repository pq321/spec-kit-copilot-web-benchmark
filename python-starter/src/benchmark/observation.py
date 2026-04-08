"""Page observation capture for the benchmark framework."""

from __future__ import annotations

import os

from playwright.async_api import Page

from .browser_adapter import BrowserAdapter
from .types import Observation


async def capture_observation(
    page: Page,
    adapter: BrowserAdapter,
    *,
    screenshot_dir: str,
    step_id: str,
) -> Observation:
    """Capture the current page state including screenshot and DOM evidence."""
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, f"{step_id}.png")
    await adapter.screenshot(screenshot_path)

    url = page.url
    title = await page.title()

    headings = await page.locator("h1, h2").evaluate_all(
        """elements => elements
            .map(el => (el.textContent || '').trim())
            .filter(Boolean)"""
    )

    banners = await page.locator(
        "[role='alert'], [data-status-banner]"
    ).evaluate_all(
        """elements => elements
            .map(el => (el.textContent || '').trim())
            .filter(Boolean)"""
    )

    dom_evidence = ""
    try:
        raw = await page.locator("main").inner_text()
        dom_evidence = " ".join(raw.split())[:500]
    except Exception:
        pass

    controls = await adapter.extract_controls()

    return Observation(
        url=url,
        title=title,
        headings=headings,
        banners=banners,
        dom_evidence=dom_evidence,
        screenshot_path=screenshot_path,
        controls=controls,
    )
