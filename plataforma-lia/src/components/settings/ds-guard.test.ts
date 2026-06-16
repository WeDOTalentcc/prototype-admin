/**
 * ds-guard.test.ts — Guard anti-regressão do Design System nos painéis de Configurações.
 *
 * POR QUE: desvios de DS em `src/components/settings/` são recorrentes — um painel
 * novo reintroduz `rounded-xl` num campo, sobrescreve o raio do `<Button>`, ou usa
 * cor crua do Tailwind onde existe token. Este teste é a trava automatizada que
 * FALHA o `pnpm test` quando um desses anti-padrões NOVO aparece, sem precisar
 * corrigir as ocorrências legadas primeiro (essas vivem no baseline e são
 * remediadas pelas tarefas T3–T7).
 *
 * MECANISMO: ratchet por baseline (padrão já usado no repo, ex.: audit baselines).
 *   - Conta violações por (arquivo, regra).
 *   - Compara com `ds-guard.baseline.json`.
 *   - FALHA se a contagem de qualquer (arquivo, regra) EXCEDER o baseline
 *     (= regressão nova) — imune a mudança de número de linha.
 *   - FALHA se o baseline tiver entradas obsoletas (count caiu abaixo do baseline)
 *     para forçar o ratchet a apertar conforme a remediação avança.
 *
 * Por que NÃO ESLint: a flat config (`eslint.config.mjs`) só permite `warn`
 * (nunca falha o CI numa regressão) ou `error` (quebra já nas ~50 violações
 * legadas, antes da remediação); não há baseline per-rule. Além disso, um bloco
 * `no-restricted-syntax` escopado a settings SUBSTITUI (não mescla) os seletores
 * DS globais para esses arquivos. O ratchet via Vitest atende "falha quando
 * reintroduz" sem quebrar antes da remediação.
 *
 * COMO RODAR:
 *   pnpm test                       # roda junto do projeto unit-colocated
 *   pnpm test:ds-settings           # roda só este guard
 *
 * COMO ATUALIZAR O BASELINE (após remediar ou ao adicionar exceção em massa):
 *   pnpm test:ds-settings:update    # regrava ds-guard.baseline.json
 *
 * COMO SUPRIMIR UMA EXCEÇÃO LEGÍTIMA (ex.: paleta de gráfico/chart):
 *   Adicione o comentário `ds-guard-ignore` na MESMA linha da ocorrência.
 *   Linhas com esse marcador são ignoradas pelo scanner.
 */
import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { extname, join, relative } from "node:path";

import { describe, expect, it } from "vitest";

const SETTINGS_ROOT = join(__dirname);
const BASELINE_PATH = join(__dirname, "ds-guard.baseline.json");
const IGNORE_MARKER = "ds-guard-ignore";

type RuleId =
  | "field-rounded-override"
  | "button-rounded-override"
  | "raw-tailwind-color";

interface Rule {
  id: RuleId;
  description: string;
}

const RULES: Record<RuleId, Rule> = {
  "field-rounded-override": {
    id: "field-rounded-override",
    description:
      "input/textarea/select/checkbox não pode usar rounded-lg/rounded-xl — use rounded-md (ou rounded-sm).",
  },
  "button-rounded-override": {
    id: "button-rounded-override",
    description:
      "<Button> nunca sobrescreve o raio (rounded-lg/rounded-xl proibido no className) — as variantes já resolvem rounded-md.",
  },
  "raw-tailwind-color": {
    id: "raw-tailwind-color",
    description:
      "Cor crua do Tailwind (bg-/text-/border- com amber/emerald/purple/blue/red) onde há token — use status-* ou wedo-*.",
  },
};

const FIELD_TAGS = ["input", "textarea", "select", "Input", "Textarea", "Select", "Checkbox"];
const ROUNDED_OVERRIDE = /\brounded-(lg|xl)\b/;
const RAW_COLOR = /\b(bg|text|border)-(amber|emerald|purple|blue|red)-\d{2,3}\b/g;

/** Walk all .ts/.tsx source files under settings/, skipping tests, stories, backups. */
function* walkSourceFiles(dir: string): Generator<string> {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".")) continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walkSourceFiles(full);
      continue;
    }
    if (!entry.isFile()) continue;
    const ext = extname(entry.name);
    if (ext !== ".ts" && ext !== ".tsx") continue;
    if (/\.(test|spec|stories)\.[tj]sx?$/.test(entry.name)) continue;
    yield full;
  }
}

/**
 * Extract the opening tag text starting at `start` (pointing at `<`), tracking
 * brace depth + quote state so arrow functions (`=>`) and `{...}` props don't
 * truncate the tag prematurely. Returns the opening-tag substring up to its `>`.
 */
function extractOpeningTag(source: string, start: number): string {
  let depth = 0;
  let quote: string | null = null;
  for (let i = start; i < source.length; i++) {
    const ch = source[i];
    if (quote) {
      if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === "`") {
      quote = ch;
      continue;
    }
    if (ch === "{") depth++;
    else if (ch === "}") depth--;
    else if (ch === ">" && depth === 0) {
      return source.slice(start, i + 1);
    }
  }
  return source.slice(start);
}

/** Lines carrying the ignore marker (1-indexed set). */
function ignoredLines(source: string): Set<number> {
  const set = new Set<number>();
  source.split("\n").forEach((line, idx) => {
    if (line.includes(IGNORE_MARKER)) set.add(idx + 1);
  });
  return set;
}

function lineAt(source: string, index: number): number {
  let line = 1;
  for (let i = 0; i < index && i < source.length; i++) {
    if (source[i] === "\n") line++;
  }
  return line;
}

function scanFile(source: string): Record<RuleId, number> {
  const counts: Record<RuleId, number> = {
    "field-rounded-override": 0,
    "button-rounded-override": 0,
    "raw-tailwind-color": 0,
  };
  const ignored = ignoredLines(source);

  // Element-scoped checks: walk every JSX opening tag of interest.
  const tagStart = /<([A-Za-z][A-Za-z0-9]*)/g;
  let m: RegExpExecArray | null;
  while ((m = tagStart.exec(source))) {
    const tagName = m[1];
    const isField = FIELD_TAGS.includes(tagName);
    const isButton = tagName === "Button";
    if (!isField && !isButton) continue;
    if (ignored.has(lineAt(source, m.index))) continue;
    const openingTag = extractOpeningTag(source, m.index);
    if (!ROUNDED_OVERRIDE.test(openingTag)) continue;
    if (isButton) counts["button-rounded-override"]++;
    else counts["field-rounded-override"]++;
  }

  // File-wide check: raw Tailwind palette colors with a token equivalent.
  let c: RegExpExecArray | null;
  RAW_COLOR.lastIndex = 0;
  while ((c = RAW_COLOR.exec(source))) {
    if (ignored.has(lineAt(source, c.index))) continue;
    counts["raw-tailwind-color"]++;
  }

  return counts;
}

type Baseline = Record<string, Partial<Record<RuleId, number>>>;

function buildCurrentCounts(): Baseline {
  const result: Baseline = {};
  for (const file of walkSourceFiles(SETTINGS_ROOT)) {
    const source = readFileSync(file, "utf-8");
    const counts = scanFile(source);
    const rel = relative(SETTINGS_ROOT, file).split("\\").join("/");
    const entry: Partial<Record<RuleId, number>> = {};
    for (const id of Object.keys(counts) as RuleId[]) {
      if (counts[id] > 0) entry[id] = counts[id];
    }
    if (Object.keys(entry).length > 0) result[rel] = entry;
  }
  return result;
}

function loadBaseline(): Baseline {
  if (!existsSync(BASELINE_PATH)) return {};
  return JSON.parse(readFileSync(BASELINE_PATH, "utf-8")) as Baseline;
}

const UPDATE = process.env.UPDATE_DS_GUARD_BASELINE === "1";

describe("DS guard — Configurações (anti-regressão)", () => {
  const current = buildCurrentCounts();

  if (UPDATE) {
    it("regrava o baseline (UPDATE_DS_GUARD_BASELINE=1)", () => {
      const sorted: Baseline = {};
      for (const file of Object.keys(current).sort()) sorted[file] = current[file];
      writeFileSync(BASELINE_PATH, JSON.stringify(sorted, null, 2) + "\n", "utf-8");
      expect(existsSync(BASELINE_PATH)).toBe(true);
    });
    return;
  }

  const baseline = loadBaseline();

  it("não introduz NOVAS violações de DS além do baseline", () => {
    const regressions: string[] = [];
    for (const [file, rules] of Object.entries(current)) {
      for (const [id, count] of Object.entries(rules) as [RuleId, number][]) {
        const allowed = baseline[file]?.[id] ?? 0;
        if (count > allowed) {
          regressions.push(
            `  ✗ ${file} [${id}] ${count} > baseline ${allowed}\n    ${RULES[id].description}`,
          );
        }
      }
    }
    expect(
      regressions,
      regressions.length
        ? `\nNOVAS violações de Design System em src/components/settings/:\n\n${regressions.join(
            "\n",
          )}\n\nCorrija a ocorrência, ou — se for exceção legítima (ex.: paleta de gráfico) — ` +
            `adicione o comentário "${IGNORE_MARKER}" na mesma linha. ` +
            `Para regravar o baseline após remediação: pnpm test:ds-settings:update.\n`
        : undefined,
    ).toEqual([]);
  });

  it("mantém o baseline apertado (sem entradas obsoletas)", () => {
    const stale: string[] = [];
    for (const [file, rules] of Object.entries(baseline)) {
      for (const [id, allowed] of Object.entries(rules) as [RuleId, number][]) {
        const count = current[file]?.[id] ?? 0;
        if (count < allowed) {
          stale.push(`  • ${file} [${id}] agora ${count} < baseline ${allowed}`);
        }
      }
    }
    expect(
      stale,
      stale.length
        ? `\nO baseline ficou folgado (violações foram removidas). Aperte o ratchet:\n\n${stale.join(
            "\n",
          )}\n\nRode: pnpm test:ds-settings:update\n`
        : undefined,
    ).toEqual([]);
  });
});
