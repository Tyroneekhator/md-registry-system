/* MD Registry - audit.js
 * Audit logs filters convenience + date sanity checks.
 */
(function () {
  "use strict";

  function $all(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function autoSubmitAuditFilters() {
    $all('form[method="GET"]').forEach(function (form) {
      // Only apply on audit pages (heuristic: has date_from/date_to inputs)
      const from = form.querySelector('input[name="date_from"]');
      const to = form.querySelector('input[name="date_to"]');
      if (!(from || to)) return;

      // Auto-submit on date change
      [from, to].filter(Boolean).forEach(function (el) {
        el.addEventListener("change", function () {
          // basic sanity: if both set and from > to, swap
          const f = from && from.value ? from.value : "";
          const t = to && to.value ? to.value : "";
          if (f && t && f > t) {
            // swap values to keep a valid range
            const tmp = from.value;
            from.value = to.value;
            to.value = tmp;
          }
          form.submit();
        });
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    autoSubmitAuditFilters();
  });
})();
