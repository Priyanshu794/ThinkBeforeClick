// ThinkBeforeClick — Phase 6 analyzer flow
// Canvas rain + GSAP timeline sequencing + fetch to backend /analyze

// ---------------------------------------------------------------------------
// CONFIG — change this if your backend runs somewhere other than localhost:8000
// ---------------------------------------------------------------------------
const API_BASE = "http://127.0.0.1:8000";

// ===========================================================================
// MATRIX RAIN ENGINE
// ===========================================================================
const RainEngine = (() => {
  const canvas = document.getElementById("rain-canvas");
  const ctx = canvas.getContext("2d");

  const CHARS = "アイウエオカキクケコサシスセソ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const FONT_SIZE = 16;

  const BASELINE_INTERVAL = 45; // ms per step — baseline speed
  const BOOST_INTERVAL = 14;    // ms per step — processing speed

  let columns = [];
  let colCount = 0;
  let currentInterval = BASELINE_INTERVAL;
  let targetInterval = BASELINE_INTERVAL;
  let lastStepTime = 0;
  let rafId = null;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    colCount = Math.floor(canvas.width / FONT_SIZE);
    columns = new Array(colCount).fill(0).map(() => Math.random() * -canvas.height / FONT_SIZE);
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  function step() {
    ctx.fillStyle = "rgba(0,0,0,0.08)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.font = FONT_SIZE + "px monospace";

    for (let i = 0; i < colCount; i++) {
      const char = CHARS[Math.floor(Math.random() * CHARS.length)];
      const x = i * FONT_SIZE;
      const y = columns[i] * FONT_SIZE;

      // leading character brighter, rest dimmer matrix-green
      ctx.fillStyle = Math.random() > 0.93 ? "#d4ffd0" : "#39FF14";
      ctx.fillText(char, x, y);

      if (y > canvas.height && Math.random() > 0.975) {
        columns[i] = 0;
      } else {
        columns[i]++;
      }
    }
  }

  function loop(timestamp) {
    // ease currentInterval toward targetInterval so speed changes feel smooth, not abrupt
    currentInterval += (targetInterval - currentInterval) * 0.04;

    if (timestamp - lastStepTime >= currentInterval) {
      step();
      lastStepTime = timestamp;
    }
    rafId = requestAnimationFrame(loop);
  }

  function start() {
    resize();
    window.addEventListener("resize", resize);
    rafId = requestAnimationFrame(loop);
  }

  function setBoost(on) {
    targetInterval = on ? BOOST_INTERVAL : BASELINE_INTERVAL;
  }

  return { start, setBoost };
})();

// ===========================================================================
// STAGE SEQUENCING (GSAP-driven)
// ===========================================================================
const Stages = (() => {
  const stageIntro = document.getElementById("stage-intro");
  const stageTerminal = document.getElementById("stage-terminal");
  const stageVerdict = document.getElementById("stage-verdict");

  const introBox = document.getElementById("intro-box");
  const dialog = document.getElementById("think-dialog");

  function goTo(stageEl) {
    [stageIntro, stageTerminal, stageVerdict].forEach(s => s.classList.remove("active"));
    stageEl.classList.add("active");
  }

  // --- STAGE 1: Intro, 4s glitch, then a hard glitch-out ---
  function playIntro(onDone) {
    goTo(stageIntro);
    introBox.classList.add("glitching");

    gsap.delayedCall(4, () => {
      introBox.classList.remove("glitching");
      introBox.classList.add("glitch-out");
      gsap.delayedCall(0.15, () => {
        onDone();
      });
    });
  }

  // --- STAGE 2: Terminal panel glitches into view, dialog stays open indefinitely ---
  function playTerminalReveal() {
    goTo(stageTerminal);

    gsap.fromTo(dialog,
      { opacity: 0, scale: 0.85 },
      {
        opacity: 1, scale: 1, duration: 0.6, ease: "back.out(1.5)",
        onComplete: () => {
          dialog.classList.add("visible");
          document.getElementById("url-input").focus();
        }
      }
    );
  }

  // --- STAGE 5: Verdict card entrance ---
  function playVerdict(onReady) {
    goTo(stageVerdict);
    const card = document.getElementById("verdict-card");
    gsap.fromTo(card, { opacity: 0, scale: 0.9 }, {
      opacity: 1, scale: 1, duration: 0.6, ease: "power2.out",
      onComplete: onReady
    });
  }

  // --- Reset back to the dialog (used by "Scan again") ---
  function backToDialog() {
    goTo(stageTerminal);
  }

  return { playIntro, playTerminalReveal, playVerdict, backToDialog };
})();

// ===========================================================================
// VERDICT RENDERING
// ===========================================================================
const ICONS = {
  warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
    <path d="M12 2 L23 21 H1 Z" stroke-linejoin="round"/>
    <line x1="12" y1="9" x2="12" y2="14"/>
    <circle cx="12" cy="17.2" r="0.9" fill="currentColor" stroke="none"/>
  </svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
    <path d="M3 13 L9 19 L21 5" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`
};

function renderVerdict(result) {
  const card = document.getElementById("verdict-card");
  const icon = document.getElementById("verdict-icon");
  const scoreEl = document.getElementById("verdict-score");
  const labelEl = document.getElementById("verdict-label");
  const detailsEl = document.getElementById("verdict-details");
  const whyHeading = document.getElementById("verdict-why-heading");
  const whyList = document.getElementById("verdict-why-list");
  const recoList = document.getElementById("verdict-reco-list");

  card.classList.remove("theme-high", "theme-suspicious", "theme-safe");

  const label = result.final_risk_label;
  scoreEl.textContent = "SCORE " + result.final_risk_score;
  labelEl.textContent = label;

  whyList.innerHTML = "";
  recoList.innerHTML = "";

  if (label === "High Risk") {
    card.classList.add("theme-high");
    icon.innerHTML = ICONS.warning;
    whyHeading.textContent = "Why Risky";
    detailsEl.classList.remove("hidden");
  } else if (label === "Suspicious") {
    card.classList.add("theme-suspicious");
    icon.innerHTML = ICONS.warning;
    whyHeading.textContent = "Why Suspicious?";
    detailsEl.classList.remove("hidden");
  } else {
    // Safe — deliberately simpler, no bullet lists at all
    card.classList.add("theme-safe");
    icon.innerHTML = ICONS.check;
    detailsEl.classList.add("hidden");
  }

  if (label !== "Safe") {
    (result.explanation || []).forEach(line => {
      const li = document.createElement("li");
      li.textContent = line;
      whyList.appendChild(li);
    });
    (result.recommendation || []).forEach(line => {
      const li = document.createElement("li");
      li.textContent = line;
      recoList.appendChild(li);
    });
  }
}

// ===========================================================================
// BACKEND CALL
// ===========================================================================
async function analyze(message, url) {
  const payload = {};
  if (message) payload.message = message;
  if (url) payload.url = url;

  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail ? JSON.stringify(errBody.detail) : `Request failed (${res.status})`);
  }
  return res.json();
}

// ===========================================================================
// WIRE UP THE "THINK" BUTTON
// ===========================================================================
function initThinkButton() {
  const btn = document.getElementById("think-btn");
  const urlInput = document.getElementById("url-input");
  const msgInput = document.getElementById("msg-input");
  const status = document.getElementById("think-status");

  btn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    const message = msgInput.value.trim();

    if (!url && !message) {
      status.textContent = "Enter a URL or paste a message first.";
      return;
    }

    btn.disabled = true;
    status.textContent = "ANALYZING...";
    RainEngine.setBoost(true);

    try {
      const result = await analyze(message, url);
      RainEngine.setBoost(false); // ease back to baseline once we have a result
      Stages.playVerdict(() => {});
      renderVerdict(result);
    } catch (err) {
      RainEngine.setBoost(false);
      status.textContent = "Something went wrong — is the backend running? (" + err.message + ")";
    } finally {
      btn.disabled = false;
    }
  });
}

function initScanAgain() {
  document.getElementById("scan-again-btn").addEventListener("click", () => {
    document.getElementById("url-input").value = "";
    document.getElementById("msg-input").value = "";
    document.getElementById("think-status").textContent = "";
    Stages.backToDialog();
  });
}

// ===========================================================================
// BOOT
// ===========================================================================
document.addEventListener("DOMContentLoaded", () => {
  if (typeof gsap === "undefined") {
    document.body.innerHTML =
      '<div style="color:#ff5555;font-family:monospace;padding:40px;font-size:1.1rem;">' +
      'GSAP failed to load — check that <code>static/js/vendor/gsap.min.js</code> exists ' +
      'and that index.html is loading it before analyzer.js.</div>';
    return;
  }

  RainEngine.start();
  initThinkButton();
  initScanAgain();

  Stages.playIntro(() => {
    Stages.playTerminalReveal();
  });
});