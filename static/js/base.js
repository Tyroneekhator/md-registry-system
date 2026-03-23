/* MD Registry - base.js
 * Global helpers used across the site.
 * Records-table-specific behavior has been moved to records.js.
 */
(function () {
  "use strict";

  function $all(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function confirmMessageForHref(href) {
    const h = (href || "").toLowerCase();
    if (h.includes("soft_delete") || h.includes("delete"))
      return "Are you sure you want to delete this item?";
    if (h.includes("restore")) return "Restore this item?";
    if (h.includes("disable")) return "Disable this item?";
    if (h.includes("enable")) return "Enable this item?";
    if (h.includes("approve")) return "Approve this request?";
    if (h.includes("reject")) return "Proceed?";
    return "Are you sure you want to continue?";
  }

  function wireConfirmations() {
    // Explicit confirmations
    $all("a[data-confirm], button[data-confirm], input[data-confirm]").forEach(
      function (el) {
        el.addEventListener("click", function (e) {
          const msg = el.getAttribute("data-confirm") || "Are you sure?";
          if (!window.confirm(msg)) e.preventDefault();
        });
      },
    );

    // Implicit confirmations for legacy action links
    const implicit = [
      'a[href*="soft_delete"]',
      'a[href*="restore"]',
      'a[href*="disable"]',
      'a[href*="enable"]',
      'a[href*="approve"]',
    ].join(", ");

    $all(implicit).forEach(function (a) {
      a.addEventListener("click", function (e) {
        if (a.hasAttribute("data-confirm")) return;
        const msg = confirmMessageForHref(a.getAttribute("href"));
        if (!window.confirm(msg)) e.preventDefault();
      });
    });
  }

  function preventDoubleSubmit() {
    $all("form").forEach(function (form) {
      form.addEventListener("submit", function () {
        $all('button[type="submit"], input[type="submit"]', form).forEach(
          function (btn) {
            btn.disabled = true;
          },
        );
      });
    });
  }

  function improveFileInputs() {
    $all('input[type="file"]').forEach(function (input) {
      const helperClass = "js-file-helper";

      function ensureHelper() {
        let helper = input.parentElement
          ? input.parentElement.querySelector("." + helperClass)
          : null;

        if (!helper) {
          helper = document.createElement("div");
          helper.className = helperClass + " form-text";
          helper.textContent = "No file selected.";

          if (input.nextSibling)
            input.parentElement.insertBefore(helper, input.nextSibling);
          else input.parentElement.appendChild(helper);
        }
        return helper;
      }

      const helper = ensureHelper();

      input.addEventListener("change", function () {
        const file = input.files && input.files[0] ? input.files[0].name : "";
        helper.textContent = file ? "Selected: " + file : "No file selected.";
      });
    });
  }

  function initBootstrapTooltips() {
    if (!window.bootstrap || !window.bootstrap.Tooltip) return;

    $all('[data-bs-toggle="tooltip"]').forEach(function (el) {
      if (el._mdTooltipInitialized) return;
      new bootstrap.Tooltip(el);
      el._mdTooltipInitialized = true;
    });
  }

  function initSortDirectionLabels() {
    const sortSelect = document.getElementById("sortSelect");
    const dirSelect = document.getElementById("dirSelect");

    // CORRECTION: this stays global because it is harmless and reusable
    // on any page that uses sortSelect + dirSelect.
    if (!sortSelect || !dirSelect) return;

    const labelSets = {
      invoice: {
        asc: "Lowest number to Highest number",
        desc: "Highest number to Lowest number",
      },
      messenger: {
        asc: "A to Z",
        desc: "Z to A",
      },
      subject: {
        asc: "A to Z",
        desc: "Z to A",
      },
      received: {
        asc: "Oldest date to Newest date",
        desc: "Newest date to Oldest date",
      },
      dispatched: {
        asc: "Oldest date to Newest date",
        desc: "Newest date to Oldest date",
      },
      returned: {
        asc: "Oldest date to Newest date",
        desc: "Newest date to Oldest date",
      },
      default: {
        asc: "Ascending",
        desc: "Descending",
      },
    };

    function applyDirLabels() {
      const sortVal = (sortSelect.value || "").toLowerCase();
      const set = labelSets[sortVal] || labelSets.default;

      const optAsc = dirSelect.querySelector('option[value="asc"]');
      const optDesc = dirSelect.querySelector('option[value="desc"]');

      if (optAsc) optAsc.textContent = set.asc;
      if (optDesc) optDesc.textContent = set.desc;
    }

    applyDirLabels();
    sortSelect.addEventListener("change", applyDirLabels);
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireConfirmations();
    preventDoubleSubmit();
    improveFileInputs();
    initBootstrapTooltips();
    initSortDirectionLabels();

    // CORRECTION: removed all records-table-specific logic from base.js
    // base.js is now global helpers only.
  });
})();
