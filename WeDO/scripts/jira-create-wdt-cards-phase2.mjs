import * as fs from 'fs';
import * as path from 'path';

const PROJECT_KEY = 'WT';

let BASE_URL = '';
let AUTH_TOKEN = '';

const EPIC_KEYS = {
  0: 'WT-1307',
  1: 'WT-1308',
  2: 'WT-1309',
  3: 'WT-1310',
};

const EPIC_LABELS = {
  0: 'epic-otm-busca',
  1: 'epic-criterios',
  2: 'epic-aprendizado',
  3: 'epic-observ',
};

const WDT_CARDS = [
  { code: 'WDT-008', epicIndex: 0 },
  { code: 'WDT-009', epicIndex: 0 },
  { code: 'WDT-010', epicIndex: 0 },
  { code: 'WDT-011', epicIndex: 0 },
  { code: 'WDT-012', epicIndex: 0 },
  { code: 'WDT-013', epicIndex: 0 },
  { code: 'WDT-014', epicIndex: 0 },
  { code: 'WDT-015', epicIndex: 0 },
  { code: 'WDT-016', epicIndex: 1 },
  { code: 'WDT-017', epicIndex: 1 },
  { code: 'WDT-018', epicIndex: 1 },
  { code: 'WDT-019', epicIndex: 1 },
  { code: 'WDT-020', epicIndex: 1 },
  { code: 'WDT-021', epicIndex: 1 },
  { code: 'WDT-022', epicIndex: 1 },
  { code: 'WDT-023', epicIndex: 2 },
  { code: 'WDT-024', epicIndex: 2 },
  { code: 'WDT-025', epicIndex: 2 },
  { code: 'WDT-026', epicIndex: 2 },
  { code: 'WDT-027', epicIndex: 2 },
  { code: 'WDT-028', epicIndex: 2 },
  { code: 'WDT-029', epicIndex: 3 },
  { code: 'WDT-030', epicIndex: 3 },
];

async function initJiraAuth() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY
    ? 'repl ' + process.env.REPL_IDENTITY
    : process.env.WEB_REPL_RENEWAL
    ? 'depl ' + process.env.WEB_REPL_RENEWAL
    : null;
  const data = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=jira',
    { headers: { 'Accept': 'application/json', 'X_REPLIT_TOKEN': xReplitToken } }
  ).then(res => res.json());
  AUTH_TOKEN = data.items?.[0]?.settings?.access_token;
  if (!AUTH_TOKEN) throw new Error('Token Jira não encontrado');

  const resources = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: { 'Authorization': `Bearer ${AUTH_TOKEN}`, 'Accept': 'application/json' }
  }).then(r => r.json());
  const cloudId = resources[0].id;
  BASE_URL = `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3`;
  return cloudId;
}

function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

function parseWdtCard(content, wdtCode) {
  const escapedCode = wdtCode.replace(/[-]/g, '\\-');

  const cardPattern = new RegExp(
    `#{3,6}\\s*(?:CARD\\s+)?${escapedCode}:[^\\n]*\\n(?:(?!#{3,6}\\s*(?:CARD|Prompt))[\\s\\S])*?\`\`\`yaml\\n([\\s\\S]*?)\`\`\``,
    'i'
  );
  const match = content.match(cardPattern);
  if (!match) {
    console.error(`   ❌ YAML não encontrado para ${wdtCode}`);
    return null;
  }
  const yamlContent = match[1];

  const promptPattern = new RegExp(
    `#{3,6}\\s*Prompt para IA \\(Cursor\\/VSCode\\)\\s*(?:—|-)\\s*${escapedCode}\\n\\n\`\`\`[^\\n]*\\n([\\s\\S]*?)\`\`\``,
    'i'
  );
  const promptMatch = content.match(promptPattern);
  const promptContent = promptMatch ? promptMatch[1] : null;

  const extractField = (field) => {
    const fieldPattern = new RegExp(`^${field}:\\s*(.*)$`, 'mi');
    const m = yamlContent.match(fieldPattern);
    return m ? m[1].trim().replace(/^["'\[]|["'\]]$/g, '') : '';
  };

  const titulo = extractField('Titulo');
  const tipo = extractField('Tipo');
  const sprint = extractField('Sprint');
  const pontos = extractField('Pontos');
  const prioridade = extractField('Prioridade');
  const epic = extractField('Epic');
  const fase = extractField('Fase');
  const status = extractField('Status');
  const dependencias = extractField('Dependencias');
  const bloqueia = extractField('Bloqueia');
  const labelsRaw = extractField('Labels');

  const isCancelled = titulo.includes('CANCELADO') ||
    content.match(new RegExp(`CARD\\s+${escapedCode}:[^\\n]*CANCELADO`, 'i')) !== null;

  const labels = ['lia-mvp', 'talent-funnel', wdtCode.toLowerCase()];
  if (sprint) labels.push(`sprint-${sprint}`);
  if (prioridade) {
    const prioMap = {
      'crítica': 'priority-critica', 'critica': 'priority-critica',
      'alta': 'priority-alta', 'média': 'priority-media', 'media': 'priority-media',
      'baixa': 'priority-baixa'
    };
    const p = prioMap[prioridade.toLowerCase()];
    if (p) labels.push(p);
  }
  if (labelsRaw) {
    labelsRaw.split(',').map(l => l.trim()).forEach(l => { if (l && !labels.includes(l)) labels.push(l); });
  }

  const tituloLower = titulo.toLowerCase();
  if (tituloLower.includes('[be/fe]') || tituloLower.includes('[full-stack]')) {
    labels.push('area-fullstack');
  } else if (tituloLower.includes('[be]') || tipo.toLowerCase() === 'backend' || tipo.toLowerCase() === 'task') {
    labels.push('area-backend');
  } else if (tituloLower.includes('[fe]') || tipo.toLowerCase() === 'frontend') {
    labels.push('area-frontend');
  } else if (tituloLower.includes('[ai]') || tipo.toLowerCase().includes('ai')) {
    labels.push('area-ia');
  } else {
    labels.push('area-backend');
  }

  if (isCancelled) labels.push('cancelado');

  return {
    codigo: wdtCode, titulo, tipo, sprint, pontos, prioridade, epic, fase, status,
    dependencias, bloqueia, yamlContent, promptContent, labels: [...new Set(labels)], isCancelled,
  };
}

function truncateText(text, maxLen) {
  if (!text || text.length <= maxLen) return text;
  return text.substring(0, maxLen - 50) + '\n\n... [TRUNCATED - ver documento completo no repositório] ...';
}

function buildADFDescription(card) {
  const content = [];

  content.push({
    type: "heading", attrs: { level: 2 },
    content: [{ type: "text", text: `${card.codigo}: ${card.titulo}` }]
  });

  if (card.isCancelled) {
    content.push({
      type: "panel", attrs: { panelType: "error" },
      content: [{
        type: "paragraph",
        content: [{ type: "text", text: "❌ CARD CANCELADO — Substituído por sistema auto-evolutivo sem interface admin", marks: [{ type: "strong" }] }]
      }]
    });
  }

  content.push({
    type: "table",
    attrs: { isNumberColumnEnabled: false, layout: "default" },
    content: [
      { type: "tableRow", content: [
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Tipo", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.tipo || "-" }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Sprint", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.sprint || "-" }] }] }
      ]},
      { type: "tableRow", content: [
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Pontos", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.pontos || "-" }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Prioridade", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.prioridade || "-" }] }] }
      ]},
      { type: "tableRow", content: [
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Epic", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.epic || "-" }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Fase", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.fase || "-" }] }] }
      ]},
      { type: "tableRow", content: [
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Dependências", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.dependencias || "-" }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Bloqueia", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.bloqueia || "-" }] }] }
      ]},
      { type: "tableRow", content: [
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Status", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.status || "📋 Pendente" }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "", marks: [{ type: "strong" }] }] }] },
        { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "" }] }] }
      ]}
    ]
  });

  content.push({ type: "rule" });
  content.push({
    type: "heading", attrs: { level: 3 },
    content: [{ type: "text", text: "Especificação Completa (YAML)" }]
  });
  content.push({
    type: "codeBlock", attrs: { language: "yaml" },
    content: [{ type: "text", text: truncateText(card.yamlContent, 30000) }]
  });

  if (card.promptContent) {
    content.push({ type: "rule" });
    content.push({
      type: "heading", attrs: { level: 3 },
      content: [{ type: "text", text: "Prompt para IA (Cursor/VSCode)" }]
    });
    content.push({
      type: "codeBlock", attrs: { language: "text" },
      content: [{ type: "text", text: truncateText(card.promptContent, 20000) }]
    });
  }

  return { version: 1, type: "doc", content };
}

async function createCard(card) {
  const description = buildADFDescription(card);

  const fields = {
    project: { key: PROJECT_KEY },
    summary: `${card.codigo}: ${card.titulo}`,
    description: description,
    issuetype: { name: 'Task' },
    labels: card.labels,
  };

  const res = await fetch(`${BASE_URL}/issue`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${AUTH_TOKEN}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ fields })
  });

  if (!res.ok) {
    const err = await res.text();
    return { success: false, error: `${res.status}: ${err.substring(0, 500)}` };
  }

  const result = await res.json();
  return { success: true, key: result.key, id: result.id };
}

async function linkToEpic(issueKey, epicKey) {
  const res = await fetch(`${BASE_URL}/issueLink`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${AUTH_TOKEN}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      type: { name: "Epic-Story Link" },
      inwardIssue: { key: issueKey },
      outwardIssue: { key: epicKey }
    })
  });

  if (!res.ok) {
    const linkTypes = await fetch(`${BASE_URL}/issueLinkType`, {
      headers: { 'Authorization': `Bearer ${AUTH_TOKEN}`, 'Accept': 'application/json' }
    }).then(r => r.json());

    for (const lt of (linkTypes.issueLinkTypes || [])) {
      const res2 = await fetch(`${BASE_URL}/issueLink`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${AUTH_TOKEN}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: { name: lt.name },
          inwardIssue: { key: issueKey },
          outwardIssue: { key: epicKey }
        })
      });
      if (res2.ok || res2.status === 201) {
        console.log(`      🔗 Link ${lt.name} criado`);
        return true;
      }
    }
    console.log(`      ⚠️ Não foi possível linkar ao epic (sem link types compatíveis)`);
    return false;
  }
  return true;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('   🆕 FASE 2: Criação de 23 Cards WDT no Jira');
  console.log('   (Épicos já criados: WT-1307 a WT-1310)');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const docPath = path.join(process.cwd(), 'docs/lia-mvp-cards-jira.md');
  const docContent = fs.readFileSync(docPath, 'utf-8');
  console.log(`📄 Documento carregado: ${docContent.length} chars\n`);

  const cloudId = await initJiraAuth();
  console.log(`✅ Autenticação Jira OK (Cloud: ${cloudId})\n`);

  console.log('--- Parsing dos 23 Cards WDT ---\n');
  const parsedCards = [];
  for (const wdtDef of WDT_CARDS) {
    const card = parseWdtCard(docContent, wdtDef.code);
    if (card) {
      card.labels.push(EPIC_LABELS[wdtDef.epicIndex]);
      card.labels = [...new Set(card.labels)];
      parsedCards.push({ card, epicKey: EPIC_KEYS[wdtDef.epicIndex], epicIndex: wdtDef.epicIndex });
      console.log(`   ✅ ${wdtDef.code}: "${card.titulo}" (YAML=${card.yamlContent.length}c, Prompt=${card.promptContent?.length || 0}c${card.isCancelled ? ' ❌' : ''})`);
    } else {
      parsedCards.push({ card: null, epicKey: null, epicIndex: wdtDef.epicIndex });
    }
  }
  console.log(`\n📊 Cards parseados: ${parsedCards.filter(p => p.card).length}/23\n`);

  console.log('--- Criando Cards no Jira ---\n');
  let successCount = 0;
  let errorCount = 0;
  const results = [];

  for (let i = 0; i < parsedCards.length; i++) {
    const { card, epicKey } = parsedCards[i];
    if (!card) {
      results.push({ code: WDT_CARDS[i].code, status: 'parse_error' });
      errorCount++;
      continue;
    }

    console.log(`[${i + 1}/23] Criando ${card.codigo}...`);
    const result = await createCard(card);

    if (result.success) {
      successCount++;
      console.log(`   ✅ ${result.key} — ${card.titulo}`);
      console.log(`      Labels (${card.labels.length}): [${card.labels.join(', ')}]`);
      console.log(`      SP: ${card.pontos || 'N/A'} | Epic: ${epicKey}`);

      if (epicKey) {
        await delay(300);
        await linkToEpic(result.key, epicKey);
      }

      results.push({ code: card.codigo, jiraKey: result.key, status: 'success', labels: card.labels, sp: card.pontos, cancelled: card.isCancelled, epicKey });
    } else {
      errorCount++;
      console.error(`   ❌ Erro: ${result.error}`);
      results.push({ code: card.codigo, status: 'error', error: result.error });
    }

    await delay(600);
  }

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('   📊 RELATÓRIO FINAL');
  console.log('═══════════════════════════════════════════════════════════════\n');

  console.log(`   Cards criados: ${successCount}/23`);
  console.log(`   Erros: ${errorCount}\n`);

  for (const r of results) {
    const icon = r.status === 'success' ? '✅' : '❌';
    const extra = r.cancelled ? ' [CANCELADO]' : '';
    console.log(`   ${icon} ${r.code}: ${r.jiraKey || 'N/A'} → ${r.epicKey || '-'}${extra}`);
  }

  const outputPath = path.join(process.cwd(), 'scripts/jira-wdt-creation-result.json');
  fs.writeFileSync(outputPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    epics: Object.entries(EPIC_KEYS).map(([idx, key]) => ({ key, label: EPIC_LABELS[idx] })),
    cards: results,
    summary: { cardsCreated: successCount, errors: errorCount }
  }, null, 2));

  console.log(`\n💾 Resultado salvo em: ${outputPath}`);
  console.log('\n✅ Script concluído!');
}

main().catch(err => {
  console.error('\n❌ Erro fatal:', err.message || err);
  process.exit(1);
});
