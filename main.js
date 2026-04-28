/* In-view sections first, then turn on "hidden until revealed" CSS so a missing/blocked script never leaves main at opacity:0. */
(function revealBootstrap() {
  function run() {
    const h = window.innerHeight || 800;
    // Be a bit generous so sections that are already visible (or just below the fold) don't look empty on load.
    const topCutoff = h * 1.12;
    document.querySelectorAll("main [data-reveal]").forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.top < topCutoff && r.bottom > 0) el.classList.add("is-in");
    });
  }

  run();
  document.documentElement.classList.add("reveal-animations-on");

  // Layout can shift after first paint (fonts/images). Re-run once on the next frame and again after full load.
  requestAnimationFrame(run);
  window.addEventListener("load", run, { once: true });
})();

const sections = Array.from(document.querySelectorAll("main .section"));
const navLinks = Array.from(document.querySelectorAll(".topbar__nav .topbar__link"));
const toastEl = document.getElementById("toast");

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function typeInto(el, text, { startDelayMs = 250, charDelayMs = 26 } = {}) {
  if (!el) return;
  await sleep(startDelayMs);
  el.textContent = "";
  for (let i = 0; i < text.length; i += 1) {
    el.textContent += text[i];
    await sleep(charDelayMs);
  }
}

let toastTimer = null;
function toast(msg) {
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add("is-on");
  if (toastTimer) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toastEl.classList.remove("is-on"), 1800);
}

let activeId = "hero";
function setActiveSection(id) {
  activeId = id;
  for (const a of navLinks) a.setAttribute("aria-current", a.getAttribute("href") === `#${id}` ? "true" : "false");
}

const supportsIo = typeof window !== "undefined" && "IntersectionObserver" in window;

if (supportsIo) {
  /* Section highlight for topbar nav */
  const sectionIo = new IntersectionObserver(
    (entries) => {
      let best = null;
      for (const e of entries) {
        if (e.isIntersecting) {
          if (!best || e.intersectionRatio > best.ratio) best = { id: e.target.id, ratio: e.intersectionRatio };
        }
      }
      if (best?.id) setActiveSection(best.id);
    },
    { threshold: [0.25, 0.45, 0.65] }
  );
  sections.forEach((s) => sectionIo.observe(s));

  /* Reveal-on-scroll */
  const revealIo = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) e.target.classList.add("is-in");
      }
    },
    { threshold: 0.15 }
  );
  document.querySelectorAll("[data-reveal]").forEach((el) => revealIo.observe(el));
} else {
  // Older embedded browsers: keep all content visible and skip scroll-driven features.
  document.querySelectorAll("[data-reveal]").forEach((el) => el.classList.add("is-in"));
}

/* JSON: contact snapshot for ATS/CRM tooling */
document.querySelectorAll(".js-download-json").forEach((btn) => {
  btn.addEventListener("click", () => {
    const data = {
      purpose:
        "Contact and key metadata in structured form. For CRM, ATS, or other tooling. Full resume: use the PDF download on this page.",
      name: "William Amor",
      role: "Principal Product Owner",
      location: "London, SE10 9JU",
      email: "william.amor@protonmail.com",
      phone: "+44 7 889 904 127",
      linkedin: "https://www.linkedin.com/in/willamor/",
      nationality: "British and Irish (dual citizenship)",
      right_to_work: "UK and EU/EEA (no sponsorship)",
      open_to: ["Principal Product Owner", "Product Owner", "Product Manager"],
      industries: ["Insurance", "Consumer Healthcare", "Pharmaceuticals"],
      open_to_locations:
        "UK, US, Canada, and EU/EEA (EU member states plus Iceland, Liechtenstein, and Norway). Sponsorship required for US and Canada only.",
      will_travel: "Up to 75%",
      certifications: ["SAFe 5 Agilist", "ITIL v3"],
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "william-amor-resume.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 800);
    toast("JSON file downloaded.");
  });
});

/* Copy email to clipboard from the closing band */
document.getElementById("copyEmail")?.addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  const email = btn.getAttribute("data-email") || "";
  const label = btn.querySelector("#copyEmailLabel");
  try {
    await navigator.clipboard.writeText(email);
    toast("Email copied to clipboard.");
    if (label) {
      const original = label.textContent;
      label.textContent = "Copied. Paste away";
      setTimeout(() => { label.textContent = original; }, 1600);
    }
  } catch {
    window.location.href = `mailto:${email}`;
  }
});

/* Track-record industry filter */
(function setupFilter() {
  const pills = Array.from(document.querySelectorAll(".filterPill"));
  const cards = Array.from(document.querySelectorAll("#xpList .xpCard"));
  const empty = document.getElementById("filterEmpty");
  const clear = document.getElementById("filterClear");
  if (!pills.length || !cards.length) return;

  function apply(filter) {
    let shown = 0;
    for (const c of cards) {
      const tags = (c.getAttribute("data-tags") || "").split(/\s+/);
      const match = filter === "all" || tags.includes(filter);
      c.classList.toggle("is-hidden", !match);
      if (match) shown += 1;
    }
    if (empty) empty.hidden = shown !== 0;
    for (const p of pills) {
      const on = p.getAttribute("data-filter") === filter;
      p.classList.toggle("is-on", on);
      p.setAttribute("aria-selected", on ? "true" : "false");
    }
  }

  pills.forEach((p) => p.addEventListener("click", () => apply(p.getAttribute("data-filter") || "all")));
  clear?.addEventListener("click", () => apply("all"));
})();

/* Hero rotator: cross-fade through positioning lines */
(function setupHeroRotator() {
  const rot = document.getElementById("heroRotator");
  if (!rot) return;
  const lines = Array.from(rot.querySelectorAll(".heroRotator__line"));
  if (lines.length <= 1) return;

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;

  let i = 0;
  setInterval(() => {
    lines[i].classList.remove("is-on");
    i = (i + 1) % lines.length;
    lines[i].classList.add("is-on");
  }, 3600);
})();

/* Carousel: Impact examples */
(function setupCarousels() {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const carousels = Array.from(document.querySelectorAll("[data-carousel]"));
  if (!carousels.length) return;

  for (const root of carousels) {
    const viewport = root.querySelector("[data-carousel-viewport]") || root;
    const track = root.querySelector("[data-carousel-track]");
    const slides = Array.from(root.querySelectorAll("[data-carousel-slide]"));
    const prev = root.querySelector("[data-carousel-prev]");
    const next = root.querySelector("[data-carousel-next]");
    const dotsHost = root.querySelector("[data-carousel-dots]");
    if (!track || slides.length === 0) continue;

    let i = 0;
    let timer = null;

    function renderDots() {
      if (!dotsHost) return;
      dotsHost.innerHTML = "";
      slides.forEach((_, idx) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = `carousel__dot${idx === i ? " is-on" : ""}`;
        b.setAttribute("aria-label", `Show example ${idx + 1}`);
        b.addEventListener("click", () => go(idx));
        dotsHost.appendChild(b);
      });
    }

    function go(idx) {
      i = (idx + slides.length) % slides.length;
      track.style.transform = `translateX(${-i * 100}%)`;
      renderDots();
    }

    function step(dir) {
      go(i + dir);
    }

    function stop() {
      if (timer) window.clearInterval(timer);
      timer = null;
    }

    function start() {
      if (reduce) return;
      stop();
      timer = window.setInterval(() => step(1), 6500);
    }

    prev?.addEventListener("click", () => step(-1));
    next?.addEventListener("click", () => step(1));

    // Drag/swipe support (mobile + trackpads). Only capture mostly-horizontal gestures.
    (function setupDrag() {
      let pointerId = null;
      let startX = 0;
      let startY = 0;
      let dx = 0;
      let dragging = false;
      let locked = false;
      let w = 0;
      let lastDown = 0;

      function width() {
        const rect = viewport.getBoundingClientRect();
        return Math.max(1, rect.width);
      }

      function setTransform(px) {
        track.style.transform = `translateX(${px}px)`;
      }

      function snap() {
        track.style.transition = "";
        track.style.transform = `translateX(${-i * 100}%)`;
      }

      viewport.addEventListener("pointerdown", (e) => {
        // Ignore non-primary buttons/multi-touch.
        if (e.pointerType === "mouse" && e.button !== 0) return;
        if (pointerId !== null) return;
        pointerId = e.pointerId;
        startX = e.clientX;
        startY = e.clientY;
        dx = 0;
        dragging = false;
        locked = false;
        w = width();
        lastDown = Date.now();
        stop();
        viewport.setPointerCapture?.(pointerId);
      });

      viewport.addEventListener("pointermove", (e) => {
        if (pointerId !== e.pointerId) return;
        dx = e.clientX - startX;
        const dy = e.clientY - startY;

        if (!locked) {
          // Decide if this is a horizontal drag or a normal vertical scroll.
          const ax = Math.abs(dx);
          const ay = Math.abs(dy);
          if (ax < 6 && ay < 6) return;
          locked = true;
          dragging = ax > ay;
          if (dragging) track.style.transition = "none";
        }

        if (!dragging) return;
        e.preventDefault();

        // Convert the current slide position into pixels, then add dx.
        const base = -i * w;
        setTransform(base + dx);
      }, { passive: false });

      function finish(e) {
        if (pointerId !== e.pointerId) return;
        viewport.releasePointerCapture?.(pointerId);

        const wasDragging = dragging;
        const moved = Math.abs(dx);
        const threshold = Math.max(44, w * 0.18);

        pointerId = null;
        dragging = false;
        locked = false;

        if (wasDragging && moved > threshold) {
          step(dx < 0 ? 1 : -1);
        } else {
          snap();
          renderDots();
        }

        // Prevent a click from firing after a swipe.
        if (wasDragging || moved > 10 || (Date.now() - lastDown) < 160) {
          window.setTimeout(() => start(), 250);
        } else {
          start();
        }
      }

      viewport.addEventListener("pointerup", finish);
      viewport.addEventListener("pointercancel", (e) => {
        if (pointerId !== e.pointerId) return;
        pointerId = null;
        dragging = false;
        locked = false;
        snap();
        renderDots();
        start();
      });

      // Keep pixel math correct if the viewport size changes.
      window.addEventListener("resize", () => { w = width(); snap(); });
    })();

    // Pause on hover/focus so it doesn't fight the user.
    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    root.addEventListener("focusin", stop);
    root.addEventListener("focusout", start);

    // Keyboard support
    root.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") step(-1);
      if (e.key === "ArrowRight") step(1);
    });

    go(0);
    start();
  }
})();

/* Mini runner game (bottom of page) */
(function setupRunnerGame() {
  const canvas = document.getElementById("runnerGame");
  const scoreEl = document.getElementById("gameScore");
  const startBtn = document.getElementById("gameStart");
  const restartBtn = document.getElementById("gameRestart");
  const overlay = document.getElementById("gameOverlay");
  if (!canvas || !scoreEl || !startBtn || !restartBtn || !overlay) return;

  const ctx = canvas.getContext("2d", { alpha: true });
  if (!ctx) return;

  let running = false;
  let raf = 0;
  let lastT = 0;

  // World units are based on the canvas' CSS pixels; we scale for devicePixelRatio.
  function resize() {
    const dpr = Math.max(1, Math.floor(window.devicePixelRatio || 1));
    const rect = canvas.getBoundingClientRect();
    const w = Math.max(320, Math.floor(rect.width));
    const h = Math.max(160, Math.floor((rect.width * 180) / 720));
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.height = `${h}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { w, h };
  }

  let size = resize();
  window.addEventListener("resize", () => { size = resize(); });

  const state = {
    groundY: 0,
    player: { x: 0, y: 0, vy: 0, w: 0, h: 0, onGround: true },
    obstacles: [],
    speed: 260,          // px/s
    gravity: 1700,       // px/s^2
    jumpVy: -620,        // px/s
    spawnTimer: 0,
    score: 0,
  };

  function reset() {
    size = resize();
    state.groundY = size.h - 26;
    state.player = { x: 48, y: state.groundY - 34, vy: 0, w: 26, h: 34, onGround: true };
    state.obstacles = [];
    state.speed = 260;
    state.spawnTimer = 0.9;
    state.score = 0;
    scoreEl.textContent = "0";
    restartBtn.hidden = true;
  }

  function setOverlay(title, sub) {
    overlay.querySelector(".game__overlayTitle")?.replaceChildren(document.createTextNode(title));
    overlay.querySelector(".game__overlaySub")?.replaceChildren(document.createTextNode(sub));
    overlay.classList.remove("is-off");
  }
  function hideOverlay() { overlay.classList.add("is-off"); }

  function jump() {
    if (!running) return;
    if (!state.player.onGround) return;
    state.player.vy = state.jumpVy;
    state.player.onGround = false;
  }

  function rectsOverlap(a, b) {
    return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
  }

  function spawnObstacle() {
    const h = 18 + Math.random() * 18;
    const w = 12 + Math.random() * 18;
    state.obstacles.push({
      x: size.w + 10,
      y: state.groundY - h,
      w,
      h,
      passed: false,
    });
  }

  function update(dt) {
    // Increase difficulty slowly.
    state.speed = Math.min(520, state.speed + dt * 10);

    // Player physics
    state.player.vy += state.gravity * dt;
    state.player.y += state.player.vy * dt;
    if (state.player.y + state.player.h >= state.groundY) {
      state.player.y = state.groundY - state.player.h;
      state.player.vy = 0;
      state.player.onGround = true;
    }

    // Obstacles
    for (const o of state.obstacles) o.x -= state.speed * dt;
    state.obstacles = state.obstacles.filter((o) => o.x + o.w > -20);

    // Spawn timer
    state.spawnTimer -= dt;
    if (state.spawnTimer <= 0) {
      spawnObstacle();
      // Vary spacing a bit; tighter as speed increases.
      const base = 0.95 - (state.speed - 260) / 700;
      state.spawnTimer = Math.max(0.48, base) + Math.random() * 0.35;
    }

    // Score: time + obstacles passed.
    state.score += dt * 10;
    for (const o of state.obstacles) {
      if (!o.passed && o.x + o.w < state.player.x) {
        o.passed = true;
        state.score += 12;
      }
      if (rectsOverlap(state.player, o)) return false;
    }

    scoreEl.textContent = String(Math.floor(state.score));
    return true;
  }

  function draw() {
    ctx.clearRect(0, 0, size.w, size.h);

    // Ground
    ctx.fillStyle = "rgba(255,255,255,0.10)";
    ctx.fillRect(0, state.groundY, size.w, 1);
    ctx.fillStyle = "rgba(255,255,255,0.06)";
    ctx.fillRect(0, state.groundY + 1, size.w, size.h - state.groundY);

    // Player
    ctx.fillStyle = "rgba(125, 211, 252, 0.95)";
    ctx.fillRect(state.player.x, state.player.y, state.player.w, state.player.h);

    // Obstacles
    ctx.fillStyle = "rgba(255,255,255,0.75)";
    for (const o of state.obstacles) ctx.fillRect(o.x, o.y, o.w, o.h);
  }

  function frame(t) {
    if (!running) return;
    if (!lastT) lastT = t;
    const dt = Math.min(0.04, (t - lastT) / 1000);
    lastT = t;

    const ok = update(dt);
    draw();
    if (!ok) {
      running = false;
      window.cancelAnimationFrame(raf);
      raf = 0;
      restartBtn.hidden = false;
      const s = Math.floor(state.score);
      setOverlay("Game over", `Score: ${s}. Hit restart to try again.`);
      return;
    }
    raf = window.requestAnimationFrame(frame);
  }

  function start() {
    reset();
    running = true;
    lastT = 0;
    hideOverlay();
    raf = window.requestAnimationFrame(frame);
  }

  // Controls
  let starting = false;
  function startOnce(e) {
    if (starting) return;
    starting = true;
    // On some mobile browsers, click can be finicky; pointer/touch is more reliable.
    e?.preventDefault?.();
    start();
    window.setTimeout(() => { starting = false; }, 300);
  }

  startBtn.addEventListener("click", startOnce);
  restartBtn.addEventListener("click", startOnce);
  startBtn.addEventListener("pointerdown", startOnce);
  restartBtn.addEventListener("pointerdown", startOnce);
  startBtn.addEventListener("touchstart", startOnce, { passive: false });
  restartBtn.addEventListener("touchstart", startOnce, { passive: false });
  canvas.addEventListener("pointerdown", () => { if (!running) return; jump(); });
  window.addEventListener("keydown", (e) => {
    if (!running) return;
    if (e.code === "Space" || e.code === "ArrowUp") {
      e.preventDefault();
      jump();
    }
  });

  reset();
  setOverlay("Press Start", "Then jump over the blocks.");
})();

/* If loaded with a hash, let CSS smooth-scroll handle it, but make nav state match quickly. */
function onReady(fn) {
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn, { once: true });
  else fn();
}

onReady(() => {
  const id = decodeURIComponent(window.location.hash || "#hero").replace("#", "");
  if (document.getElementById(id)) setActiveSection(id);
  else setActiveSection("hero");

  const roleEl = document.getElementById("roleType");
  const roleText = roleEl?.getAttribute("data-text") || "Principal Product Owner";

  if (roleEl) roleEl.textContent = roleText;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      void typeInto(roleEl, roleText, { startDelayMs: 120, charDelayMs: 24 });
    });
  });
});
