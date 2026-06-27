// Logic for the login / register page (index.html).

// If the user already has a token, skip straight to the chat.
if (getToken()) {
  window.location.href = "/chat";
}

const tabsContainer = document.getElementById("tabs");
const tabs = document.querySelectorAll(".tab");
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const message = document.getElementById("authMessage");

// Switch between the Login and Register tabs (drives the sliding animation).
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const which = tab.dataset.tab;
    tabs.forEach((t) => t.classList.toggle("active", t === tab));
    tabsContainer.classList.toggle("show-register", which === "register");
    loginForm.classList.toggle("active", which === "login");
    registerForm.classList.toggle("active", which === "register");
    message.textContent = "";
    message.className = "message";
  });
});

function showMessage(text, isError = true) {
  message.textContent = text;
  message.className = "message " + (isError ? "error" : "success");
}

// Briefly show a loading label on a button while an async action runs.
function withLoading(button, loadingText, action) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = loadingText;
  return action().finally(() => {
    button.disabled = false;
    button.textContent = original;
  });
}

// ── Register ────────────────────────────────────────────────────────────────
registerForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const button = registerForm.querySelector("button");
  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value;

  withLoading(button, "Creating...", async () => {
    try {
      const res = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        showMessage(data.detail || "Registration failed.");
        return;
      }
      showMessage("Account created! You can now log in.", false);
      document.querySelector('.tab[data-tab="login"]').click();
    } catch {
      showMessage("Could not reach the server.");
    }
  });
});

// ── Login ─────────────────────────────────────────────────────────────────────
loginForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const button = loginForm.querySelector("button");
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;

  // The /login endpoint expects form-encoded fields named username/password.
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  withLoading(button, "Signing in...", async () => {
    try {
      const res = await fetch("/login", { method: "POST", body });
      const data = await res.json();
      if (!res.ok) {
        showMessage(data.detail || "Login failed.");
        return;
      }
      setToken(data.access_token);
      window.location.href = "/chat";
    } catch {
      showMessage("Could not reach the server.");
    }
  });
});
