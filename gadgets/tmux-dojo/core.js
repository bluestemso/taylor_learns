export const DEFAULT_PREFIX = "Ctrl+b";

export const ACTION_CATALOG = [
  { id: "new-window", label: "Create a new window", command: "new-window" },
  { id: "next-window", label: "Switch to next window", command: "next-window" },
  { id: "prev-window", label: "Switch to previous window", command: "previous-window" },
  { id: "split-horizontal", label: "Split pane top/bottom", command: "split-window" },
  { id: "split-vertical", label: "Split pane left/right", command: "split-window -h" },
  { id: "close-pane", label: "Close current pane", command: "kill-pane" },
  { id: "detach-session", label: "Detach without killing session", command: "detach-client" },
  { id: "rename-window", label: "Rename current window", command: "rename-window" },
  { id: "list-sessions", label: "List tmux sessions", command: "list-sessions" }
];

const ACTION_BY_ID = Object.fromEntries(ACTION_CATALOG.map((action) => [action.id, action]));

const DEFAULT_ACTION_KEYS = {
  "new-window": "c",
  "next-window": "n",
  "prev-window": "p",
  "split-horizontal": '"',
  "split-vertical": "%",
  "close-pane": "x",
  "detach-session": "d",
  "rename-window": ",",
  "list-sessions": "s"
};

const MODIFIER_ORDER = ["Ctrl", "Alt", "Shift", "Meta"];

const MODIFIER_ALIASES = {
  c: "Ctrl",
  ctrl: "Ctrl",
  control: "Ctrl",
  m: "Alt",
  alt: "Alt",
  meta: "Meta",
  cmd: "Meta",
  command: "Meta",
  s: "Shift",
  shift: "Shift"
};

const KEY_ALIASES = {
  space: "Space",
  spacebar: "Space",
  bspace: "Backspace",
  backspace: "Backspace",
  del: "Delete",
  delete: "Delete",
  return: "Enter",
  enter: "Enter",
  esc: "Escape",
  escape: "Escape",
  pgup: "PageUp",
  pgdn: "PageDown",
  pageup: "PageUp",
  pagedown: "PageDown",
  up: "ArrowUp",
  down: "ArrowDown",
  left: "ArrowLeft",
  right: "ArrowRight"
};

export function getDefaultBindings(prefix = DEFAULT_PREFIX) {
  const normalizedPrefix = normalizeComboString(prefix) || DEFAULT_PREFIX;
  const bindings = {};

  for (const action of ACTION_CATALOG) {
    const key = DEFAULT_ACTION_KEYS[action.id];
    if (key) {
      bindings[action.id] = [normalizedPrefix, key];
    }
  }

  return bindings;
}

export function parseTmuxConfig(configText) {
  const text = typeof configText === "string" ? configText : "";
  let prefix = DEFAULT_PREFIX;
  const bindings = {};
  const importedBindings = [];
  let recognizedCount = 0;
  let ignoredCount = 0;
  const warnings = [];

  for (const rawLine of text.split(/\r?\n/)) {
    const line = stripInlineComment(rawLine).trim();
    if (!line) {
      continue;
    }

    const tokens = tokenizeLine(line);
    if (tokens.length === 0) {
      continue;
    }

    const head = tokens[0].toLowerCase();

    if (head === "set" || head === "set-option") {
      const prefixIndex = tokens.findIndex((token) => token.toLowerCase() === "prefix");
      if (prefixIndex !== -1 && prefixIndex < tokens.length - 1) {
        const parsedPrefix = normalizeComboString(tokens[prefixIndex + 1]);
        if (parsedPrefix) {
          prefix = parsedPrefix;
        } else {
          warnings.push(`Could not parse prefix value: ${tokens[prefixIndex + 1]}`);
        }
      }
      continue;
    }

    if (head === "bind" || head === "bind-key") {
      const binding = parseBinding(tokens, prefix, line);
      if (binding && binding.actionId && binding.sequence.length > 0) {
        bindings[binding.actionId] = binding.sequence;
        importedBindings.push({
          line: binding.line,
          actionId: binding.actionId,
          description: ACTION_BY_ID[binding.actionId]?.label || binding.actionId,
          sequence: binding.sequence
        });
        recognizedCount += 1;
      } else {
        ignoredCount += 1;
      }
      continue;
    }

    ignoredCount += 1;
  }

  return {
    prefix,
    bindings,
    importedBindings,
    recognizedCount,
    ignoredCount,
    warnings
  };
}

export function parseSequenceString(value) {
  if (typeof value !== "string") {
    return [];
  }

  const pieces = value
    .split(/\s*(?:then|->)+\s*/i)
    .map((piece) => normalizeComboString(piece))
    .filter(Boolean);

  return pieces;
}

export function formatSequence(sequence) {
  if (!Array.isArray(sequence) || sequence.length === 0) {
    return "";
  }

  return sequence.map((step) => normalizeComboString(step) || step).join(" then ");
}

export function areSequencesEqual(left, right) {
  return sequenceToId(left) === sequenceToId(right);
}

export function sequenceToId(sequence) {
  if (!Array.isArray(sequence)) {
    return "";
  }

  return sequence
    .map((step) => normalizeComboString(step))
    .filter(Boolean)
    .join(" > ");
}

export function buildKeyMapIndex(bindings) {
  const index = {};
  const source = bindings && typeof bindings === "object" ? bindings : {};

  for (const [actionId, sequence] of Object.entries(source)) {
    const key = sequenceToId(sequence);
    if (key) {
      index[key] = actionId;
    }
  }

  return index;
}

export function getMappedActionForSequence(sequence, keyMapIndex) {
  const key = sequenceToId(sequence);
  if (!key) {
    return null;
  }

  return keyMapIndex && keyMapIndex[key] ? keyMapIndex[key] : null;
}

export function buildMnemonicLabelParts(label, mnemonicKey, enabled = true) {
  const safeLabel = typeof label === "string" ? label : "";
  if (!enabled) {
    return {
      before: safeLabel,
      hit: "",
      after: ""
    };
  }

  if (typeof mnemonicKey !== "string" || !/^[a-z]$/i.test(mnemonicKey)) {
    return {
      before: safeLabel,
      hit: "",
      after: ""
    };
  }

  const index = safeLabel.toLowerCase().indexOf(mnemonicKey.toLowerCase());
  if (index === -1) {
    return {
      before: safeLabel,
      hit: "",
      after: ""
    };
  }

  return {
    before: safeLabel.slice(0, index),
    hit: safeLabel[index],
    after: safeLabel.slice(index + 1)
  };
}

function parseBinding(tokens, prefix, line) {
  let index = 1;
  let noPrefix = false;
  let table = "";

  while (index < tokens.length && tokens[index].startsWith("-")) {
    const option = tokens[index];

    if (option === "-n") {
      noPrefix = true;
      index += 1;
      continue;
    }

    if (option === "-T" || option === "-t" || option === "-N") {
      if (index + 1 < tokens.length) {
        if (option === "-T") {
          table = tokens[index + 1].toLowerCase();
        }
        index += 2;
      } else {
        index += 1;
      }
      continue;
    }

    index += 1;
  }

  if (index >= tokens.length) {
    return null;
  }

  const key = normalizeComboString(tokens[index]);
  if (!key) {
    return null;
  }

  const command = tokens.slice(index + 1).join(" ").trim();
  if (!command) {
    return null;
  }

  const actionId = mapCommandToAction(command);
  if (!actionId) {
    return null;
  }

  const normalizedPrefix = normalizeComboString(prefix) || DEFAULT_PREFIX;
  const usesPrefix = !noPrefix && table !== "root";

  return {
    line,
    actionId,
    sequence: usesPrefix ? [normalizedPrefix, key] : [key]
  };
}

function mapCommandToAction(command) {
  const normalized = command.toLowerCase().trim();
  const first = normalized.split(/\s+/)[0] || "";

  if (isAlias(first, ["new-window", "neww"])) {
    return "new-window";
  }

  if (isAlias(first, ["next-window", "next"])) {
    return "next-window";
  }

  if (isAlias(first, ["previous-window", "prev-window", "prev"])) {
    return "prev-window";
  }

  if (isAlias(first, ["split-window", "splitw"])) {
    if (/\s-h(\s|$)|\s+-h\b/.test(normalized)) {
      return "split-vertical";
    }
    return "split-horizontal";
  }

  if (isAlias(first, ["kill-pane", "killp"])) {
    return "close-pane";
  }

  if (isAlias(first, ["detach-client", "detach"])) {
    return "detach-session";
  }

  if (isAlias(first, ["rename-window", "renamew"])) {
    return "rename-window";
  }

  if (isAlias(first, ["list-sessions", "ls"])) {
    return "list-sessions";
  }

  if (first === "choose-tree" && /(^|\s)-s(\s|$)/.test(normalized)) {
    return "list-sessions";
  }

  return null;
}

function isAlias(value, aliases) {
  return aliases.includes(value.replace(/;$/, ""));
}

function stripInlineComment(line) {
  let inSingle = false;
  let inDouble = false;
  let output = "";

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];

    if (char === "'" && !inDouble) {
      inSingle = !inSingle;
      output += char;
      continue;
    }

    if (char === '"' && !inSingle) {
      inDouble = !inDouble;
      output += char;
      continue;
    }

    if (char === "#" && !inSingle && !inDouble) {
      break;
    }

    output += char;
  }

  return output;
}

function tokenizeLine(line) {
  const matches = line.match(/"[^"]*"|'[^']*'|\S+/g);
  if (!matches) {
    return [];
  }

  return matches.map((token) => stripWrappingQuotes(token));
}

function stripWrappingQuotes(value) {
  if (!value) {
    return "";
  }

  const startsWithQuote = value.startsWith("\"") || value.startsWith("'");
  const endsWithQuote = value.endsWith("\"") || value.endsWith("'");

  if (startsWithQuote && endsWithQuote && value.length >= 2) {
    return value.slice(1, -1);
  }

  return value;
}

function normalizeComboString(value) {
  if (typeof value !== "string") {
    return "";
  }

  const raw = stripWrappingQuotes(value).trim();
  if (!raw) {
    return "";
  }

  if (raw.includes("+")) {
    return normalizePlusDelimitedCombo(raw);
  }

  if (/^[CMS]-/i.test(raw)) {
    return normalizeTmuxStyleCombo(raw);
  }

  return normalizeKey(raw);
}

function normalizePlusDelimitedCombo(raw) {
  const parts = raw.split("+").map((piece) => piece.trim()).filter(Boolean);
  if (parts.length === 0) {
    return "";
  }

  let baseKey = "";
  const modifiers = [];

  for (const part of parts) {
    const modifier = MODIFIER_ALIASES[part.toLowerCase()];
    if (modifier) {
      modifiers.push(modifier);
    } else {
      baseKey = normalizeKey(part);
    }
  }

  if (!baseKey) {
    baseKey = normalizeKey(parts[parts.length - 1]);
  }

  const orderedModifiers = orderModifiers(modifiers);
  return [...orderedModifiers, baseKey].join("+");
}

function normalizeTmuxStyleCombo(raw) {
  const parts = raw.split("-").map((part) => part.trim()).filter(Boolean);
  if (parts.length === 0) {
    return "";
  }

  const basePart = parts[parts.length - 1];
  const modifiers = parts
    .slice(0, -1)
    .map((part) => MODIFIER_ALIASES[part.toLowerCase()])
    .filter(Boolean);

  const baseKey = normalizeKey(basePart);
  const orderedModifiers = orderModifiers(modifiers);

  if (orderedModifiers.length === 0) {
    return baseKey;
  }

  return [...orderedModifiers, baseKey].join("+");
}

function normalizeKey(raw) {
  if (!raw) {
    return "";
  }

  const cleaned = raw.trim();
  const lower = cleaned.toLowerCase();

  if (KEY_ALIASES[lower]) {
    return KEY_ALIASES[lower];
  }

  if (cleaned.length === 1) {
    if (/^[A-Z]$/.test(cleaned)) {
      return cleaned.toLowerCase();
    }
    return cleaned;
  }

  if (/^f\d{1,2}$/i.test(cleaned)) {
    return cleaned.toUpperCase();
  }

  return cleaned;
}

function orderModifiers(modifiers) {
  const unique = [...new Set(modifiers)];
  unique.sort((left, right) => MODIFIER_ORDER.indexOf(left) - MODIFIER_ORDER.indexOf(right));
  return unique;
}
