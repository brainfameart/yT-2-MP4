const urlInput = document.getElementById("urlInput");
const qualitySelect = document.getElementById("quality");
const startBtn = document.getElementById("startBtn");
const progressWrap = document.getElementById("progressWrap");
const progressFill = document.getElementById("progressFill");
const statusText = document.getElementById("statusText");
const downloadLink = document.getElementById("downloadLink");
const errorText = document.getElementById("errorText");

let pollTimer = null;

function resetUI() {
  progressWrap.classList.add("hidden");
  downloadLink.classList.add("hidden");
  errorText.classList.add("hidden");
  progressFill.style.width = "0%";
  statusText.textContent = "Starting…";
  if (pollTimer) clearInterval(pollTimer);
}

function showError(msg) {
  errorText.textContent = msg;
  errorText.classList.remove("hidden");
  progressWrap.classList.add("hidden");
  startBtn.disabled = false;
}

async function startConversion() {
  const url = urlInput.value.trim();
  if (!url) {
    showError("Please paste a YouTube link first.");
    return;
  }

  resetUI();
  startBtn.disabled = true;
  progressWrap.classList.remove("hidden");

  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, quality: qualitySelect.value }),
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.error || "Something went wrong.");
      return;
    }

    pollStatus(data.job_id);
  } catch (err) {
    showError("Could not reach the server.");
  }
}

function pollStatus(jobId) {
  pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`/api/status/${jobId}`);
      const job = await res.json();

      if (job.status === "downloading") {
        const pct = Math.round(job.percent || 0);
        progressFill.style.width = pct + "%";
        statusText.textContent = `Downloading… ${pct}%`;
      } else if (job.status === "processing") {
        progressFill.style.width = "100%";
        statusText.textContent = "Converting to MP4…";
      } else if (job.status === "done") {
        clearInterval(pollTimer);
        progressFill.style.width = "100%";
        statusText.textContent = "Done!";
        downloadLink.href = `/api/download/${jobId}`;
        downloadLink.classList.remove("hidden");
        startBtn.disabled = false;
      } else if (job.status === "error") {
        clearInterval(pollTimer);
        showError(job.error || "Conversion failed.");
      }
    } catch (err) {
      clearInterval(pollTimer);
      showError("Lost connection to the server.");
    }
  }, 1200);
}

startBtn.addEventListener("click", startConversion);
urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") startConversion();
});
