/**
 * CareerOS — Learning Roadmap Page
 */
import { api } from "../api.js";
import { el } from "../utils/dom.js";
import { toast, createSpinner } from "../ui.js";

export async function renderRoadmap(container) {
  container.replaceChildren(createSpinner("Loading learning roadmap..."));

  async function loadData() {
    try {
      const data = await api.getRoadmap();
      const missions = data.missions || [];

      const generateBtn = el("button", {
        className: "btn btn-primary",
        onClick: async () => {
          try {
            generateBtn.disabled = true;
            toast.info("Synthesizing learning missions from skill gaps...");
            await api.generateRoadmap(8, true);
            toast.success("Roadmap generated!");
            loadData();
          } catch (err) {
            toast.error(err.message);
          } finally {
            generateBtn.disabled = false;
          }
        }
      }, "⚡ Generate / Refresh Missions");

      const header = el("div", { style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-6);" },
        el("div", {},
          el("h2", { style: "font-size: var(--font-size-xl); font-weight: 700;" }, "Personalized Learning Roadmap"),
          el("p", { style: "color: var(--text-muted); font-size: var(--font-size-sm);" },
            "Actionable coding challenges and target competencies prioritized by market frequency."
          )
        ),
        generateBtn
      );

      if (missions.length === 0) {
        container.replaceChildren(
          header,
          el("div", { className: "empty-state" },
            el("h3", { className: "empty-state-title" }, "No Missions Generated Yet"),
            el("p", { className: "empty-state-desc" }, "Generate missions to receive practical coding exercises tailored to your verified skill gaps.")
          )
        );
        return;
      }

      const missionCards = missions.map(m => {
        const status = m.status || "not_started";
        const isCompleted = status === "completed";
        const isInProgress = status === "in_progress";

        const badgeClass = isCompleted ? "badge-success" : (isInProgress ? "badge-warning" : "badge-neutral");
        const statusLabel = isCompleted ? "Completed" : (isInProgress ? "In Progress" : "Not Started");

        return el("div", { className: `mission-card ${status}` },
          el("div", { className: "mission-header" },
            el("div", {},
              el("span", { className: `badge ${badgeClass}`, style: "margin-bottom: 6px;" }, statusLabel),
              el("h3", { className: "mission-title" }, `Learn ${m.skill}`)
            ),
            el("div", { style: "text-align: right;" },
              el("div", { style: "font-weight: 700; color: var(--accent-primary);" }, `Priority: ${m.priority_score}`),
              el("div", { style: "font-size: var(--font-size-xs); color: var(--text-dim);" }, `~${m.estimated_hours || 10} hours`)
            )
          ),
          el("div", { className: "mission-details" },
            m.why_it_matters ? el("div", {}, el("strong", {}, "Why it matters: "), m.why_it_matters) : null,
            m.target_competency ? el("div", {}, el("strong", {}, "Target competency: "), m.target_competency) : null,
            m.practical_exercise
              ? el("div", { style: "background: var(--bg-surface-subtle); padding: 12px; border-radius: var(--radius-md); margin-top: 8px;" },
                  el("strong", {}, "Practical Coding Task:"),
                  el("div", { style: "margin-top: 4px; font-size: var(--font-size-sm); color: var(--text-main);" }, m.practical_exercise)
                )
              : null
          ),
          el("div", { style: "display: flex; gap: var(--space-2); margin-top: var(--space-3);" },
            !isInProgress && !isCompleted
              ? el("button", {
                  className: "btn btn-secondary",
                  onClick: async () => {
                    await api.startMission(m.id);
                    toast.info(`Started mission: ${m.skill}`);
                    loadData();
                  }
                }, "▶ Start Mission")
              : null,
            !isCompleted
              ? el("button", {
                  className: "btn btn-primary",
                  onClick: async () => {
                    await api.completeMission(m.id);
                    toast.success(`Completed: ${m.skill}`);
                    loadData();
                  }
                }, "✓ Mark Complete")
              : null
          )
        );
      });

      container.replaceChildren(
        el("div", {},
          header,
          el("div", { className: "missions-list" }, ...missionCards)
        )
      );
    } catch (err) {
      container.replaceChildren(el("div", { className: "alert alert-danger" }, `Error: ${err.message}`));
    }
  }

  loadData();
}
