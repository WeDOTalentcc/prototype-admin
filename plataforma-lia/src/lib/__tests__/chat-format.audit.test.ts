/**
 * Vitest Unit Tests: chat-format.ts Audit
 * Tests cleanAgentResponse and parseChatMarkdown for correctness.
 * Run via: pnpm test (or npx vitest run)
 */

import { describe, it, expect } from 'vitest';
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from '../chat-format';

describe('cleanAgentResponse — Limpeza de respostas do agente', () => {

  it('TC-UNIT-001: Remove tags <thought>...</thought> completas', () => {
    const raw = '<thought>Este é um pensamento interno</thought>Esta é a resposta visível.';
    const result = cleanAgentResponse(raw);
    expect(result).not.toContain('<thought>');
    expect(result).not.toContain('pensamento interno');
    expect(result).toContain('Esta é a resposta visível');
  });

  it('TC-UNIT-002: Remove blocos ```json {...} ```', () => {
    const raw = '```json\n{"thought": "algo", "response": null}\n```\nResposta final aqui.';
    const result = cleanAgentResponse(raw);
    expect(result).not.toContain('```json');
    expect(result).toContain('Resposta final');
  });

  it('TC-UNIT-003: Remove JSON raw com campo "thought"', () => {
    const raw = '{"thought": "raciocínio interno", "response": null}\nResposta limpa.';
    const result = cleanAgentResponse(raw);
    expect(result).not.toContain('"thought"');
  });

  it('TC-UNIT-004: Retorna texto original quando não há tags especiais', () => {
    const raw = 'Esta é uma mensagem simples sem tags especiais.';
    const result = cleanAgentResponse(raw);
    expect(result).toBe(raw);
  });

  it('TC-UNIT-005: Remove <thought> incompleto (sem fechamento)', () => {
    const raw = '<thought>pensamento não fechado... resto do texto.';
    const result = cleanAgentResponse(raw);
    expect(result).not.toContain('pensamento não fechado');
  });

  it('TC-UNIT-006: Case-insensitive — remove <THOUGHT>...</THOUGHT>', () => {
    const raw = '<THOUGHT>internal reasoning</THOUGHT>Visible response.';
    const result = cleanAgentResponse(raw);
    expect(result).not.toContain('<THOUGHT>');
    expect(result).not.toContain('internal reasoning');
    expect(result).toContain('Visible response');
  });

  it('TC-UNIT-007: Remove espaços em branco extras no início e fim', () => {
    const raw = '\n\n<thought>thinking</thought>\n\nResposta.\n\n';
    const result = cleanAgentResponse(raw);
    expect(result.startsWith('Resposta')).toBe(true);
    expect(result.endsWith('.')).toBe(true);
  });
});

describe('parseChatMarkdown — Renderização de Markdown', () => {

  it('TC-UNIT-010: Renderiza **bold** como <strong>', () => {
    const html = parseChatMarkdown('Esta palavra é **negrito** aqui.');
    expect(html).toContain('<strong>negrito</strong>');
    expect(html).not.toContain('**negrito**');
  });

  it('TC-UNIT-011: Renderiza *italic* como <em>', () => {
    const html = parseChatMarkdown('Esta palavra é *itálico* aqui.');
    expect(html).toContain('<em>itálico</em>');
    expect(html).not.toContain('*itálico*');
  });

  it('TC-UNIT-012: Renderiza listas com traços como <ul><li>', () => {
    const html = parseChatMarkdown('- Item 1\n- Item 2\n- Item 3');
    expect(html).toContain('<ul');
    expect(html).toContain('<li>Item 1</li>');
    expect(html).toContain('<li>Item 2</li>');
  });

  it('TC-UNIT-013: Renderiza listas com bullet • como <ul><li>', () => {
    const html = parseChatMarkdown('• Item A\n• Item B');
    expect(html).toContain('<ul');
    expect(html).toContain('<li>Item A</li>');
  });

  it('TC-UNIT-014: Renderiza listas ordenadas 1. 2. como <ol><li>', () => {
    const html = parseChatMarkdown('1. Primeiro\n2. Segundo\n3. Terceiro');
    expect(html).toContain('<ol');
    expect(html).toContain('<li>Primeiro</li>');
    expect(html).not.toContain('1. Primeiro');
  });

  it('TC-UNIT-015: Renderiza `inline code` como <code>', () => {
    const html = parseChatMarkdown('Use o comando `npm install` para instalar.');
    expect(html).toContain('<code');
    expect(html).toContain('npm install');
    expect(html).not.toContain('`npm install`');
  });

  it('TC-UNIT-016: Renderiza bloco ```code``` como <pre><code>', () => {
    const html = parseChatMarkdown('```\nconst x = 1;\nconsole.log(x);\n```');
    expect(html).toContain('<pre');
    expect(html).toContain('<code');
    expect(html).toContain('const x = 1');
    expect(html).not.toContain('```');
  });

  it('TC-UNIT-017: Renderiza # Header como div com font-semibold', () => {
    const html = parseChatMarkdown('# Título Principal');
    expect(html).not.toContain('# Título');
    expect(html).toContain('Título Principal');
    expect(html).toContain('font-semibold');
  });

  it('TC-UNIT-018: Renderiza links [label](url) como <a href>', () => {
    const html = parseChatMarkdown('Acesse [Google](https://google.com) para mais info.');
    expect(html).toContain('<a href="https://google.com"');
    expect(html).toContain('Google');
    expect(html).not.toContain('[Google](https://google.com)');
  });

  it('TC-UNIT-019: Não renderiza links com protocolo inseguro javascript:', () => {
    const html = parseChatMarkdown('Clique [aqui](javascript:alert(1)) para ver.');
    expect(html).not.toContain('javascript:alert');
    expect(html).toContain('aqui');
  });

  it('TC-UNIT-020: Linha --- é convertida em <hr>', () => {
    const html = parseChatMarkdown('Acima\n---\nAbaixo');
    expect(html).toContain('<hr');
  });

  it('TC-UNIT-021: Escapa HTML perigoso <script>', () => {
    const html = parseChatMarkdown('<script>alert("xss")</script>');
    expect(html).not.toContain('<script>');
    expect(html).toContain('&lt;script&gt;');
  });

  it('TC-UNIT-022: Mensagem complexa com múltiplos elementos', () => {
    const msg = `# Candidatos\n\n**3 perfis** encontrados:\n\n1. João\n2. Maria\n\n- Revisar perfis\n- Agendar entrevistas\n\n---\n\nUse o comando \`/triagem\` para triagem.`;
    const html = parseChatMarkdown(msg);
    expect(html).toContain('<strong>3 perfis</strong>');
    expect(html).toContain('<ol');
    expect(html).toContain('<ul');
    expect(html).toContain('<hr');
    expect(html).toContain('<code');
    expect(html).not.toContain('**');
    expect(html).not.toContain('---');
  });
});

describe('escapeHtml — Escape de caracteres HTML', () => {

  it('TC-UNIT-030: Escapa & como &amp;', () => {
    expect(escapeHtml('Tom & Jerry')).toBe('Tom &amp; Jerry');
  });

  it('TC-UNIT-031: Escapa < e > como &lt; &gt;', () => {
    expect(escapeHtml('<div>')).toBe('&lt;div&gt;');
  });

  it('TC-UNIT-032: Escapa " como &quot;', () => {
    expect(escapeHtml('"hello"')).toBe('&quot;hello&quot;');
  });

  it('TC-UNIT-033: Escapa \' como &#39;', () => {
    expect(escapeHtml("it's")).toBe('it&#39;s');
  });
});
