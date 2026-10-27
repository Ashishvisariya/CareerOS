/**
 * CareerOS — Career Agent Chat Interface
 */
import { api } from "../api.js";
import { el } from "../utils/dom.js";
import { toast } from "../ui.js";

const chatHistory = [];

export async function renderAgent(container) {
  const messagesContainer = el("div", { className: "chat-messages" });

  if (chatHistory.length === 0) {
    chatHistory.push({
      role: "assistant",
      content: "Hello! I am your CareerOS Advisor. I am grounded directly in your verified skills, market job compatibility, and learning progress. How can I guide you today?"
    });
  }

  function renderMessages() {
    messagesContainer.replaceChildren(
      ...chatHistory.map(m => el("div", { className: `chat-bubble ${m.role}` }, m.content))
    );
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  const inputField = el("input", {
    type: "text",
    className: "form-control",
    placeholder: "Ask about career readiness, skill gap priority, or resume improvements...",
    style: "flex-grow: 1;",
  });

  const sendBtn = el("button", {
    className: "btn btn-primary",
    onClick: async () => {
      const msg = inputField.value.trim();
      if (!msg) return;

      inputField.value = "";
      chatHistory.push({ role: "user", content: msg });
      renderMessages();

      const thinkingBubble = el("div", { className: "chat-bubble assistant", style: "opacity: 0.6;" }, "Thinking...");
      messagesContainer.appendChild(thinkingBubble);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;

      try {
        sendBtn.disabled = true;
        const res = await api.sendChat(msg, chatHistory.slice(0, -1));
        thinkingBubble.remove();
        chatHistory.push({ role: "assistant", content: res.response || "No response received." });
        renderMessages();
      } catch (err) {
        thinkingBubble.remove();
        toast.error(`Agent error: ${err.message}`);
        chatHistory.push({ role: "assistant", content: `Apologies, I encountered an error: ${err.message}` });
        renderMessages();
      } finally {
        sendBtn.disabled = false;
        inputField.focus();
      }
    }
  }, "Send");

  inputField.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendBtn.click();
  });

  renderMessages();

  container.replaceChildren(
    el("div", {},
      el("div", { style: "margin-bottom: var(--space-4);" },
        el("h2", { style: "font-size: var(--font-size-xl); font-weight: 700;" }, "Grounded Career Agent"),
        el("p", { style: "color: var(--text-muted); font-size: var(--font-size-sm);" },
          "Consult an AI advisor grounded in your candidate state, target postings, and roadmap missions."
        )
      ),
      el("div", { className: "chat-container" },
        messagesContainer,
        el("div", { className: "chat-input-bar" }, inputField, sendBtn)
      )
    )
  );
}
