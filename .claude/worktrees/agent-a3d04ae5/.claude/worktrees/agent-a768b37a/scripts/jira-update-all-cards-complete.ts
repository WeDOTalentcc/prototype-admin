import * as fs from 'fs';
import * as path from 'path';

interface JiraAuth {
  accessToken: string;
  cloudId: string;
  baseUrl: string;
}

interface CardData {
  codigo: string;
  titulo: string;
  tipo: string;
  sprint: string;
  pontos: string;
  prioridade: string;
  epic: string;
  status: string;
  dependencias: string;
  descricaoCompleta: string;
  labels: string[];
  wdtYaml?: string;
  wdtPrompt?: string;
}

interface CardMapping {
  jiraKey: string;
  mapCode: string;
  wdtCode?: string;
}

const CARD_MAPPINGS: CardMapping[] = [
  { jiraKey: 'WT-905',  mapCode: 'MAP-001' },
  { jiraKey: 'WT-906',  mapCode: 'MAP-002' },
  { jiraKey: 'WT-907',  mapCode: 'MAP-003' },
  { jiraKey: 'WT-908',  mapCode: 'MAP-004' },
  { jiraKey: 'WT-909',  mapCode: 'MAP-005' },
  { jiraKey: 'WT-910',  mapCode: 'MAP-006' },
  { jiraKey: 'WT-1280', mapCode: 'MAP-007', wdtCode: 'WDT-001' },
  { jiraKey: 'WT-1281', mapCode: 'MAP-008', wdtCode: 'WDT-002' },
  { jiraKey: 'WT-1282', mapCode: 'MAP-009', wdtCode: 'WDT-003' },
  { jiraKey: 'WT-1283', mapCode: 'MAP-010', wdtCode: 'WDT-004' },
  { jiraKey: 'WT-1284', mapCode: 'MAP-011', wdtCode: 'WDT-006' },
  { jiraKey: 'WT-1285', mapCode: 'MAP-012', wdtCode: 'WDT-007' },
  { jiraKey: 'WT-1286', mapCode: 'MAP-013', wdtCode: 'WDT-005' },
];

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
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  );

  const connData = await connResponse.json();
  const conn = (connData as any).items?.[0];
  const accessToken = conn?.settings?.access_token;

  if (!accessToken) {
    throw new Error('Token Jira não encontrado');
  }

  const resourcesResponse = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json'
    }
  });

  if (!resourcesResponse.ok) {
    throw new Error('Erro ao obter recursos Atlassian');
  }

  const resources = await resourcesResponse.json() as any[];
  if (resources.length === 0) {
    throw new Error('Nenhum site Jira encontrado');
  }

  const cloudId = resources[0].id;
  const baseUrl = `https://api.atlassian.com/ex/jira/${cloudId}`;

  return { accessToken, cloudId, baseUrl };
}

async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function getExistingLabels(auth: JiraAuth, jiraKey: string): Promise<string[]> {
  const response = await fetch(`${auth.baseUrl}/rest/api/3/issue/${jiraKey}?fields=labels`, {
    headers: {
      'Authorization': `Bearer ${auth.accessToken}`,
      'Accept': 'application/json'
    }
  });

  if (!response.ok) {
    console.error(`   ⚠️ Erro ao buscar labels de ${jiraKey}: ${response.status}`);
    return [];
  }

  const data = await response.json() as any;
  return data.fields?.labels || [];
}

function parseMapCardFromDocument(content: string, cardCode: string): CardData | null {
  const cardPattern = new RegExp(
    `### CARD ${cardCode}:[^\\n]*\\n\\n\`\`\`yaml\\n([\\s\\S]*?)\`\`\``,
    'i'
  );
  
  const match = content.match(cardPattern);
  if (!match) {
    return null;
  }
  
  const yamlContent = match[1];
  
  const extractField = (field: string): string => {
    const fieldPattern = new RegExp(`^${field}:\\s*(.*)$`, 'mi');
    const fieldMatch = yamlContent.match(fieldPattern);
    return fieldMatch ? fieldMatch[1].trim() : '';
  };

  const titulo = extractField('Titulo');
  const tipo = extractField('Tipo');
  const sprint = extractField('Sprint');
  const pontos = extractField('Pontos');
  const prioridade = extractField('Prioridade');
  const epic = extractField('Epic');
  const status = extractField('Status');
  const dependencias = extractField('Dependencias');

  const labels: string[] = ['lia-mvp'];
  
  if (sprint) labels.push(`sprint-${sprint}`);
  if (tipo) {
    const tipoNorm = tipo.toLowerCase()
      .replace('integração', 'integracao')
      .replace(/\s+/g, '-');
    labels.push(`tipo-${tipoNorm}`);
  }
  if (epic) labels.push(epic.toLowerCase().replace(/\s+/g, '-'));
  if (prioridade) {
    const prioMap: Record<string, string> = {
      'crítica': 'priority-critica',
      'critica': 'priority-critica',
      'alta': 'priority-alta',
      'média': 'priority-media',
      'media': 'priority-media',
      'baixa': 'priority-baixa'
    };
    const prioLabel = prioMap[prioridade.toLowerCase()];
    if (prioLabel) labels.push(prioLabel);
  }
  labels.push(cardCode.toLowerCase());

  const tipoLower = tipo.toLowerCase();
  if (tipoLower.includes('backend') || tipoLower === 'task' || tipoLower === 'story') {
    labels.push('area-backend');
  } else if (tipoLower.includes('frontend')) {
    labels.push('area-frontend');
  } else if (tipoLower.includes('full-stack') || tipoLower.includes('full stack') || tipoLower.includes('fullstack')) {
    labels.push('area-fullstack');
  } else if (tipoLower.includes('ai') || tipoLower.includes('ia')) {
    labels.push('area-ia');
  }

  return {
    codigo: cardCode,
    titulo: titulo.replace(/^["'\[]|["'\]]$/g, ''),
    tipo,
    sprint,
    pontos,
    prioridade,
    epic,
    status,
    dependencias,
    descricaoCompleta: yamlContent,
    labels: [...new Set(labels)],
  };
}

function parseWdtYaml(content: string, wdtCode: string): string | null {
  const cardPattern = new RegExp(
    `### CARD ${wdtCode}:[^\\n]*\\n\\n\`\`\`yaml\\n([\\s\\S]*?)\`\`\``,
    'i'
  );
  
  const match = content.match(cardPattern);
  return match ? match[1] : null;
}

function parseWdtPrompt(content: string, wdtCode: string): string | null {
  const promptHeaderPattern = new RegExp(
    `#### Prompt para IA \\(Cursor/VSCode\\) — ${wdtCode}\\n\\n\`\`\`\\n([\\s\\S]*?)\`\`\``,
    'i'
  );
  
  const match = content.match(promptHeaderPattern);
  return match ? match[1] : null;
}

function getAreaLabel(card: CardData): string {
  const titulo = card.titulo.toLowerCase();
  const tipo = card.tipo.toLowerCase();
  
  if (titulo.includes('[be]') || tipo === 'backend' || tipo === 'task') {
    return 'area-backend';
  } else if (titulo.includes('[fe]') || tipo === 'frontend') {
    return 'area-frontend';
  } else if (titulo.includes('[full-stack]') || tipo.includes('full-stack') || tipo.includes('fullstack')) {
    return 'area-fullstack';
  } else if (titulo.includes('[ai]') || tipo === 'ai' || tipo === 'ia') {
    return 'area-ia';
  }
  return 'area-backend';
}

function buildLabels(card: CardData, mapping: CardMapping, existingLabels: string[]): string[] {
  const labels = new Set<string>(existingLabels);
  
  labels.add('lia-mvp');
  if (card.sprint) labels.add(`sprint-${card.sprint}`);
  
  if (card.tipo) {
    const tipoLower = card.tipo.toLowerCase();
    if (tipoLower.includes('backend')) {
      labels.add('tipo-backend');
    } else if (tipoLower.includes('frontend')) {
      labels.add('tipo-frontend');
    } else if (tipoLower.includes('full-stack') || tipoLower.includes('fullstack')) {
      labels.add('tipo-full-stack');
    } else if (tipoLower.includes('ai') || tipoLower.includes('ia')) {
      labels.add('tipo-ai');
    } else if (tipoLower === 'story') {
      labels.add('tipo-story');
    } else if (tipoLower === 'task') {
      labels.add('tipo-task');
    } else {
      const tipoNorm = tipoLower
        .replace('integração', 'integracao')
        .replace(/\s+/g, '-');
      labels.add(`tipo-${tipoNorm}`);
    }
  }

  labels.add('epic-mapping');
  
  if (card.prioridade) {
    const prioMap: Record<string, string> = {
      'crítica': 'priority-critica',
      'critica': 'priority-critica',
      'alta': 'priority-alta',
      'média': 'priority-media',
      'media': 'priority-media',
      'baixa': 'priority-baixa'
    };
    const prioLabel = prioMap[card.prioridade.toLowerCase()];
    if (prioLabel) labels.add(prioLabel);
  }
  
  labels.add(mapping.mapCode.toLowerCase());
  
  const areaLabel = getAreaLabel(card);
  labels.add(areaLabel);
  
  if (mapping.wdtCode) {
    labels.add('talent-funnel');
    labels.add('quick-win');
  }
  
  return [...labels];
}

function formatDescriptionADF(card: CardData): object {
  const content: any[] = [
    {
      type: "heading",
      attrs: { level: 2 },
      content: [{ type: "text", text: `${card.codigo}: ${card.titulo}` }]
    },
    {
      type: "table",
      attrs: { isNumberColumnEnabled: false, layout: "default" },
      content: [
        {
          type: "tableRow",
          content: [
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Tipo", marks: [{ type: "strong" }] }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.tipo || "-" }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Sprint", marks: [{ type: "strong" }] }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.sprint || "-" }] }] }
          ]
        },
        {
          type: "tableRow",
          content: [
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Pontos", marks: [{ type: "strong" }] }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.pontos || "-" }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Prioridade", marks: [{ type: "strong" }] }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.prioridade || "-" }] }] }
          ]
        },
        {
          type: "tableRow",
          content: [
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Epic", marks: [{ type: "strong" }] }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.epic || "-" }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Dependências", marks: [{ type: "strong" }] }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.dependencias || "-" }] }] }
          ]
        },
        {
          type: "tableRow",
          content: [
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "Status", marks: [{ type: "strong" }] }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: card.status || "-" }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "", marks: [{ type: "strong" }] }] }] },
            { type: "tableCell", content: [{ type: "paragraph", content: [{ type: "text", text: "" }] }] }
          ]
        }
      ]
    },
    {
      type: "rule"
    },
    {
      type: "heading",
      attrs: { level: 3 },
      content: [{ type: "text", text: "Especificação Completa" }]
    },
    {
      type: "codeBlock",
      attrs: { language: "yaml" },
      content: [{ type: "text", text: card.descricaoCompleta }]
    }
  ];

  if (card.wdtYaml) {
    content.push({
      type: "rule"
    });
    content.push({
      type: "heading",
      attrs: { level: 3 },
      content: [{ type: "text", text: "Especificação WDT Detalhada" }]
    });
    content.push({
      type: "codeBlock",
      attrs: { language: "yaml" },
      content: [{ type: "text", text: card.wdtYaml }]
    });
  }

  if (card.wdtPrompt) {
    content.push({
      type: "rule"
    });
    content.push({
      type: "heading",
      attrs: { level: 3 },
      content: [{ type: "text", text: "Prompt para IA (Cursor/VSCode)" }]
    });
    content.push({
      type: "codeBlock",
      attrs: { language: "text" },
      content: [{ type: "text", text: card.wdtPrompt }]
    });
  }

  return {
    version: 1,
    type: "doc",
    content
  };
}

async function updateJiraIssue(
  auth: JiraAuth,
  jiraKey: string,
  card: CardData,
  labels: string[]
): Promise<boolean> {
  const description = formatDescriptionADF(card);
  
  const response = await fetch(`${auth.baseUrl}/rest/api/3/issue/${jiraKey}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${auth.accessToken}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      fields: {
        summary: `${card.codigo}: ${card.titulo}`,
        description: description,
        labels: labels,
      }
    })
  });

  if (response.ok) {
    return true;
  } else {
    const errorText = await response.text();
    console.error(`   ❌ Erro ao atualizar ${jiraKey}: ${response.status}`);
    console.error(`      ${errorText.substring(0, 500)}`);
    return false;
  }
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('   📋 Atualização Completa de TODOS os 13 Cards Epic 3');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const mapDocPath = path.join(process.cwd(), 'docs/lia-mvp-cards-jira.md');
  const wdtDocPath = path.join(process.cwd(), 'docs/epic-wdt-talent-funnel.md');
  
  const mapDocContent = fs.readFileSync(mapDocPath, 'utf-8');
  const wdtDocContent = fs.readFileSync(wdtDocPath, 'utf-8');
  console.log(`📄 Documentos carregados:`);
  console.log(`   - lia-mvp-cards-jira.md (${mapDocContent.length} chars)`);
  console.log(`   - epic-wdt-talent-funnel.md (${wdtDocContent.length} chars)\n`);

  const auth = await getJiraAuth();
  console.log(`✅ Autenticação Jira obtida (Cloud ID: ${auth.cloudId})\n`);

  let successCount = 0;
  let errorCount = 0;
  const results: { card: string; jiraKey: string; status: string; labels: number }[] = [];

  for (let i = 0; i < CARD_MAPPINGS.length; i++) {
    const mapping = CARD_MAPPINGS[i];
    console.log(`\n--- [${i + 1}/${CARD_MAPPINGS.length}] ${mapping.mapCode} → ${mapping.jiraKey} ${mapping.wdtCode ? `(${mapping.wdtCode})` : ''} ---`);

    const cardData = parseMapCardFromDocument(mapDocContent, mapping.mapCode);
    if (!cardData) {
      console.error(`   ❌ ${mapping.mapCode} não encontrado em lia-mvp-cards-jira.md`);
      errorCount++;
      results.push({ card: mapping.mapCode, jiraKey: mapping.jiraKey, status: 'PARSE_ERROR', labels: 0 });
      continue;
    }
    console.log(`   📝 Título: ${cardData.titulo}`);
    console.log(`   📊 Tipo: ${cardData.tipo} | Sprint: ${cardData.sprint} | Pontos: ${cardData.pontos}`);

    if (mapping.wdtCode) {
      const wdtYaml = parseWdtYaml(wdtDocContent, mapping.wdtCode);
      if (wdtYaml) {
        cardData.wdtYaml = wdtYaml;
        console.log(`   📎 WDT YAML carregado (${wdtYaml.length} chars)`);
      } else {
        console.warn(`   ⚠️ WDT YAML não encontrado para ${mapping.wdtCode}`);
      }

      const wdtPrompt = parseWdtPrompt(wdtDocContent, mapping.wdtCode);
      if (wdtPrompt) {
        cardData.wdtPrompt = wdtPrompt;
        console.log(`   🤖 Prompt IA carregado (${wdtPrompt.length} chars)`);
      } else {
        console.warn(`   ⚠️ Prompt IA não encontrado para ${mapping.wdtCode}`);
      }
    }

    console.log(`   🔍 Buscando labels existentes de ${mapping.jiraKey}...`);
    const existingLabels = await getExistingLabels(auth, mapping.jiraKey);
    console.log(`   📌 Labels existentes: [${existingLabels.join(', ')}]`);
    await delay(500);

    const mergedLabels = buildLabels(cardData, mapping, existingLabels);
    console.log(`   🏷️ Labels finais (${mergedLabels.length}): [${mergedLabels.join(', ')}]`);

    console.log(`   🚀 Atualizando ${mapping.jiraKey}...`);
    const success = await updateJiraIssue(auth, mapping.jiraKey, cardData, mergedLabels);
    
    if (success) {
      console.log(`   ✅ ${mapping.jiraKey} atualizado com sucesso!`);
      successCount++;
      results.push({ card: mapping.mapCode, jiraKey: mapping.jiraKey, status: 'OK', labels: mergedLabels.length });
    } else {
      errorCount++;
      results.push({ card: mapping.mapCode, jiraKey: mapping.jiraKey, status: 'ERROR', labels: mergedLabels.length });
    }

    await delay(500);
  }

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('   📊 RESUMO DA ATUALIZAÇÃO');
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  console.log(`   ✅ Sucesso: ${successCount}/${CARD_MAPPINGS.length}`);
  console.log(`   ❌ Erros:   ${errorCount}/${CARD_MAPPINGS.length}\n`);
  
  console.log('   Detalhes:');
  console.log('   ┌──────────┬──────────┬────────┬────────┐');
  console.log('   │ Card     │ Jira Key │ Status │ Labels │');
  console.log('   ├──────────┼──────────┼────────┼────────┤');
  for (const r of results) {
    const icon = r.status === 'OK' ? '✅' : '❌';
    console.log(`   │ ${r.card.padEnd(8)} │ ${r.jiraKey.padEnd(8)} │ ${icon}${r.status.padEnd(5)}│ ${String(r.labels).padEnd(6)} │`);
  }
  console.log('   └──────────┴──────────┴────────┴────────┘');
  
  console.log('\n✅ Script concluído!');
}

main().catch(err => {
  console.error('\n❌ Erro fatal:', err.message || err);
  process.exit(1);
});
