/**
 * CareerOS — Dashboard Page View
 * Shows calculable metrics, progress, recurring gaps, and onboarding guidance.
 */
import { api } from "../api.js";
import { el, formatPct } from "../utils/dom.js";
import { createSpinner } from "../ui.js";

export async function renderDashboard(container) {
  container.replaceChildren(createSpinner("Loading career dashboard..."));

  try {
    const [statusData, stateData, profileData] = await Promise.all([
      api.getStatus().catch(() => ({})),
      api.getCareerState().catch(() => ({})),
      api.getResumeProfile().catch(() => ({})),
    ]);

    const state = stateData?.state || {};
    const profile = profileData?.profile || {};
    const hasData = Boolean(state.candidate_name || profile.name);

    // Onboarding state if no resume uploaded
    if (!hasData) {
      container.replaceChildren(
        el("div", { className: "card", style: "border-left: 4px solid var(--accent-primary);" },
          el("h2", { style: "font-size: var(--font-size-xl); margin-bottom: var(--space-2);" }, "Welcome to CareerOS"),
          el("p", { style: "color: var(--text-muted); margin-bottom: var(--space-6);" },
            "CareerOS is an AI-powered career intelligence operating system. Upload your resume to extract candidate intelligence, compare against market job requirements, pinpoint recurring skill gaps, and generate actionable learning roadmaps."
          ),
          el("div", { className: "empty-state", style: "margin: 0 0 var(--space-6) 0;" },
            el("h3", { className: "empty-state-title" }, "No Candidate Profile Active"),
            el("p", { className: "empty-state-desc" }, "Upload your resume (PDF or image) to index your qualifications and calculate real market compatibility."),
            el("a", { href: "#/resume", className: "btn btn-primary" }, "Upload Resume →")
          )
        )
      );
      return;
    }

    const candidateName = state.candidate_name || profile.name || "Candidate";
    const careerStage = state.career_stage || "Exploring";
    const marketCov = state.market_skill_coverage;
    const jobsCount = state.jobs_analyzed || statusData?.jobs_analyzed || 0;
    const activeMissions = statusData?.roadmap_missions || 0;
    const interviewsDone = statusData?.interview_sessions || 0;

    // Metrics Row
    const metricsRow = el("div", { className: "grid-cards" },
      el("div", { className: "card" },
        el("div", { className: "metric-label" }, "Candidate Profile"),
        el("div", { className: "metric-value", style: "font-size: var(--font-size-2xl);" }, candidateName),
        el("div", { className: "badge badge-neutral" }, careerStage.toUpperCase())
      ),
      el("div", { className: "card" },
        el("div", { className: "metric-label" }, "Market Skill Coverage"),
        el("div", { className: "metric-value" }, formatPct(marketCov)),
        el("div", { className: "badge badge-info" }, `Across ${jobsCount} Evaluated Jobs`)
      ),
      el("div", { className: "card" },
        el("div", { className: "metric-label" }, "Roadmap Missions"),
        el("div", { className: "metric-value" }, String(activeMissions)),
        el("a", { href: "#/roadmap", className: "badge badge-neutral" }, "View Active Missions →")
      ),
      el("div", { className: "card" },
        el("div", { className: "metric-label" }, "Interview Simulations"),
        el("div", { className: "metric-value" }, String(interviewsDone)),
        el("a", { href: "#/interview", className: "badge badge-neutral" }, "Practice Sessions →")
      )
    );

    // Summary Card
    const summaryCard = el("div", { className: "card", style: "margin-bottom: var(--space-6);" },
      el("h3", { className: "card-title", style: "margin-bottom: var(--space-2);" }, "Executive Career Assessment"),
      el("p", { style: "color: var(--text-muted); line-height: 1.6;" }, state.summary || "Complete matching to generate career summary.")
    );

    // Two Column Gaps & Skills
    const gaps = state.recurring_skill_gaps || [];
    const skills = state.current_skills || profile.skills || [];

    const detailsRow = el("div", { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: var(--space-6);" },
      el("div", { className: "card" },
        el("h3", { className: "card-title", style: "margin-bottom: var(--space-4);" }, "Top Recurring Market Gaps"),
        gaps.length > 0
          ? el("div", { style: "display: flex; flex-direction: column; gap: var(--space-2);" },
              ...gaps.slice(0, 8).map(g => el("div", { style: "display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--bg-surface-subtle); border-radius: var(--radius-sm);" },
                el("span", { style: "font-weight: 500;" }, g),
                el("span", { className: "badge badge-danger" }, "Gap")
              ))
            )
          : el("p", { style: "color: var(--text-dim);" }, "No recurring gaps identified.")
      ),
      el("div", { className: "card" },
        el("h3", { className: "card-title", style: "margin-bottom: var(--space-4);" }, `Verified Skills (${skills.length})`),
        el("div", { style: "display: flex; flex-wrap: wrap; gap: var(--space-2);" },
          ...skills.map(s => el("span", { className: "badge badge-neutral" }, s))
        )
      )
    );

    container.replaceChildren(metricsRow, summaryCard, detailsRow);
  } catch (err) {
    container.replaceChildren(
      el("div", { className: "alert alert-danger" }, `Error loading dashboard: ${err.message}`)
    );
  }
}
