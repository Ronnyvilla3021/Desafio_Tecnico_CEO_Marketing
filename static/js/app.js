/* ==========================================================================
   Mini CRM · CEO Marketing — JavaScript vanilla (sin librerías)
   Índice:
   1. Utilidades               5. Modal de crear / editar
   2. Toasts                   6. Validaciones del formulario
   3. Contadores y header      7. Eliminar con confirmación
   4. Buscador y filtro        8. Inicio
   ========================================================================== */
(() => {
  "use strict";

  /* 1. UTILIDADES -------------------------------------------------------- */
  const $ = (selector, context = document) => context.querySelector(selector);
  const $$ = (selector, context = document) => [...context.querySelectorAll(selector)];

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const AJAX_HEADERS = { "X-Requested-With": "XMLHttpRequest" };

  /** Activa o desactiva el estado de carga de un botón (spinner + bloqueo). */
  function setLoading(button, isLoading, loadingText = "Procesando…") {
    const label = $(".btn__label", button);
    button.classList.toggle("is-loading", isLoading);
    button.disabled = isLoading;
    if (!label) return;

    if (isLoading) {
      if (!button.dataset.label) button.dataset.label = label.textContent;
      label.textContent = loadingText;
    } else if (button.dataset.label) {
      label.textContent = button.dataset.label;
      delete button.dataset.label;
    }
  }

  function getCsrfToken() {
    const input = $("input[name='csrfmiddlewaretoken']");
    return input ? input.value : "";
  }


  /* 2. TOASTS ------------------------------------------------------------ */
  const TOAST_ICONS = {
    success: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/></svg>',
    error: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>',
    info: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>',
  };
  const CLOSE_ICON = '<svg class="icon" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg>';

  /** Muestra una notificación. type: "success" | "error" | "info". */
  function showToast(message, type = "success", duration = 4500) {
    const region = $("#toast-region");
    if (!region) return;

    const toast = document.createElement("div");
    toast.className = `toast toast--${type}`;
    toast.setAttribute("role", type === "error" ? "alert" : "status");
    toast.innerHTML =
      `<span class="toast__icon" aria-hidden="true">${TOAST_ICONS[type] || TOAST_ICONS.info}</span>` +
      '<p class="toast__text"></p>' +
      `<button type="button" class="toast__close" aria-label="Cerrar notificación">${CLOSE_ICON}</button>`;
    $(".toast__text", toast).textContent = message; // textContent: nunca HTML del usuario

    const dismiss = () => {
      toast.classList.add("is-leaving");
      setTimeout(() => toast.remove(), 260);
    };
    $(".toast__close", toast).addEventListener("click", dismiss);
    setTimeout(dismiss, duration);

    region.append(toast);
  }

  /** Convierte los mensajes de Django (success, error…) en toasts. */
  function initDjangoMessages() {
    const list = $("#django-messages");
    if (!list) return;

    const levelToType = { success: "success", error: "error" };
    $$("li", list).forEach((item, index) => {
      const type = levelToType[item.dataset.level] || "info";
      setTimeout(() => showToast(item.textContent.trim(), type), index * 150);
    });
    list.remove();
  }


  /* 3. CONTADORES Y HEADER ----------------------------------------------- */
  /** Anima los números del dashboard de 0 hasta su valor. */
  function initCounters() {
    $$("[data-stat]").forEach((element) => {
      const target = Number.parseInt(element.textContent, 10);
      if (prefersReducedMotion || !Number.isFinite(target) || target === 0) return;

      const duration = 700;
      const start = performance.now();
      element.textContent = "0";

      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        element.textContent = Math.round(target * eased);
        if (progress < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }

  /** Agrega sombra al header cuando se hace scroll. */
  function initHeaderShadow() {
    const header = $(".site-header");
    if (!header) return;
    const update = () => header.classList.toggle("is-scrolled", window.scrollY > 8);
    window.addEventListener("scroll", update, { passive: true });
    update();
  }


  /* 4. BUSCADOR Y FILTRO DINÁMICOS --------------------------------------- */
  function initFilters() {
    const form = $("#filter-form");
    const searchInput = $("#search-input");
    const tbody = $("#clients-body");
    const resultsCount = $("#results-count");
    const emptyState = $("#empty-state");
    if (!form || !searchInput || !tbody) return;

    let controller = null; // permite cancelar la petición anterior
    let debounceTimer = null;

    async function applyFilters() {
      const params = new URLSearchParams();
      const query = searchInput.value.trim();
      const status = $("input[name='status']:checked", form)?.value;
      if (query) params.set("q", query);
      if (status) params.set("status", status);
      const queryString = params.toString();

      controller?.abort();
      controller = new AbortController();
      tbody.setAttribute("aria-busy", "true");

      try {
        const response = await fetch(`${form.action}${queryString ? `?${queryString}` : ""}`, {
          headers: AJAX_HEADERS,
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        // Se lee la página que ya filtró el backend y se reemplaza solo lo necesario.
        const doc = new DOMParser().parseFromString(await response.text(), "text/html");
        const newBody = $("#clients-body", doc);
        tbody.innerHTML = newBody.innerHTML;
        resultsCount.innerHTML = $("#results-count", doc).innerHTML;
        emptyState.hidden = Boolean($("tr", newBody));

        // Mantiene la URL compartible sin recargar la página.
        history.replaceState(null, "", queryString ? `?${queryString}` : window.location.pathname);
        tbody.removeAttribute("aria-busy");
      } catch (error) {
        if (error.name === "AbortError") return; // llegó una búsqueda más nueva
        tbody.removeAttribute("aria-busy");
        showToast("No se pudo actualizar el listado. Intenta de nuevo.", "error");
      }
    }

    // Buscador: espera 250 ms después de la última tecla (debounce).
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(applyFilters, 250);
    });

    // Filtro por estado: inmediato.
    form.addEventListener("change", (event) => {
      if (event.target.name === "status") applyFilters();
    });

    // Enter en el buscador: evita recargar la página.
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      clearTimeout(debounceTimer);
      applyFilters();
    });
  }


  /* 5. MODAL DE CREAR / EDITAR ------------------------------------------- */
  const FIELDS = ["first_name", "last_name", "company", "email", "phone", "status"];

  /** "first_name" -> "firstName": así lee JavaScript los atributos data-first-name. */
  const toDatasetKey = (field) => field.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());

  function initClientModal() {
    const modal = $("#client-modal");
    const form = $("#client-form");
    if (!modal || !form) return;

    const title = $("#client-modal-title");
    const submitButton = $("#client-submit");
    const formAlert = $("#form-alert");
    const createUrl = form.dataset.createUrl;
    let currentAction = createUrl; // URL a la que se envía el formulario

    const getField = (name) => form.elements.namedItem(name);

    function resetForm() {
      form.reset();
      clearErrors(form);
      formAlert.hidden = true;
    }

    function openCreate() {
      resetForm();
      currentAction = createUrl;
      title.textContent = "Nuevo cliente";
      $(".btn__label", submitButton).textContent = "Guardar cliente";
      modal.showModal();
      getField("first_name")?.focus();
    }

    function openEdit(row, updateUrl) {
      resetForm();
      currentAction = updateUrl;
      FIELDS.forEach((field) => {
        const input = getField(field);
        if (input) input.value = row.dataset[toDatasetKey(field)] ?? "";
      });
      title.textContent = "Editar cliente";
      $(".btn__label", submitButton).textContent = "Guardar cambios";
      modal.showModal();
      getField("first_name")?.focus();
    }

    // Nuevo cliente
    $("#btn-new-client")?.addEventListener("click", openCreate);

    // Editar: delegación de eventos (las filas se reemplazan al filtrar)
    $("#clients-body")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-action='edit']");
      if (!button) return;
      openEdit(button.closest("[data-client-row]"), button.dataset.url);
    });

    // Envío del formulario
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      formAlert.hidden = true;
      clearErrors(form);

      const errors = validateForm(form);
      if (Object.keys(errors).length) {
        showFieldErrors(form, errors);
        return;
      }

      setLoading(submitButton, true, "Guardando…");
      try {
        const response = await fetch(currentAction, {
          method: "POST",
          body: new FormData(form), // incluye el token CSRF
          headers: AJAX_HEADERS,
          credentials: "same-origin",
        });
        const data = await response.json();

        if (response.ok && data.ok) {
          modal.close();
          window.location.reload(); // el mensaje de Django se muestra como toast
          return;
        }

        // Errores de validación del backend (ej. correo duplicado)
        showFieldErrors(form, data.errors || {});
        formAlert.textContent = data.message || "No se pudo guardar el cliente.";
        formAlert.hidden = false;
      } catch (error) {
        formAlert.textContent = "No se pudo conectar con el servidor. Intenta de nuevo.";
        formAlert.hidden = false;
        showToast("Error de conexión al guardar el cliente.", "error");
      }
      setLoading(submitButton, false);
    });

    // Validación al salir del campo y limpieza al corregir
    form.addEventListener("focusout", (event) => {
      const name = event.target.name;
      if (FIELDS.includes(name)) setFieldError(form, name, validators[name](event.target.value.trim()));
    });
    form.addEventListener("input", (event) => {
      if (event.target.classList.contains("is-invalid")) setFieldError(form, event.target.name, "");
    });

    // Cierre: botones, clic en el fondo y tecla Esc (bloqueado mientras guarda)
    setupDialogClosing(modal, () => submitButton.disabled);
    modal.addEventListener("close", () => setLoading(submitButton, false));
  }

  /** Botones [data-close-modal], clic en el fondo y Esc para un <dialog>. */
  function setupDialogClosing(dialog, isBusy) {
    dialog.addEventListener("click", (event) => {
      const clickedBackdrop = event.target === dialog;
      const clickedClose = event.target.closest("[data-close-modal]");
      if ((clickedBackdrop || clickedClose) && !isBusy()) dialog.close();
    });
    dialog.addEventListener("cancel", (event) => {
      if (isBusy()) event.preventDefault(); // Esc no cierra mientras se envía
    });
  }


  /* 6. VALIDACIONES DEL FORMULARIO --------------------------------------- */
  const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const PHONE_PATTERN = /^\+?\d{7,15}$/;

  /** Valida nombre o apellido: obligatorio y de al menos 2 caracteres. */
  const nameValidator = (label) => (value) => {
    if (!value) return `El ${label} es obligatorio.`;
    return value.length < 2 ? `El ${label} debe tener al menos 2 caracteres.` : "";
  };

  // Mismas reglas que el backend (models.py / forms.py)
  const validators = {
    first_name: nameValidator("nombre"),
    last_name: nameValidator("apellido"),
    company: () => "",
    email: (value) => {
      if (!value) return "El correo electrónico es obligatorio.";
      return EMAIL_PATTERN.test(value) ? "" : "Ingresa un correo válido, por ejemplo juan@email.com.";
    },
    phone: (value) =>
      value && !PHONE_PATTERN.test(value)
        ? "Ingresa un teléfono válido: solo dígitos, entre 7 y 15 (puede iniciar con +)."
        : "",
    status: (value) => (value ? "" : "Selecciona un estado."),
  };

  /** Devuelve {campo: mensaje} solo con los campos inválidos. */
  function validateForm(form) {
    const errors = {};
    FIELDS.forEach((name) => {
      const message = validators[name](form.elements.namedItem(name).value.trim());
      if (message) errors[name] = message;
    });
    return errors;
  }

  function setFieldError(form, name, message) {
    const input = form.elements.namedItem(name);
    const errorElement = $(`[data-error-for="${name}"]`, form);
    if (!input || !errorElement) return;
    input.classList.toggle("is-invalid", Boolean(message));
    input.setAttribute("aria-invalid", message ? "true" : "false");
    errorElement.textContent = message;
  }

  function clearErrors(form) {
    FIELDS.forEach((name) => setFieldError(form, name, ""));
  }

  /** Pinta errores (del frontend o del backend) y enfoca el primer campo inválido. */
  function showFieldErrors(form, errors) {
    let firstInvalid = null;
    Object.entries(errors).forEach(([name, messages]) => {
      if (!FIELDS.includes(name)) return;
      setFieldError(form, name, Array.isArray(messages) ? messages.join(" ") : messages);
      firstInvalid ??= form.elements.namedItem(name);
    });
    firstInvalid?.focus();
  }


  /* 7. ELIMINAR CON CONFIRMACIÓN ----------------------------------------- */
  function initDeleteFlow() {
    const modal = $("#confirm-modal");
    const confirmButton = $("#confirm-delete");
    const text = $("#confirm-text");
    if (!modal || !confirmButton) return;

    let pending = null; // { url, row } del cliente que se quiere eliminar

    $("#clients-body")?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-action='delete']");
      if (!button) return;

      const row = button.closest("[data-client-row]");
      pending = { url: button.dataset.url, row };
      text.textContent = `Vas a eliminar a ${row.dataset.fullName}. Esta acción no se puede deshacer.`;
      modal.showModal();
      $("[data-close-modal]", modal).focus(); // foco en "Cancelar": acción segura
    });

    confirmButton.addEventListener("click", async () => {
      if (!pending) return;
      setLoading(confirmButton, true, "Eliminando…");

      try {
        const response = await fetch(pending.url, {
          method: "POST",
          headers: { ...AJAX_HEADERS, "X-CSRFToken": getCsrfToken() },
          credentials: "same-origin",
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.message || "Error al eliminar");

        modal.close();
        pending.row.classList.add("row-removing"); // animación de salida
        setTimeout(() => window.location.reload(), prefersReducedMotion ? 0 : 280);
      } catch (error) {
        showToast("No se pudo eliminar el cliente. Intenta de nuevo.", "error");
        setLoading(confirmButton, false);
      }
    });

    setupDialogClosing(modal, () => confirmButton.disabled);
    modal.addEventListener("close", () => {
      setLoading(confirmButton, false);
      pending = null;
    });
  }


  /* 8. INICIO ------------------------------------------------------------ */
  initHeaderShadow();
  initDjangoMessages();
  initCounters();
  initFilters();
  initClientModal();
  initDeleteFlow();
})();