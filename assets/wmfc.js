/* ============================================================
   WMFC — shared behaviour for every page.
   Motion rule: data animates once, on arrival. Decoration never moves.
   Every figure is fully drawn without JavaScript; the animation only
   resets it to zero the moment before it scrolls into view.
   ============================================================ */
(function () {
  "use strict";
  var W = window.WMFC = window.WMFC || {};
  var root = document.documentElement;
  W.reduced = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);

  W.esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  };
  W.el = function (tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  };
  W.link = function (url, text) {
    var a = document.createElement("a");
    a.href = url; a.textContent = text; a.rel = "noopener";
    return a.outerHTML;
  };
  W.json = function (url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error(url); return r.json(); });
  };

  /* ---- theme: saved choice, else the system setting ---- */
  try { var saved = localStorage.getItem("wmfc-theme"); if (saved) root.setAttribute("data-theme", saved); } catch (e) {}
  var tog = document.getElementById("tog");
  if (tog) tog.addEventListener("click", function () {
    var cur = root.getAttribute("data-theme");
    var dark = cur ? cur === "dark" : !!(window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches);
    var next = dark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("wmfc-theme", next); } catch (e) {}
  });

  /* ---- keep the current page visible in the scrolling mobile nav ---- */
  var cur = document.querySelector("nav a[aria-current]");
  if (cur && cur.parentNode.scrollWidth > cur.parentNode.clientWidth) cur.parentNode.scrollLeft = cur.offsetLeft - 24;

  /* ---- once-only arrival animation ---- */
  W.onSee = function (node, fn) {
    if (!node || W.reduced || !("IntersectionObserver" in window)) return;
    fn(true);
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { fn(false); io.disconnect(); } });
    }, { threshold: 0.2 });
    io.observe(node);
  };
  W.countUp = function (box) {
    var nums = box ? box.querySelectorAll("[data-n]") : [];
    if (!nums.length) return;
    W.onSee(box, function (reset) {
      Array.prototype.forEach.call(nums, function (n, i) {
        var t = +n.dataset.n, suf = n.dataset.suf || "";
        if (reset) { n.textContent = "0" + suf; return; }
        var t0 = null;
        setTimeout(function () {
          requestAnimationFrame(function st(ts) {
            if (!t0) t0 = ts;
            var p = Math.min((ts - t0) / 800, 1);
            n.textContent = Math.round(t * (1 - Math.pow(1 - p, 3))) + suf;
            if (p < 1) requestAnimationFrame(st);
          });
        }, i * 110);
      });
    });
  };
  W.growBars = function (box, sel) {
    W.onSee(box, function (reset) {
      Array.prototype.forEach.call(box.querySelectorAll(sel || ".fi"), function (f, i) {
        if (reset) { f.dataset.w = f.style.width; f.style.width = "0"; }
        else setTimeout(function () { f.style.width = f.dataset.w; }, i * 90);
      });
    });
  };
  W.growStack = function (box) {
    W.onSee(box, function (reset) {
      Array.prototype.forEach.call(box.children, function (d, i) {
        if (reset) { d.dataset.g = d.style.flexGrow; d.style.flexGrow = "0.001"; }
        else setTimeout(function () { d.style.flexGrow = d.dataset.g; }, i * 120);
      });
    });
  };

  /* ---- hover tooltip for charts ---- */
  var tip;
  W.tip = function (html, ev) {
    if (!tip) { tip = W.el("div", "tip"); tip.setAttribute("aria-hidden", "true"); document.body.appendChild(tip); }
    if (!html) { tip.className = "tip"; return; }
    tip.innerHTML = html; tip.className = "tip on";
    var x = ev.clientX + 14, y = ev.clientY + 14, r = tip.getBoundingClientRect();
    if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
    if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - 14;
    tip.style.left = x + "px"; tip.style.top = y + "px";
  };

  /* ---- chips: one-of-many filter buttons ---- */
  W.chips = function (box, items, onPick) {
    box.innerHTML = "";
    items.forEach(function (it, i) {
      var b = W.el("button", "chip", (it.sw ? '<span class="sw ' + it.sw + '"></span>' : "") + W.esc(it.label) + (it.n != null ? ' <span class="n">' + it.n + "</span>" : ""));
      b.type = "button"; b.dataset.k = it.key; b.setAttribute("aria-pressed", i === 0 ? "true" : "false");
      b.addEventListener("click", function () {
        Array.prototype.forEach.call(box.children, function (c) { c.setAttribute("aria-pressed", String(c === b)); });
        onPick(it.key);
      });
      box.appendChild(b);
    });
  };

  /* ---- expandable table rows ---- */
  W.wireRows = function (scope) {
    Array.prototype.forEach.call((scope || document).querySelectorAll("tr.ex"), function (tr) {
      if (tr.dataset.wired) return;
      tr.dataset.wired = "1"; tr.tabIndex = 0; tr.setAttribute("aria-expanded", "false");
      function toggle() {
        var d = tr.nextElementSibling;
        if (!d || !d.classList.contains("dt")) return;
        var open = d.hasAttribute("hidden");
        if (open) d.removeAttribute("hidden"); else d.setAttribute("hidden", "");
        tr.setAttribute("aria-expanded", String(open));
      }
      tr.addEventListener("click", function (e) { if (e.target.closest("a")) return; toggle(); });
      tr.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
    });
  };


  /* ---- figure tools: Table · Copy link · Cite · CSV, on any chart card ----
     opts: {id, title, cols:[...], rows:[[...]], file, source} */
  W.figTools = function (card, o) {
    if (!card) return;
    if (o.id && !card.id) card.id = o.id;
    var bar = W.el("div", "ftools"), tbl = null, msg = W.el("span", "ok");
    function btn(label, fn) { var b = W.el("button", "", label); b.type = "button"; b.addEventListener("click", function () { fn(b); }); bar.appendChild(b); return b; }
    function say(t) { msg.textContent = t; setTimeout(function () { msg.textContent = ""; }, 1800); }
    function copy(t, ok) {
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function () { say(ok); }, function () { window.prompt("Copy:", t); });
      else window.prompt("Copy:", t);
    }
    if (o.rows && o.cols) btn("Table", function (b) {
      if (!tbl) {
        tbl = W.el("div", "", '<table class="ftab"><thead><tr>' + o.cols.map(function (c) { return "<th>" + W.esc(c) + "</th>"; }).join("") + "</tr></thead><tbody>" +
          o.rows.map(function (r) { return "<tr>" + r.map(function (v) { return "<td>" + W.esc(v) + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table>");
        tbl.hidden = true; card.insertBefore(tbl, bar);
      }
      tbl.hidden = !tbl.hidden; b.setAttribute("aria-pressed", String(!tbl.hidden));
    });
    btn("Copy link", function () { copy(location.origin + location.pathname + "#" + card.id, "Link copied"); });
    btn("Cite", function () {
      var d = new Date();
      copy("When Money Follows the Child. \u201c" + o.title + ".\u201d " + location.origin + location.pathname + "#" + card.id + ". Accessed " + d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }) + ".", "Citation copied");
    });
    if (o.rows && o.cols) btn("CSV", function () {
      W.csv(o.rows.map(function (r) { var x = {}; o.cols.forEach(function (c, i) { x[c] = r[i]; }); return x; }), o.cols, (o.file || card.id || "wmfc") + ".csv");
    });
    bar.appendChild(msg);
    card.appendChild(bar);
  };

  /* ---- CSV download from rows ---- */
  W.csv = function (rows, cols, name) {
    var q = function (v) {
      v = v == null ? "" : String(v).replace(/<[^>]+>/g, "");
      return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
    };
    var out = [cols.join(",")].concat(rows.map(function (r) {
      return cols.map(function (c) { return q(r[c]); }).join(",");
    })).join("\n");
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([out], { type: "text/csv" }));
    a.download = name; document.body.appendChild(a); a.click(); a.remove();
  };

  /* ---- derived numbers: [data-derive] from the Readiness Index data.
     The HTML always ships a correct value; this only keeps it from drifting. ---- */
  var dn = document.querySelectorAll("[data-derive]");
  if (dn.length && window.fetch) {
    W.json("/data/scan-2026.json").then(function (d) {
      if (!d || !d.institutions) return;
      var I = d.institutions, st = {};
      I.forEach(function (r) { st[r.state] = 1; });
      function n(f) { return I.filter(f).length; }
      var v = {
        total: I.length, states: Object.keys(st).length,
        tier1: n(function (r) { return r.tier === "Tier 1"; }),
        "tier1.prep": n(function (r) { return r.tier === "Tier 1" && (r.engagement || []).indexOf("program") > -1; }),
        "tier1.ops": n(function (r) { return r.tier === "Tier 1" && (r.engagement || []).indexOf("program") < 0; }),
        tier2: n(function (r) { return r.tier === "Tier 2"; }),
        tier3: n(function (r) { return r.tier === "Tier 3"; }),
        tier0: n(function (r) { return r.tier === "Tier 0"; }),
        "fl.total": n(function (r) { return r.state === "Florida"; }),
        "fl.tier2": n(function (r) { return r.state === "Florida" && r.tier === "Tier 2"; }),
        "fl.tier1": n(function (r) { return r.state === "Florida" && r.tier === "Tier 1"; }),
        "mi.total": n(function (r) { return r.state === "Michigan"; }),
        aggregates: n(function (r) { return r.scope === "aggregate"; }),
        institutions: n(function (r) { return r.scope !== "aggregate"; })
      };
      Array.prototype.forEach.call(dn, function (e) {
        var k = e.dataset.derive;
        if (!(k in v)) return;
        var tpl = e.dataset.deriveTpl;
        e.textContent = tpl ? tpl.replace("{n}", v[k]) : String(v[k]);
        var p = e.parentNode;
        if (p && p.parentNode && p.parentNode.classList && p.parentNode.classList.contains("stack")) {
          p.style.flexGrow = v[k]; p.dataset.g = v[k];
        }
      });
    }).catch(function () {});
  }

  window.addEventListener("beforeprint", function () {
    Array.prototype.forEach.call(document.querySelectorAll("tr.dt[hidden]"), function (d) { d.removeAttribute("hidden"); });
  });
})();
/* ARCHIVE:START — 'N years ago' stamps, the current year, and a slow zoom as photographs come into view. */
(function () {
  var now = new Date().getFullYear();
  Array.prototype.forEach.call(document.querySelectorAll("[data-ago]"), function (e) {
    var y = +e.getAttribute("data-ago"); if (y) e.textContent = (now - y) + " years ago";
  });
  Array.prototype.forEach.call(document.querySelectorAll("[data-now]"), function (e) { e.textContent = now; });
  var els = document.querySelectorAll(".arch,.tn,.archclose");
  if (!("IntersectionObserver" in window)) { Array.prototype.forEach.call(els, function (e) { e.classList.add("seen"); }); return; }
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add("seen"); io.unobserve(x.target); } });
  }, { threshold: 0.25 });
  Array.prototype.forEach.call(els, function (e) { io.observe(e); });
})();
/* ARCHIVE:END */
