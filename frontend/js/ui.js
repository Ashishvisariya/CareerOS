/**
 * CareerOS — UI Managers (Toasts, Modals, Spinners)
 */
import { el } from "./utils/dom.js";

// Toast Notification Manager
export const toast = {
  show(message, type = "info", duration = 4000) {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = el("div", { id: "toast-container" });
      document.body.appendChild(container);
    }

    const toastEl = el("div", { className: `toast toast-${type}` },
      el("span", {}, type === "success" ? "✓" : (type === "error" ? "⚠" : "ℹ")),
      el("span", {}, message)
    );

    container.appendChild(toastEl);
    setTimeout(() => {
      toastEl.style.opacity = "0";
      toastEl.style.transition = "opacity 200ms ease";
      setTimeout(() => toastEl.remove(), 200);
    }, duration);
  },
  success(msg) { this.show(msg, "success"); },
  error(msg) { this.show(msg, "error"); },
  info(msg) { this.show(msg, "info"); },
};

// Modal Confirmation Dialog
export function showConfirmDialog({ title, message, confirmText = "Confirm", isDanger = false, onConfirm }) {
  const overlay = el("div", { className: "modal-overlay" });
  const content = el("div", { className: "modal-content" },
    el("h3", { className: "modal-title" }, title),
    el("p", { className: "modal-body" }, message),
    el("div", { className: "modal-actions" },
      el("button", {
        className: "btn btn-secondary",
        onClick: () => overlay.remove(),
      }, "Cancel"),
      el("button", {
        className: `btn ${isDanger ? "btn-danger" : "btn-primary"}`,
        onClick: async () => {
          overlay.remove();
          if (onConfirm) await onConfirm();
        },
      }, confirmText)
    )
  );

  overlay.appendChild(content);
  document.body.appendChild(overlay);
}

// Global Loading Indicator
export function createSpinner(text = "Loading...") {
  return el("div", { className: "empty-state" },
    el("div", { className: "badge badge-neutral", style: "padding: 8px 16px; margin-bottom: 12px;" }, "⏳ Working"),
    el("p", { className: "empty-state-desc" }, text)
  );
}
