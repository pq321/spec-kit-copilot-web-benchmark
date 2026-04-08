"""Playwright browser adapter for element resolution."""

from __future__ import annotations

from typing import Any

from playwright.async_api import Locator, Page

from .types import LOCATOR_STRATEGY_ORDER, LocatorDescriptor, LocatorStrategy


def _build_candidate_factories(descriptor: LocatorDescriptor) -> list[dict[str, Any]]:
    """Build ordered list of locator strategies from a descriptor."""
    candidates: list[dict[str, Any]] = []

    if descriptor.role and descriptor.name:
        candidates.append({
            "strategy": LocatorStrategy.ROLE,
            "available": True,
        })

    if descriptor.label:
        candidates.append({
            "strategy": LocatorStrategy.LABEL,
            "available": True,
        })

    if descriptor.text:
        candidates.append({
            "strategy": LocatorStrategy.TEXT,
            "available": True,
        })

    if descriptor.test_id:
        candidates.append({
            "strategy": LocatorStrategy.TEST_ID,
            "available": True,
        })

    if descriptor.css:
        candidates.append({
            "strategy": LocatorStrategy.CSS,
            "available": True,
        })

    if descriptor.xpath:
        candidates.append({
            "strategy": LocatorStrategy.XPATH,
            "available": True,
        })

    return candidates


def build_locator_plan(descriptor: LocatorDescriptor) -> list[LocatorStrategy]:
    """Return ordered list of strategies available for this descriptor."""
    available = [c["strategy"] for c in _build_candidate_factories(descriptor)]
    return [s for s in LOCATOR_STRATEGY_ORDER if s in available]


def _create_locator_for_strategy(
    page: Page,
    strategy: LocatorStrategy,
    descriptor: LocatorDescriptor,
) -> Locator:
    """Create a Playwright locator for the given strategy."""
    if strategy == LocatorStrategy.ROLE:
        return page.get_by_role(descriptor.role, name=descriptor.name)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.LABEL:
        return page.get_by_label(descriptor.label)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.TEXT:
        return page.get_by_text(descriptor.text)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.TEST_ID:
        return page.get_by_test_id(descriptor.test_id)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.CSS:
        return page.locator(descriptor.css)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.XPATH:
        return page.locator(f"xpath={descriptor.xpath}")  # type: ignore[arg-type]
    msg = f"Unknown strategy: {strategy}"
    raise ValueError(msg)


async def _resolve_locator(
    page: Page,
    descriptor: LocatorDescriptor,
) -> tuple[Locator, LocatorStrategy]:
    """Try each strategy in order, return the first matching locator."""
    roots: list[Locator] = (
        [page.locator(descriptor.scope)] if descriptor.scope else [page]
    )
    candidates = _build_candidate_factories(descriptor)

    for root in roots:
        for entry in candidates:
            strategy = entry["strategy"]
            candidate = _create_locator_for_strategy(page, strategy, descriptor)
            if descriptor.scope:
                candidate = root.locator(
                    _create_locator_for_strategy(page, strategy, descriptor)
                )
            count = await candidate.count()
            if count > 0:
                return candidate.first, strategy

    msg = f"Unable to resolve locator for {descriptor}"
    raise RuntimeError(msg)


class BrowserAdapter:
    """Wraps a Playwright page with high-level element operations."""

    def __init__(self, page: Page) -> None:
        self._page = page

    async def goto_request_page(self, base_url: str, scenario: str) -> None:
        await self._page.goto(
            f"{base_url}/request.html?scenario={scenario}",
            wait_until="domcontentloaded",
        )

    async def click(self, descriptor: LocatorDescriptor) -> str:
        locator, strategy = await _resolve_locator(self._page, descriptor)
        await locator.click()
        return strategy.value

    async def select_option(self, descriptor: LocatorDescriptor, value: str) -> str:
        locator, strategy = await _resolve_locator(self._page, descriptor)
        await locator.select_option(value)
        return strategy.value

    async def check(self, descriptor: LocatorDescriptor) -> str:
        locator, strategy = await _resolve_locator(self._page, descriptor)
        await locator.check()
        return strategy.value

    async def wait_for(self, wait_ms: int) -> None:
        await self._page.wait_for_timeout(wait_ms)

    async def screenshot(self, file_path: str) -> str:
        await self._page.screenshot(path=file_path, full_page=True)
        return file_path

    async def extract_controls(self) -> list[dict[str, Any]]:
        return await self._page.locator(
            "main button, main select, main input, main [role='button']"
        ).evaluate_all(
            """elements => elements.map(el => ({
                role: el.getAttribute('role') || (el.tagName === 'BUTTON' ? 'button' : el.tagName === 'SELECT' ? 'combobox' : el.type === 'checkbox' ? 'checkbox' : 'input'),
                label: el.getAttribute('aria-label') || (el.labels && el.labels[0] ? el.labels[0].textContent.trim() : ''),
                text: (el.textContent || '').trim(),
                disabled: Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true'),
                value: 'value' in el ? String(el.value || '') : '',
                checked: 'checked' in el ? Boolean(el.checked) : false
            }))"""
        )
