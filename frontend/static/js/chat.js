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
const deleteDocsBtn = document.getElementById("deleteDocsBtn");
const deleteAccountBtn = document.getElementById("deleteAccountBtn");

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

// Minimal, SAFE Markdown renderer (escapes HTML first, then applies a few rules).
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderInline(s) {
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return s;
}

function renderMarkdown(md) {
  const lines = escapeHtml(md).split(/\r?\n/);
  let html = "";
  let inList = false;
  const closeList = () => {
    if (inList) {
      html += "</ul>";
      inList = false;
    }
  };
  for (const raw of lines) {
    const line = raw.trim();
    if (/^###?\s+/.test(line)) {
      closeList();
      html += "<h3>" + renderInline(line.replace(/^###?\s+/, "")) + "</h3>";
    } else if (/^#\s+/.test(line)) {
      closeList();
      html += "<h2>" + renderInline(line.replace(/^#\s+/, "")) + "</h2>";
    } else if (/^[-*]\s+/.test(line)) {
      if (!inList) {
        html += "<ul>";
        inList = true;
      }
      html += "<li>" + renderInline(line.replace(/^[-*]\s+/, "")) + "</li>";
    } else if (line === "") {
      closeList();
    } else {
      closeList();
      html += "<p>" + renderInline(line) + "</p>";
    }
  }
  closeList();
  return html;
}

function addMessage(role, text, sources) {
  clearEmptyState();
  const wrap = document.createElement("div");
  wrap.className = "msg " + role;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  // Render the assistant's answer as Markdown; keep user text plain.
  if (role === "assistant") {
    bubble.innerHTML = renderMarkdown(text);
  } else {
    bubble.textContent = text;
  }
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

// ── Privacy / GDPR actions ───────────────────────────────────────────────────
deleteDocsBtn.addEventListener("click", async () => {
  if (!confirm("Delete ALL your uploaded documents? This cannot be undone.")) return;
  try {
    const res = await fetch("/me/documents", { method: "DELETE", headers: authHeaders() });
    if (res.ok) {
      uploadStatus.textContent = "Your documents were deleted.";
      messages.innerHTML = '<div class="empty-state"><p>Upload your PDFs and ask a question to get started.</p></div>';
    } else {
      uploadStatus.textContent = "Could not delete your documents.";
    }
  } catch {
    uploadStatus.textContent = "Could not reach the server.";
  }
});

deleteAccountBtn.addEventListener("click", async () => {
  if (!confirm("Delete your account and ALL your data permanently? This cannot be undone.")) return;
  try {
    const res = await fetch("/me", { method: "DELETE", headers: authHeaders() });
    if (res.ok) {
      clearToken();
      window.location.href = "/";
    } else {
      uploadStatus.textContent = "Could not delete your account.";
    }
  } catch {
    uploadStatus.textContent = "Could not reach the server.";
  }
});

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
