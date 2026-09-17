const configuredUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_BASE_URL = configuredUrl.replace(/\/$/, "").endsWith("/api")
  ? configuredUrl.replace(/\/$/, "")
  : `${configuredUrl.replace(/\/$/, "")}/api`;

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

export function getSummary() {
  return request("/summary");
}

export function getOpenTasks() {
  return request("/tasks/open");
}

export function getCompletedTasks() {
  return request("/tasks/completed");
}

export function getMeetings() {
  return request("/meetings");
}

export function getDeadlines() {
  return request("/deadlines");
}

export function getFollowUps() {
  return request("/follow-ups");
}

export function getUnresolved() {
  return request("/unresolved");
}

export function sendChatMessage(message) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}