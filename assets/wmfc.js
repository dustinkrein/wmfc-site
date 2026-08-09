/* ============================================================
   WMFC — shared behaviour
   Motion rule: data animates, decoration never does. Once only.
   The zero holds still.
   ============================================================ */
(function () {
  "use strict";
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function ease(t) { return 1 - Math.pow(1 - t, 3); }

  /* ---- Count-up numerals + bar fills, once, on first view ---- */
  var fired = false;
  function animate() {
    if (fired) return; fired = true;
    var nums = document.querySelectorAll("[data-count]");
    Array.prototype.forEach.call(nums, function (el, i) {
      var target = +el.dataset.count, suf = el.dataset.suffix || "";
      if (reduced) { el.textContent = target + suf; return; }
      setTimeout(function () {
        var t0 = null;
        function step(ts) {
          if (!t0) t0 = ts;
          var p = Math.min((ts - t0) / 750, 1);
          el.textContent = Math.round(target * ease(p)) + suf;
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      }, i * 110);
    });
    var fills = document.querySelectorAll(".fill[data-w]");
    Array.prototype.forEach.call(fills, function (f, i) {
      var w = f.dataset.w + "%";
      if (reduced) { f.style.width = w; return; }
      setTimeout(function () { f.style.width = w; }, 300 + i * 90);
    });
  }
  if ("IntersectionObserver" in window) {
    var target = document.querySelector(".strip") || document.querySelector(".card");
    if (target) {
      var io = new IntersectionObserver(function (en) {
        en.forEach(function (e) { if (e.isIntersecting) { animate(); io.disconnect(); } });
      }, { threshold: 0.2 });
      io.observe(target);
    }
  }
  window.addEventListener("load", function () { setTimeout(animate, 700); });

  /* ------------------------------------------------------------
     Derived headline numbers.

     Any element with data-derive="<key>" has its text (or, if it also
     carries data-count, its count-up target) replaced with a value
     computed from data/scan-2026.json at load. The HTML always ships a
     correct hardcoded value, so if the fetch fails nothing breaks and
     nothing goes blank — this only protects against the numbers and the
     dataset drifting apart.

     Keys:
       total            institutions in the Index
       states           distinct states
       tier1|2|3|0      institutions in that category
       fl.total         Florida institutions
       fl.tier2         Florida institutions naming the sector
       fl.tier1         Florida Tier 1 institutions
       mi.total         Michigan rows

     NOT derived, and deliberately so:
       "Programs built for the sector" and "Operating & authorizing
       moves" are different things, and the dataset does not yet carry a
       field distinguishing a built program from an operating move — tier
       alone cannot tell them apart. "Verification coverage" likewise has
       no backing field. Those stay hardcoded until the schema can
       support them honestly.
     ------------------------------------------------------------ */
  function derive() {
    var nodes = document.querySelectorAll("[data-derive]");
    if (!nodes.length || !window.fetch) return;
    fetch("/data/scan-2026.json").then(function (r) {
      return r.ok ? r.json() : null;
    }).then(function (d) {
      if (!d || !d.institutions) return;
      var inst = d.institutions;
      function count(fn) { return inst.filter(fn).length; }
      var st = {};
      inst.forEach(function (r) { st[r.state] = 1; });
      var v = {
        total: inst.length,
        states: Object.keys(st).length,
        tier1: count(function (r) { return r.tier === "Tier 1"; }),
        tier2: count(function (r) { return r.tier === "Tier 2"; }),
        tier3: count(function (r) { return r.tier === "Tier 3"; }),
        tier0: count(function (r) { return r.tier === "Tier 0"; }),
        "fl.total": count(function (r) { return r.state === "Florida"; }),
        "fl.tier2": count(function (r) { return r.state === "Florida" && r.tier === "Tier 2"; }),
        "fl.tier1": count(function (r) { return r.state === "Florida" && r.tier === "Tier 1"; }),
        "mi.total": count(function (r) { return r.state === "Michigan"; })
      };
      Array.prototype.forEach.call(nodes, function (el) {
        var key = el.dataset.derive;
        if (!(key in v)) return;
        var n = v[key];
        if (el.hasAttribute("data-count")) {
          if (+el.dataset.count !== n) {
            el.dataset.count = n;
            if (fired) el.textContent = n + (el.dataset.suffix || "");
          }
        } else {
          var tpl = el.dataset.deriveTpl;
          el.textContent = tpl ? tpl.replace("{n}", n) : String(n);
        }
      });
    }).catch(function () { /* keep the hardcoded values */ });
  }
  derive();

  /* ---- Expandable table rows (keyboard accessible) ---- */
  window.wmfcWireRows = function (scope) {
    var rows = document.querySelectorAll((scope || "") + " tr.ex");
    Array.prototype.forEach.call(rows, function (tr) {
      if (tr.dataset.wired) return;
      tr.dataset.wired = "1";
      function toggle() {
        var d = tr.nextElementSibling;
        if (!d) return;
        if (d.hasAttribute("hidden")) d.removeAttribute("hidden");
        else d.setAttribute("hidden", "");
      }
      tr.onclick = toggle;
      tr.onkeydown = function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
      };
    });
  };
  window.wmfcWireRows("");

  /* ---- Print: expand everything ---- */
  window.addEventListener("beforeprint", function () {
    Array.prototype.forEach.call(document.querySelectorAll("details"), function (d) { d.setAttribute("open", ""); });
    Array.prototype.forEach.call(document.querySelectorAll(".dt[hidden]"), function (d) { d.removeAttribute("hidden"); });
  });
})();
