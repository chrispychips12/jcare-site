// Staggered reveals. Each .rv item inside a [data-reveal] section rises in as it scrolls into
// view; items arriving together are staggered 70ms apart (capped). Content stays visible without
// JS and for anyone who prefers reduced motion: the hidden start state is opt-in via .js-reveal.
// Safety nets: focus, an anchor jump or printing reveals the section at once.
(() => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!("IntersectionObserver" in window)) return;

  const items = Array.from(document.querySelectorAll("[data-reveal] .rv"));
  if (!items.length) return;
  document.documentElement.classList.add("js-reveal");

  const STEP = 70;
  const MAX_STEPS = 5;
  const show = (el, delay) => {
    el.style.transitionDelay = delay ? `${delay}ms` : "";
    el.classList.add("is-visible");
    io.unobserve(el);
  };

  const io = new IntersectionObserver(
    (entries) => {
      const arriving = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top || a.boundingClientRect.left - b.boundingClientRect.left);
      arriving.forEach((e, n) => show(e.target, Math.min(n, MAX_STEPS) * STEP));
    },
    { rootMargin: "0px 0px -8% 0px" }
  );
  items.forEach((el) => io.observe(el));

  const revealWithin = (node) => {
    const section = node && node.closest ? node.closest("[data-reveal]") : null;
    if (section) section.querySelectorAll(".rv:not(.is-visible)").forEach((el) => show(el, 0));
  };
  document.addEventListener("focusin", (e) => revealWithin(e.target));
  const revealHash = () => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (id) revealWithin(document.getElementById(id));
  };
  window.addEventListener("hashchange", revealHash);
  revealHash();
  window.addEventListener("beforeprint", () => items.forEach((el) => show(el, 0)));
})();

// The bookends' decorative layers (hero, footer) overhang their boxes. Browsers without
// overflow: clip (Safari before 16) treat them as scroll containers that focus can scroll; pin
// them so the copy never slides away.
document.querySelectorAll(".bookend").forEach((el) => {
  el.addEventListener("scroll", () => {
    el.scrollTop = 0;
    el.scrollLeft = 0;
  }, { passive: true });
});

// Carousels: one shared initialiser for every [data-carousel] (promises, testimonials).
// The buttons must work for everyone, so reduced motion only changes the scroll behaviour, it
// never switches the controls off. Without JS each track is a plain horizontal scroller with
// its controls hidden. Slide position is in the markup (aria-roledescription="slide",
// aria-label "n of N"), so nothing here needs to announce it.
function initCarousel(root) {
  const list = root.querySelector(".carousel-track");
  const prev = root.querySelector(".carousel-prev");
  const next = root.querySelector(".carousel-next");
  if (!list || !prev || !next) return;
  const cards = Array.from(list.children);
  const dotsWrap = root.querySelector(".carousel-dots");
  const dots = dotsWrap ? Array.from(dotsWrap.querySelectorAll(".dot")) : [];
  const count = root.querySelector(".carousel-count");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  const behavior = () => (reduce.matches ? "auto" : "smooth");
  const step = () => (cards.length > 1 ? cards[1].offsetLeft - cards[0].offsetLeft : list.clientWidth);
  const maxScroll = () => list.scrollWidth - list.clientWidth;
  const atStart = () => list.scrollLeft <= 2;
  const atEnd = () => list.scrollLeft >= maxScroll() - 2;

  const currentIndex = () => {
    if (atEnd()) return cards.length - 1;
    return Math.min(cards.length - 1, Math.max(0, Math.round(list.scrollLeft / step())));
  };

  const update = () => {
    const i = currentIndex();
    dots.forEach((d, n) => d.classList.toggle("is-current", n === i));
    if (count) count.textContent = `${i + 1} of ${cards.length}`;
    prev.setAttribute("aria-disabled", String(atStart()));
    next.setAttribute("aria-disabled", String(atEnd()));
    // Nothing to scroll (very wide screens): no buttons to press.
    const fits = maxScroll() <= 2;
    prev.hidden = fits;
    next.hidden = fits;
  };

  const go = (direction) => {
    if (direction < 0 ? atStart() : atEnd()) return;
    list.scrollBy({ left: direction * step(), behavior: behavior() });
  };

  prev.addEventListener("click", () => go(-1));
  next.addEventListener("click", () => go(1));

  let frame = 0;
  const schedule = () => {
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      update();
    });
  };
  list.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);

  if (dotsWrap) dotsWrap.removeAttribute("hidden");
  root.classList.add("is-enhanced");
  update();
}

document.querySelectorAll("[data-carousel]").forEach(initCarousel);

// Contact form: the client/staff switch, links that preselect it, and the preview submit.
// Works for everyone; reduced motion only drops the animation. Without JS, CSS :has() still
// shows the matching question set. The form doesn't send anywhere yet: it is an honest preview.
(() => {
  const form = document.querySelector("form.contact-form");
  if (!form) return;
  const section = document.getElementById("contact");
  const title = document.getElementById("contact-title");
  const TITLES = { client: "Let's talk.", staff: "Let's talk work." };
  const sets = { client: form.querySelector(".fields-client"), staff: form.querySelector(".fields-staff") };
  const submit = form.querySelector(".form-submit");
  const nameField = form.querySelector('[name="name"]');
  const done = section.querySelector(".form-done");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  const LEAVE_MS = 180;

  let token = 0;
  let timer = 0;

  const currentMode = () => (form.querySelector('input[name="mode"]:checked') || {}).value || "client";

  const show = (mode, animate) => {
    const incoming = sets[mode];
    const outgoing = sets[mode === "staff" ? "client" : "staff"];
    form.dataset.mode = mode;
    submit.textContent = mode === "staff" ? "Send application" : "Send";
    // The heading follows the switch; focus stays on the switch, so no live region is needed.
    const heading = TITLES[mode] || TITLES.client;
    if (title && title.textContent !== heading) {
      title.textContent = heading;
      if (animate && !reduce.matches) {
        title.classList.remove("is-swapping");
        void title.offsetWidth; // restart the crossfade
        title.classList.add("is-swapping");
      }
    }
    // Hidden fields never block submit: a disabled fieldset is skipped by validation.
    incoming.disabled = false;
    outgoing.disabled = true;

    const run = ++token;
    clearTimeout(timer);
    const settle = () => {
      outgoing.hidden = true;
      outgoing.classList.remove("is-leaving");
      incoming.hidden = false;
      incoming.classList.remove("is-leaving");
    };

    if (!animate || reduce.matches || outgoing.hidden) {
      incoming.classList.remove("is-entering");
      settle();
      return;
    }

    incoming.classList.remove("is-leaving", "is-entering");
    outgoing.classList.add("is-leaving");
    timer = setTimeout(() => {
      if (run !== token) return;
      incoming.classList.add("is-entering");
      settle();
      void incoming.offsetWidth; // commit the start state before fading in
      incoming.classList.remove("is-entering");
    }, LEAVE_MS);
  };

  const setMode = (mode, animate) => {
    const radio = form.querySelector(`input[name="mode"][value="${mode === "staff" ? "staff" : "client"}"]`);
    radio.checked = true;
    show(radio.value, animate);
  };

  const restore = () => {
    done.replaceChildren();
    form.hidden = false;
  };

  form.addEventListener("change", (e) => {
    if (e.target.name === "mode") show(e.target.value, true);
  });

  // Links marked data-mode (hero, careers) open the form in the right mode.
  document.querySelectorAll("a[data-mode]").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      if (form.hidden) restore();
      setMode(link.getAttribute("data-mode"), false);
      section.scrollIntoView({ behavior: reduce.matches ? "auto" : "smooth", block: "start" });
      nameField.focus({ preventScroll: true });
    });
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const first = nameField.value.trim().split(/\s+/)[0];

    const message = document.createElement("p");
    message.textContent = `Thanks, ${first}. This is a preview, so nothing has been sent yet.`;
    const again = document.createElement("button");
    again.type = "button";
    again.className = "btn btn-ghost";
    again.textContent = "Start again";
    again.addEventListener("click", () => {
      const mode = currentMode();
      form.reset();
      setMode(mode, false);
      restore();
      nameField.focus();
    });

    form.hidden = true;
    done.replaceChildren(message, again);
    done.focus();
  });

  form.classList.add("is-enhanced");
  show(currentMode(), false);
})();
