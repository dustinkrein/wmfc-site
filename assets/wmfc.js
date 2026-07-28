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
