// Logic for the main chat page (chat.html).

// Must be logged in to be here.
if (!getToken()) {
  window.location.href = "/";
}

const userEmail = document.getElementById("userEmail");
const logoutBtn = document.getElementById("logoutBtn");
const fileInput = document.getElementById("fileInput");
const processBtn = document.getElementById("processBtn");
const uploadStatus = document.getElementById("uploadStatus");
const messages = document.getElementById("messages");
const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");

// ── Load the current user (and validate the token) ───────────────────────────
async function loadUser() {
  try {
    const res = await fetch("/me", { headers: authHeaders() });
    if (!res.ok) {
      clearToken();
      window.location.href = "/";
      return;
    }
    const data = await res.json();
    userEmail.textContent = data.email;
  } catch {
    uploadStatus.textContent = "Could not reach the server.";
  }
}
loadUser();

logoutBtn.addEventListener("click", () => {
  clearToken();
  window.location.href = "/";
});

// ── Process uploaded PDFs ────────────────────────────────────────────────────
processBtn.addEventListener("click", async () => {
  if (!fileInput.files.length) {
    uploadStatus.textContent = "Please choose at least one PDF.";
    return;
  }

  const formData = new FormData();
  for (const file of fileInput.files) {
    formData.append("files", file);
  }

  uploadStatus.textContent = "Processing your PDFs...";
  processBtn.disabled = true;
  try {
    const res = await fetch("/process", {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) {
      uploadStatus.textContent = data.detail || "Processing failed.";
    } else {
      uploadStatus.textContent = `Done! ${data.chunks} chunks from ${data.files} file(s).`;
    }
  } catch {
    uploadStatus.textContent = "Could not reach the server.";
  } finally {
    processBtn.disabled = false;
  }
});

// ── Chat ──────────────────────────────────────────────────────────────────────
function clearEmptyState() {
  const empty = messages.querySelector(".empty-state");
  if (empty) empty.remove();
}

function addMessage(role, text, sources) {
  clearEmptyState();
  const wrap = document.createElement("div");
  wrap.className = "msg " + role;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);

  if (sources && sources.length) {
    const src = document.createElement("div");
    src.className = "sources";
    src.textContent = "Sources: " + sources.join(", ");
    wrap.appendChild(src);
  }

  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  addMessage("user", question);
  questionInput.value = "";

  const thinking = addMessage("assistant", "Thinking…");

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    thinking.remove();
    if (!res.ok) {
      addMessage("assistant", data.detail || "Something went wrong.");
    } else {
      addMessage("assistant", data.answer, data.sources);
    }
  } catch {
    thinking.remove();
    addMessage("assistant", "Could not reach the server.");
  }
});
