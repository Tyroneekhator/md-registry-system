/* MD Registry - workflow.js
 * Workflow pages: request approval UX and reject reason enhancements.
 */
(function () {
  "use strict";

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function enhanceRejectReason() {
    const textarea = $('textarea[name="reason"]');
    if (!textarea) return;

    // Add a subtle character counter (no custom CSS; uses small text-muted)
    let counter = textarea.parentElement ? textarea.parentElement.querySelector(".js-reason-counter") : null;
    if (!counter) {
      counter = document.createElement("div");
      counter.className = "js-reason-counter small text-muted mt-1";
      counter.textContent = "0 characters";
      textarea.parentElement.appendChild(counter);
    }

    function update() { counter.textContent = (textarea.value || "").length + " characters"; }
    textarea.addEventListener("input", update);
    update();
  }


  function syncDeletedHiddenInputs(containerId, selectedDeletedRecordIds) {
    const container = $("#" + containerId);
    if (!container) return;

    container.innerHTML = "";
    Array.from(selectedDeletedRecordIds).forEach(function (id) {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = "record_ids";
      input.value = id;
      container.appendChild(input);
    });
  }


  function initDeletedRecordsBulkUi() {
    const rowCheckboxes = $all(".deleted-record-select-checkbox");
    const selectAll = $("#selectAllDeletedRecords");

    // CORRECTION: do nothing unless this is the deleted records page
    if (!rowCheckboxes.length || !selectAll) return;

    const countEl = $("#selectedDeletedRecordsCount");
    const restoreBtn = $("#bulkRestoreDeletedBtn");
    const deleteBtn = $("#bulkPermanentDeleteBtn");
    const restoreForm = $("#bulkRestoreDeletedForm");
    const deleteForm = $("#bulkPermanentDeleteForm");

    const selectedDeletedRecordIds = new Set();
    function updateUi() {
      if (countEl) {
        countEl.textContent = String(selectedDeletedRecordIds.size);
      }

      if (restoreBtn) {
        restoreBtn.disabled = selectedDeletedRecordIds.size === 0;
      }

      if (deleteBtn) {
        deleteBtn.disabled = selectedDeletedRecordIds.size === 0;
      }

      const enabledCheckboxes = rowCheckboxes.filter(function (cb) {
        return !cb.disabled;
      });

      const checkedEnabledCount = enabledCheckboxes.filter(function (cb) {
        return cb.checked;
      }).length;

      selectAll.checked =
        enabledCheckboxes.length > 0 &&
        checkedEnabledCount === enabledCheckboxes.length;

      selectAll.indeterminate =
        checkedEnabledCount > 0 &&
        checkedEnabledCount < enabledCheckboxes.length;

      syncDeletedHiddenInputs("bulkRestoreDeletedHiddenInputs", selectedDeletedRecordIds);
      syncDeletedHiddenInputs("bulkPermanentDeleteHiddenInputs", selectedDeletedRecordIds);
    }

    rowCheckboxes.forEach(function (cb) {
      cb.addEventListener("change", function () {
        if (cb.checked) {
          selectedDeletedRecordIds.add(cb.value);
        } else {
          selectedDeletedRecordIds.delete(cb.value);
        }
        updateUi();
      });
    });

    selectAll.addEventListener("change", function () {
      rowCheckboxes.forEach(function (cb) {
        if (cb.disabled) return;

        cb.checked = selectAll.checked;

        if (cb.checked) {
          selectedDeletedRecordIds.add(cb.value);
        } else {
          selectedDeletedRecordIds.delete(cb.value);
        }
      });
      updateUi();
    });
    if (restoreForm) {
      restoreForm.addEventListener("submit", function (e) {
        if (selectedDeletedRecordIds.size === 0) {
          e.preventDefault();
        }
      });
    }
    if (deleteForm) {
      deleteForm.addEventListener("submit", function (e) {
        if (selectedDeletedRecordIds.size === 0) {
          e.preventDefault();
          return;
        }
        if (!window.confirm("Proceed with permanent delete for the selected records? This cannot be undone.")) {
          e.preventDefault();
        }
      });
    }
    updateUi();
  }
    


  document.addEventListener("DOMContentLoaded", function () {
    enhanceRejectReason();
    initDeletedRecordsBulkUi();
  });
})();
