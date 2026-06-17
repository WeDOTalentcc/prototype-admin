import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// tailwind-merge não conhece os tokens font-size customizados deste projeto
// (definidos em tailwind.config.ts theme.extend.fontSize). Sem esse registro,
// `text-micro` e cia são tratados como "unknown text-*" e podem conflitar
// incorretamente com classes text-color (text-status-success, text-lia-text-*),
// causando remoção do font-size no merge — resultado: badges herdam font-size
// do ancestral em vez de renderizar em 11px (text-micro).
//
// Sintoma observado: badge "Manual" em TemplatesTab renderizava com fonte grande
// ao receber color override do TRIGGER_TYPE_LABELS (2026-05-25).
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [{ text: ["micro", "xs", "sm-ui", "base-ui"] }],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
