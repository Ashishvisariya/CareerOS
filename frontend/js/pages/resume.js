/**
 * CareerOS — Resume Upload & Intelligence Page
 */
import { api } from "../api.js";
import { el } from "../utils/dom.js";
import { toast, createSpinner } from "../ui.js";

export async function renderResume(container) {
  container.replaceChildren(createSpinner("Loading resume data..."));

  try {
    const profileRes = await api.getResumeProfile().catch(() => ({}));
    const profile = profileRes?.profile || {};

    // Upload Card
    const fileInput = el("input", {
      type: "file",
      accept: ".pdf,.png,.jpg,.jpeg",
      style: "display: none;",
    });

    const uploadStatus = el("div", { style: "margin-top: var(--space-4); color: var(--text-muted); font-size: var(--font-size-sm);" });

    const uploadZone = el("div", {
      className: "empty-state",
      style: "cursor: pointer; border-style: dashed; padding: var(--space-8);",
      onClick: () => fileInput.click(),
    },
      el("div", { style: "font-size: 32px; margin-bottom: var(--space-2);" }, "📄"),
      el("h3", { className: "empty-state-title" }, "Select or Drop Resume (PDF, PNG, JPG)"),
      el("p", { className: "empty-state-desc" }, "Upload limit: 10MB. Files are indexed into Chroma vector storage with Gemini embeddings and parsed with Groq."),
      el("button", { type: "button", className: "btn btn-primary", onClick: (e) => { e.stopPropagation(); fileInput.click(); } }, "Choose File"),
      fileInput,
      uploadStatus
    );

    fileInput.addEventListener("change", async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      uploadStatus.textContent = `Uploading and indexing ${file.name}...`;
      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await api.uploadResume(formData);
        toast.success(`Ingested! Stored ${res.chunks_stored} chunks in vector database.`);
        uploadStatus.textContent = "Analyzing candidate profile with Groq...";
        await api.analyzeResume(true);
        toast.success("Profile parsed and cached!");
        renderResume(container);
      } catch (err) {
        toast.error(`Upload error: ${err.message}`);
        uploadStatus.textContent = `Error: ${err.message}`;
      }
    });

    const pageContent = el("div", {},
      el("div", { className: "card", style: "margin-bottom: var(--space-6);" },
        el("h3", { className: "card-title", style: "margin-bottom: var(--space-2);" }, "Resume Ingestion & Analysis"),
        el("p", { style: "color: var(--text-muted); font-size: var(--font-size-sm); margin-bottom: var(--space-4);" },
          "Ingest a resume to extract structured candidate intelligence without mixing candidate profiles."
        ),
        uploadZone
      )
    );

    // Profile Display Card if exists
    if (profile.name) {
      const profileCard = el("div", { className: "card" },
        el("div", { style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4);" },
          el("h3", { className: "card-title" }, `Extracted Profile: ${profile.name}`),
          el("button", {
            className: "btn btn-secondary",
            onClick: async () => {
              try {
                toast.info("Re-analyzing with Groq...");
                await api.analyzeResume(true);
                toast.success("Profile refreshed!");
                renderResume(container);
              } catch (err) {
                toast.error(err.message);
              }
            }
          }, "↻ Re-Analyze")
        ),
        el("div", { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--space-6);" },
          el("div", {},
            el("h4", { style: "font-size: var(--font-size-sm); margin-bottom: var(--space-2); color: var(--text-muted);" }, "SKILLS"),
            el("div", { style: "display: flex; flex-wrap: wrap; gap: var(--space-1); margin-bottom: var(--space-4);" },
              ...(profile.skills || []).map(s => el("span", { className: "badge badge-neutral" }, s))
            ),
            el("h4", { style: "font-size: var(--font-size-sm); margin-bottom: var(--space-2); color: var(--text-muted);" }, "DOCUMENTED STRENGTHS"),
            el("ul", { style: "padding-left: var(--space-4); font-size: var(--font-size-sm); color: var(--text-muted);" },
              ...(profile.strengths || []).map(s => el("li", { style: "margin-bottom: 4px;" }, s))
            )
          ),
          el("div", {},
            el("h4", { style: "font-size: var(--font-size-sm); margin-bottom: var(--space-2); color: var(--text-muted);" }, "EXPERIENCE"),
            el("ul", { style: "padding-left: var(--space-4); font-size: var(--font-size-sm); color: var(--text-muted); margin-bottom: var(--space-4);" },
              ...(profile.experience || []).map(exp => el("li", { style: "margin-bottom: 6px;" }, exp))
            ),
            el("h4", { style: "font-size: var(--font-size-sm); margin-bottom: var(--space-2); color: var(--text-muted);" }, "PROJECTS"),
            el("ul", { style: "padding-left: var(--space-4); font-size: var(--font-size-sm); color: var(--text-muted);" },
              ...(profile.projects || []).map(prj => el("li", { style: "margin-bottom: 6px;" }, prj))
            )
          )
        )
      );
      pageContent.appendChild(profileCard);
    }

    container.replaceChildren(pageContent);
  } catch (err) {
    container.replaceChildren(el("div", { className: "alert alert-danger" }, `Error: ${err.message}`));
  }
}
