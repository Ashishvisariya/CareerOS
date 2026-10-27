/**
 * CareerOS — Data Management & Privacy Page
 */
import { api } from "../api.js";
import { el, formatDate } from "../utils/dom.js";
import { toast, showConfirmDialog, createSpinner } from "../ui.js";

export async function renderPrivacy(container) {
  container.replaceChildren(createSpinner("Loading stored data overview..."));

  async function loadData() {
    try {
      const summary = await api.getDataSummary();

      const purgeBtn = el("button", {
        className: "btn btn-danger",
        onClick: () => {
          showConfirmDialog({
            title: "Delete All Candidate Data?",
            message: "This will permanently purge your vector embeddings, parsed resume files, career state, active learning roadmap, and completed interview records from this machine. This action cannot be undone.",
            confirmText: "Yes, Delete Everything",
            isDanger: true,
            onConfirm: async () => {
              try {
                toast.info("Purging stored data...");
                await api.purgeData();
                toast.success("All candidate data has been permanently deleted.");
                loadData();
              } catch (err) {
                toast.error(err.message);
              }
            }
          });
        }
      }, "🗑️ Purge All My Data");

      const filesList = (summary.resume_files || []).map(f =>
        el("div", { style: "display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border-subtle);" },
          el("span", {}, f.name),
          el("span", { style: "color: var(--text-dim);" }, `${Math.round(f.size_bytes / 1024)} KB`)
        )
      );

      const content = el("div", {},
        el("div", { className: "card", style: "margin-bottom: var(--space-6);" },
          el("h3", { className: "card-title", style: "margin-bottom: var(--space-2);" }, "Data Privacy & Storage Inspection"),
          el("p", { style: "color: var(--text-muted); font-size: var(--font-size-sm); margin-bottom: var(--space-4);" },
            summary.privacy_notice
          ),
          el("div", { className: "grid-cards", style: "margin-bottom: var(--space-6);" },
            el("div", { style: "padding: 12px; background: var(--bg-surface-subtle); border-radius: var(--radius-md);" },
              el("div", { className: "metric-label" }, "Active Candidate"),
              el("div", { style: "font-weight: 600; font-size: var(--font-size-base);" }, summary.candidate_name || "None")
            ),
            el("div", { style: "padding: 12px; background: var(--bg-surface-subtle); border-radius: var(--radius-md);" },
              el("div", { className: "metric-label" }, "Vector Collection"),
              el("div", { style: "font-weight: 600; font-size: var(--font-size-base);" }, summary.has_resume ? "Indexed in Chroma" : "Empty")
            ),
            el("div", { style: "padding: 12px; background: var(--bg-surface-subtle); border-radius: var(--radius-md);" },
              el("div", { className: "metric-label" }, "Missions Stored"),
              el("div", { style: "font-weight: 600; font-size: var(--font-size-base);" }, `${summary.roadmap_missions_count || 0}`)
            ),
            el("div", { style: "padding: 12px; background: var(--bg-surface-subtle); border-radius: var(--radius-md);" },
              el("div", { className: "metric-label" }, "Interviews Stored"),
              el("div", { style: "font-weight: 600; font-size: var(--font-size-base);" }, `${summary.interview_sessions_count || 0}`)
            )
          ),
          el("h4", { style: "font-size: var(--font-size-sm); margin-bottom: var(--space-2); color: var(--text-muted);" }, "STORED FILES ON DISK"),
          filesList.length > 0 ? el("div", { style: "margin-bottom: var(--space-6);" }, ...filesList) : el("p", { style: "color: var(--text-dim); margin-bottom: var(--space-6);" }, "No files currently saved."),
          purgeBtn
        )
      );

      container.replaceChildren(content);
    } catch (err) {
      container.replaceChildren(el("div", { className: "alert alert-danger" }, `Error: ${err.message}`));
    }
  }

  loadData();
}
