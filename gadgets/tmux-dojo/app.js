import {
  ACTION_CATALOG,
  DEFAULT_PREFIX,
  getDefaultBindings,
  parseTmuxConfig,
  parseSequenceString,
  formatSequence,
  areSequencesEqual,
  buildKeyMapIndex,
  getMappedActionForSequence,
  buildMnemonicLabelParts
} from "./core.js";

const STORAGE_KEY = "tmuxShortcutDojo:v1";

const actionById = Object.fromEntries(ACTION_CATALOG.map((action) => [action.id, action]));

const elements = {
  setupSection: document.querySelector("#setup-section"),
  setupBody: document.querySelector("#setup-body"),
  toggleSetup: document.querySelector("#toggle-setup"),
  bindingsSection: document.querySelector("#bindings-section"),
  bindingsBody: document.querySelector("#bindings-body"),
  toggleBindings: document.querySelector("#toggle-bindings"),
  parseSummary: document.querySelector("#parse-summary"),
  importedBindingList: document.querySelector("#imported-binding-list"),
  configUpload: document.querySelector("#config-upload"),
  prefixInput: document.querySelector("#prefix-input"),
  bindingList: document.querySelector("#binding-list"),
  resetDefaults: document.querySelector("#reset-defaults"),
  mnemonicMode: document.querySelector("#mnemonic-mode"),
  challengeText: document.querySelector("#challenge-text"),
  challengeSubtext: document.querySelector("#challenge-subtext"),
  capturePanel: document.querySelector("#capture-panel"),
  capturedSequence: document.querySelector("#captured-sequence"),
  submitBtn: document.querySelector("#submit-btn"),
  clearBtn: document.querySelector("#clear-btn"),
  hintBtn: document.querySelector("#hint-btn"),
  revealBtn: document.querySelector("#reveal-btn"),
  nextBtn: document.querySelector("#next-btn"),
  hintText: document.querySelector("#hint-text"),
  resultBox: document.querySelector("#result-box"),
  stats: document.querySelector("#stats")
};

const bindingInputByAction = new Map();

const state = {
  parseMeta: null,
  config: {
    prefix: DEFAULT_PREFIX,
    bindings: getDefaultBindings(DEFAULT_PREFIX)
  },
  ui: {
    setupCollapsed: false,
    bindingsCollapsed: false,
    mnemonicMode: true
  },
  keyMapIndex: {},
  practice: {
    queue: [],
    currentActionId: null,
    captured: [],
    attempts: 0,
    correct: 0,
    streak: 0,
    skipped: 0,
    hintLevel: 0,
    revealed: false,
    result: null
  }
};

bootstrap();

function bootstrap() {
  hydrateFromStorage();
  setupBindingsEditor();
  wireEvents();
  refreshDerivedState();
  renderSetupSection();
  nextChallenge();
  elements.capturePanel.focus();
}

function wireEvents() {
  elements.configUpload.addEventListener("change", onConfigUpload);

  elements.toggleSetup.addEventListener("click", () => {
    state.ui.setupCollapsed = !state.ui.setupCollapsed;
    saveToStorage();
    renderSetupSection();
  });

  elements.toggleBindings.addEventListener("click", () => {
    state.ui.bindingsCollapsed = !state.ui.bindingsCollapsed;
    saveToStorage();
    renderSetupSection();
  });

  elements.prefixInput.addEventListener("change", () => {
    applyPrefixUpdate(elements.prefixInput.value, { fromUser: true });
  });

  elements.resetDefaults.addEventListener("click", resetToDefaults);

  elements.mnemonicMode.checked = state.ui.mnemonicMode;
  elements.mnemonicMode.addEventListener("change", () => {
    state.ui.mnemonicMode = elements.mnemonicMode.checked;
    saveToStorage();
    renderChallenge();
  });

  elements.submitBtn.addEventListener("click", submitAttempt);
  elements.clearBtn.addEventListener("click", clearCapture);
  elements.hintBtn.addEventListener("click", showHint);
  elements.revealBtn.addEventListener("click", revealAnswer);
  elements.nextBtn.addEventListener("click", nextChallenge);

  elements.capturePanel.addEventListener("keydown", (event) => {
    if (runShortcut(event)) {
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      submitAttempt();
      return;
    }

    if (event.key === "Backspace") {
      event.preventDefault();
      state.practice.captured.pop();
      renderCapturedSequence();
      return;
    }

    const combo = comboFromKeyboardEvent(event);
    if (!combo || event.repeat) {
      return;
    }

    event.preventDefault();
    state.practice.captured.push(combo);

    const expected = getExpectedSequence();
    if (state.practice.captured.length > Math.max(expected.length, 2)) {
      state.practice.captured.shift();
    }

    renderCapturedSequence();

    if (expected.length > 0 && state.practice.captured.length === expected.length) {
      submitAttempt();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (shouldIgnoreGlobalShortcut(event)) {
      return;
    }

    runShortcut(event);
  });
}

function shouldIgnoreGlobalShortcut(event) {
  const target = event.target;
  if (!target || !(target instanceof HTMLElement)) {
    return false;
  }

  if (target === elements.capturePanel) {
    return false;
  }

  return ["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(target.tagName);
}

function runShortcut(event) {
  if (event.ctrlKey || event.metaKey || event.altKey) {
    return false;
  }

  const key = event.key.toLowerCase();

  if (event.shiftKey && key === "h") {
    event.preventDefault();
    showHint();
    return true;
  }

  if (event.shiftKey && key === "r") {
    event.preventDefault();
    revealAnswer();
    return true;
  }

  if (event.shiftKey && key === "n") {
    event.preventDefault();
    nextChallenge();
    return true;
  }

  if (key === "escape") {
    event.preventDefault();
    clearCapture();
    return true;
  }

  return false;
}

function setupBindingsEditor() {
  elements.bindingList.innerHTML = "";
  bindingInputByAction.clear();

  for (const action of ACTION_CATALOG) {
    const row = document.createElement("div");
    row.className = "binding-row";

    const label = document.createElement("label");
    label.textContent = action.label;
    label.setAttribute("for", `binding-${action.id}`);

    const input = document.createElement("input");
    input.type = "text";
    input.id = `binding-${action.id}`;
    input.autocomplete = "off";
    input.spellcheck = false;
    input.addEventListener("change", () => onBindingInputChange(action.id, input));

    row.append(label, input);
    elements.bindingList.append(row);
    bindingInputByAction.set(action.id, input);
  }
}

function onBindingInputChange(actionId, input) {
  const parsed = parseSequenceString(input.value);
  if (parsed.length === 0) {
    input.classList.add("invalid");
    return;
  }

  input.classList.remove("invalid");
  state.config.bindings[actionId] = parsed;
  saveToStorage();
  refreshDerivedState();
  renderSetupSection();
}

function applyPrefixUpdate(rawValue, options = {}) {
  const parsed = parseSequenceString(rawValue);
  if (parsed.length === 0) {
    elements.prefixInput.classList.add("invalid");
    if (!options.fromUser) {
      elements.prefixInput.value = state.config.prefix;
    }
    return;
  }

  elements.prefixInput.classList.remove("invalid");
  const prefix = parsed[0];
  const previousPrefix = state.config.prefix;
  state.config.prefix = prefix;

  for (const action of ACTION_CATALOG) {
    const sequence = state.config.bindings[action.id];
    if (!Array.isArray(sequence) || sequence.length < 2) {
      continue;
    }

    if (sequence[0] === previousPrefix || sequence[0] === state.config.prefix) {
      state.config.bindings[action.id] = [prefix, ...sequence.slice(1)];
    }
  }

  saveToStorage();
  refreshDerivedState();
  renderSetupSection();
}

async function onConfigUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) {
    return;
  }

  const text = await file.text();
  const parsed = parseTmuxConfig(text);

  state.config = {
    prefix: parsed.prefix,
    bindings: {
      ...getDefaultBindings(parsed.prefix),
      ...parsed.bindings
    }
  };
  state.parseMeta = parsed;
  state.ui.setupCollapsed = true;

  saveToStorage();
  refreshDerivedState();
  renderSetupSection();
  clearResultAndHint();
  elements.capturePanel.focus();
  event.target.value = "";
}

function resetToDefaults() {
  state.parseMeta = null;
  state.config = {
    prefix: DEFAULT_PREFIX,
    bindings: getDefaultBindings(DEFAULT_PREFIX)
  };

  saveToStorage();
  refreshDerivedState();
  renderSetupSection();
  clearResultAndHint();
}

function hydrateFromStorage() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return;
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return;
  }

  const parsedPrefix = parseSequenceString(String(parsed.prefix || ""))[0] || DEFAULT_PREFIX;
  const defaults = getDefaultBindings(parsedPrefix);
  const hydratedBindings = { ...defaults };

  if (parsed.bindings && typeof parsed.bindings === "object") {
    for (const action of ACTION_CATALOG) {
      const incoming = parsed.bindings[action.id];
      if (!incoming) {
        continue;
      }

      const sequence = Array.isArray(incoming)
        ? parseSequenceString(incoming.join(" then "))
        : parseSequenceString(String(incoming));

      if (sequence.length > 0) {
        hydratedBindings[action.id] = sequence;
      }
    }
  }

  state.config = {
    prefix: parsedPrefix,
    bindings: hydratedBindings
  };

  if (parsed.ui && typeof parsed.ui === "object") {
    if (typeof parsed.ui.setupCollapsed === "boolean") {
      state.ui.setupCollapsed = parsed.ui.setupCollapsed;
    }

    if (typeof parsed.ui.bindingsCollapsed === "boolean") {
      state.ui.bindingsCollapsed = parsed.ui.bindingsCollapsed;
    }

    if (typeof parsed.ui.mnemonicMode === "boolean") {
      state.ui.mnemonicMode = parsed.ui.mnemonicMode;
    }
  }

  if (parsed.parseMeta && typeof parsed.parseMeta === "object") {
    state.parseMeta = parsed.parseMeta;
  }
}

function saveToStorage() {
  const payload = {
    prefix: state.config.prefix,
    bindings: state.config.bindings,
    parseMeta: state.parseMeta,
    ui: state.ui
  };

  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function refreshDerivedState() {
  state.keyMapIndex = buildKeyMapIndex(state.config.bindings);
}

function renderSetupSection() {
  elements.prefixInput.value = state.config.prefix;
  elements.mnemonicMode.checked = state.ui.mnemonicMode;

  if (state.ui.setupCollapsed) {
    elements.setupSection.classList.add("collapsed");
    elements.toggleSetup.textContent = "Expand setup";
    elements.toggleSetup.setAttribute("aria-expanded", "false");
  } else {
    elements.setupSection.classList.remove("collapsed");
    elements.toggleSetup.textContent = "Minimize setup";
    elements.toggleSetup.setAttribute("aria-expanded", "true");
  }

  if (state.ui.bindingsCollapsed) {
    elements.bindingsSection.classList.add("collapsed");
    elements.toggleBindings.textContent = "Expand bindings";
    elements.toggleBindings.setAttribute("aria-expanded", "false");
  } else {
    elements.bindingsSection.classList.remove("collapsed");
    elements.toggleBindings.textContent = "Minimize bindings";
    elements.toggleBindings.setAttribute("aria-expanded", "true");
  }

  for (const action of ACTION_CATALOG) {
    const input = bindingInputByAction.get(action.id);
    if (!input) {
      continue;
    }

    const sequence = state.config.bindings[action.id] || [];
    input.value = formatSequence(sequence);
    input.classList.remove("invalid");
  }

  renderImportedBindings();

  if (!state.parseMeta) {
    elements.parseSummary.textContent = state.ui.setupCollapsed
      ? `Using ${state.config.prefix} prefix. Setup is minimized - expand to edit bindings.`
      : "Using current saved bindings (or defaults if none saved).";
    return;
  }

  const warningSuffix =
    state.parseMeta.warnings && state.parseMeta.warnings.length > 0
      ? ` ${state.parseMeta.warnings.length} warning(s) found.`
      : "";

  const summary = `Imported prefix ${state.config.prefix}. Recognized ${state.parseMeta.recognizedCount} binding line(s), ignored ${state.parseMeta.ignoredCount}.${warningSuffix}`;
  elements.parseSummary.textContent = state.ui.setupCollapsed
    ? `${summary} Setup is minimized - expand if you want to adjust bindings.`
    : summary;
}

function renderImportedBindings() {
  const imported =
    state.parseMeta && Array.isArray(state.parseMeta.importedBindings)
      ? state.parseMeta.importedBindings
      : [];

  elements.importedBindingList.textContent = "";

  if (imported.length === 0) {
    const emptyItem = document.createElement("li");
    emptyItem.className = "imported-empty";
    emptyItem.textContent = "No recognized binding lines imported yet.";
    elements.importedBindingList.append(emptyItem);
    return;
  }

  for (const item of imported) {
    const row = document.createElement("li");
    row.className = "imported-item";

    const line = document.createElement("code");
    line.textContent = item.line;

    const description = document.createElement("span");
    description.className = "imported-description";
    description.textContent = `${item.description} (${formatSequence(item.sequence)})`;

    row.append(line, description);
    elements.importedBindingList.append(row);
  }
}

function nextChallenge() {
  if (state.practice.queue.length === 0) {
    state.practice.queue = shuffle(ACTION_CATALOG.map((action) => action.id));
  }

  state.practice.currentActionId = state.practice.queue.shift();
  state.practice.captured = [];
  state.practice.hintLevel = 0;
  state.practice.revealed = false;
  state.practice.result = null;

  renderPracticeSection();
}

function renderPracticeSection() {
  renderChallenge();
  renderCapturedSequence();
  renderHint();
  renderResult();
  renderStats();
}

function renderChallenge() {
  const action = actionById[state.practice.currentActionId];
  if (!action) {
    elements.challengeText.textContent = "No challenge available.";
    elements.challengeSubtext.textContent = "";
    return;
  }

  const mnemonicKey = getMnemonicKeyForAction(action.id);
  const parts = buildMnemonicLabelParts(action.label, mnemonicKey, state.ui.mnemonicMode);

  elements.challengeText.textContent = "";

  elements.challengeText.append(document.createTextNode(parts.before));

  if (parts.hit) {
    const mnemonic = document.createElement("span");
    mnemonic.className = "mnemonic-hit";
    mnemonic.textContent = parts.hit;
    elements.challengeText.append(mnemonic);
    elements.challengeText.append(document.createTextNode(parts.after));
  }

  if (!parts.hit) {
    elements.challengeText.append(document.createTextNode(parts.after));
  }

  if (state.ui.mnemonicMode && parts.hit) {
    elements.challengeSubtext.textContent = `Mnemonic mode is on. Highlighted letter links to the command key.`;
  } else if (state.ui.mnemonicMode) {
    elements.challengeSubtext.textContent = "Mnemonic mode is on. No letter cue available for this challenge.";
  } else {
    elements.challengeSubtext.textContent = `Command target: ${action.command}`;
  }
}

function renderCapturedSequence() {
  if (state.practice.captured.length === 0) {
    elements.capturedSequence.textContent = "(nothing captured)";
    return;
  }

  elements.capturedSequence.textContent = formatSequence(state.practice.captured);
}

function submitAttempt() {
  const expected = getExpectedSequence();
  const entered = [...state.practice.captured];

  if (expected.length === 0 || entered.length === 0) {
    return;
  }

  const isCorrect = areSequencesEqual(entered, expected);
  state.practice.attempts += 1;

  if (isCorrect) {
    state.practice.correct += 1;
    state.practice.streak += 1;
    const action = actionById[state.practice.currentActionId];
    state.practice.result = {
      type: "ok",
      message: `Correct. ${formatSequence(entered)} runs ${action.label.toLowerCase()}.`
    };
  } else {
    state.practice.streak = 0;
    const mappedActionId = getMappedActionForSequence(entered, state.keyMapIndex);

    if (mappedActionId && mappedActionId !== state.practice.currentActionId) {
      state.practice.result = {
        type: "bad",
        message: `Incorrect. You entered ${formatSequence(entered)}, which maps to ${actionById[mappedActionId].label.toLowerCase()}.`
      };
    } else {
      state.practice.result = {
        type: "bad",
        message: `Incorrect. You entered ${formatSequence(entered)}. That sequence is not mapped to a known core action in your current config.`
      };
    }
  }

  renderResult(true);
  renderStats();
}

function showHint() {
  const expected = getExpectedSequence();
  if (expected.length === 0) {
    return;
  }

  state.practice.hintLevel += 1;
  if (state.practice.hintLevel > 3) {
    state.practice.hintLevel = 3;
  }

  renderHint();
}

function revealAnswer() {
  const expected = getExpectedSequence();
  if (expected.length === 0) {
    return;
  }

  if (!state.practice.revealed) {
    state.practice.skipped += 1;
    state.practice.streak = 0;
    state.practice.revealed = true;
  }

  state.practice.result = {
    type: "reveal",
    message: `Reveal: ${formatSequence(expected)}.`
  };

  renderResult(true);
  renderStats();
}

function clearCapture() {
  state.practice.captured = [];
  renderCapturedSequence();
}

function clearResultAndHint() {
  state.practice.result = null;
  state.practice.hintLevel = 0;
  renderHint();
  renderResult();
}

function renderHint() {
  const expected = getExpectedSequence();
  if (expected.length === 0 || state.practice.hintLevel === 0) {
    elements.hintText.textContent = "";
    return;
  }

  if (state.practice.hintLevel === 1) {
    elements.hintText.textContent =
      expected.length > 1
        ? `Hint: Start with your prefix (${expected[0]}).`
        : `Hint: The key starts with ${expected[0]}.`;
    return;
  }

  if (state.practice.hintLevel === 2 && expected.length > 1) {
    elements.hintText.textContent = `Hint: Then press ${expected[1]}.`;
    return;
  }

  elements.hintText.textContent = `Hint: Full sequence is ${formatSequence(expected)}.`;
}

function renderResult(withFlash = false) {
  const result = state.practice.result;
  if (!result) {
    elements.resultBox.textContent = "";
    elements.resultBox.className = "result";
    return;
  }

  elements.resultBox.textContent = "";
  const row = document.createElement("div");
  row.className = "result-row";

  const icon = document.createElement("span");
  icon.className = `result-icon ${result.type}`;
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = getResultIconText(result.type);

  const message = document.createElement("span");
  message.className = "result-message";
  message.textContent = result.message;

  row.append(icon, message);
  elements.resultBox.append(row);
  elements.resultBox.className = `result ${result.type}`;

  if (withFlash) {
    elements.resultBox.classList.add("flash");
    setTimeout(() => elements.resultBox.classList.remove("flash"), 380);
  }
}

function getResultIconText(type) {
  if (type === "ok") {
    return "OK";
  }

  if (type === "bad") {
    return "NO";
  }

  return "SHOW";
}

function renderStats() {
  const attempts = state.practice.attempts;
  const correct = state.practice.correct;
  const accuracy = attempts === 0 ? 0 : Math.round((correct / attempts) * 100);

  elements.stats.textContent = `Attempts: ${attempts} | Correct: ${correct} | Accuracy: ${accuracy}% | Streak: ${state.practice.streak} | Skipped: ${state.practice.skipped} | Remaining in round: ${state.practice.queue.length}`;
}

function getExpectedSequence() {
  const actionId = state.practice.currentActionId;
  if (!actionId) {
    return [];
  }

  if (Array.isArray(state.config.bindings[actionId])) {
    return state.config.bindings[actionId];
  }

  const fallback = getDefaultBindings(state.config.prefix)[actionId];
  return Array.isArray(fallback) ? fallback : [];
}

function getMnemonicKeyForAction(actionId) {
  const sequence = state.config.bindings[actionId] || [];
  if (!Array.isArray(sequence) || sequence.length === 0) {
    return "";
  }

  const finalStep = sequence[sequence.length - 1];
  if (typeof finalStep !== "string") {
    return "";
  }

  if (/^[a-z]$/i.test(finalStep)) {
    return finalStep;
  }

  return "";
}

function comboFromKeyboardEvent(event) {
  const key = normalizeEventKey(event);
  if (!key) {
    return "";
  }

  const parts = [];
  if (event.ctrlKey) {
    parts.push("Ctrl");
  }
  if (event.altKey) {
    parts.push("Alt");
  }
  if (event.shiftKey && shouldIncludeShift(event, key)) {
    parts.push("Shift");
  }
  if (event.metaKey) {
    parts.push("Meta");
  }
  parts.push(key);

  return parseSequenceString(parts.join("+"))[0] || "";
}

function shouldIncludeShift(event, key) {
  if (!event.shiftKey) {
    return false;
  }

  if (/^[a-z]$/i.test(key)) {
    return false;
  }

  if (key.length === 1 && /[^a-z0-9]/i.test(key)) {
    return false;
  }

  return true;
}

function normalizeEventKey(event) {
  const key = event.key;
  if (!key) {
    return "";
  }

  if (["Control", "Shift", "Alt", "Meta"].includes(key)) {
    return "";
  }

  if (key === " ") {
    return "Space";
  }

  if (key.length === 1) {
    return /^[A-Z]$/.test(key) ? key.toLowerCase() : key;
  }

  const aliases = {
    Esc: "Escape",
    ArrowUp: "ArrowUp",
    ArrowDown: "ArrowDown",
    ArrowLeft: "ArrowLeft",
    ArrowRight: "ArrowRight"
  };

  return aliases[key] || key;
}

function shuffle(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[swapIndex]] = [copy[swapIndex], copy[index]];
  }
  return copy;
}
