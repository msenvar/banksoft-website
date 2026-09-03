/* Banksoft — small progressive enhancements. The site works fully without JS. */
(function () {
  "use strict";

  // Mobile menu
  var btn = document.querySelector(".menu-btn");
  var mobile = document.querySelector(".mobile-nav");
  if (btn && mobile) {
    btn.addEventListener("click", function () {
      var open = mobile.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Reveal on scroll
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("is-in"); });
  }

  // Count-up for stats (data-count="25" data-suffix="M")
  var counters = document.querySelectorAll("[data-count]");
  function runCounter(el) {
    var target = parseFloat(el.getAttribute("data-count"));
    var decimals = (el.getAttribute("data-count").split(".")[1] || "").length;
    var suffix = el.querySelector("small");
    var start = null, dur = 1400;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min(1, (ts - start) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      el.firstChild.nodeValue = (target * eased).toFixed(decimals);
      if (p < 1) requestAnimationFrame(step);
    }
    if (reduce) { el.firstChild.nodeValue = target.toFixed(decimals); return; }
    requestAnimationFrame(step);
    if (suffix) el.appendChild(suffix);
  }
  if (counters.length) {
    if ("IntersectionObserver" in window) {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { runCounter(e.target); cio.unobserve(e.target); }
        });
      }, { threshold: 0.4 });
      counters.forEach(function (el) { cio.observe(el); });
    } else {
      counters.forEach(runCounter);
    }
  }

  // Solutions page: highlight active group in side nav
  var groups = document.querySelectorAll(".sol-group");
  var navLinks = document.querySelectorAll(".sol-nav a");
  if (groups.length && navLinks.length && "IntersectionObserver" in window) {
    var gio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          navLinks.forEach(function (a) {
            a.classList.toggle("is-active", a.getAttribute("href") === "#" + e.target.id);
          });
        }
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    groups.forEach(function (g) { gio.observe(g); });
  }

  // Contact form.
  // Set data-endpoint on the <form> to a form service URL (e.g. Formspree,
  // Basin, or your own POST handler) to send by fetch. With no endpoint the
  // form opens the visitor's mail client addressed to contact@banksoft.com.tr.
  var form = document.querySelector(".form");
  if (form) {
    var status = form.querySelector(".form__status");
    var msg = function (key) { return form.getAttribute("data-msg-" + key) || ""; };
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (form.querySelector(".hp input") && form.querySelector(".hp input").value) return; // bot
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var data = new FormData(form);
      var endpoint = form.getAttribute("data-endpoint");
      var btn = form.querySelector("button[type=submit]");
      if (endpoint) {
        btn.disabled = true;
        status.className = "form__status"; status.textContent = msg("sending");
        fetch(endpoint, { method: "POST", body: data, headers: { "Accept": "application/json" } })
          .then(function (r) { if (!r.ok) throw new Error(r.status); status.className = "form__status is-ok"; status.textContent = msg("ok"); form.reset(); })
          .catch(function () { status.className = "form__status is-err"; status.textContent = msg("err"); })
          .then(function () { btn.disabled = false; });
      } else {
        var lines = [];
        data.forEach(function (v, k) { if (k !== "website") lines.push(k + ": " + v); });
        var subject = "[banksoft.com.tr] " + (data.get("topic") || "Contact") + " — " + (data.get("organization") || "");
        location.href = "mailto:contact@banksoft.com.tr?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(lines.join("\n"));
        status.className = "form__status is-ok"; status.textContent = msg("mail");
      }
    });
  }
})();
