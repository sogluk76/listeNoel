/* Zone de saisie des commentaires.
   Mentions (US-27) : liste de prénoms quand on tape « @ », et clic sur le prénom
   d'un auteur pour insérer « @Prénom ».
   Envoi (US-21) : sur ordinateur, Entrée envoie et Maj+Entrée va à la ligne.
   Seul JavaScript maison du site, validé par Lukas. Sans lui, on peut toujours
   taper @Prénom à la main : la reconnaissance se fait côté serveur. */
(function () {
  "use strict";

  var MAX_ITEMS = 6;
  var MAX_QUERY = 50;
  var WORD_CHAR = /[\p{L}\p{N}]/u;

  /* Forme de comparaison : sans accents ni majuscules (comme fold() côté serveur). */
  function fold(value) {
    return value.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  /* Cherche un « @… » en cours de saisie juste avant le curseur.
     Renvoie { start, query } ou null. */
  function findQuery(text, caret) {
    var limit = Math.max(0, caret - MAX_QUERY - 1);
    for (var i = caret - 1; i >= limit; i--) {
      var ch = text[i];
      if (ch === "\n") return null;
      if (ch === "@") {
        if (i > 0 && WORD_CHAR.test(text[i - 1])) return null; // adresse mail
        return { start: i, query: text.slice(i + 1, caret) };
      }
    }
    return null;
  }

  /* Prénoms qui commencent par ce qui est tapé après le « @ ». */
  function matchNames(query, names) {
    var wanted = fold(query);
    return names
      .filter(function (name) {
        return fold(name).indexOf(wanted) === 0;
      })
      .slice(0, MAX_ITEMS);
  }

  /* Remplace text[start:end] par « @Prénom » suivi d'une espace.
     Renvoie { text, caret }. */
  function applyMention(text, start, end, name) {
    var before = text.slice(0, start);
    var after = text.slice(end);
    if (before && !/\s$/.test(before)) before += " ";
    var inserted = "@" + name + (/^\s/.test(after) ? "" : " ");
    var caret = before.length + inserted.length;
    if (/^\s/.test(after)) caret += 1;
    return { text: before + inserted + after, caret: caret };
  }

  function setValue(textarea, result) {
    textarea.value = result.text;
    textarea.focus();
    textarea.setSelectionRange(result.caret, result.caret);
  }

  function setup(textarea) {
    if (textarea.dataset.mentionsReady) return;
    var names;
    try {
      names = JSON.parse(textarea.dataset.mentions || "[]");
    } catch (_err) {
      names = [];
    }
    if (!names.length) return;
    textarea.dataset.mentionsReady = "1";

    var list = document.createElement("ul");
    list.className = "mention-list";
    list.id = (textarea.id || "message") + "-mentions";
    list.hidden = true;
    list.setAttribute("role", "listbox");
    list.setAttribute("aria-label", "Personnes à mentionner");
    textarea.parentNode.classList.add("mention-host");
    textarea.parentNode.insertBefore(list, textarea.nextSibling);
    textarea.setAttribute("aria-autocomplete", "list");
    textarea.setAttribute("aria-controls", list.id);
    textarea.setAttribute("aria-expanded", "false");

    var items = [];
    var active = 0;
    var current = null;

    function close() {
      items = [];
      current = null;
      list.hidden = true;
      list.textContent = "";
      textarea.setAttribute("aria-expanded", "false");
      textarea.removeAttribute("aria-activedescendant");
    }

    function render() {
      list.textContent = "";
      items.forEach(function (name, index) {
        var option = document.createElement("li");
        option.className = "mention-list__item";
        option.id = list.id + "-" + index;
        option.setAttribute("role", "option");
        option.setAttribute("aria-selected", index === active ? "true" : "false");
        option.dataset.name = name;
        option.textContent = "@" + name;
        list.appendChild(option);
      });
      list.hidden = false;
      textarea.setAttribute("aria-expanded", "true");
      textarea.setAttribute("aria-activedescendant", list.id + "-" + active);
    }

    function update() {
      var caret = textarea.selectionStart;
      if (caret !== textarea.selectionEnd) return close();
      current = findQuery(textarea.value, caret);
      items = current ? matchNames(current.query, names) : [];
      if (!items.length) return close();
      active = 0;
      render();
    }

    function choose(name) {
      if (!current) return;
      var result = applyMention(textarea.value, current.start, textarea.selectionStart, name);
      close();
      setValue(textarea, result);
    }

    textarea.addEventListener("input", update);
    textarea.addEventListener("click", update);
    textarea.addEventListener("blur", close);
    textarea.addEventListener("keydown", function (event) {
      if (list.hidden) return;
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        var step = event.key === "ArrowDown" ? 1 : -1;
        active = (active + step + items.length) % items.length;
        render();
      } else if (event.key === "Enter" || event.key === "Tab") {
        event.preventDefault();
        choose(items[active]);
      } else if (event.key === "Escape") {
        event.preventDefault();
        close();
      }
    });
    // Garde le curseur dans la zone de saisie quand on touche la liste.
    list.addEventListener("mousedown", function (event) {
      event.preventDefault();
    });
    list.addEventListener("click", function (event) {
      var option = event.target.closest("[data-name]");
      if (option) choose(option.dataset.name);
    });
    if (textarea.form) textarea.form.addEventListener("reset", close);
  }

  /* Sur ordinateur : Entrée envoie le message, Maj+Entrée va à la ligne.
     Sur téléphone ou tablette (écran tactile), Entrée reste un saut de ligne. */
  function isDesktop() {
    return !!window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  }

  function setupEnterToSend(textarea) {
    textarea.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) return;
      if (event.defaultPrevented || event.isComposing) return; // la liste de mentions a pris la touche
      if (!isDesktop() || !textarea.form) return;
      event.preventDefault();
      textarea.form.requestSubmit();
    });
  }

  function init() {
    document.querySelectorAll("textarea[data-mentions]").forEach(setup);
    // Après setup : la liste de mentions doit voir la touche Entrée en premier.
    document.querySelectorAll("textarea[data-enter-sends]").forEach(setupEnterToSend);
    // Délégation : le fil est rechargé régulièrement par HTMX.
    document.addEventListener("click", function (event) {
      var author = event.target.closest("[data-mention]");
      if (!author) return;
      var textarea = document.querySelector("textarea[data-mentions]");
      if (!textarea) return;
      var caret = textarea.selectionStart;
      setValue(textarea, applyMention(textarea.value, caret, caret, author.dataset.mention));
    });
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { fold: fold, findQuery: findQuery, matchNames: matchNames, applyMention: applyMention };
  }
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }
})();
