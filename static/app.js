const leadsInput = document.getElementById("leadsPath");
const subjectInput = document.getElementById("subjectPath");
const bodyInput = document.getElementById("bodyPath");
const sendBtn = document.getElementById("sendBtn");
const cancelBtn = document.getElementById("cancelBtn");
const dryRunBtn = document.getElementById("dryRunBtn");
const retryBtn = document.getElementById("retryBtn");
const logsWindow = document.getElementById("logsWindow");
const failureList = document.getElementById("failureList");
const progressBar = document.getElementById("progressBar");
const clearLogsBtn = document.getElementById("clearLogsBtn");
const copyEmailsBtn = document.getElementById("copyEmailsBtn");
const clearFailuresBtn = document.getElementById("clearFailuresBtn");

// Mode toggle elements
const staticMode = document.getElementById("staticMode");
const dynamicMode = document.getElementById("dynamicMode");
const staticFields = document.getElementById("staticFields");
const dynamicFields = document.getElementById("dynamicFields");
const dynamicSubject = document.getElementById("dynamicSubject");
const dynamicBody = document.getElementById("dynamicBody");
const dynamicLeadsPath = document.getElementById("dynamicLeadsPath");

// Stats
const statSuccess = document.getElementById("statSuccess");
const statFail = document.getElementById("statFail");
const statProgress = document.getElementById("statProgress");
const statTotalTime = document.getElementById("statTotalTime");
const statAvgTime = document.getElementById("statAvgTime");

// Tab Logic
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document
      .querySelectorAll(".tab")
      .forEach((t) => t.classList.remove("active"));
    document
      .querySelectorAll(".tab-content")
      .forEach((c) => c.classList.remove("active"));

    tab.classList.add("active");
    document.getElementById(`${tab.dataset.tab}Tab`).classList.add("active");

    if (tab.dataset.tab === "failures") {
      loadFailures();
    }
  });
});

// Toggle between static and dynamic modes
staticMode.addEventListener("change", () => {
  if (staticMode.checked) {
    staticFields.style.display = "block";
    dynamicFields.style.display = "none";
  }
});

dynamicMode.addEventListener("change", () => {
  if (dynamicMode.checked) {
    staticFields.style.display = "none";
    dynamicFields.style.display = "block";
  }
});

async function startMailing(isRetry = false, isDryRun = false) {
  const isDynamic = dynamicMode.checked;

  const payload = {
    is_retry: isRetry,
    is_dry_run: isDryRun,
    is_dynamic: isDynamic,
  };

  if (isDynamic) {
    // Dynamic mode: send content directly
    payload.leads_path = dynamicLeadsPath.value;
    payload.subject_content = dynamicSubject.value;
    payload.body_content = dynamicBody.value;
  } else {
    // Static mode: send file paths
    payload.leads_path = leadsInput.value;
    payload.subject_path = subjectInput.value;
    payload.body_path = bodyInput.value;
  }

  try {
    const res = await fetch("/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      sendBtn.style.display = "none";
      cancelBtn.style.display = "flex";
      pollStatus();
    } else {
      const err = await res.json();
      alert(err.detail || "Error starting process");
    }
  } catch (e) {
    console.error(e);
    alert("Server connection failed");
  }
}

async function cancelMailing() {
  await fetch("/cancel", { method: "POST" });
}

async function pollStatus() {
  const interval = setInterval(async () => {
    const res = await fetch("/status");
    const data = await res.json();

    // Update Stats
    statSuccess.innerText = data.success;
    statFail.innerText = data.fail;
    statProgress.innerText = `${data.progress}%`;
    statTotalTime.innerText = `${data.total_elapsed}s`;
    statAvgTime.innerText = `${data.avg_time_per_email}s`;
    progressBar.style.width = `${data.progress}%`;

    // Update Logs
    logsWindow.innerHTML = data.logs
      .map((log) => {
        let cls = "log-info";
        if (log.includes("Success")) cls = "log-success";
        if (log.includes("Failed")) cls = "log-error";
        return `<div class="log-entry ${cls}">${log}</div>`;
      })
      .join("");
    logsWindow.scrollTop = logsWindow.scrollHeight;

    if (!data.is_running) {
      clearInterval(interval);
      sendBtn.style.display = "flex";
      cancelBtn.style.display = "none";
    }
  }, 1000);
}

async function loadFailures() {
  const res = await fetch("/failures");
  const data = await res.json();

  if (data.length === 0) {
    failureList.innerHTML =
      '<div class="log-entry log-info" style="padding: 2rem; text-align: center; opacity: 0.5;">No failed emails found.</div>';
    retryBtn.disabled = true;
    return;
  }

  retryBtn.disabled = false;
  failureList.innerHTML = data
    .map(
      (f) => `
        <div class="failure-item">
            <span class="failure-email">${f.email}</span>
            <span class="failure-error">${f.error}</span>
            <div style="font-size: 0.65rem; color: var(--text-secondary); margin-top: 0.25rem;">${f.timestamp}</div>
        </div>
    `,
    )
    .join("");
}

async function clearLogs() {
  logsWindow.innerHTML = '<div class="log-entry log-info">Logs cleared.</div>';
  // Also clear backend state if needed
  await fetch("/clear-logs", { method: "POST" });
}

async function copyFailedEmails() {
  const res = await fetch("/failures");
  const data = await res.json();

  if (data.length === 0) {
    alert("No failed emails to copy");
    return;
  }

  const emails = data.map((f) => f.email).join("\n");

  try {
    await navigator.clipboard.writeText(emails);
    alert(`Copied ${data.length} email(s) to clipboard!`);
  } catch (e) {
    // Fallback for older browsers
    const textarea = document.createElement("textarea");
    textarea.value = emails;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    alert(`Copied ${data.length} email(s) to clipboard!`);
  }
}

async function clearFailures() {
  if (!confirm("Are you sure you want to clear all failure logs?")) {
    return;
  }

  await fetch("/clear-failures", { method: "POST" });
  loadFailures();
}

sendBtn.addEventListener("click", () => startMailing(false, false));
dryRunBtn.addEventListener("click", () => startMailing(false, true));
retryBtn.addEventListener("click", () => startMailing(true, false));
cancelBtn.addEventListener("click", cancelMailing);
clearLogsBtn.addEventListener("click", clearLogs);
copyEmailsBtn.addEventListener("click", copyFailedEmails);
clearFailuresBtn.addEventListener("click", clearFailures);

// Initial Load
pollStatus();
loadFailures();
