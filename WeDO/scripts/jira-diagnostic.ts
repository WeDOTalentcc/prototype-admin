import { jiraService } from '../plataforma-lia/src/lib/api/jira-service';
import * as fs from 'fs';
import * as path from 'path';

interface CardFromDoc {
  codigo: string;
  titulo: string;
  tipo: string;
  status: string;
  jiraKey?: string;
}

interface DiagnosticResult {
  timestamp: string;
  projectKey: string;
  totalCardsInDoc: number;
  totalCardsInJira: number;
  cardsToCreate: CardFromDoc[];
  cardsToUpdate: { jiraKey: string; docCode: string; reason: string }[];
  cardsToDelete: { jiraKey: string; summary: string; reason: string }[];
  cardsOk: { jiraKey: string; docCode: string }[];
  warnings: string[];
}

async function runDiagnostic(): Promise<DiagnosticResult> {
  const projectKey = 'WT';
  const result: DiagnosticResult = {
    timestamp: new Date().toISOString(),
    projectKey,
    totalCardsInDoc: 0,
    totalCardsInJira: 0,
    cardsToCreate: [],
    cardsToUpdate: [],
    cardsToDelete: [],
    cardsOk: [],
    warnings: [],
  };

  console.log('🔍 Iniciando diagnóstico do Jira...\n');
  console.log(`📁 Projeto: ${projectKey} (wedotalent tasks 2026)\n`);

  // 1. Ler e parsear o documento de cards
  console.log('📄 Lendo documento lia-mvp-cards-jira.md...');
  const docPath = path.join(process.cwd(), 'docs', 'lia-mvp-cards-jira.md');
  const docContent = fs.readFileSync(docPath, 'utf-8');

  // Extrair códigos de cards do documento
  const cardCodes: Map<string, CardFromDoc> = new Map();
  
  // Padrões de códigos de cards do documento
  const codePatterns = [
    /\| (AUTH-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (WIZ-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (MAP-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (WSI-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (TRI-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (SCO-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (GAT-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (TPL-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (AGE-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (NOT-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (KAN-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (TAB-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (PRV-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (VAG-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (INT-[A-Z]+-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (JD-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (JDW-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (CFG-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (IMP-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (AGT-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (DAT-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
    /\| (ENT-\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|/g,
  ];

  for (const pattern of codePatterns) {
    let match;
    while ((match = pattern.exec(docContent)) !== null) {
      const code = match[1].trim();
      if (!cardCodes.has(code)) {
        cardCodes.set(code, {
          codigo: code,
          titulo: match[2].trim(),
          tipo: match[3].trim(),
          status: match[4].trim(),
        });
      }
    }
  }

  result.totalCardsInDoc = cardCodes.size;
  console.log(`   ✅ Encontrados ${cardCodes.size} cards no documento\n`);

  // 2. Buscar cards no Jira (busca ampla)
  console.log('🔄 Buscando cards no Jira (projeto WT)...');
  
  // Primeiro, buscar todas as issues do projeto
  const allIssues = await searchAllProjectIssues(projectKey, 1000);
  
  // Também tentar buscar por labels específicas
  const liaMvpIssues = await searchIssuesByLabel(projectKey, 'lia-mvp', 500);
  const configAdminIssues = await searchIssuesByLabel(projectKey, 'config-admin', 200);
  
  // Combinar todas as issues e remover duplicatas
  const jiraIssuesMap = new Map<string, any>();
  for (const issue of [...allIssues, ...liaMvpIssues, ...configAdminIssues]) {
    jiraIssuesMap.set(issue.issueKey, issue);
  }
  
  const jiraIssues = Array.from(jiraIssuesMap.values());
  result.totalCardsInJira = jiraIssues.length;
  console.log(`   ✅ Encontrados ${jiraIssues.length} cards únicos no Jira\n`);

  // 3. Criar mapeamento de código de card para issue Jira
  const jiraByCode = new Map<string, any>();
  const unmappedJiraIssues: any[] = [];

  for (const issue of jiraIssues) {
    const summary = issue.summary || '';
    // Tentar extrair código do summary (ex: "[FRONTEND] AUTH-001: Tela de Login")
    const codeMatch = summary.match(/([A-Z]+-[A-Z]*-?\d+)/);
    if (codeMatch) {
      const code = codeMatch[1];
      jiraByCode.set(code, issue);
    } else {
      unmappedJiraIssues.push(issue);
    }
  }

  console.log(`   📊 Cards Jira com código identificado: ${jiraByCode.size}`);
  console.log(`   ⚠️ Cards Jira sem código identificado: ${unmappedJiraIssues.length}\n`);

  // 4. Comparar documento com Jira
  console.log('📊 Analisando diferenças...\n');

  // Cards que estão no documento mas não no Jira (criar)
  for (const [code, docCard] of cardCodes) {
    if (!jiraByCode.has(code)) {
      // Verificar se é obsoleto/pós-mvp
      if (docCard.status.includes('Obsoleto') || docCard.status.includes('Pós-MVP') || docCard.status.includes('Consolidado')) {
        result.warnings.push(`${code}: Marcado como "${docCard.status}" no doc, não precisa criar`);
      } else {
        result.cardsToCreate.push(docCard);
      }
    } else {
      // Card existe, verificar se precisa atualizar
      const jiraIssue = jiraByCode.get(code)!;
      result.cardsOk.push({ jiraKey: jiraIssue.issueKey, docCode: code });
    }
  }

  // Cards que estão no Jira mas não no documento (verificar para exclusão)
  for (const [code, jiraIssue] of jiraByCode) {
    if (!cardCodes.has(code)) {
      result.cardsToDelete.push({
        jiraKey: jiraIssue.issueKey,
        summary: jiraIssue.summary,
        reason: 'Código não encontrado no documento atualizado',
      });
    }
  }

  // Cards sem código mapeado
  for (const issue of unmappedJiraIssues) {
    result.warnings.push(`${issue.issueKey}: "${issue.summary}" - Sem código de card identificado no título`);
  }

  // 5. Gerar relatório
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                    📋 RELATÓRIO DE DIAGNÓSTICO');
  console.log('═══════════════════════════════════════════════════════════════\n');

  console.log(`📅 Data: ${new Date().toLocaleDateString('pt-BR')}`);
  console.log(`📁 Projeto: ${projectKey} (wedotalent tasks 2026)\n`);

  console.log('📊 RESUMO:');
  console.log(`   Total de cards no documento: ${result.totalCardsInDoc}`);
  console.log(`   Total de cards no Jira: ${result.totalCardsInJira}`);
  console.log(`   Cards OK (sincronizados): ${result.cardsOk.length}`);
  console.log(`   Cards a CRIAR: ${result.cardsToCreate.length}`);
  console.log(`   Cards a EXCLUIR: ${result.cardsToDelete.length}`);
  console.log(`   Cards a ATUALIZAR: ${result.cardsToUpdate.length}`);
  console.log(`   Avisos: ${result.warnings.length}\n`);

  if (result.cardsToCreate.length > 0) {
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('🆕 CARDS A CRIAR:');
    console.log('═══════════════════════════════════════════════════════════════');
    for (const card of result.cardsToCreate) {
      console.log(`   • ${card.codigo}: ${card.titulo}`);
    }
    console.log('');
  }

  if (result.cardsToDelete.length > 0) {
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('🗑️ CARDS A EXCLUIR (avaliar):');
    console.log('═══════════════════════════════════════════════════════════════');
    for (const card of result.cardsToDelete) {
      console.log(`   • ${card.jiraKey}: ${card.summary}`);
      console.log(`     Motivo: ${card.reason}`);
    }
    console.log('');
  }

  if (result.cardsToUpdate.length > 0) {
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('🔄 CARDS A ATUALIZAR:');
    console.log('═══════════════════════════════════════════════════════════════');
    for (const card of result.cardsToUpdate) {
      console.log(`   • ${card.jiraKey} (${card.docCode}): ${card.reason}`);
    }
    console.log('');
  }

  if (result.warnings.length > 0) {
    console.log('═══════════════════════════════════════════════════════════════');
    console.log('⚠️ AVISOS:');
    console.log('═══════════════════════════════════════════════════════════════');
    for (const warning of result.warnings.slice(0, 20)) {
      console.log(`   • ${warning}`);
    }
    if (result.warnings.length > 20) {
      console.log(`   ... e mais ${result.warnings.length - 20} avisos`);
    }
    console.log('');
  }

  // Salvar resultado em JSON
  const resultPath = path.join(process.cwd(), 'scripts', 'jira-diagnostic-result.json');
  fs.writeFileSync(resultPath, JSON.stringify(result, null, 2));
  console.log(`\n💾 Resultado salvo em: ${resultPath}`);

  return result;
}

async function searchJqlIssues(jql: string, maxResults: number = 100): Promise<any[]> {
  const { accessToken, apiBaseUrl } = await getAuth();
  
  try {
    // Nova API de busca JQL (migração obrigatória)
    const response = await fetch(
      `${apiBaseUrl}/rest/api/3/search/jql`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jql,
          maxResults,
          fields: ['summary', 'status', 'labels', 'updated', 'issuetype'],
        }),
      }
    );
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Erro na busca JQL:`, response.status, errorText.substring(0, 300));
      return [];
    }
    
    const data = await response.json();
    console.log(`   📊 Query retornou ${data.total || 0} issues`);
    return (data.issues || []).map((issue: any) => ({
      issueKey: issue.key,
      summary: issue.fields?.summary || '',
      status: issue.fields?.status?.name || 'Unknown',
      labels: issue.fields?.labels || [],
      issueType: issue.fields?.issuetype?.name || 'Unknown',
      updatedAt: issue.fields?.updated || '',
    }));
  } catch (error) {
    console.error(`Erro ao buscar issues:`, error);
    return [];
  }
}

async function searchIssuesByLabel(projectKey: string, label: string, maxResults: number = 100): Promise<any[]> {
  return searchJqlIssues(`project = ${projectKey} AND labels = "${label}" ORDER BY key ASC`, maxResults);
}

async function searchAllProjectIssues(projectKey: string, maxResults: number = 500): Promise<any[]> {
  return searchJqlIssues(`project = ${projectKey} ORDER BY key ASC`, maxResults);
}

async function getAuth() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('Token de autenticação não encontrado');
  }

  const connResp = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=jira',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  );
  
  const connData = await connResp.json();
  const settings = connData.items?.[0]?.settings;
  const accessToken = settings?.access_token || settings?.oauth?.credentials?.access_token;
  
  if (!accessToken) {
    throw new Error('Token Jira não encontrado');
  }

  // Get cloud ID
  const resourcesResp = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json'
    }
  });
  
  const resources = await resourcesResp.json();
  const cloudId = resources[0]?.id;
  
  if (!cloudId) {
    throw new Error('Cloud ID não encontrado');
  }

  return {
    accessToken,
    apiBaseUrl: `https://api.atlassian.com/ex/jira/${cloudId}`,
  };
}

runDiagnostic()
  .then(result => {
    console.log('\n✅ Diagnóstico concluído!');
    process.exit(0);
  })
  .catch(error => {
    console.error('\n❌ Erro no diagnóstico:', error);
    process.exit(1);
  });
