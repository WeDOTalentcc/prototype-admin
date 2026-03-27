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

  const resources = await resourcesResponse.json() as any[];
  if (resources.length === 0) {
    throw new Error('Nenhum site Jira encontrado');
  }

  const cloudId = resources[0].id;
  const baseUrl = `https://api.atlassian.com/ex/jira/${cloudId}`;

  return { accessToken, cloudId, baseUrl };
}

async function searchJqlNew(auth: JiraAuth, jql: string): Promise<any[]> {
  const response = await fetch(`${auth.baseUrl}/rest/api/3/search/jql`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${auth.accessToken}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      jql: jql,
      maxResults: 50,
      fields: ['summary', 'labels', 'status', 'description']
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`   Erro na busca JQL: ${response.status}`);
    console.error(`      JQL: ${jql}`);
    console.error(`      ${errorText.substring(0, 300)}`);
    return [];
  }

  const data = await response.json() as any;
  return data.issues || [];
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

async function main() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('   🔍 Busca e Atualização de MAP-002 e MAP-003 no Jira');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const docPath = path.join(process.cwd(), 'docs/lia-mvp-cards-jira.md');
  const docContent = fs.readFileSync(docPath, 'utf-8');
  console.log(`📄 Documento carregado\n`);

  const auth = await getJiraAuth();
  console.log(`✅ Autenticação Jira obtida (Cloud ID: ${auth.cloudId})\n`);

  console.log('--- FASE 1: Buscar cards existentes do Épico 3 ---\n');

  const jql = 'project = WT AND labels = "epic-mapping" ORDER BY summary ASC';
  console.log(`🔍 JQL: ${jql}\n`);
  
  const issues = await searchJqlNew(auth, jql);
  
  if (issues.length === 0) {
    console.log('⚠️ Nenhuma issue encontrada com label epic-mapping.');
    console.log('Tentando busca alternativa por summary...\n');
    
    const jql2 = 'project = WT AND summary ~ "MAP-002" ORDER BY summary ASC';
    console.log(`🔍 JQL alternativa: ${jql2}\n`);
    const issues2 = await searchJqlNew(auth, jql2);
    
    if (issues2.length > 0) {
      console.log(`✅ Encontradas ${issues2.length} issues para MAP-002:`);
      for (const issue of issues2) {
        console.log(`   - ${issue.key}: ${issue.fields?.summary} [Labels: ${(issue.fields?.labels || []).join(', ')}]`);
      }
      issues.push(...issues2);
    }

    await new Promise(resolve => setTimeout(resolve, 500));
    
    const jql3 = 'project = WT AND summary ~ "MAP-003" ORDER BY summary ASC';
    console.log(`\n🔍 JQL alternativa: ${jql3}\n`);
    const issues3 = await searchJqlNew(auth, jql3);
    
    if (issues3.length > 0) {
      console.log(`✅ Encontradas ${issues3.length} issues para MAP-003:`);
      for (const issue of issues3) {
        console.log(`   - ${issue.key}: ${issue.fields?.summary} [Labels: ${(issue.fields?.labels || []).join(', ')}]`);
      }
      issues.push(...issues3);
    }
  } else {
    console.log(`✅ Encontradas ${issues.length} issues com label epic-mapping:\n`);
    for (const issue of issues) {
      console.log(`   - ${issue.key}: ${issue.fields?.summary}`);
      console.log(`     Labels: ${(issue.fields?.labels || []).join(', ')}`);
      console.log(`     Status: ${issue.fields?.status?.name || 'N/A'}`);
    }
  }

  console.log('\n--- FASE 2: Atualizar MAP-002 e MAP-003 ---\n');

  const cardsToUpdate: { code: string; jiraKey: string | null }[] = [
    { code: 'MAP-002', jiraKey: null },
    { code: 'MAP-003', jiraKey: null },
  ];

  for (const card of cardsToUpdate) {
    const found = issues.find(i => 
      i.fields?.summary?.includes(card.code) || 
      (i.fields?.labels || []).includes(card.code.toLowerCase())
    );
    if (found) {
      card.jiraKey = found.key;
    }
  }

  for (const card of cardsToUpdate) {
    const cardData = parseCardFromDocument(docContent, card.code);
    if (!cardData) {
      console.log(`❌ ${card.code} não encontrado no documento`);
      continue;
    }

    if (!card.jiraKey) {
      console.log(`⚠️ ${card.code} não encontrado no Jira - pulando atualização`);
      console.log(`   Dados do documento disponíveis:`);
      console.log(`   Título: ${cardData.titulo}`);
      console.log(`   Labels: ${cardData.labels.join(', ')}`);
      continue;
    }

    console.log(`📝 Atualizando ${card.jiraKey} (${card.code})...`);
    
    const description = formatDescriptionADF(cardData);
    const response = await fetch(`${auth.baseUrl}/rest/api/3/issue/${card.jiraKey}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${auth.accessToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        fields: {
          summary: `${card.code}: ${cardData.titulo}`,
          description: description,
          labels: cardData.labels,
        }
      })
    });

    if (response.ok) {
      console.log(`   ✅ ${card.jiraKey} atualizado com sucesso`);
      console.log(`      Novo título: ${card.code}: ${cardData.titulo}`);
      console.log(`      Labels: ${cardData.labels.join(', ')}`);
    } else {
      const errorText = await response.text();
      console.log(`   ❌ Erro ao atualizar ${card.jiraKey}: ${response.status}`);
      console.log(`      ${errorText.substring(0, 300)}`);
    }

    await new Promise(resolve => setTimeout(resolve, 500));
  }

  console.log('\n✅ Script concluído!');
}

main().catch(console.error);
