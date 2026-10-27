/**
 * CareerOS — DOM & Formatting Utilities
 * Safe DOM rendering (no innerHTML with untrusted/model text)
 */

export function el(tag, attributes = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, val] of Object.entries(attributes)) {
    if (key === "className") {
      element.className = val;
    } else if (key.startsWith("on") && typeof val === "function") {
      element.addEventListener(key.slice(2).toLowerCase(), val);
    } else if (key === "dataset" && typeof val === "object") {
      Object.assign(element.dataset, val);
    } else if (val !== false && val !== null && val !== undefined) {
      element.setAttribute(key, val);
    }
  }

  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    if (typeof child === "string" || typeof child === "number") {
      element.appendChild(document.createTextNode(String(child)));
    } else if (child instanceof Node) {
      element.appendChild(child);
    } else if (Array.isArray(child)) {
      for (const subChild of child) {
        if (subChild instanceof Node) element.appendChild(subChild);
        else if (subChild !== null && subChild !== undefined) {
          element.appendChild(document.createTextNode(String(subChild)));
        }
      }
    }
  }
  return element;
}

export function formatDate(isoString) {
  if (!isoString) return "N/A";
  try {
    const d = new Date(isoString);
    return isNaN(d.getTime()) ? isoString : d.toLocaleDateString(undefined, {
      month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit"
    });
  } catch {
    return isoString;
  }
}

export function formatPct(val) {
  if (val === null || val === undefined) return "N/A";
  return `${Math.round(Number(val))}%`;
}
