import * as fs from 'fs';
import * as path from 'path';

interface JiraAuth {
  accessToken: string;
  cloudId: string;
  baseUrl: string;
}

interface ParsedCard {
  code: string;
  title: string;
  yamlContent: string;
  disclaimer: string;
  fields: {
    titulo: string;
    tipo: string;
    sprint: string;
    pontos: string;
    prioridade: string;
    epic: string;
    status: string;
    dependencias: string;
  };
}

interface SyncResult {
  cardCode: string;
  jiraKey: string;
  action: 'created' | 'updated' | 'removed' | 'error' | 'skipped';
  error?: string;
}

const PROJECT_KEY = 'WT';
const PROJECT_ID = '10033';
const ISSUE_TYPE_TASK = '10034';
const ISSUE_TYPE_EPIC = '10036';

const SPRINT_START_DATES: Record<string, string> = {
  '0': '2026-02-09',
  '1': '2026-02-09',
  '2': '2026-02-23',
  '3': '2026-03-09',
  '4': '2026-03-23',
};

const EXISTING_EPICS: Record<string, string> = {
  'TRI': 'WT-1258',
  'SCO': 'WT-1259',
  'GAT': 'WT-1260',
  'TPL': 'WT-1261',
  'AGE': 'WT-1262',
  'NOT': 'WT-1263',
  'INT-LLM': 'WT-1264',
  'INT-WOS': 'WT-1264',
  'INT-APY': 'WT-1264',
  'INT-MSG': 'WT-1264',
  'INT-TWI': 'WT-1264',
  'KAN': 'WT-1256',
  'TAB': 'WT-1256',
  'PRV': 'WT-1256',
  'VAG': 'WT-1256',
  'MAP': 'WT-1271',
  'WSI': 'WT-1272',
  'AGT': 'WT-1276',
  'DAT': 'WT-1258',
  'ENT': 'WT-1258',
};

const EPICS_ALREADY_CREATED: Record<string, string> = {
  'EPIC-AUTH': 'WT-1287',
  'EPIC-WIZARD': 'WT-1288',
  'EPIC-JD-WIZARD': 'WT-1289',
  'EPIC-CONFIG': 'WT-1290',
};

const EPIC_NAME_TO_PREFIX: Record<string, string[]> = {
  'EPIC-AUTH': ['AUTH'],
  'EPIC-WIZARD': ['WIZ'],
  'EPIC-JD-WIZARD': ['JD', 'JDW'],
  'EPIC-CONFIG': ['CFG', 'IMP'],
};

const REMOVED_CARDS: Record<string, { jiraKey: string; label: string; prefix: string }> = {
  'WSI-004': { jiraKey: 'WT-914', label: 'status-removido', prefix: '[REMOVIDO]' },
  'KAN-005': { jiraKey: 'WT-967', label: 'status-obsoleto', prefix: '[OBSOLETO]' },
};

const createdEpicKeys: Record<string, string> = {};

async function getJiraAuth(): Promise<JiraAuth> {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY
    ? 'repl ' + process.env.REPL_IDENTITY
    : process.env.WEB_REPL_RENEWAL
    ? 'depl ' + process.env.WEB_REPL_RENEWAL
    : null;

  if (!xReplitToken || !hostname) {
    throw new Error('Variáveis de ambiente Replit não encontradas');
  }

  const connResponse = await fetch(
    `https://${hostname}/api/v2/connection?include_secrets=true&connector_names=jira`,
    { headers: { 'Accept': 'application/json', 'X_REPLIT_TOKEN': xReplitToken! } }
  );

  const connData = await connResponse.json();
  const conn = (connData as any).items?.[0];
  const accessToken = conn?.settings?.access_token;

  if (!accessToken) {
    throw new Error('Token Jira não encontrado');
  }

  const resourcesResponse = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: { 'Authorization': `Bearer ${accessToken}`, 'Accept': 'application/json' }
  });

  if (!resourcesResponse.ok) {
    throw new Error('Erro ao obter recursos Atlassian');
  }

  const resources = await resourcesResponse.json() as any[];
  if (resources.length === 0) {
    throw new Error('Nenhum site Jira encontrado');
  }

  const cloudId = resources[0].id;
  return { accessToken, cloudId, baseUrl: `https://api.atlassian.com/ex/jira/${cloudId}` };
}

async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getCardPrefix(code: string): string {
  const prefixes = ['INT-TWI', 'INT-LLM', 'INT-WOS', 'INT-APY', 'INT-MSG'];
  for (const p of prefixes) {
    if (code.startsWith(p + '-')) return p;
  }
  const match = code.match(/^([A-Z]+)-\d+$/);
  return match ? match[1] : code;
}

function getEpicKeyForCard(code: string): string | null {
  const prefix = getCardPrefix(code);
  if (EXISTING_EPICS[prefix]) return EXISTING_EPICS[prefix];
  for (const [epicName, prefixes] of Object.entries(EPIC_NAME_TO_PREFIX)) {
    if (prefixes.includes(prefix)) {
      return EPICS_ALREADY_CREATED[epicName] || createdEpicKeys[epicName] || null;
    }
  }
  return null;
}

function getEpicLabelForCard(code: string): string {
  const prefix = getCardPrefix(code);
  const numMatch = code.match(/(\d+)$/);
  const num = numMatch ? numMatch[1].padStart(3, '0') : '001';
  return `epic-${prefix.toLowerCase()}-${num}`;
}

function extractField(yaml: string, field: string): string {
  const pattern = new RegExp(`^${field}:\\s*(.*)$`, 'mi');
  const match = yaml.match(pattern);
  if (!match) return '';
  let val = match[1].trim();
  val = val.replace(/^["']|["']$/g, '');
  return val;
}

function deriveAreaLabel(titulo: string, tipo: string): string {
  const t = titulo.toLowerCase();
  const tp = tipo.toLowerCase();

  if (t.includes('[frontend]') || t.includes('[fe]') || tp === 'frontend') return 'area-frontend';
  if (t.includes('[backend]') || t.includes('[be]') || tp === 'backend') return 'area-backend';
  if (t.includes('[full-stack]') || t.includes('[fullstack]') || tp.includes('full-stack') || tp.includes('fullstack')) return 'area-fullstack';
  if (t.includes('[ai]') || t.includes('[ia]') || tp === 'ai' || tp === 'ia') return 'area-ia';
  if (t.includes('[integra') || t.includes('[infra]') || tp.includes('integra') || tp.includes('configuração') || tp.includes('configuracao')) return 'area-integracao';
  if (t.includes('[design]') || tp === 'design') return 'area-design';
  if (tp === 'feature') return 'area-frontend';
  return 'area-backend';
}

function computeLabels(card: ParsedCard): string[] {
  const labels = new Set<string>();
  const { fields, code } = card;

  labels.add('lia-mvp');
  labels.add(code.toLowerCase());

  if (fields.sprint && fields.sprint !== 'Pós-MVP' && fields.sprint !== 'pos-mvp') {
    labels.add(`sprint-${fields.sprint}`);
  }

  if (fields.tipo) {
    const tipoNorm = fields.tipo.toLowerCase()
      .replace('integração', 'integracao')
      .replace('configuração saas', 'config-saas')
      .replace('infraestrutura', 'infra')
      .replace(/\s+/g, '-');
    labels.add(`tipo-${tipoNorm}`);
  }

  if (fields.prioridade) {
    const prioMap: Record<string, string> = {
      'crítica': 'priority-critica',
      'critica': 'priority-critica',
      'alta': 'priority-alta',
      'média': 'priority-media',
      'media': 'priority-media',
      'baixa': 'priority-baixa',
    };
    const prio = prioMap[fields.prioridade.toLowerCase()];
    if (prio) labels.add(prio);
  }

  labels.add(getEpicLabelForCard(code));
  labels.add(deriveAreaLabel(fields.titulo, fields.tipo));

  return [...labels];
}

function parseAllCards(content: string): ParsedCard[] {
  const cards: ParsedCard[] = [];
  const cardRegex = /### CARD ([A-Z]+-(?:[A-Z]+-)?[\d]+):\s*(.+?)(?:\s*⏸️[^\n]*)?\n/g;
  let match: RegExpExecArray | null;
  const positions: { code: string; title: string; start: number }[] = [];

  while ((match = cardRegex.exec(content)) !== null) {
    positions.push({ code: match[1], title: match[2].trim(), start: match.index });
  }

  for (let i = 0; i < positions.length; i++) {
    const pos = positions[i];
    const endPos = i + 1 < positions.length ? positions[i + 1].start : content.length;
    const section = content.substring(pos.start, endPos);

    const yamlMatch = section.match(/```yaml\n([\s\S]*?)```/);
    if (!yamlMatch) continue;

    const yamlContent = yamlMatch[1];
    const yamlStartIdx = section.indexOf('```yaml');
    const headerEndIdx = section.indexOf('\n') + 1;
    const disclaimer = section.substring(headerEndIdx, yamlStartIdx).trim();

    const titulo = extractField(yamlContent, 'Titulo');
    const tipo = extractField(yamlContent, 'Tipo');
    const sprint = extractField(yamlContent, 'Sprint');
    const pontos = extractField(yamlContent, 'Pontos');
    const prioridade = extractField(yamlContent, 'Prioridade');
    const epic = extractField(yamlContent, 'Epic');
    const status = extractField(yamlContent, 'Status');
    const dependencias = extractField(yamlContent, 'Dependencias');

    cards.push({
      code: pos.code,
      title: pos.title,
      yamlContent,
      disclaimer,
      fields: { titulo: titulo || pos.title, tipo, sprint, pontos, prioridade, epic, status, dependencias },
    });
  }

  return cards;
}

function buildADF(card: ParsedCard): object {
  const { code, fields, yamlContent, disclaimer } = card;
  const content: any[] = [];

  content.push({
    type: 'heading',
    attrs: { level: 2 },
    content: [{ type: 'text', text: `${code}: ${fields.titulo}` }],
  });

  const tableRows: any[] = [
    {
      type: 'tableRow',
      content: [
        { type: 'tableHeader', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Campo' }] }] },
        { type: 'tableHeader', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Valor' }] }] },
      ],
    },
  ];

  const metaFields = [
    ['Sprint', fields.sprint],
    ['Pontos', fields.pontos],
    ['Prioridade', fields.prioridade],
    ['Epic', fields.epic],
    ['Dependências', fields.dependencias],
    ['Status', fields.status],
    ['Tipo', fields.tipo],
  ];

  for (const [name, value] of metaFields) {
    if (value) {
      tableRows.push({
        type: 'tableRow',
        content: [
          { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: name, marks: [{ type: 'strong' }] }] }] },
          { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: value || '-' }] }] },
        ],
      });
    }
  }

  content.push({
    type: 'table',
    attrs: { isNumberColumnEnabled: false, layout: 'default' },
    content: tableRows,
  });

  if (disclaimer) {
    content.push({
      type: 'paragraph',
      content: [{ type: 'text', text: disclaimer, marks: [{ type: 'em' }] }],
    });
  }

  content.push({ type: 'rule' });

  content.push({
    type: 'heading',
    attrs: { level: 3 },
    content: [{ type: 'text', text: 'Especificação Completa' }],
  });

  content.push({
    type: 'codeBlock',
    attrs: { language: 'yaml' },
    content: [{ type: 'text', text: yamlContent }],
  });

  return { version: 1, type: 'doc', content };
}

function buildSummary(card: ParsedCard): string {
  return `[${card.code}] ${card.fields.titulo}`;
}

function buildIssueFields(card: ParsedCard, epicKey: string | null): Record<string, any> {
  const labels = computeLabels(card);
  const fields: Record<string, any> = {
    project: { key: PROJECT_KEY },
    issuetype: { id: ISSUE_TYPE_TASK },
    summary: buildSummary(card),
    description: buildADF(card),
    labels,
  };

  if (card.fields.sprint && SPRINT_START_DATES[card.fields.sprint]) {
    fields.customfield_10015 = SPRINT_START_DATES[card.fields.sprint];
    fields.customfield_10135 = [`sprint-${card.fields.sprint}`];
  }

  if (epicKey) {
    fields.parent = { key: epicKey };
  }

  return fields;
}

async function jiraRequest(
  auth: JiraAuth,
  method: string,
  endpoint: string,
  body?: any,
): Promise<{ ok: boolean; status: number; data: any }> {
  const url = `${auth.baseUrl}${endpoint}`;
  const headers: Record<string, string> = {
    'Authorization': `Bearer ${auth.accessToken}`,
    'Accept': 'application/json',
  };
  if (body) headers['Content-Type'] = 'application/json';

  const resp = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data: any = null;
  const text = await resp.text();
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }

  return { ok: resp.ok, status: resp.status, data };
}

async function createIssue(auth: JiraAuth, card: ParsedCard, epicKey: string | null): Promise<string> {
  const fields = buildIssueFields(card, epicKey);
  const result = await jiraRequest(auth, 'POST', '/rest/api/3/issue', { fields });

  if (!result.ok) {
    console.error(`  ❌ Failed to create ${card.code}:`, JSON.stringify(result.data).substring(0, 500));
    throw new Error(`Failed to create issue: ${card.code}`);
  }

  return result.data.key;
}

async function updateIssue(auth: JiraAuth, jiraKey: string, card: ParsedCard, epicKey: string | null): Promise<void> {
  const labels = computeLabels(card);
  const updateFields: Record<string, any> = {
    summary: buildSummary(card),
    description: buildADF(card),
    labels,
  };

  if (card.fields.sprint && SPRINT_START_DATES[card.fields.sprint]) {
    updateFields.customfield_10015 = SPRINT_START_DATES[card.fields.sprint];
    updateFields.customfield_10135 = [`sprint-${card.fields.sprint}`];
  }

  if (epicKey) {
    updateFields.parent = { key: epicKey };
  }

  const result = await jiraRequest(auth, 'PUT', `/rest/api/3/issue/${jiraKey}`, { fields: updateFields });

  if (!result.ok) {
    console.error(`  ❌ Failed to update ${jiraKey} (${card.code}):`, JSON.stringify(result.data).substring(0, 500));
    throw new Error(`Failed to update issue: ${jiraKey}`);
  }
}

async function markRemoved(
  auth: JiraAuth,
  jiraKey: string,
  cardCode: string,
  statusLabel: string,
  prefix: string,
): Promise<void> {
  const getResult = await jiraRequest(auth, 'GET', `/rest/api/3/issue/${jiraKey}?fields=summary,labels`);
  if (!getResult.ok) {
    throw new Error(`Failed to get issue ${jiraKey}`);
  }

  const currentSummary: string = getResult.data.fields.summary || '';
  const currentLabels: string[] = getResult.data.fields.labels || [];

  const newSummary = currentSummary.startsWith(prefix) ? currentSummary : `${prefix} ${currentSummary}`;
  const newLabels = [...new Set([...currentLabels, statusLabel])];

  const result = await jiraRequest(auth, 'PUT', `/rest/api/3/issue/${jiraKey}`, {
    fields: { summary: newSummary, labels: newLabels },
  });

  if (!result.ok) {
    throw new Error(`Failed to mark ${jiraKey} as removed`);
  }
}

async function processBatch<T>(
  items: T[],
  batchSize: number,
  batchDelayMs: number,
  itemDelayMs: number,
  fn: (item: T, index: number) => Promise<void>,
): Promise<void> {
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    for (let j = 0; j < batch.length; j++) {
      await fn(batch[j], i + j);
      if (j < batch.length - 1) await delay(itemDelayMs);
    }
    if (i + batchSize < items.length) {
      console.log(`  ⏳ Batch pause (${batchDelayMs}ms)...`);
      await delay(batchDelayMs);
    }
  }
}

function parseArgs(): { start: number; count: number; skipCreate: boolean; skipRemoved: boolean } {
  const args = process.argv.slice(2);
  let start = 0;
  let count = 30;
  let skipCreate = false;
  let skipRemoved = false;

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--start':
        start = parseInt(args[++i], 10);
        if (isNaN(start) || start < 0) {
          console.error('❌ --start must be a non-negative integer');
          process.exit(1);
        }
        break;
      case '--count':
        count = parseInt(args[++i], 10);
        if (isNaN(count) || count < 1) {
          console.error('❌ --count must be a positive integer');
          process.exit(1);
        }
        break;
      case '--skip-create':
        skipCreate = true;
        break;
      case '--skip-removed':
        skipRemoved = true;
        break;
      default:
        console.error(`❌ Unknown argument: ${args[i]}`);
        console.log('Usage: npx tsx scripts/jira-sync/02-sync-batch.ts --start N --count N [--skip-create] [--skip-removed]');
        process.exit(1);
    }
  }

  return { start, count, skipCreate, skipRemoved };
}

async function main() {
  const { start, count, skipCreate, skipRemoved } = parseArgs();

  console.log('🚀 LIA MVP Batch Jira Sync');
  console.log('='.repeat(60));
  console.log(`  📋 Range: cards[${start}..${start + count}) (0-based)`);
  console.log(`  ⏭️  Skip create: ${skipCreate}`);
  console.log(`  ⏭️  Skip removed: ${skipRemoved}`);
  console.log(`  ⏱️  Delays: 200ms/item, 500ms/batch(10)`);
  console.log('='.repeat(60));

  const auth = await getJiraAuth();
  console.log('✅ Jira authenticated');

  console.log('\n📄 Phase 1: Parsing cards from docs/lia-mvp-cards-jira.md...');
  const docPath = path.resolve(__dirname, '../../docs/lia-mvp-cards-jira.md');
  const docContent = fs.readFileSync(docPath, 'utf-8');
  const allCards = parseAllCards(docContent);
  console.log(`  📊 Parsed ${allCards.length} total cards`);

  const mappingPath = path.resolve(__dirname, '../card-to-jira-key.json');
  const existingMapping: Record<string, string> = JSON.parse(fs.readFileSync(mappingPath, 'utf-8'));

  console.log('\n🏗️  Phase 2: Loading epic keys...');
  for (const [epicName, epicKey] of Object.entries(EPICS_ALREADY_CREATED)) {
    createdEpicKeys[epicName] = epicKey;
    console.log(`  ✅ ${epicName} → ${epicKey}`);
  }

  const results: SyncResult[] = [];
  let successCount = 0;
  let errorCount = 0;
  let skippedCount = 0;

  if (!skipCreate) {
    console.log('\n📝 Phase 3: Creating new cards (if any without Jira key in range)...');
    const cardsInRange = allCards.slice(start, start + count);
    const newCardsInRange = cardsInRange.filter(c => !existingMapping[c.code] && !REMOVED_CARDS[c.code]);

    if (newCardsInRange.length === 0) {
      console.log('  📊 No new cards to create in this range');
    } else {
      console.log(`  📊 ${newCardsInRange.length} cards to create`);
      await processBatch(newCardsInRange, 10, 500, 200, async (card, idx) => {
        const epicKey = getEpicKeyForCard(card.code);
        try {
          const jiraKey = await createIssue(auth, card, epicKey);
          results.push({ cardCode: card.code, jiraKey, action: 'created' });
          successCount++;
          console.log(`  ✅ [${idx + 1}/${newCardsInRange.length}] Created ${card.code} → ${jiraKey}`);
        } catch (err: any) {
          results.push({ cardCode: card.code, jiraKey: '', action: 'error', error: err.message });
          errorCount++;
          console.error(`  ❌ [${idx + 1}/${newCardsInRange.length}] Error creating ${card.code}: ${err.message}`);
        }
      });
    }
  } else {
    console.log('\n⏭️  Phase 3: Skipped (--skip-create)');
  }

  console.log('\n🔄 Phase 4: Updating cards in range...');
  const cardsToUpdate = allCards.slice(start, start + count).filter(c => {
    if (REMOVED_CARDS[c.code]) {
      console.log(`  ⏭️  Skipping removed card: ${c.code}`);
      skippedCount++;
      return false;
    }
    const jiraKey = existingMapping[c.code];
    if (!jiraKey) {
      console.log(`  ⏭️  Skipping card without Jira key: ${c.code}`);
      skippedCount++;
      return false;
    }
    return true;
  });

  console.log(`  📊 ${cardsToUpdate.length} cards to update (from index ${start} to ${Math.min(start + count, allCards.length) - 1})`);

  await processBatch(cardsToUpdate, 10, 500, 200, async (card, idx) => {
    const jiraKey = existingMapping[card.code];
    const epicKey = getEpicKeyForCard(card.code);
    try {
      await updateIssue(auth, jiraKey, card, epicKey);
      results.push({ cardCode: card.code, jiraKey, action: 'updated' });
      successCount++;
      console.log(`  ✅ [${idx + 1}/${cardsToUpdate.length}] Updated ${card.code} → ${jiraKey}`);
    } catch (err: any) {
      results.push({ cardCode: card.code, jiraKey, action: 'error', error: err.message });
      errorCount++;
      console.error(`  ❌ [${idx + 1}/${cardsToUpdate.length}] Error updating ${card.code} (${jiraKey}): ${err.message}`);
    }
  });

  if (!skipRemoved) {
    console.log('\n🗑️  Phase 5: Marking removed/obsolete cards...');
    for (const [code, info] of Object.entries(REMOVED_CARDS)) {
      try {
        await markRemoved(auth, info.jiraKey, code, info.label, info.prefix);
        results.push({ cardCode: code, jiraKey: info.jiraKey, action: 'removed' });
        successCount++;
        console.log(`  ✅ Marked ${code} (${info.jiraKey}) as ${info.prefix}`);
        await delay(200);
      } catch (err: any) {
        results.push({ cardCode: code, jiraKey: info.jiraKey, action: 'error', error: err.message });
        errorCount++;
        console.error(`  ❌ Error marking ${code}: ${err.message}`);
      }
    }
  } else {
    console.log('\n⏭️  Phase 5: Skipped (--skip-removed)');
  }

  const syncResultsPath = path.resolve(__dirname, `sync-batch-results-${start}-${count}.json`);
  const syncOutput = {
    timestamp: new Date().toISOString(),
    batchArgs: { start, count, skipCreate, skipRemoved },
    totalCardsParsed: allCards.length,
    rangeProcessed: `[${start}, ${Math.min(start + count, allCards.length)})`,
    created: results.filter(r => r.action === 'created').length,
    updated: results.filter(r => r.action === 'updated').length,
    removed: results.filter(r => r.action === 'removed').length,
    skipped: skippedCount,
    errors: results.filter(r => r.action === 'error').length,
    successCount,
    errorCount,
    results,
  };
  fs.writeFileSync(syncResultsPath, JSON.stringify(syncOutput, null, 2) + '\n');

  console.log('\n' + '='.repeat(60));
  console.log('📊 BATCH SYNC SUMMARY');
  console.log('='.repeat(60));
  console.log(`  Total cards parsed: ${allCards.length}`);
  console.log(`  Range processed: [${start}, ${Math.min(start + count, allCards.length)})`);
  console.log(`  Created: ${syncOutput.created}`);
  console.log(`  Updated: ${syncOutput.updated}`);
  console.log(`  Removed/Obsolete: ${syncOutput.removed}`);
  console.log(`  Skipped: ${skippedCount}`);
  console.log(`  Errors: ${syncOutput.errors}`);
  console.log(`  Results saved to: ${syncResultsPath}`);
  console.log('='.repeat(60));

  if (errorCount > 0) {
    console.log('\n⚠️  Some operations failed. Check results file for details.');
    process.exit(1);
  } else {
    console.log('\n🎉 Batch completed successfully!');
  }
}

main().catch(err => {
  console.error('💥 Fatal error:', err);
  process.exit(1);
});
