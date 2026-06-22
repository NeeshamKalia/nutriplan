/**
 * HTML sanitization utility — SEC-010
 *
 * Strips dangerous HTML tags (script, iframe, object, embed, form, style)
 * and event handler attributes from user-generated content before rendering.
 * Also blocks dangerous URI schemes: javascript:, data:, vbscript:.
 *
 * Uses the browser's native DOMParser for safe parsing — no external deps.
 */

const DANGEROUS_TAGS = new Set([
  'script', 'iframe', 'object', 'embed', 'form', 'style',
  'link', 'meta', 'base', 'applet',
]);

const EVENT_HANDLER_REGEX = /^on[a-z]+$/i;

/** URI schemes that can execute code or be used for phishing. */
const DANGEROUS_URI_SCHEMES = ['javascript:', 'data:', 'vbscript:'];

function isDangerousUri(value: string): boolean {
  const trimmed = value.trim().toLowerCase();
  return DANGEROUS_URI_SCHEMES.some((scheme) => trimmed.startsWith(scheme));
}

export function sanitizeHtml(dirty: string): string {
  if (!dirty) return '';

  const parser = new DOMParser();
  const doc = parser.parseFromString(dirty, 'text/html');

  // Remove dangerous elements
  const allElements = doc.body.querySelectorAll('*');
  allElements.forEach((el) => {
    if (DANGEROUS_TAGS.has(el.tagName.toLowerCase())) {
      el.remove();
      return;
    }

    // Remove event handler attributes (onclick, onerror, etc.)
    // and attributes with dangerous URI values
    const attrs = Array.from(el.attributes);
    attrs.forEach((attr) => {
      if (EVENT_HANDLER_REGEX.test(attr.name)) {
        el.removeAttribute(attr.name);
      }
      if (attr.value && isDangerousUri(attr.value)) {
        el.removeAttribute(attr.name);
      }
    });

    // Double-check href and src specifically (belt-and-suspenders)
    for (const attrName of ['href', 'src', 'action', 'formaction'] as const) {
      const val = el.getAttribute(attrName);
      if (val && isDangerousUri(val)) {
        el.removeAttribute(attrName);
      }
    }
  });

  return doc.body.innerHTML;
}
