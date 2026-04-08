"""Decision policy helpers for internal and external benchmark modes."""

from __future__ import annotations

from dataclasses import asdict

from .types import (
    ActionType,
    Decision,
    DecisionResponse,
    LocatorDescriptor,
    Observation,
    RequestContext,
    TerminalState,
)


def _has_text(observation: Observation, text: str) -> bool:
    haystack = (
        f"{observation.title} "
        f"{' '.join(observation.headings)} "
        f"{' '.join(observation.banners)} "
        f"{observation.dom_evidence}"
    ).lower()
    return text.lower() in haystack


def _find_control(
    observation: Observation,
    predicate: object,
) -> dict | None:
    """Find the first control matching the supplied predicate."""
    if not callable(predicate):
        return None
    for control in observation.controls:
        if predicate(control):
            return control
    return None


def detect_page_state(observation: Observation) -> str:
    """Detect the current page state from observation text."""
    if _has_text(observation, "Request submitted successfully"):
        return TerminalState.SUCCESS.value

    if _has_text(observation, "Request already exists"):
        return TerminalState.ALREADY_REQUESTED.value

    if _has_text(observation, "Manager approval required"):
        return TerminalState.MANUAL_REVIEW_REQUIRED.value

    if _has_text(observation, "Permission is not available"):
        return TerminalState.PERMISSION_NOT_AVAILABLE.value

    if _has_text(observation, "Temporary service issue"):
        return "transient_failure"

    if _has_text(observation, "Unlocking permissions"):
        return "dynamic_loading"

    if _has_text(observation, "Step 1: Choose a system"):
        return "step_system"

    if _has_text(observation, "Step 2: Choose access package"):
        return "step_package"

    if _has_text(observation, "Step 3: Review request"):
        return "step_review"

    return TerminalState.UNKNOWN_STATE.value


def _terminal_decision(state: str, reason: str) -> Decision:
    return Decision(
        state=state,
        action_type=ActionType.TERMINAL,
        reason=reason,
        terminal=True,
    )


def decide_next_action(
    request_context: RequestContext,
    observation: Observation,
) -> Decision:
    """Determine the next internal action from the current page observation."""
    state = detect_page_state(observation)

    if state == TerminalState.SUCCESS.value:
        return _terminal_decision(state, "The benchmark page reports a successful request.")

    if state == TerminalState.ALREADY_REQUESTED.value:
        return _terminal_decision(
            state,
            "The page states that the permission request already exists.",
        )

    if state == TerminalState.MANUAL_REVIEW_REQUIRED.value:
        return _terminal_decision(
            state,
            "The workflow reached a human approval gate.",
        )

    if state == TerminalState.PERMISSION_NOT_AVAILABLE.value:
        return _terminal_decision(
            state,
            "The requested permission is not available in the current workflow.",
        )

    if state == TerminalState.UNKNOWN_STATE.value:
        return _terminal_decision(
            state,
            "The page does not match a supported benchmark state.",
        )

    if state == "dynamic_loading":
        return Decision(
            state=state,
            action_type=ActionType.WAIT,
            reason="The page is still re-rendering the permission controls.",
            terminal=False,
            wait_ms=400,
        )

    if state == "transient_failure":
        return Decision(
            state=state,
            action_type=ActionType.CLICK,
            reason="The page indicates a transient failure and a retry submit is available.",
            terminal=False,
            locator=LocatorDescriptor(
                scope="main",
                role="button",
                name="Retry submit",
                text="Retry submit",
                test_id="submit-request",
                css="#submit-request-button",
            ),
        )

    if state == "step_system":
        system_select = _find_control(
            observation,
            lambda control: control.get("role") == "combobox"
            and control.get("label") == "System",
        )
        if not system_select or not system_select.get("value"):
            return Decision(
                state=state,
                action_type=ActionType.SELECT_OPTION,
                reason="The system is not selected yet.",
                terminal=False,
                locator=LocatorDescriptor(
                    scope="main",
                    label="System",
                    test_id="system-select",
                    css="#system-select",
                ),
                value=request_context.target_system,
            )
        return Decision(
            state=state,
            action_type=ActionType.CLICK,
            reason="The system is selected, so the workflow can continue.",
            terminal=False,
            locator=LocatorDescriptor(
                scope="main",
                role="button",
                name="Next",
                text="Next",
                test_id="workflow-next",
                css="#workflow-next-button",
            ),
        )

    if state == "step_package":
        package_select = _find_control(
            observation,
            lambda control: control.get("role") == "combobox"
            and control.get("label") == "Access package",
        )
        permission_select = _find_control(
            observation,
            lambda control: control.get("role") == "combobox"
            and control.get("label") == "Permission",
        )
        acknowledgement = _find_control(
            observation,
            lambda control: control.get("role") == "checkbox"
            and "Acknowledge production access" in (control.get("label") or ""),
        )

        if not package_select or not package_select.get("value"):
            return Decision(
                state=state,
                action_type=ActionType.SELECT_OPTION,
                reason="The access package must be selected before continuing.",
                terminal=False,
                locator=LocatorDescriptor(
                    scope="main",
                    label="Access package",
                    test_id="package-select",
                    css="#package-select",
                ),
                value=request_context.target_package,
            )

        if acknowledgement and not acknowledgement.get("checked"):
            return Decision(
                state=state,
                action_type=ActionType.CHECK_BOX,
                reason="The production prerequisite checkbox is required to unlock permissions.",
                terminal=False,
                locator=LocatorDescriptor(
                    scope="main",
                    label="Acknowledge production access",
                    test_id="production-ack",
                    css="#production-ack",
                ),
            )

        if permission_select and permission_select.get("disabled"):
            return _terminal_decision(
                TerminalState.BLOCKED_BY_VALIDATION.value,
                "Permission selection is still disabled after the expected prerequisites.",
            )

        if not permission_select or not permission_select.get("value"):
            return Decision(
                state=state,
                action_type=ActionType.SELECT_OPTION,
                reason="A permission must be selected before proceeding to review.",
                terminal=False,
                locator=LocatorDescriptor(
                    scope="main",
                    label="Permission",
                    test_id="permission-select",
                    css="#permission-select",
                ),
                value=request_context.target_permission,
            )

        return Decision(
            state=state,
            action_type=ActionType.CLICK,
            reason="The package and permission are selected, so the workflow can continue.",
            terminal=False,
            locator=LocatorDescriptor(
                scope="main",
                role="button",
                name="Next",
                text="Next",
                test_id="workflow-next",
                css="#workflow-next-button",
            ),
        )

    if state == "step_review":
        submit_button = _find_control(
            observation,
            lambda control: control.get("role") == "button"
            and "submit" in (control.get("text") or "").lower(),
        )

        if submit_button and submit_button.get("disabled"):
            return _terminal_decision(
                TerminalState.BLOCKED_BY_VALIDATION.value,
                "The submit button is disabled and the page does not expose a valid forward path.",
            )

        return Decision(
            state=state,
            action_type=ActionType.CLICK,
            reason="The request is ready for submission.",
            terminal=False,
            locator=LocatorDescriptor(
                scope="main",
                role="button",
                name="Submit request",
                text="Submit request",
                test_id="submit-request",
                css="#submit-request-button",
            ),
        )

    return _terminal_decision(
        TerminalState.UNKNOWN_STATE.value,
        "No policy rule matched the current page.",
    )


def coerce_locator_descriptor(payload: dict | LocatorDescriptor | None) -> LocatorDescriptor | None:
    """Convert a dict payload into a locator descriptor."""
    if payload is None or isinstance(payload, LocatorDescriptor):
        return payload
    return LocatorDescriptor(**payload)


def normalize_external_decision(
    payload: dict,
    *,
    expected_run_id: str,
    expected_step_id: str,
) -> Decision:
    """Validate and normalize an external GHC decision payload."""
    required_fields = {"runId", "stepId", "actionType", "reason"}
    missing = sorted(field for field in required_fields if field not in payload)
    if missing:
        raise ValueError(f"Missing decision response fields: {', '.join(missing)}")

    if payload["runId"] != expected_run_id:
        raise ValueError("Decision response runId does not match the active run.")

    if payload["stepId"] != expected_step_id:
        raise ValueError("Decision response stepId does not match the pending step.")

    action_type = ActionType(payload["actionType"])
    locator = coerce_locator_descriptor(payload.get("locator"))
    wait_ms = payload.get("waitMs")
    reason = str(payload.get("reason") or "").strip()

    if action_type in {ActionType.CLICK, ActionType.CHECK_BOX, ActionType.SELECT_OPTION} and locator is None:
        raise ValueError("Locator is required for click, checkbox, and select_option actions.")

    if action_type == ActionType.SELECT_OPTION and not payload.get("value"):
        raise ValueError("value is required for select_option actions.")

    terminal_state = payload.get("terminalState")
    if action_type == ActionType.TERMINAL:
        state = terminal_state or TerminalState.UNKNOWN_STATE.value
        return Decision(
            state=state,
            action_type=action_type,
            reason=reason or "The external controller requested a terminal stop.",
            terminal=True,
        )

    return Decision(
        state="external_decision",
        action_type=action_type,
        reason=reason or "Execute the external controller decision.",
        terminal=False,
        locator=locator,
        value=payload.get("value"),
        wait_ms=wait_ms,
    )
