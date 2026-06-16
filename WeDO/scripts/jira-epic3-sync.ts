import * as fs from 'fs';
import * as path from 'path';

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
}

interface JiraAuth {
  accessToken: string;
  cloudId: string;
  baseUrl: string;
}

interface JiraIssue {
  key: string;
  fields: {
    summary: string;
    labels: string[];
    status: { name: string };
    description: any;
  };
}

interface SyncResult {
  timestamp: string;
  phase1: {
    generalSearch: { total: number; issues: { key: string; summary: string; labels: string[]; status: string }[] };
    map002Search: { total: number; issues: { key: string; summary: string }[] };
    map003Search: { total: number; issues: { key: string; summary: string }[] };
  };
  phase2: {
    updates: { cardCode: string; jiraKey: string; status: string; error?: string }[];
    successCount: number;
    errorCount: number;
  };
  phase3: {
    creates: { cardCode: string; jiraKey?: string; status: string; labels?: string[]; error?: string }[];
    successCount: number;
    errorCount: number;
  };
  summary: {
    totalFound: number;
    totalUpdated: number;
    totalCreated: number;
    totalErrors: number;
  };
}

const CARDS_TO_UPDATE = ['MAP-002', 'MAP-003'];
const CARDS_TO_CREATE = ['MAP-007', 'MAP-008', 'MAP-009', 'MAP-010', 'MAP-011', 'MAP-012', 'MAP-013'];
const PROJECT_KEY = 'WT';

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
  const conn = connData.items?.[0];
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

  const resources = await resourcesResponse.json();
  if (resources.length === 0) {
    throw new Error('Nenhum site Jira encontrado');
  }

  const cloudId = resources[0].id;
  const baseUrl = `https://api.atlassian.com/ex/jira/${cloudId}`;

  return { accessToken, cloudId, baseUrl };
}

function parseCardFromDocument(content: string, cardCode: string): CardData | null {
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
    const match = yamlContent.match(fieldPattern);
    return match ? match[1].trim() : '';
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
  if (epic) labels.push(epic.toLowerCase());
  if (prioridade) {
    const prioMap: Record<string, string> = {
      'crítica': 'priority-critica',
      'alta': 'priority-alta',
      'média': 'priority-media',
      'baixa': 'priority-baixa'
    };
    const prioLabel = prioMap[prioridade.toLowerCase()];
    if (prioLabel) labels.push(prioLabel);
  }
  labels.push(cardCode.toLowerCase());

  const isNewCard = CARDS_TO_CREATE.includes(cardCode);
  if (isNewCard) {
    labels.push('talent-funnel');
    labels.push('quick-win');
  }

  return {
    codigo: cardCode,
    titulo,
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

function formatDescriptionADF(card: CardData): object {
  return {
    version: 1,
    type: "doc",
    content: [
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
    ]
  };
}

async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function searchJira(auth: JiraAuth, jql: string): Promise<JiraIssue[]> {
  const encodedJql = encodeURIComponent(jql);
  const url = `${auth.baseUrl}/rest/api/3/search?jql=${encodedJql}&fields=summary,labels,status,description&maxResults=100`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${auth.accessToken}`,
      'Accept': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`   ❌ Erro na busca JQL: ${response.status}`);
    console.error(`      JQL: ${jql}`);
    console.error(`      ${errorText.substring(0, 300)}`);
    return [];
  }

  const data = await response.json();
  return data.issues || [];
}

async function updateJiraCard(
  auth: JiraAuth,
  jiraKey: string,
  card: CardData
): Promise<{ success: boolean; error?: string }> {
  try {
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
          labels: card.labels,
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      return { success: false, error: `${response.status}: ${errorText.substring(0, 200)}` };
    }

    return { success: true };
  } catch (error: any) {
    return { success: false, error: error.message || String(error) };
  }
}

async function createJiraCard(
  auth: JiraAuth,
  card: CardData
): Promise<{ success: boolean; key?: string; error?: string }> {
  try {
    const description = formatDescriptionADF(card);
    
    const response = await fetch(`${auth.baseUrl}/rest/api/3/issue`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${auth.accessToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        fields: {
          project: { key: PROJECT_KEY },
          summary: `${card.codigo}: ${card.titulo}`,
          description: description,
          issuetype: { name: 'Task' },
          labels: card.labels,
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      return { success: false, error: `${response.status}: ${errorText.substring(0, 200)}` };
    }

    const result = await response.json();
    return { success: true, key: result.key };
  } catch (error: any) {
    return { success: false, error: error.message || String(error) };
  }
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('        🔄 EPIC 3 (Mapping) - Jira Sync Script');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const docPath = path.join(process.cwd(), 'docs/lia-mvp-cards-jira.md');

  if (!fs.existsSync(docPath)) {
    console.error('❌ Documento lia-mvp-cards-jira.md não encontrado');
    process.exit(1);
  }

  const docContent = fs.readFileSync(docPath, 'utf-8');
  console.log(`📄 Documento carregado: ${docPath}\n`);

  const auth = await getJiraAuth();
  console.log(`✅ Autenticação Jira obtida (Cloud ID: ${auth.cloudId})\n`);

  const syncResult: SyncResult = {
    timestamp: new Date().toISOString(),
    phase1: {
      generalSearch: { total: 0, issues: [] },
      map002Search: { total: 0, issues: [] },
      map003Search: { total: 0, issues: [] },
    },
    phase2: { updates: [], successCount: 0, errorCount: 0 },
    phase3: { creates: [], successCount: 0, errorCount: 0 },
    summary: { totalFound: 0, totalUpdated: 0, totalCreated: 0, totalErrors: 0 },
  };

  console.log('═══════════════════════════════════════════════════════════════');
  console.log('        📡 PHASE 1: Discovery - Searching Jira');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const generalJql = 'project = WT AND (labels = "epic-mapping" OR summary ~ "MAP-") ORDER BY summary ASC';
  console.log(`🔍 Busca geral: ${generalJql}\n`);
  const generalIssues = await searchJira(auth, generalJql);
  
  syncResult.phase1.generalSearch.total = generalIssues.length;
  console.log(`   📊 Encontrados: ${generalIssues.length} issues\n`);

  for (const issue of generalIssues) {
    const issueInfo = {
      key: issue.key,
      summary: issue.fields.summary,
      labels: issue.fields.labels || [],
      status: issue.fields.status?.name || 'Unknown',
    };
    syncResult.phase1.generalSearch.issues.push(issueInfo);
    console.log(`   📋 ${issue.key}: ${issue.fields.summary}`);
    console.log(`      Status: ${issueInfo.status} | Labels: ${issueInfo.labels.join(', ') || 'nenhuma'}`);
  }

  await delay(500);

  console.log(`\n🔍 Busca específica: MAP-002\n`);
  const map002Issues = await searchJira(auth, 'project = WT AND summary ~ "MAP-002"');
  syncResult.phase1.map002Search.total = map002Issues.length;
  for (const issue of map002Issues) {
    syncResult.phase1.map002Search.issues.push({ key: issue.key, summary: issue.fields.summary });
    console.log(`   📋 ${issue.key}: ${issue.fields.summary}`);
  }

  await delay(500);

  console.log(`\n🔍 Busca específica: MAP-003\n`);
  const map003Issues = await searchJira(auth, 'project = WT AND summary ~ "MAP-003"');
  syncResult.phase1.map003Search.total = map003Issues.length;
  for (const issue of map003Issues) {
    syncResult.phase1.map003Search.issues.push({ key: issue.key, summary: issue.fields.summary });
    console.log(`   📋 ${issue.key}: ${issue.fields.summary}`);
  }

  syncResult.summary.totalFound = generalIssues.length;

  const foundMap: Record<string, string> = {};
  for (const issue of generalIssues) {
    for (const code of CARDS_TO_UPDATE) {
      if (issue.fields.summary.includes(code)) {
        foundMap[code] = issue.key;
      }
    }
  }
  for (const issue of map002Issues) {
    if (issue.fields.summary.includes('MAP-002')) {
      foundMap['MAP-002'] = issue.key;
    }
  }
  for (const issue of map003Issues) {
    if (issue.fields.summary.includes('MAP-003')) {
      foundMap['MAP-003'] = issue.key;
    }
  }

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('        ✏️ PHASE 2: Update MAP-002 and MAP-003');
  console.log('═══════════════════════════════════════════════════════════════\n');

  for (const cardCode of CARDS_TO_UPDATE) {
    const jiraKey = foundMap[cardCode];
    
    if (!jiraKey) {
      console.log(`   ⚠️ ${cardCode}: Não encontrado no Jira - pulando atualização`);
      syncResult.phase2.updates.push({ cardCode, jiraKey: 'NOT_FOUND', status: 'skipped', error: 'Issue not found in Jira' });
      syncResult.phase2.errorCount++;
      continue;
    }

    console.log(`   🔄 Atualizando ${cardCode} (${jiraKey})...`);

    const cardData = parseCardFromDocument(docContent, cardCode);
    if (!cardData) {
      console.log(`      ⚠️ Card ${cardCode} não encontrado no documento`);
      syncResult.phase2.updates.push({ cardCode, jiraKey, status: 'not_in_doc', error: 'Card not found in document' });
      syncResult.phase2.errorCount++;
      continue;
    }

    const result = await updateJiraCard(auth, jiraKey, cardData);
    
    if (result.success) {
      console.log(`      ✅ ${jiraKey} atualizado com sucesso`);
      console.log(`         Título: ${cardData.titulo}`);
      console.log(`         Labels: ${cardData.labels.join(', ')}`);
      syncResult.phase2.updates.push({ cardCode, jiraKey, status: 'success' });
      syncResult.phase2.successCount++;
    } else {
      console.log(`      ❌ Erro: ${result.error}`);
      syncResult.phase2.updates.push({ cardCode, jiraKey, status: 'error', error: result.error });
      syncResult.phase2.errorCount++;
    }

    await delay(500);
  }

  syncResult.summary.totalUpdated = syncResult.phase2.successCount;

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('        🆕 PHASE 3: Create MAP-007 to MAP-013');
  console.log('═══════════════════════════════════════════════════════════════\n');

  for (let i = 0; i < CARDS_TO_CREATE.length; i++) {
    const cardCode = CARDS_TO_CREATE[i];
    console.log(`   [${i + 1}/${CARDS_TO_CREATE.length}] Criando ${cardCode}...`);

    const cardData = parseCardFromDocument(docContent, cardCode);
    if (!cardData) {
      console.log(`      ⚠️ Card ${cardCode} não encontrado no documento`);
      syncResult.phase3.creates.push({ cardCode, status: 'not_in_doc', error: 'Card not found in document' });
      syncResult.phase3.errorCount++;
      continue;
    }

    const result = await createJiraCard(auth, cardData);
    
    if (result.success) {
      console.log(`      ✅ Criado: ${result.key}`);
      console.log(`         Título: ${cardData.titulo}`);
      console.log(`         Labels: ${cardData.labels.join(', ')}`);
      syncResult.phase3.creates.push({ cardCode, jiraKey: result.key, status: 'success', labels: cardData.labels });
      syncResult.phase3.successCount++;
    } else {
      console.log(`      ❌ Erro: ${result.error}`);
      syncResult.phase3.creates.push({ cardCode, status: 'error', error: result.error });
      syncResult.phase3.errorCount++;
    }

    await delay(500);
  }

  syncResult.summary.totalCreated = syncResult.phase3.successCount;
  syncResult.summary.totalErrors = syncResult.phase2.errorCount + syncResult.phase3.errorCount;

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('                    📋 RELATÓRIO FINAL');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(`   📡 Phase 1 - Discovery:`);
  console.log(`      Issues encontrados: ${syncResult.summary.totalFound}`);
  console.log(`      MAP-002 encontrado: ${foundMap['MAP-002'] || 'NÃO'}`);
  console.log(`      MAP-003 encontrado: ${foundMap['MAP-003'] || 'NÃO'}`);
  console.log('');
  console.log(`   ✏️ Phase 2 - Updates:`);
  console.log(`      Atualizados com sucesso: ${syncResult.phase2.successCount}`);
  console.log(`      Erros: ${syncResult.phase2.errorCount}`);
  console.log('');
  console.log(`   🆕 Phase 3 - Creates:`);
  console.log(`      Criados com sucesso: ${syncResult.phase3.successCount}`);
  console.log(`      Erros: ${syncResult.phase3.errorCount}`);
  console.log('');
  console.log(`   📊 Total:`);
  console.log(`      Encontrados: ${syncResult.summary.totalFound}`);
  console.log(`      Atualizados: ${syncResult.summary.totalUpdated}`);
  console.log(`      Criados: ${syncResult.summary.totalCreated}`);
  console.log(`      Erros: ${syncResult.summary.totalErrors}`);

  if (syncResult.phase3.successCount > 0) {
    console.log('\n   📋 Cards criados:');
    syncResult.phase3.creates
      .filter(r => r.status === 'success')
      .forEach(r => console.log(`      - ${r.jiraKey} (${r.cardCode})`));
  }

  const outputPath = path.join(process.cwd(), 'scripts/jira-epic3-sync-result.json');
  fs.writeFileSync(outputPath, JSON.stringify(syncResult, null, 2));
  console.log(`\n💾 Resultado salvo em: ${outputPath}`);
  console.log('\n✅ Sincronização Epic 3 concluída!');
}

main().catch(console.error);
