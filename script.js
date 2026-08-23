const story = document.querySelector(".scroll-story");
const hero = document.querySelector(".hero");
const aboutInner = document.querySelector(".about__inner");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

let frameRequested = false;

const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
const smoothstep = (value) => value * value * (3 - 2 * value);

function phase(progress, start, end) {
  return smoothstep(clamp((progress - start) / (end - start)));
}

function setProperty(name, value) {
  hero?.style.setProperty(name, value);
}

function setAboutReveal(value) {
  if (!aboutInner) return;
  const normalized = Number(value);
  const ready = normalized >= 0.98;
  aboutInner.style.setProperty("--about-reveal", ready ? "1" : "0");
  aboutInner.style.setProperty("--about-visibility", ready ? "visible" : "hidden");
  aboutInner.style.pointerEvents = ready ? "auto" : "none";
}

function resetStory() {
  setProperty("--fog-bank-x", "112vw");
  setProperty("--fog-bank-y", "0vh");
  setProperty("--fog-engulf-y", "0vh");
  setProperty("--fog-engulf-scale", "1");
  setProperty("--fog-handoff", "0");
  setAboutReveal(1);
}

function renderStory() {
  frameRequested = false;

  if (
    !story
    || !hero
    || reducedMotion.matches
    || window.innerWidth / window.innerHeight <= 0.8
  ) {
    resetStory();
    return;
  }

  const travel = story.offsetHeight - window.innerHeight;
  const progress = travel > 0
    ? clamp(-story.getBoundingClientRect().top / travel)
    : 0;

  // Four equal-scale pieces are composed as one bank, so they arrive and rise
  // together without a long sequence or any independent vertical drift.
  const bankArrival = phase(progress, 0.03, 0.24);
  setProperty("--fog-bank-x", `${(112 * (1 - bankArrival)).toFixed(3)}vw`);

  // The large continuous field rises in front shortly after the bank lands.
  // The whole modular bank then climbs behind it as one unit, leaving a little
  // of its scalloped edge visible before the clean field completes the cover.
  const engulf = phase(progress, 0.26, 0.70);
  const bankRise = phase(progress, 0.38, 0.72);

  setProperty("--fog-engulf-y", `${(-170 * engulf).toFixed(3)}vh`);
  setProperty("--fog-engulf-scale", "1");
  setProperty("--fog-bank-y", `${(-92 * bankRise).toFixed(3)}vh`);

  // Keep the transparent follow-on experiment from appearing over the city.
  // It fades in only once the fog has become the handoff surface.
  setAboutReveal(phase(progress, 0.68, 0.84));

  // As the sticky scene releases, let the bottom of the textured fog dissolve
  // into the plain paper surface of the next section instead of ending on a
  // hard horizontal texture line.
  setProperty("--fog-handoff", phase(progress, 0.76, 0.98).toFixed(3));
}

function requestStoryRender() {
  if (frameRequested) return;
  frameRequested = true;
  requestAnimationFrame(renderStory);
}

window.addEventListener("scroll", requestStoryRender, { passive: true });
window.addEventListener("resize", requestStoryRender);
window.addEventListener("pageshow", requestStoryRender);
reducedMotion.addEventListener?.("change", requestStoryRender);
requestStoryRender();

const askForm = document.querySelector(".about__search");
const askInput = document.querySelector("#about-query");
const askButton = askForm?.querySelector("button");

if (askForm && askInput && askButton) {
  const prompts = [
    "ask me anything...",
    "how did you build this portfolio site?",
    "what are you working on right now?",
    "tell me something not on your resume",
    "walk me through your favorite project",
  ];

  let promptIndex = 0;
  let characterIndex = 0;
  let deleting = false;
  let promptTimer;
  let promptActive = true;

  const updateAskButton = () => {
    askButton.hidden = askInput.value.trim().length === 0;
  };

  const typePrompt = () => {
    if (!promptActive || document.activeElement === askInput) return;

    const prompt = prompts[promptIndex];
    askInput.placeholder = prompt.slice(0, characterIndex);

    if (!deleting && characterIndex < prompt.length) {
      characterIndex += 1;
      promptTimer = window.setTimeout(typePrompt, 62);
      return;
    }

    if (!deleting) {
      deleting = true;
      promptTimer = window.setTimeout(typePrompt, 1450);
      return;
    }

    if (characterIndex > 0) {
      characterIndex -= 1;
      promptTimer = window.setTimeout(typePrompt, 32);
      return;
    }

    deleting = false;
    promptIndex = (promptIndex + 1) % prompts.length;
    promptTimer = window.setTimeout(typePrompt, 260);
  };

  const stopPrompt = () => {
    promptActive = false;
    window.clearTimeout(promptTimer);
    askInput.placeholder = "";
  };

  askInput.addEventListener("focus", stopPrompt);
  askInput.addEventListener("input", updateAskButton);
  askForm.addEventListener("submit", (event) => {
    event.preventDefault();
    updateAskButton();
  });

  updateAskButton();
  typePrompt();
}
