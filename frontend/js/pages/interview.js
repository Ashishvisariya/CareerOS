/**
 * CareerOS — Adaptive AI Interview Simulation Page
 */
import { api } from "../api.js";
import { el } from "../utils/dom.js";
import { toast, createSpinner } from "../ui.js";

let activeSessionId = null;

export async function renderInterview(container) {
  container.replaceChildren(createSpinner("Loading interview simulation..."));

  async function loadView() {
    try {
      if (!activeSessionId) {
        // Setup view or list past sessions
        const historyData = await api.listInterviews().catch(() => ({ sessions: [] }));
        const sessions = historyData.sessions || [];

        const roleInput = el("input", {
          type: "text",
          className: "form-control",
          value: "Machine Learning Engineer",
          placeholder: "e.g. AI Engineer, ML Engineer",
        });

        const typeSelect = el("select", { className: "form-control" },
          el("option", { value: "technical" }, "Technical"),
          el("option", { value: "behavioral" }, "Behavioral"),
          el("option", { value: "project-based" }, "Project-based"),
          el("option", { value: "mixed" }, "Mixed")
        );

        const diffSelect = el("select", { className: "form-control" },
          el("option", { value: "entry" }, "Entry Level"),
          el("option", { value: "mid", selected: true }, "Mid Level"),
          el("option", { value: "senior" }, "Senior Level")
        );

        const startBtn = el("button", {
          className: "btn btn-primary",
          onClick: async () => {
            try {
              startBtn.disabled = true;
              toast.info("Generating opening interview question with Groq...");
              const newSession = await api.createInterview({
                target_role: roleInput.value.trim() || "AI/ML Engineer",
                interview_type: typeSelect.value,
                difficulty: diffSelect.value,
                max_questions: 4,
              });
              activeSessionId = newSession.session_id;
              toast.success("Interview session initialized!");
              loadView();
            } catch (err) {
              toast.error(err.message);
              startBtn.disabled = false;
            }
          }
        }, "🚀 Begin Interview Simulation");

        const setupCard = el("div", { className: "card", style: "margin-bottom: var(--space-6);" },
          el("h3", { className: "card-title", style: "margin-bottom: var(--space-2);" }, "Start Adaptive Practice Session"),
          el("p", { style: "color: var(--text-muted); font-size: var(--font-size-sm); margin-bottom: var(--space-4);" },
            "Questions are generated dynamically based on your candidate skills and target role. Feedback is scored across a transparent 5-dimension rubric."
          ),
          el("div", { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-4); margin-bottom: var(--space-4);" },
            el("div", { className: "form-group" }, el("label", { className: "form-label" }, "Target Role"), roleInput),
            el("div", { className: "form-group" }, el("label", { className: "form-label" }, "Interview Type"), typeSelect),
            el("div", { className: "form-group" }, el("label", { className: "form-label" }, "Difficulty Level"), diffSelect)
          ),
          startBtn
        );

        // Past sessions
        const historyRows = sessions.map(s => el("tr", {},
          el("td", {}, s.target_role || "Practice Role"),
          el("td", {}, s.interview_type || "Technical"),
          el("td", {}, el("span", { className: `badge ${s.status === 'completed' ? 'badge-success' : 'badge-neutral'}` }, s.status || "Active")),
          el("td", {}, `${s.turns_completed || 0} / ${s.max_questions || 4}`),
          el("td", {},
            el("button", {
              className: "btn btn-secondary",
              onClick: () => {
                activeSessionId = s.session_id;
                loadView();
              }
            }, "Review →")
          )
        ));

        const historyCard = el("div", { className: "card" },
          el("h3", { className: "card-title", style: "margin-bottom: var(--space-4);" }, "Session History"),
          sessions.length > 0
            ? el("div", { className: "table-responsive" },
                el("table", {},
                  el("thead", {},
                    el("tr", {},
                      el("th", {}, "Target Role"),
                      el("th", {}, "Type"),
                      el("th", {}, "Status"),
                      el("th", {}, "Turns"),
                      el("th", {}, "Action")
                    )
                  ),
                  el("tbody", {}, ...historyRows)
                )
              )
            : el("p", { style: "color: var(--text-dim);" }, "No past interview sessions.")
        );

        container.replaceChildren(el("div", {}, setupCard, historyCard));
      } else {
        // Active session workspace
        const session = await api.getInterviewResults(activeSessionId);
        const turns = session.turns || [];
        const isCompleted = session.status === "completed";

        const backBtn = el("button", {
          className: "btn btn-secondary",
          onClick: () => {
            activeSessionId = null;
            loadView();
          }
        }, "← Back to Sessions");

        const header = el("div", { style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-6);" },
          el("div", {},
            el("h2", { style: "font-size: var(--font-size-xl); font-weight: 700;" }, `Interview: ${session.target_role}`),
            el("p", { style: "color: var(--text-muted); font-size: var(--font-size-sm);" },
              `Type: ${session.interview_type} | Level: ${session.difficulty} | Status: ${session.status}`
            )
          ),
          backBtn
        );

        // Turn history items
        const turnItems = turns.map(t => {
          const ev = t.evaluation || {};
          return el("div", { className: "turn-item" },
            el("div", { className: "question-box", style: "margin-bottom: var(--space-3);" },
              el("strong", {}, `Q${t.turn}: `),
              t.question
            ),
            t.answer ? el("div", { className: "answer-preview" }, el("strong", {}, "Your Response: "), t.answer) : null,
            ev.overall_score !== undefined
              ? el("div", { style: "margin-top: var(--space-3);" },
                  el("div", { style: "display: flex; justify-content: space-between; align-items: center;" },
                    el("span", { style: "font-weight: 600; font-size: var(--font-size-sm);" }, "Rubric Evaluation"),
                    el("span", { className: "badge badge-info" }, `Score: ${ev.overall_score}/10`)
                  ),
                  el("div", { className: "rubric-grid" },
                    el("div", { className: "rubric-item" }, el("span", {}, "Technical:"), el("strong", {}, `${ev.technical || 0}/10`)),
                    el("div", { className: "rubric-item" }, el("span", {}, "Reasoning:"), el("strong", {}, `${ev.reasoning || 0}/10`)),
                    el("div", { className: "rubric-item" }, el("span", {}, "Relevance:"), el("strong", {}, `${ev.relevance || 0}/10`)),
                    el("div", { className: "rubric-item" }, el("span", {}, "Clarity:"), el("strong", {}, `${ev.clarity || 0}/10`)),
                    el("div", { className: "rubric-item" }, el("span", {}, "Practical:"), el("strong", {}, `${ev.practical || 0}/10`))
                  ),
                  ev.strengths ? el("div", { style: "font-size: var(--font-size-xs); color: var(--status-success); margin-top: 6px;" }, `Strengths: ${ev.strengths}`) : null,
                  ev.gaps ? el("div", { style: "font-size: var(--font-size-xs); color: var(--status-warning); margin-top: 2px;" }, `Growth areas: ${ev.gaps}`) : null
                )
              : null
          );
        });

        // Unanswered input area if active
        let inputSection = null;
        if (!isCompleted) {
          const currentTurn = turns.find(t => !t.answer);
          if (currentTurn) {
            const answerInput = el("textarea", {
              className: "form-control",
              rows: "5",
              placeholder: "Type your answer or technical reasoning here...",
              style: "margin-bottom: var(--space-4);",
            });

            const submitBtn = el("button", {
              className: "btn btn-primary",
              onClick: async () => {
                const text = answerInput.value.trim();
                if (!text) {
                  toast.error("Please enter your answer.");
                  return;
                }
                try {
                  submitBtn.disabled = true;
                  toast.info("Evaluating answer and generating adaptive follow-up...");
                  await api.submitAnswer(activeSessionId, text);
                  toast.success("Answer evaluated!");
                  loadView();
                } catch (err) {
                  toast.error(err.message);
                  submitBtn.disabled = false;
                }
              }
            }, "Submit Response");

            inputSection = el("div", { className: "card", style: "margin-top: var(--space-6);" },
              el("h4", { className: "card-title", style: "margin-bottom: var(--space-3);" }, "Your Answer"),
              answerInput,
              submitBtn
            );
          }
        } else {
          // Session Summary
          const sum = session.summary || {};
          inputSection = el("div", { className: "alert alert-success", style: "margin-top: var(--space-6);" },
            el("div", {},
              el("h4", { style: "font-weight: 700; margin-bottom: 4px;" }, "Session Completed"),
              el("p", { style: "font-size: var(--font-size-sm); margin-bottom: 4px;" }, `Average Score: ${sum.session_score || 0}/10`),
              sum.overall_strengths ? el("p", { style: "font-size: var(--font-size-sm); margin-bottom: 2px;" }, `• Strengths: ${sum.overall_strengths}`) : null,
              sum.improvement_areas ? el("p", { style: "font-size: var(--font-size-sm);" }, `• Focus areas: ${sum.improvement_areas}`) : null
            )
          );
        }

        container.replaceChildren(
          el("div", { className: "interview-workspace" },
            header,
            el("div", { className: "turn-history" }, ...turnItems),
            inputSection
          )
        );
      }
    } catch (err) {
      container.replaceChildren(el("div", { className: "alert alert-danger" }, `Error: ${err.message}`));
    }
  }

  loadView();
}
