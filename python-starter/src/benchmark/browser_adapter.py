"""Playwright browser adapter for locator resolution and page actions."""

from __future__ import annotations

from typing import Any

from playwright.async_api import Locator, Page

from .types import LOCATOR_STRATEGY_ORDER, LocatorDescriptor, LocatorStrategy


def _build_candidate_factories(descriptor: LocatorDescriptor) -> list[LocatorStrategy]:
    candidates: list[LocatorStrategy] = []

    if descriptor.role and descriptor.name:
        candidates.append(LocatorStrategy.ROLE)
    if descriptor.label:
        candidates.append(LocatorStrategy.LABEL)
    if descriptor.text:
        candidates.append(LocatorStrategy.TEXT)
    if descriptor.test_id:
        candidates.append(LocatorStrategy.TEST_ID)
    if descriptor.css:
        candidates.append(LocatorStrategy.CSS)
    if descriptor.xpath:
        candidates.append(LocatorStrategy.XPATH)

    return [strategy for strategy in LOCATOR_STRATEGY_ORDER if strategy in candidates]


def build_locator_plan(descriptor: LocatorDescriptor) -> list[LocatorStrategy]:
    """Return the ordered list of strategies available for the descriptor."""
    return _build_candidate_factories(descriptor)


def _create_locator_for_strategy(
    root: Page | Locator,
    strategy: LocatorStrategy,
    descriptor: LocatorDescriptor,
) -> Locator:
    if strategy == LocatorStrategy.ROLE:
        return root.get_by_role(descriptor.role, name=descriptor.name)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.LABEL:
        return root.get_by_label(descriptor.label)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.TEXT:
        return root.get_by_text(descriptor.text)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.TEST_ID:
        return root.get_by_test_id(descriptor.test_id)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.CSS:
        return root.locator(descriptor.css)  # type: ignore[arg-type]
    if strategy == LocatorStrategy.XPATH:
        return root.locator(f"xpath={descriptor.xpath}")  # type: ignore[arg-type]
    raise ValueError(f"Unknown strategy: {strategy}")


async def _resolve_locator(
    page: Page,
    descriptor: LocatorDescriptor,
) -> tuple[Locator, LocatorStrategy]:
    """Try each strategy in order and return the first matching locator."""
    root: Page | Locator = page.locator(descriptor.scope) if descriptor.scope else page

    for strategy in _build_candidate_factories(descriptor):
        candidate = _create_locator_for_strategy(root, strategy, descriptor)
        if await candidate.count() > 0:
            return candidate.first, strategy

    raise RuntimeError(f"Unable to resolve locator for {descriptor}")


class BrowserAdapter:
    """Wraps a Playwright page with high-level benchmark operations."""

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
