/* MD Registry - records.js
 * Records page only:
 * - records filtering
 * - pagination
 * - live typing
 * - export filtered button syncing
 */
(function () {
  "use strict";
  let currentFetchController = null;
  let selectedRecordIds = new Set();

  function $all(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function initBootstrapTooltips() {
    if (!window.bootstrap || !window.bootstrap.Tooltip) return;

    $all('[data-bs-toggle="tooltip"]').forEach(function (el) {
      if (el._mdTooltipInitialized) return;
      new bootstrap.Tooltip(el);
      el._mdTooltipInitialized = true;
    });
  }

  function buildUrlFromForm(form) {
    const action = form.getAttribute("action") || window.location.pathname;
    const url = new URL(action, window.location.origin);
    const formData = new FormData(form);

    formData.forEach(function (value, key) {
      const v = String(value || "").trim();
      if (v !== "") {
        url.searchParams.set(key, v);
      }
    });

    return url.toString();
  }

  function updateExportFilteredButton(url) {
    const exportBtn = document.getElementById("exportFilteredBtn");
    const wrapper = document.getElementById("exportFilteredWrapper");
    if (!exportBtn || !wrapper) return;

    const parsedUrl = new URL(url, window.location.origin);
    const hasFilters = Array.from(parsedUrl.searchParams.keys()).length > 0;
    const exportBaseUrl = exportBtn.dataset.exportBase || "";

    if (hasFilters && exportBaseUrl) {
      exportBtn.classList.remove("disabled");
      exportBtn.removeAttribute("aria-disabled");
      exportBtn.href = `${exportBaseUrl}?${parsedUrl.searchParams.toString()}`;

      wrapper.removeAttribute("data-bs-toggle");
      wrapper.removeAttribute("data-bs-placement");
      wrapper.removeAttribute("data-bs-custom-class");
      wrapper.removeAttribute("title");
    } else {
      exportBtn.classList.add("disabled");
      exportBtn.setAttribute("aria-disabled", "true");
      exportBtn.href = "javascript:void(0);";

      wrapper.setAttribute("data-bs-toggle", "tooltip");
      wrapper.setAttribute("data-bs-placement", "top");
      wrapper.setAttribute("data-bs-custom-class", "tooltip-dark");
      wrapper.setAttribute(
        "title",
        "Works only when records are filtered or sorted.",
      );
    }

    initBootstrapTooltips();
  }


    // ============================================================
  // CORRECTION: bulk selection helpers
  // ============================================================
  function syncBulkDeleteHiddenInputs() {
    const container = document.getElementById("bulkDeleteHiddenInputs");
    if (!container) return;

    container.innerHTML = "";
    Array.from(selectedRecordIds).forEach(function (id) {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = "record_ids";
      input.value = id;
      container.appendChild(input);
    });
  }

  function updateBulkSelectionUi() {
    const countEl = document.getElementById("selectedRecordsCount");
    const bulkBtn = document.getElementById("bulkDeleteBtn");
    const checkboxes = $all(".record-select-checkbox");
    const enabledCheckboxes = checkboxes.filter(function (cb) {
      return !cb.disabled;
    });

    if (countEl) {
      countEl.textContent = String(selectedRecordIds.size);
    }

    if (bulkBtn) {
      bulkBtn.disabled = selectedRecordIds.size === 0;
    }

    const selectAll = document.getElementById("selectAllRecords");
    if (selectAll) {
      const checkedEnabledCount = enabledCheckboxes.filter(function (cb) {
        return cb.checked;
      }).length;

      selectAll.checked =
        enabledCheckboxes.length > 0 &&
        checkedEnabledCount === enabledCheckboxes.length;

      selectAll.indeterminate =
        checkedEnabledCount > 0 &&
        checkedEnabledCount < enabledCheckboxes.length;
    }

    syncBulkDeleteHiddenInputs();
  }

  function restoreBulkSelectionsFromState() {
    $all(".record-select-checkbox").forEach(function (cb) {
      cb.checked = selectedRecordIds.has(cb.value);
    });
    updateBulkSelectionUi();
  }

  function initBulkSelectionUi() {
    const selectAll = document.getElementById("selectAllRecords");
    const bulkForm = document.getElementById("bulkDeleteForm");

    $all(".record-select-checkbox").forEach(function (cb) {
      cb.addEventListener("change", function () {
        if (cb.checked) {
          selectedRecordIds.add(cb.value);
        } else {
          selectedRecordIds.delete(cb.value);
        }
        updateBulkSelectionUi();
      });
    });

    if (selectAll) {
      selectAll.addEventListener("change", function () {
        $all(".record-select-checkbox").forEach(function (cb) {
          if (cb.disabled) return;
          cb.checked = selectAll.checked;
          if (cb.checked) {
            selectedRecordIds.add(cb.value);
          } else {
            selectedRecordIds.delete(cb.value);
          }
        });
        updateBulkSelectionUi();
      });
    }

    if (bulkForm) {
      bulkForm.addEventListener("submit", function (e) {
        if (selectedRecordIds.size === 0) {
          e.preventDefault();
          return;
        }

        const isAdminDelete = bulkForm.querySelector("#bulkDeleteBtn")?.textContent?.toLowerCase().includes("delete selected");
        const msg = isAdminDelete
          ? "Are you sure you want to delete the selected records?"
          : "Are you sure you want to submit delete requests for the selected records?";

        if (!window.confirm(msg)) {
          e.preventDefault();
          return;
        }
      });
    }

    restoreBulkSelectionsFromState();
  }

  async function fetchAndSwap(url, pushState) {


    if (currentFetchController) {
      currentFetchController.abort();
    }

    currentFetchController = new AbortController();
    const signal = currentFetchController.signal;
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
        signal: signal,
      });

      if (!response.ok) {
        window.location.href = url;
        return;
      }

      const html = await response.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");

      const currentResults = document.getElementById("recordsResultsContainer");
      const currentTotal = document.getElementById("totalRecordsCount");

      const newResults = doc.getElementById("recordsResultsContainer");
      const newTotal = doc.getElementById("totalRecordsCount");

      // CORRECTION: records.js owns records page DOM replacement
      if (!newResults) {
        window.location.href = url;
        return;
      }

      if (currentTotal && newTotal) {
        currentTotal.textContent = newTotal.textContent;
      }

      if (currentResults) {
        currentResults.replaceWith(newResults);
      }

      if (pushState !== false) {
        window.history.pushState({ url: url }, "", url);
      }

      updateExportFilteredButton(url);
      initBootstrapTooltips();
      bindRecordsUi();
    } catch (err) {

      if (err.name === "AbortError") {
        return;
      }
      window.location.href = url;
    }
  }

  function initApplyFiltersButton() {
    const form = document.getElementById("recordsFiltersForm");
    const applyBtn = document.getElementById("applyFiltersBtn");
    if (!form || !applyBtn) return;

    applyBtn.addEventListener("click", function (e) {
      e.preventDefault();
      const url = buildUrlFromForm(form);
      fetchAndSwap(url, true);
    });
  }

  function initResetFiltersButton() {
    const form = document.getElementById("recordsFiltersForm");
    const resetBtn = document.getElementById("resetFiltersBtn");
    if (!form || !resetBtn) return;

    resetBtn.addEventListener("click", function (e) {
      e.preventDefault();

      // CORRECTION: clear current form without replacing it
      form.reset();

      ["messenger_name", "subject", "invoice_number"].forEach(function (name) {
        const el = form.querySelector(`[name="${name}"]`);
        if (el) el.value = "";
      });

      const action = form.getAttribute("action") || window.location.pathname;
      const url = new URL(action, window.location.origin).toString();
      selectedRecordIds.clear();
      fetchAndSwap(url, true);
    });
  }

  function initAjaxPagination() {
    const resultsContainer = document.getElementById("recordsResultsContainer");
    if (!resultsContainer) return;

    $all(".pagination a.page-link", resultsContainer).forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        const href = link.getAttribute("href");
        if (!href) return;
        fetchAndSwap(href, true);
      });
    });
  }

  function initLiveTypingFilters() {
    const form = document.getElementById("recordsFiltersForm");
    if (!form) return;

    const messengerInput = document.getElementById("messengerNameInput");
    const subjectInput = document.getElementById("subjectInput");
    const invoiceInput = document.getElementById("invoiceNumberInput");

    let typingTimer = null;
    const delayMs = 500;

    function triggerLiveFilter() {
      const url = buildUrlFromForm(form);

      // CORRECTION: avoid redundant requests
      if (url === window.location.href) return;

      fetchAndSwap(url, true);
    }

    function handleTyping() {
      window.clearTimeout(typingTimer);
      typingTimer = window.setTimeout(triggerLiveFilter, delayMs);
    }

    [messengerInput, subjectInput, invoiceInput].forEach(function (input) {
      if (!input) return;

      input.addEventListener("input", handleTyping);

      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          window.clearTimeout(typingTimer);
          triggerLiveFilter();
        }
      });
    });
  }

  function updateExternalDocumentUi() {
    const externalSelect = document.getElementById("externalDocumentSelect");
    if (!externalSelect) return;

    const incomingSelect = document.getElementById("incomingDepartmentSelect");
    const outgoingSelect = document.getElementById("outgoingDepartmentSelect");
    const incomingNew = document.getElementById("incomingDepartmentNewInput");
    const outgoingNew = document.getElementById("outgoingDepartmentNewInput");
    const notice = document.getElementById("externalDocumentNotice");

    const isExternal = externalSelect.value === "Yes";

    [incomingSelect, outgoingSelect, incomingNew, outgoingNew].forEach(
      function (el) {
        if (!el) return;

        el.disabled = isExternal;

        if (isExternal) {
          el.value = "";
        }
      },
    );

    if (notice) {
      notice.classList.toggle("d-none", !isExternal);
    }
  }


  function updateReturnUi() {
    const statusSelect = document.getElementById("statusSelect");
    const dateDispatchedInput = document.getElementById("dateDispatchedInput");
    const returnedSelect = document.getElementById("returnedSelect");
    const dateReturnedInput = document.getElementById("dateReturnedInput");

    if (
      !statusSelect ||
      !dateDispatchedInput ||
      !returnedSelect ||
      !dateReturnedInput
    ) {
      return;
    }

    const status = (statusSelect.value || "").trim();
    const hasDateDispatched = (dateDispatchedInput.value || "").trim() !== "";
    const isWithMd = status === "With MD";
    const isNotWithMd = status === "Not with MD";

    // Default state
    returnedSelect.disabled = false;
    dateReturnedInput.disabled = false;
    returnedSelect.required = false;
    dateReturnedInput.required = false;

    // If status is Not with MD, clear and disable return fields
    if (isNotWithMd) {
      returnedSelect.value = "";
      dateReturnedInput.value = "";
      returnedSelect.disabled = true;
      dateReturnedInput.disabled = true;
      return;
    }

    // If dispatched and With MD, enforce return fields
    if (hasDateDispatched && isWithMd) {
      returnedSelect.required = true;
      dateReturnedInput.required = true;
    }
  }

  function initRecordFormReturnUi() {
    const statusSelect = document.getElementById("statusSelect");
    const dateDispatchedInput = document.getElementById("dateDispatchedInput");
    const returnedSelect = document.getElementById("returnedSelect");

    if (!statusSelect || !dateDispatchedInput || !returnedSelect) return;

    statusSelect.addEventListener("change", updateReturnUi);
    dateDispatchedInput.addEventListener("input", updateReturnUi);
    returnedSelect.addEventListener("change", updateReturnUi);

    updateReturnUi();
  }

  function initRecordFormExternalDocumentUi() {
    const externalSelect = document.getElementById("externalDocumentSelect");
    if (!externalSelect) return;

    externalSelect.addEventListener("change", updateExternalDocumentUi);
    updateExternalDocumentUi();
  }

  function bindRecordsUi() {
    initApplyFiltersButton();
    initResetFiltersButton();
    initAjaxPagination();
    initLiveTypingFilters();
    initBulkSelectionUi();
    initRecordFormExternalDocumentUi();
    initRecordFormReturnUi();
  }

  document.addEventListener("DOMContentLoaded", function () {
    // CORRECTION: records.js now owns records page behavior completely
    initBootstrapTooltips();
    updateExportFilteredButton(window.location.href);
    bindRecordsUi();
  });

  window.addEventListener("popstate", function () {
    fetchAndSwap(window.location.href, false);
  });
})();
