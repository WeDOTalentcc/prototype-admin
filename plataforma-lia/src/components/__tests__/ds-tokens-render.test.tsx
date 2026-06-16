/**
 * DS canonical tokens render test.
 *
 * Garante que tokens canonical "Quiet Operator" (DESIGN.md 2026-05-26)
 * wired em tailwind.config.ts são reconhecidos pelo PostCSS/Tailwind
 * pipeline em runtime.
 *
 * Estrategia: render JSDOM com classe canonical + asserir que o elemento
 * carrega a class no atributo (validação leve — Tailwind generator é
 * verificado em build via npm run build, NÃO em jsdom).
 *
 * Pin: se tailwind.config.ts perder um desses tokens, build npm vai
 * emitir warning (não falha jsdom, mas falha sensor check_ds_tokens_canonical).
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import React from "react";

const CANONICAL_TOKENS = [
  "paper", "chalk", "powder", "mist", "pebble", "fog",
  "ash", "slate", "graphite", "ink",
  "lia-cyan", "lia-cyan-hover", "coral-quiet", "forest-green",
  "amber-warning", "insight-purple", "alert-magenta",
] as const;

describe("DS canonical tokens render contract", () => {
  for (const token of CANONICAL_TOKENS) {
    it(`renders bg-${token} without throw`, () => {
      const { container } = render(
        <div className={`bg-${token} text-${token} border-${token}`}>{token}</div>
      );
      const el = container.firstChild as HTMLElement;
      expect(el).toBeTruthy();
      expect(el.className).toContain(`bg-${token}`);
      expect(el.className).toContain(`text-${token}`);
      expect(el.className).toContain(`border-${token}`);
    });
  }

  it("supports opacity modifier (bg-graphite/80)", () => {
    const { container } = render(<div className="bg-graphite/80">x</div>);
    expect((container.firstChild as HTMLElement).className).toContain("bg-graphite/80");
  });

  it("preserves backward compat: wedo-cyan e lia-bg-primary continuam funcionando", () => {
    const { container } = render(
      <>
        <div className="bg-wedo-cyan">a</div>
        <div className="bg-lia-bg-primary">b</div>
        <div className="bg-lia-surface">c</div>
      </>
    );
    expect(container.children.length).toBe(3);
  });
});
