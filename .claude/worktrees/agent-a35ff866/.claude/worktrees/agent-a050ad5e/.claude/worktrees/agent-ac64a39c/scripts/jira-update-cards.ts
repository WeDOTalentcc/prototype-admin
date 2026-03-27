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

interface SyncedCard {
  jiraKey: string;
  docCode: string;
}

interface JiraAuth {
  accessToken: string;
  cloudId: string;
  baseUrl: string;
}

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

async function updateJiraCard(
  auth: JiraAuth,
  jiraKey: string, 
  card: CardData
): Promise<boolean> {
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
          description: description,
          labels: card.labels,
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`   ❌ Erro ao atualizar ${jiraKey}: ${response.status}`);
      console.error(`      ${errorText.substring(0, 200)}`);
      return false;
    }

    return true;
  } catch (error: any) {
    console.error(`   ❌ Erro ao atualizar ${jiraKey}:`, error.message || error);
    return false;
  }
}

async function main() {
  console.log('🔄 Iniciando atualização dos 100 cards sincronizados...\n');

  const docPath = path.join(process.cwd(), 'docs/lia-mvp-cards-jira.md');
  const resultPath = path.join(process.cwd(), 'scripts/jira-diagnostic-result.json');

  if (!fs.existsSync(docPath)) {
    console.error('❌ Documento lia-mvp-cards-jira.md não encontrado');
    process.exit(1);
  }

  if (!fs.existsSync(resultPath)) {
    console.error('❌ Resultado do diagnóstico não encontrado. Execute jira-diagnostic.ts primeiro.');
    process.exit(1);
  }

  const docContent = fs.readFileSync(docPath, 'utf-8');
  const diagnosticResult = JSON.parse(fs.readFileSync(resultPath, 'utf-8'));
  const syncedCards: SyncedCard[] = diagnosticResult.cardsOk || [];

  console.log(`📄 Documento carregado: ${docPath}`);
  console.log(`📊 Cards sincronizados a atualizar: ${syncedCards.length}\n`);

  const auth = await getJiraAuth();
  console.log(`✅ Autenticação Jira obtida (Cloud ID: ${auth.cloudId})\n`);

  let successCount = 0;
  let errorCount = 0;
  let notFoundCount = 0;

  const updateResults: { jiraKey: string; docCode: string; status: string; labels?: string[] }[] = [];

  for (let i = 0; i < syncedCards.length; i++) {
    const { jiraKey, docCode } = syncedCards[i];
    console.log(`[${i + 1}/${syncedCards.length}] Processando ${jiraKey} (${docCode})...`);

    const cardData = parseCardFromDocument(docContent, docCode);
    
    if (!cardData) {
      console.log(`   ⚠️ Card ${docCode} não encontrado no documento`);
      notFoundCount++;
      updateResults.push({ jiraKey, docCode, status: 'not_found' });
      continue;
    }

    const success = await updateJiraCard(auth, jiraKey, cardData);
    
    if (success) {
      successCount++;
      console.log(`   ✅ ${jiraKey} atualizado com sucesso`);
      console.log(`      Labels: ${cardData.labels.join(', ')}`);
      updateResults.push({ jiraKey, docCode, status: 'success', labels: cardData.labels });
    } else {
      errorCount++;
      updateResults.push({ jiraKey, docCode, status: 'error' });
    }

    if ((i + 1) % 10 === 0) {
      console.log(`\n📊 Progresso: ${i + 1}/${syncedCards.length} processados\n`);
    }

    await new Promise(resolve => setTimeout(resolve, 300));
  }

  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('                    📋 RELATÓRIO FINAL');
  console.log('═══════════════════════════════════════════════════════════════\n');
  console.log(`   ✅ Atualizados com sucesso: ${successCount}`);
  console.log(`   ❌ Erros: ${errorCount}`);
  console.log(`   ⚠️ Não encontrados no doc: ${notFoundCount}`);
  console.log(`   📊 Total processado: ${syncedCards.length}`);

  const outputPath = path.join(process.cwd(), 'scripts/jira-update-result.json');
  fs.writeFileSync(outputPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    totalProcessed: syncedCards.length,
    successCount,
    errorCount,
    notFoundCount,
    results: updateResults,
  }, null, 2));
  
  console.log(`\n💾 Resultado salvo em: ${outputPath}`);
  console.log('\n✅ Atualização concluída!');
}

main().catch(console.error);
