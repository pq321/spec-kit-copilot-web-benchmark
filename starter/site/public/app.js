const scenario = new URLSearchParams(window.location.search).get("scenario") || "normal";

const systems = ["Payroll Portal", "Finance Hub", "Analytics Console"];
const packages = ["Finance Reporter", "Payroll Editor", "Quarterly Auditor"];
const permissions = ["View Reports", "Submit Change Requests", "Approve Access Reviews"];

const scenarioMeta = {
  normal: "Happy path with a standard successful request.",
  already_requested: "The request already exists and submit must not proceed.",
  prerequisite_unlock: "A prerequisite must be satisfied before permissions unlock.",
  ambiguous_locator: "Multiple similar buttons exist and only the main workflow button advances.",
  dynamic_dom: "Controls are replaced after the previous choice, forcing a re-observation step.",
  manual_review: "The flow reaches a human approval gate and must stop safely.",
  failure_recovery: "The first submit attempt fails transiently, then succeeds on retry."
};

const state = {
  scenario,
  step: 1,
  system: "",
  packageName: "",
  permission: "",
  acknowledgedProduction: false,
  loadingPermissions: false,
  failureCount: 0,
  statusBanner: {
    kind: "info",
    text: "Complete the workflow one step at a time."
  }
};

const scenarioDescription = document.getElementById("scenario-description");
const sidebarPanel = document.getElementById("sidebar-panel");
const workflowRoot = document.getElementById("workflow-root");

scenarioDescription.textContent = scenarioMeta[scenario] || scenarioMeta.normal;

function setBanner(kind, text) {
  state.statusBanner = { kind, text };
}

function renderBanner() {
  return `
    <div class="banner ${state.statusBanner.kind}" role="alert" data-status-banner="${state.statusBanner.kind}">
      ${state.statusBanner.text}
    </div>
  `;
}

function renderSidebar() {
  if (scenario !== "ambiguous_locator") {
    sidebarPanel.innerHTML = `
      <h2 class="panel-title">Scenario Notes</h2>
      <p class="hint">${scenarioDescription.textContent}</p>
      <p class="hint">Observe the main workflow before clicking anything.</p>
    `;
    return;
  }

  sidebarPanel.innerHTML = `
    <h2 class="panel-title">Shortcut Panel</h2>
    <p class="hint">This panel intentionally contains misleading buttons.</p>
    <button type="button" class="secondary" id="sidebar-next-button">Next</button>
    <button type="button" class="secondary" id="sidebar-submit-button">Submit request</button>
  `;

  document.getElementById("sidebar-next-button").addEventListener("click", () => {
    setBanner("warning", "The sidebar Next button is not part of the workflow.");
    render();
  });
  document.getElementById("sidebar-submit-button").addEventListener("click", () => {
    setBanner("warning", "The sidebar submit button does not submit the request.");
    render();
  });
}

function renderSystemStep() {
  const nextDisabled = state.system === "";
  return `
    ${renderBanner()}
    <section data-step="system">
      <h2>Step 1: Choose a system</h2>
      <div class="control-group">
        <label for="system-select">System</label>
        <select id="system-select" data-testid="system-select" aria-describedby="system-hint">
          <option value="">Select a system</option>
          ${systems
            .map(
              (entry) =>
                `<option value="${entry}" ${state.system === entry ? "selected" : ""}>${entry}</option>`
            )
            .join("")}
        </select>
        <p id="system-hint" class="hint">Selecting a system unlocks the request package step.</p>
      </div>
      <div class="button-row">
        <button type="button" class="primary" id="workflow-next-button" data-testid="workflow-next" ${
          nextDisabled ? "disabled" : ""
        }>Next</button>
      </div>
    </section>
  `;
}

function renderPackageStep() {
  if (scenario === "dynamic_dom" && state.loadingPermissions) {
    return `
      ${renderBanner()}
      <section data-step="dynamic-loading">
        <h2>Step 2: Unlocking permissions</h2>
        <div class="loading-box" aria-live="polite">
          Unlocking permissions for <strong>${state.system}</strong>. Re-observe the page after this state changes.
        </div>
      </section>
    `;
  }

  const permissionLockedByPackage = state.packageName === "";
  const permissionLockedByAck = scenario === "prerequisite_unlock" && !state.acknowledgedProduction;
  const permissionDisabled = permissionLockedByPackage || permissionLockedByAck;
  const nextDisabled = state.permission === "";

  return `
    ${renderBanner()}
    <section data-step="package">
      <h2>Step 2: Choose access package</h2>
      <div class="control-group">
        <label for="package-select">Access package</label>
        <select id="package-select" data-testid="package-select">
          <option value="">Select a package</option>
          ${packages
            .map(
              (entry) =>
                `<option value="${entry}" ${state.packageName === entry ? "selected" : ""}>${entry}</option>`
            )
            .join("")}
        </select>
      </div>
      <fieldset class="control-group" ${scenario !== "prerequisite_unlock" ? "hidden" : ""}>
        <legend>Production prerequisite</legend>
        <label for="production-ack">
          <input type="checkbox" id="production-ack" data-testid="production-ack" ${
            state.acknowledgedProduction ? "checked" : ""
          } />
          Acknowledge production access
        </label>
        <p class="hint">This checkbox must be enabled before the permission list unlocks.</p>
      </fieldset>
      <div class="control-group">
        <label for="permission-select">Permission</label>
        <select id="permission-select" data-testid="permission-select" ${permissionDisabled ? "disabled" : ""}>
          <option value="">Select a permission</option>
          ${permissions
            .map(
              (entry) =>
                `<option value="${entry}" ${state.permission === entry ? "selected" : ""}>${entry}</option>`
            )
            .join("")}
        </select>
        ${
          permissionDisabled
            ? `<p class="hint">Choose the required upstream options to unlock permissions.</p>`
            : `<p class="hint">Permissions are now available for selection.</p>`
        }
      </div>
      <div class="button-row">
        <button type="button" class="secondary" id="back-button">Back</button>
        <button type="button" class="primary" id="workflow-next-button" data-testid="workflow-next" ${
          nextDisabled ? "disabled" : ""
        }>Next</button>
      </div>
    </section>
  `;
}

function renderReviewStep() {
  const alreadyRequested = scenario === "already_requested";
  const submitDisabled = alreadyRequested;
  const submitLabel = scenario === "failure_recovery" && state.failureCount > 0 ? "Retry submit" : "Submit request";

  return `
    ${renderBanner()}
    <section data-step="review">
      <h2>Step 3: Review request</h2>
      <div class="review-card">
        <p><strong>System:</strong> ${state.system}</p>
        <p><strong>Access package:</strong> ${state.packageName}</p>
        <p><strong>Permission:</strong> ${state.permission}</p>
      </div>
      ${
        alreadyRequested
          ? `<div class="banner info" role="alert" data-status-banner="already-requested">Request already exists for this permission.</div>`
          : ""
      }
      <div class="button-row">
        <button type="button" class="secondary" id="back-button">Back</button>
        <button type="button" class="primary" id="submit-request-button" data-testid="submit-request" ${
          submitDisabled ? "disabled" : ""
        }>${submitLabel}</button>
      </div>
    </section>
  `;
}

function renderTerminalStep() {
  if (scenario === "manual_review") {
    return `
      <section class="status-card" data-step="manual-review">
        <div class="banner warning" role="alert" data-status-banner="manual-review">Manager approval required before access can be granted.</div>
        <h2>Manual approval required</h2>
        <p>The request has been assembled, but a human reviewer must approve the final access grant.</p>
        <span class="pill">manual_approval_required</span>
      </section>
    `;
  }

  return `
    <section class="status-card" data-step="completed">
      <div class="banner success" role="alert" data-status-banner="success">Request submitted successfully.</div>
      <h2>Request complete</h2>
      <p>The fake permission request was submitted and recorded successfully.</p>
      <span class="pill">success</span>
    </section>
  `;
}

function renderWorkflow() {
  if (state.step === 1) {
    return renderSystemStep();
  }
  if (state.step === 2) {
    return renderPackageStep();
  }
  if (state.step === 3) {
    return renderReviewStep();
  }
  return renderTerminalStep();
}

function handleSystemChange(event) {
  state.system = event.target.value;
  if (state.system) {
    setBanner("info", `System selected: ${state.system}.`);
  }
  render();
}

function handlePackageChange(event) {
  state.packageName = event.target.value;
  if (state.packageName) {
    setBanner("info", `Package selected: ${state.packageName}.`);
  }
  render();
}

function handlePermissionChange(event) {
  state.permission = event.target.value;
  if (state.permission) {
    setBanner("info", `Permission selected: ${state.permission}.`);
  }
  render();
}

function handleAckChange(event) {
  state.acknowledgedProduction = event.target.checked;
  setBanner(
    "info",
    state.acknowledgedProduction
      ? "Production prerequisite acknowledged."
      : "Production prerequisite removed."
  );
  render();
}

function goToNextStep() {
  if (state.step === 1 && state.system) {
    state.step = 2;
    if (scenario === "dynamic_dom") {
      state.loadingPermissions = true;
      setBanner("info", "Loading permissions after the system change.");
      render();
      window.setTimeout(() => {
        state.loadingPermissions = false;
        setBanner("info", "Permissions re-rendered. Re-observe before continuing.");
        render();
      }, 300);
      return;
    }
    setBanner("info", "Continue to choose access details.");
  } else if (state.step === 2 && state.permission) {
    state.step = 3;
    setBanner("info", "Review the request before submitting.");
  }
  render();
}

function goToPreviousStep() {
  if (state.step > 1 && state.step < 4) {
    state.step -= 1;
    setBanner("info", "Returned to the previous step.");
    render();
  }
}

function submitRequest() {
  if (scenario === "manual_review") {
    state.step = 4;
    setBanner("warning", "Human manager approval is required.");
    render();
    return;
  }

  if (scenario === "failure_recovery" && state.failureCount === 0) {
    state.failureCount += 1;
    setBanner("error", "Temporary service issue detected. Retry the submit action.");
    render();
    return;
  }

  state.step = 4;
  setBanner("success", "Request submitted successfully.");
  render();
}

function bindEvents() {
  const systemSelect = document.getElementById("system-select");
  const packageSelect = document.getElementById("package-select");
  const permissionSelect = document.getElementById("permission-select");
  const productionAck = document.getElementById("production-ack");
  const nextButton = document.getElementById("workflow-next-button");
  const backButton = document.getElementById("back-button");
  const submitButton = document.getElementById("submit-request-button");

  systemSelect?.addEventListener("change", handleSystemChange);
  packageSelect?.addEventListener("change", handlePackageChange);
  permissionSelect?.addEventListener("change", handlePermissionChange);
  productionAck?.addEventListener("change", handleAckChange);
  nextButton?.addEventListener("click", goToNextStep);
  backButton?.addEventListener("click", goToPreviousStep);
  submitButton?.addEventListener("click", submitRequest);
}

function render() {
  renderSidebar();
  workflowRoot.innerHTML = renderWorkflow();
  bindEvents();
}

render();
