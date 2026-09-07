const decisionList = document.querySelector("#decision-list");
const preparedList = document.querySelector("#prepared-list");
const memoryList = document.querySelector("#memory-list");
const toast = document.querySelector("#toast");
const cloudReview = document.querySelector("#cloud-review");
const cloudResult = document.querySelector("#cloud-result");
const memorySearch = document.querySelector("#memory-search");
const memoryQuery = document.querySelector("#memory-query");
const memorySearchResult = document.querySelector("#memory-search-result");

const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2400);
}

function renderDashboard(data) {
  document.querySelector("#household-name").textContent = data.household;
  document.querySelector("#demo-mode").textContent = data.mode;
  document.querySelector("#decision-count").textContent = data.summary.decisions;
  document.querySelector("#decision-title").textContent = data.summary.decisions === 1
    ? "One thing needs you"
    : `${data.summary.decisions} things need you`;
  document.querySelector("#prepared-count").textContent = `${data.summary.prepared} prepared`;
  document.querySelector("#memory-count").textContent = `${data.summary.remembered} active`;
  document.querySelector("#retrieval-detail").textContent = data.retrieval.detail;
  document.querySelector("#retrieval-state").textContent = data.retrieval.available
    ? "Available"
    : "Adapter ready";

  decisionList.innerHTML = data.decisions.length
    ? data.decisions.map((item) => `
      <article class="decision-card">
        <div>
          <h3>${escapeHtml(item.question)}</h3>
          <p>${escapeHtml(item.reason)}</p>
          <span class="source">Source: ${escapeHtml(item.source)}</span>
        </div>
        <div class="actions">
          <button class="button" type="button" data-later>Not yet</button>
          <button class="button primary" type="button" data-approve="${escapeHtml(item.decision_id)}">Approve</button>
        </div>
      </article>`).join("")
    : '<div class="empty">Nothing needs your attention. Aster will stay quiet.</div>';

  preparedList.innerHTML = data.prepared.map((item) => `
    <article class="row">
      <span class="row-icon" aria-hidden="true">✓</span>
      <div><h3>${escapeHtml(item.label)}</h3><p>${escapeHtml(item.subject)} · ${escapeHtml(item.source)}</p></div>
      <span class="badge">${escapeHtml(item.status)}</span>
    </article>`).join("") || '<div class="row"><div><h3>No routine work is waiting.</h3></div></div>';

  memoryList.innerHTML = data.memory.map((item) => `
    <article class="row">
      <span class="row-icon" aria-hidden="true">M</span>
      <div><h3>${escapeHtml(item.value)}</h3><p>${escapeHtml(item.kind)} · ${escapeHtml(item.source)}</p></div>
      <span class="badge">Active</span>
    </article>`).join("") || '<div class="row"><div><h3>No active family memory.</h3></div></div>';
}

async function loadDashboard() {
  const response = await fetch("/api/dashboard", { cache: "no-store" });
  if (!response.ok) throw new Error("The household review could not be loaded.");
  renderDashboard(await response.json());
}

decisionList.addEventListener("click", async (event) => {
  const approve = event.target.closest("[data-approve]");
  if (event.target.closest("[data-later]")) {
    showToast("Left pending. Nothing was changed.");
    return;
  }
  if (!approve) return;
  approve.disabled = true;
  try {
    const response = await fetch("/api/decisions/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision_id: approve.dataset.approve }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The decision could not be recorded.");
    renderDashboard(data);
    cloudReview.disabled = true;
    cloudReview.textContent = "Original cloud snapshot closed";
    cloudResult.hidden = true;
    showToast("Approved. The original request remains preserved in family memory.");
  } catch (error) {
    showToast(error.message);
    approve.disabled = false;
  }
});

cloudReview.addEventListener("click", async () => {
  cloudReview.disabled = true;
  cloudReview.textContent = "Aster is reviewing...";
  cloudResult.hidden = true;
  try {
    const response = await fetch("/api/agent/review", {
      method: "POST",
      headers: { "X-Family-Steward-Action": "cloud-review" },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The cloud review could not be completed.");
    cloudResult.textContent = data.review;
    cloudResult.hidden = false;
    showToast("AgentCore reviewed the original fictional snapshot.");
  } catch (error) {
    showToast(error.message);
  } finally {
    cloudReview.disabled = false;
    cloudReview.textContent = "Run fictional cloud review";
  }
});

memorySearch.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submit = memorySearch.querySelector("button");
  submit.disabled = true;
  submit.textContent = "Searching...";
  memorySearchResult.hidden = true;
  try {
    const response = await fetch("/api/memory/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Family-Steward-Action": "memory-search",
      },
      body: JSON.stringify({ query: memoryQuery.value }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Memory search could not be completed.");
    const memories = data.results.map((item) => `
      <article>
        <strong>${escapeHtml(item.value)}</strong>
        <span>${escapeHtml(item.kind)} · ${escapeHtml(item.source)}</span>
      </article>`).join("");
    memorySearchResult.innerHTML = memories || `<p>${escapeHtml(data.detail)}</p>`;
    memorySearchResult.hidden = false;
  } catch (error) {
    showToast(error.message);
  } finally {
    submit.disabled = false;
    submit.textContent = "Search memory";
  }
});

loadDashboard().catch((error) => showToast(error.message));
