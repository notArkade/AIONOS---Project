const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    let detail = "The assistant service is unavailable.";
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Keep a useful message when the server does not return JSON.
    }
    throw new Error(detail);
  }

  return response.json();
}

export function getDashboard() {
  return request("/dashboard");
}

export function sendChatMessage(message) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}