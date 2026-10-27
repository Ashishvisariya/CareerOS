/**
 * CareerOS — Skill Gap & Readiness Page
 */
import { api } from "../api.js";
import { el, formatPct } from "../utils/dom.js";
import { createSpinner } from "../ui.js";

export async function renderReadiness(container) {
  container.replaceChildren(createSpinner("Computing readiness analysis..."));

  try {
    const [stateData, readinessData] = await Promise.all([
      api.getCareerState().catch(() => ({})),
      api.getReadiness().catch(() => ({})),
    ]);

    const state = stateData?.state || {};
    const readiness = readinessData?.readiness || {};
    const disclaimer = readinessData?.disclaimer || "";

    const disclaimerBanner = el("div", { className: "alert alert-warning" },
      el("span", {}, "⚠️"),
      el("span", {}, disclaimer || "Readiness scores are analytical estimates for skill planning only; they do not predict hiring outcomes.")
    );

    // Gaps Section
    const gaps = state.recurring_skill_gaps || [];
    const gapsCard = el("div", { className: "card", style: "margin-bottom: var(--space-6);" },
      el("h3", { className: "card-title", style: "margin-bottom: var(--space-2);" }, "Recurring Skill Gaps Across Market"),
      el("p", { style: "color: var(--text-muted); font-size: var(--font-size-sm); margin-bottom: var(--space-4);" },
        "Skills appearing repeatedly across target postings that are missing from your analyzed resume."
      ),
      gaps.length > 0
        ? el("div", { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-3);" },
            ...gaps.map(g => el("div", { style: "padding: 10px 14px; background: var(--bg-surface-subtle); border-left: 3px solid var(--status-danger); border-radius: var(--radius-sm); font-weight: 500;" }, g))
          )
        : el("p", { style: "color: var(--text-dim);" }, "No recurring gaps identified.")
    );

    // Readiness Breakdown by Job
    const jobCards = Object.entries(readiness).map(([jobId, r]) => {
      const overall = r.overall_score || 0;
      const dims = r.dimensions || {};
      const actions = r.next_actions || [];

      return el("div", { className: "card", style: "margin-bottom: var(--space-4);" },
        el("div", { style: "display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-4);" },
          el("div", {},
            el("h4", { style: "font-size: var(--font-size-base); font-weight: 600;" }, r.job_title || "Target Role"),
            el("div", { style: "font-size: var(--font-size-xs); color: var(--text-dim);" }, r.company || "Company")
          ),
          el("div", { style: "text-align: right;" },
            el("div", { style: "font-size: var(--font-size-2xl); font-weight: 700; color: var(--accent-primary);" }, formatPct(overall)),
            el("div", { className: "metric-label" }, "Readiness Score")
          )
        ),
        el("div", { className: "grid-cards", style: "margin-bottom: var(--space-4);" },
          el("div", { style: "padding: 8px; background: var(--bg-surface-subtle); border-radius: var(--radius-sm);" },
            el("div", { className: "metric-label" }, "Required Skills (40%)"),
            el("div", { style: "font-weight: 600;" }, formatPct(dims.required_skill_coverage))
          ),
          el("div", { style: "padding: 8px; background: var(--bg-surface-subtle); border-radius: var(--radius-sm);" },
            el("div", { className: "metric-label" }, "Preferred Skills (15%)"),
            el("div", { style: "font-weight: 600;" }, formatPct(dims.preferred_skill_coverage))
          ),
          el("div", { style: "padding: 8px; background: var(--bg-surface-subtle); border-radius: var(--radius-sm);" },
            el("div", { className: "metric-label" }, "Project Evidence (15%)"),
            el("div", { style: "font-weight: 600;" }, formatPct(dims.project_evidence))
          ),
          el("div", { style: "padding: 8px; background: var(--bg-surface-subtle); border-radius: var(--radius-sm);" },
            el("div", { className: "metric-label" }, "Experience Match (15%)"),
            el("div", { style: "font-weight: 600;" }, formatPct(dims.experience_alignment))
          ),
          el("div", { style: "padding: 8px; background: var(--bg-surface-subtle); border-radius: var(--radius-sm);" },
            el("div", { className: "metric-label" }, "Interview Prep (15%)"),
            el("div", { style: "font-weight: 600;" }, formatPct(dims.interview_preparation))
          )
        ),
        actions.length > 0
          ? el("div", { style: "background: var(--bg-surface-subtle); padding: 12px; border-radius: var(--radius-md);" },
              el("div", { style: "font-size: var(--font-size-xs); font-weight: 600; color: var(--text-muted); margin-bottom: 6px;" }, "RECOMMENDED IMPACT ACTIONS:"),
              ...actions.map(act => el("div", { style: "font-size: var(--font-size-sm); color: var(--text-main); margin-bottom: 4px;" }, `• ${act}`))
            )
          : null
      );
    });

    container.replaceChildren(
      el("div", {},
        disclaimerBanner,
        gapsCard,
        el("h3", { className: "card-title", style: "margin-bottom: var(--space-4);" }, "Multi-Dimensional Readiness Breakdown"),
        ...jobCards
      )
    );
  } catch (err) {
    container.replaceChildren(el("div", { className: "alert alert-danger" }, `Error: ${err.message}`));
  }
}
