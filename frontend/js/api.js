/**
 * CareerOS — Central API Client
 * Handles HTTP requests, timeouts, and standardized error envelopes.
 */

const API_BASE = "";

export async function request(endpoint, options = {}) {
  const timeoutMs = options.timeout || 30000;
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  const defaultHeaders = {
    "Accept": "application/json",
  };

  if (!(options.body instanceof FormData)) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    signal: controller.signal,
  };

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, config);
    clearTimeout(id);

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = data?.error?.detail || data?.detail || `HTTP ${response.status}: Request failed`;
      const err = new Error(typeof errorMsg === "string" ? errorMsg : JSON.stringify(errorMsg));
      err.status = response.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (error) {
    clearTimeout(id);
    if (error.name === "AbortError") {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s`);
    }
    throw error;
  }
}

export const api = {
  // System Health
  getHealth: () => request("/health", { timeout: 5000 }),
  getReady: () => request("/ready", { timeout: 5000 }),
  getStatus: () => request("/api/v1/status", { timeout: 5000 }),

  // Resume
  uploadResume: (formData) => request("/api/v1/resume/upload", { method: "POST", body: formData, timeout: 60000 }),
  analyzeResume: (forceRefresh = false) => request("/api/v1/resume/analyze", {
    method: "POST",
    body: JSON.stringify({ force_refresh: forceRefresh }),
    timeout: 60000,
  }),
  getResumeProfile: () => request("/api/v1/resume/profile"),

  // Jobs
  listJobs: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request(`/api/v1/jobs${q ? `?${q}` : ""}`);
  },
  getJob: (jobId) => request(`/api/v1/jobs/${jobId}`),

  // Matching & Career State
  runMatching: (targetRoles = [], frequencyThreshold = 0.40) => request("/api/v1/matching/run", {
    method: "POST",
    body: JSON.stringify({ target_roles: targetRoles, frequency_threshold: frequencyThreshold }),
    timeout: 60000,
  }),
  getMatchingResults: () => request("/api/v1/matching/results"),
  getCareerState: () => request("/api/v1/career/state"),
  getReadiness: () => request("/api/v1/career/readiness"),

  // Roadmap
  getRoadmap: () => request("/api/v1/roadmap"),
  generateRoadmap: (maxMissions = 8, enrich = true) => request("/api/v1/roadmap/generate", {
    method: "POST",
    body: JSON.stringify({ max_missions: maxMissions, enrich_with_llm: enrich }),
    timeout: 60000,
  }),
  startMission: (missionId) => request(`/api/v1/roadmap/missions/${missionId}/start`, { method: "POST" }),
  completeMission: (missionId, notes = "") => request(`/api/v1/roadmap/missions/${missionId}/complete`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  }),

  // Interviews
  listInterviews: () => request("/api/v1/interviews"),
  createInterview: (payload) => request("/api/v1/interviews", {
    method: "POST",
    body: JSON.stringify(payload),
    timeout: 45000,
  }),
  submitAnswer: (sessionId, answer) => request(`/api/v1/interviews/${sessionId}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer }),
    timeout: 60000,
  }),
  getInterviewResults: (sessionId) => request(`/api/v1/interviews/${sessionId}/results`),

  // Agent Chat
  sendChat: (message, history = []) => request("/api/v1/agent/chat", {
    method: "POST",
    body: JSON.stringify({ message, history }),
    timeout: 60000,
  }),

  // Data Privacy
  getDataSummary: () => request("/api/v1/data/summary"),
  purgeData: () => request("/api/v1/data/purge", { method: "DELETE" }),
};
