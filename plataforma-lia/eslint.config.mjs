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
        ],
        "patterns": [
          {
            "group": ["@/components/_wedo_internal/**", "**/_wedo_internal/**"],
            "message": "[WeDo Staff Area] Components em _wedo_internal/ são da área provisória staff WeDOTalent e NÃO devem ser importados do produto. Acessível apenas via route group (staff)/. Plan: ~/.claude/plans/jolly-roaming-moler.md"
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
      },
      {
        "selector": "JSXElement[openingElement.name.name='button'] JSXElement[openingElement.name.name='button']",
        "message": "[a11y/hydration] <button> nao pode conter outro <button> (HTML invalido -> hydration mismatch). Use <div role='button' tabIndex={0} onClick onKeyDown> no container externo, ou mova o botao interno pra fora. Auditoria 2026-06-03 (#7 WsiQuestionsPanel)."
      }
    ],
  },
}, ...storybook.configs["flat/recommended"]];

export default eslintConfig;
