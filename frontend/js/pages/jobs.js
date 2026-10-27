/**
 * CareerOS — Jobs List & Market Intelligence
 */
import { api } from "../api.js";
import { el, formatPct } from "../utils/dom.js";
import { toast, createSpinner } from "../ui.js";

export async function renderJobs(container) {
  container.replaceChildren(createSpinner("Loading job postings..."));

  let searchQuery = "";
  let currentPage = 1;

  async function loadData() {
    try {
      const [jobsData, matchesData] = await Promise.all([
        api.listJobs({ q: searchQuery, page: currentPage, page_size: 10 }),
        api.getMatchingResults().catch(() => ({})),
      ]);

      const jobs = jobsData.jobs || [];
      const total = jobsData.total || 0;
      const disclaimer = jobsData.dataset_disclaimer || "";
      const matches = matchesData.job_matches || [];
      const matchMap = new Map(matches.map(m => [m.job_id, m]));

      // Header & Controls
      const searchInput = el("input", {
        type: "text",
        className: "form-control",
        placeholder: "Search by title, company, or required skill...",
        value: searchQuery,
        style: "max-width: 380px;",
      });

      const searchBtn = el("button", {
        className: "btn btn-secondary",
        onClick: () => {
          searchQuery = searchInput.value.trim();
          currentPage = 1;
          loadData();
        }
      }, "Filter");

      const matchBtn = el("button", {
        className: "btn btn-primary",
        onClick: async () => {
          try {
            toast.info("Calculating compatibility across job specifications...");
            matchBtn.disabled = true;
            await api.runMatching();
            toast.success("Matching updated!");
            loadData();
          } catch (err) {
            toast.error(err.message);
          } finally {
            matchBtn.disabled = false;
          }
        }
      }, "⚡ Run Compatibility Matcher");

      const controls = el("div", { style: "display: flex; gap: var(--space-3); margin-bottom: var(--space-4); flex-wrap: wrap;" },
        searchInput, searchBtn, matchBtn
      );

      const disclaimerAlert = el("div", { className: "alert alert-info" },
        el("span", {}, "ℹ️"),
        el("span", {}, disclaimer)
      );

      // Jobs Table
      const tableRows = jobs.map(job => {
        const match = matchMap.get(job.job_id);
        const reqCov = match ? formatPct(match.required_skill_coverage) : "N/A";
        const matchedSkills = match ? (match.matched_required || []).length : 0;
        const missingSkills = match ? (match.missing_required || []).length : (job.required_skills || []).length;

        return el("tr", {},
          el("td", {},
            el("div", { style: "font-weight: 600;" }, job.title),
            el("div", { style: "font-size: var(--font-size-xs); color: var(--text-dim);" }, job.company || "Not specified")
          ),
          el("td", {}, job.location || "Remote / India"),
          el("td", {},
            el("span", { className: `badge ${match ? 'badge-info' : 'badge-neutral'}` }, reqCov)
          ),
          el("td", {},
            el("span", { style: "color: var(--status-success); margin-right: 8px;" }, `✓ ${matchedSkills}`),
            el("span", { style: "color: var(--status-danger);" }, `✗ ${missingSkills}`)
          ),
          el("td", {},
            el("div", { style: "display: flex; flex-wrap: wrap; gap: 4px; max-width: 300px;" },
              ...(job.required_skills || []).slice(0, 5).map(s => el("span", { className: "badge badge-neutral" }, s)),
              (job.required_skills || []).length > 5 ? el("span", { className: "badge badge-neutral" }, `+${job.required_skills.length - 5}`) : null
            )
          )
        );
      });

      const table = el("div", { className: "table-responsive" },
        el("table", {},
          el("thead", {},
            el("tr", {},
              el("th", {}, "Job Role & Company"),
              el("th", {}, "Location"),
              el("th", {}, "Required Match"),
              el("th", {}, "Skills (Match/Gap)"),
              el("th", {}, "Key Requirements")
            )
          ),
          el("tbody", {}, ...tableRows)
        )
      );

      container.replaceChildren(
        el("div", {},
          disclaimerAlert,
          controls,
          table,
          el("div", { style: "margin-top: var(--space-4); font-size: var(--font-size-sm); color: var(--text-dim);" },
            `Showing ${jobs.length} of ${total} postings`
          )
        )
      );
    } catch (err) {
      container.replaceChildren(el("div", { className: "alert alert-danger" }, `Error: ${err.message}`));
    }
  }

  loadData();
}
