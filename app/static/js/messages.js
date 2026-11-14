/* Pop-up des messages privés (US-29 à US-35).
   Deuxième JavaScript maison du site, validé par Lukas. Il ne fait que :
   - ouvrir et fermer la pop-up, et la rouvrir au même endroit quand on change de page ;
   - garder le fil calé en bas quand un message arrive ;
   - envoyer avec Entrée sur ordinateur (Maj+Entrée va à la ligne) ;
   - vider le formulaire après l'envoi et montrer l'aperçu de la photo jointe.
   Sans lui, la bulle « Messages » mène à la même messagerie en pleine page. */
(function () {
  "use strict";

  var STORAGE_KEY = "noel-messages";
  var NEAR_BOTTOM = 80;

  /* --- Logique pure (testable sans navigateur) ----------------------------- */

  /* Adresse à rouvrir : seulement une vue de la messagerie. */
  function safeUrl(url) {
    return typeof url === "string" && /^\/messages(\/[\w/]*)?$/.test(url) ? url : "/messages";
  }

  function parseState(raw) {
    try {
      var state = JSON.parse(raw || "{}") || {};
      return { open: state.open === true, url: safeUrl(state.url) };
    } catch (_err) {
      return { open: false, url: "/messages" };
    }
  }

  function isNearBottom(scrollHeight, scrollTop, clientHeight) {
    return scrollHeight - scrollTop - clientHeight < NEAR_BOTTOM;
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { safeUrl: safeUrl, parseState: parseState, isNearBottom: isNearBottom };
  }
  if (typeof document === "undefined") return;

  /* --- Navigateur ---------------------------------------------------------- */

  var dock = null; // absent sur la messagerie en pleine page
  var panel = null;
  var stick = true; // faut-il recaler le fil en bas après le prochain échange ?
  var viewLoaded = false;

  function readState() {
    try {
      return parseState(window.sessionStorage.getItem(STORAGE_KEY));
    } catch (_err) {
      return parseState(null);
    }
  }

  function writeState(state) {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (_err) {
      /* stockage indisponible : la pop-up se refermera au changement de page */
    }
  }

  function isOpen() {
    return !!dock && dock.dataset.open === "true";
  }

  function isDesktop() {
    return !!window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  }

  function openPanel(url) {
    url = safeUrl(url);
    dock.dataset.open = "true";
    panel.hidden = false;
    writeState({ open: true, url: url });
    window.htmx.ajax("GET", url, { source: panel, target: panel, swap: "innerHTML" });
  }

  function closePanel() {
    dock.dataset.open = "false";
    panel.hidden = true;
    panel.textContent = ""; // retire le fil : son rafraîchissement s'arrête, rien n'est marqué lu
    writeState({ open: false, url: "/messages" });
    var bubble = document.getElementById("msg-bubble");
    if (bubble) bubble.focus();
  }

  function scrollBox() {
    return panel.querySelector(".msg-scroll");
  }

  function scrollToBottom() {
    var box = scrollBox();
    if (box) box.scrollTop = box.scrollHeight;
  }

  function onClick(event) {
    var clearer = event.target.closest("[data-msg-photo-clear]");
    if (clearer && clearer.form !== undefined) {
      event.preventDefault();
      clearPhoto(clearer.closest("form"));
      return;
    }
    var closer = event.target.closest("[data-messages-close]");
    if (closer && dock) {
      event.preventDefault();
      closePanel();
      return;
    }
    var opener = event.target.closest("[data-messages-open]");
    if (!opener || !dock || !window.htmx) return; // sans pop-up : le lien mène à la pleine page
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.button) return;
    event.preventDefault();
    if (isOpen() && opener.hasAttribute("data-messages-toggle")) return closePanel();
    openPanel(opener.getAttribute("href"));
  }

  function onBeforeSwap(event) {
    var target = event.detail && event.detail.target;
    if (!target || !panel.contains(target)) return;
    viewLoaded = target === panel;
    var box = scrollBox();
    stick = viewLoaded || !box || isNearBottom(box.scrollHeight, box.scrollTop, box.clientHeight);
  }

  function onAfterSwap() {
    if (stick) scrollToBottom();
    var view = panel.querySelector("[data-view-url]");
    if (view && isOpen()) writeState({ open: true, url: view.dataset.viewUrl });
    if (viewLoaded && isDesktop()) {
      var field = panel.querySelector("textarea[data-msg-enter], textarea");
      if (field) field.focus();
    }
    viewLoaded = false;
  }

  /* Après un envoi réussi : formulaire vidé, fil en bas, curseur prêt pour la suite. */
  function onAfterRequest(event) {
    var form = event.detail && event.detail.elt;
    if (!form || !form.matches || !form.matches("form[data-msg-form]")) return;
    if (!event.detail.successful) return;
    form.reset();
    markPhoto(form);
    scrollToBottom();
    var field = form.querySelector("textarea");
    if (field && isDesktop()) field.focus();
  }

  /* La conversation mémorisée n'existe plus (supprimée, groupe quitté) : retour à la liste. */
  function onResponseError(event) {
    var target = event.detail && event.detail.target;
    if (target !== panel || !isOpen()) return;
    var path = event.detail.pathInfo && event.detail.pathInfo.requestPath;
    if (path && path !== "/messages") openPanel("/messages");
  }

  function onKeydown(event) {
    var field = event.target;
    if (!field.matches || !field.matches("textarea[data-msg-enter]")) return;
    if (event.key !== "Enter" || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) return;
    if (event.isComposing || !isDesktop() || !field.form) return;
    event.preventDefault();
    field.form.requestSubmit();
  }

  function markPhoto(form) {
    var input = form.querySelector("input[data-msg-photo]");
    if (!input) return;
    var label = input.closest("label");
    var chosen = input.files && input.files.length > 0;
    label.classList.toggle("is-chosen", !!chosen);
    label.title = chosen ? "Photo jointe : " + input.files[0].name : "Joindre une photo";

    // Aperçu au-dessus de la zone de saisie : on voit quelle photo va partir.
    var preview = form.querySelector("[data-msg-preview]");
    if (!preview) return;
    var image = preview.querySelector("[data-msg-preview-img]");
    if (image.dataset.objectUrl) {
      URL.revokeObjectURL(image.dataset.objectUrl);
      delete image.dataset.objectUrl;
      image.removeAttribute("src");
    }
    if (chosen) {
      image.dataset.objectUrl = URL.createObjectURL(input.files[0]);
      image.src = image.dataset.objectUrl;
      preview.querySelector("[data-msg-preview-name]").textContent = input.files[0].name;
    }
    preview.hidden = !chosen;
    if (stick) scrollToBottom();
  }

  function clearPhoto(form) {
    var input = form.querySelector("input[data-msg-photo]");
    if (!input) return;
    input.value = "";
    markPhoto(form);
    var field = form.querySelector("textarea");
    if (field) field.focus();
  }

  function init() {
    panel = document.getElementById("messages-panel");
    if (!panel) return;
    dock = document.getElementById("msg-dock");

    document.addEventListener("click", onClick);
    document.addEventListener("keydown", onKeydown);
    document.addEventListener("change", function (event) {
      if (event.target.matches && event.target.matches("input[data-msg-photo]")) {
        markPhoto(event.target.form);
      }
    });
    document.body.addEventListener("htmx:beforeSwap", onBeforeSwap);
    document.body.addEventListener("htmx:afterSwap", onAfterSwap);
    document.body.addEventListener("htmx:afterRequest", onAfterRequest);
    document.body.addEventListener("htmx:responseError", onResponseError);
    // Une photo qui finit de charger allonge le fil : on le recale.
    panel.addEventListener(
      "load",
      function (event) {
        if (stick && event.target.tagName === "IMG") scrollToBottom();
      },
      true
    );

    if (dock) {
      var state = readState();
      if (state.open && window.htmx) openPanel(state.url);
    } else {
      scrollToBottom(); // pleine page : la vue est déjà là
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
