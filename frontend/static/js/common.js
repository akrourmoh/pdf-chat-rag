// Shared helpers for managing the login token and authenticated requests.
// Loaded on every page before the page-specific script.

const TOKEN_KEY = "pdfchat_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// Returns the Authorization header (or an empty object if not logged in).
function authHeaders() {
  const token = getToken();
  return token ? { Authorization: "Bearer " + token } : {};
}
