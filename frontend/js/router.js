/**
 * CareerOS — Client Router
 */
import { renderDashboard } from "./pages/dashboard.js";
import { renderResume } from "./pages/resume.js";
import { renderJobs } from "./pages/jobs.js";
import { renderReadiness } from "./pages/readiness.js";
import { renderRoadmap } from "./pages/roadmap.js";
import { renderInterview } from "./pages/interview.js";
import { renderAgent } from "./pages/agent.js";
import { renderPrivacy } from "./pages/privacy.js";

const routes = {
  "/": renderDashboard,
  "/dashboard": renderDashboard,
  "/resume": renderResume,
  "/jobs": renderJobs,
  "/readiness": renderReadiness,
  "/roadmap": renderRoadmap,
  "/interview": renderInterview,
  "/agent": renderAgent,
  "/privacy": renderPrivacy,
};

export function initRouter() {
  const container = document.getElementById("page-content");
  const navLinks = document.querySelectorAll(".nav-item");

  function handleRoute() {
    const hash = window.location.hash.slice(1) || "/";
    const route = hash.split("?")[0];
    const handler = routes[route] || renderDashboard;

    navLinks.forEach(link => {
      const href = link.getAttribute("href")?.slice(1);
      if (href === route || (route === "/" && href === "/dashboard")) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    handler(container);
  }

  window.addEventListener("hashchange", handleRoute);
  handleRoute();
}
