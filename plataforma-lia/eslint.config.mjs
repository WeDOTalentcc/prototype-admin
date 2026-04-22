// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import storybook from "eslint-plugin-storybook";

import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [...compat.extends("next/core-web-vitals", "next/typescript"), {
  languageOptions: {
    parserOptions: {
      warnOnUnsupportedTypeScriptVersion: false,
    },
  },
  rules: {
    "@typescript-eslint/no-unused-vars": "off",
    "@typescript-eslint/no-explicit-any": "off",
    "react/no-unescaped-entities": "off",
    "@next/next/no-img-element": "off",
    "jsx-a11y/alt-text": "off",
    // Ignorar conflitos de tipos entre HTML events e motion events
    "@typescript-eslint/ban-ts-comment": "off",
    // ──────────────────────────────────────────────
    // WeDo DS — Regras de enforçamento de tokens
    // Sprint 10: prevenir regressões de padronização
    // ──────────────────────────────────────────────
    "no-restricted-imports": [
      "warn",
      {
        "paths": [
          {
            "name": "@/components/ui/badge",
            "message": "[WeDo DS] Use o componente canônico `Chip` (`@/components/ui/chip`) para pílulas de status/estado. O `Badge` primitivo está mantido apenas para affordances do tipo chip-com-botão (raro). Veja docs/design-system/00-design-system-v4.md § 3.39."
          }
        ]
      }
    ],
    "no-restricted-syntax": [
      "warn",
      {
        "selector": "JSXAttribute[name.name='className'][value.value=/transition-all/]",
        "message": "[WeDo DS] Use transition-colors, transition-opacity ou transition-transform em vez de transition-all"
      },
      {
        "selector": "JSXAttribute[name.name='className'][value.value=/rounded-2xl/]",
        "message": "[WeDo DS] rounded-2xl não é canônico. Use rounded-xl (cards/modais) ou rounded-lg (inputs)"
      },
      {
        "selector": "JSXAttribute[name.name='className'][value.value=/text-wedo-apoio/]",
        "message": "[WeDo DS] Token wedo-apoio-* está deprecated. Use tokens lia-* ou status-* equivalentes"
      },
      {
        "selector": "JSXAttribute[name.name='className'][value.value=/bg-wedo-apoio/]",
        "message": "[WeDo DS] Token wedo-apoio-* está deprecated. Use tokens lia-* ou status-* equivalentes"
      }
    ],
  },
}, {
  // ──────────────────────────────────────────────
  // Task #801 (C4/sensor): proibir `fetch()` cru em hooks/components.
  // Toda chamada deve ir por `liaApi.*` ou por `fetchWithRetry` para herdar
  // retry, timeout e o wrapping HttpError(transientNetworkError) — sem isso
  // erros de rede transientes (cold-start, HMR) zeram listas e disparam o
  // dev-overlay. Allowlist: services/lia-api/**, app/api/**, tests, próprio
  // base.ts.
  // ──────────────────────────────────────────────
  files: ["src/hooks/**/*.{ts,tsx}", "src/components/**/*.{ts,tsx}"],
  ignores: [
    "src/services/lia-api/**",
    "src/app/api/**",
    "**/__tests__/**",
    "**/*.test.ts",
    "**/*.test.tsx",
    "**/*.spec.ts",
    "**/*.spec.tsx",
  ],
  rules: {
    "no-restricted-syntax": [
      "warn",
      // Re-declara as regras DS para não sobrescrevê-las neste escopo
      // (flat config: o último bloco match vence, então precisamos repetir).
      {
        "selector": "JSXAttribute[name.name='className'][value.value=/transition-all/]",
        "message": "[WeDo DS] Use transition-colors, transition-opacity ou transition-transform em vez de transition-all"
      },
      {
        "selector": "JSXAttribute[name.name='className'][value.value=/rounded-2xl/]",
        "message": "[WeDo DS] rounded-2xl não é canônico. Use rounded-xl (cards/modais) ou rounded-lg (inputs)"
      },
      {
        "selector": "JSXAttribute[name.name='className'][value.value=/text-wedo-apoio/]",
        "message": "[WeDo DS] Token wedo-apoio-* está deprecated. Use tokens lia-* ou status-* equivalentes"
      },
      {
        "selector": "JSXAttribute[name.name='className'][value.value=/bg-wedo-apoio/]",
        "message": "[WeDo DS] Token wedo-apoio-* está deprecated. Use tokens lia-* ou status-* equivalentes"
      },
      // Task #801: bare `fetch(...)`
      {
        "selector": "CallExpression[callee.type='Identifier'][callee.name='fetch']",
        "message": "[Task #801] Não use `fetch()` cru em hooks/components — use `liaApi.*` ou `fetchWithRetry` (services/lia-api/base) para herdar retry, timeout e HttpError(transientNetworkError). Veja CLAUDE.md § HMR-resilience."
      },
      // Task #801: `window.fetch(...)` / `globalThis.fetch(...)` / `self.fetch(...)`
      {
        "selector": "CallExpression[callee.type='MemberExpression'][callee.property.name='fetch'][callee.object.name=/^(window|globalThis|self)$/]",
        "message": "[Task #801] Não use `window.fetch()` cru em hooks/components — use `liaApi.*` ou `fetchWithRetry` (services/lia-api/base). Veja CLAUDE.md § HMR-resilience."
      }
    ],
  },
}, ...storybook.configs["flat/recommended"]];

export default eslintConfig;
