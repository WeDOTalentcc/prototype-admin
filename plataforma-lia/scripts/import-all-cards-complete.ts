import * as fs from 'fs';
import * as path from 'path';

let accessToken: string;
let siteUrl: string;
let cloudId: string;

async function initializeJiraConnection() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) throw new Error('X_REPLIT_TOKEN not found');

  const url = 'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=jira';
  
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json', 'X_REPLIT_TOKEN': xReplitToken }
  });
  
  const data = await response.json();
  const connectionSettings = data.items?.[0];

  accessToken = connectionSettings?.settings?.access_token || 
                connectionSettings?.settings?.oauth?.credentials?.access_token;
  siteUrl = connectionSettings?.settings?.site_url;
  
  if (!accessToken || !siteUrl) throw new Error('Jira not connected');
  console.log('✅ Connected to Jira:', siteUrl);
}

async function getCloudId(): Promise<string> {
  const response = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: { 'Accept': 'application/json', 'Authorization': `Bearer ${accessToken}` }
  });
  const resources = await response.json();
  return resources.find((r: any) => r.url.includes('wedotalent'))?.id;
}

async function jiraRequest(endpoint: string, method: string = 'GET', body?: any) {
  if (!cloudId) cloudId = await getCloudId();
  
  const url = `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3${endpoint}`;
  const options: RequestInit = {
    method,
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    }
  };
  if (body) options.body = JSON.stringify(body);

  const response = await fetch(url, options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Jira API error ${response.status}: ${errorText}`);
  }
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

interface CardData {
  id: string;
  name: string;
  fullYamlContent: string;
  hasDisclaimer: boolean;
}

function parseAllCards(content: string): CardData[] {
  const cards: CardData[] = [];
  
  // Match ALL cards with pattern ### CARD XX-NNN: Name followed by yaml block
  const cardRegex = /### CARD ([A-Z]+-\d+): ([^\n]+)\n\n```yaml\n([\s\S]*?)```/g;
  let match;
  
  while ((match = cardRegex.exec(content)) !== null) {
    const cardId = match[1];
    const cardName = match[2].trim();
    const yamlContent = match[3];
    
    // Skip archived/obsolete cards
    if (yamlContent.includes('ARQUIVADO') || yamlContent.includes('OBSOLETO')) {
      console.log(`⏭️  Skipping archived: ${cardId}`);
      continue;
    }
    
    // Check for config menu disclaimer
    const cardStart = match.index;
    const cardSection = content.substring(cardStart, cardStart + 4000);
    const hasDisclaimer = cardSection.includes('DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES');
    
    cards.push({
      id: cardId,
      name: cardName,
      fullYamlContent: yamlContent,
      hasDisclaimer
    });
  }
  
  return cards;
}

function extractField(yaml: string, fieldName: string, nextFields: string[]): string {
  const nextPattern = nextFields.map(f => `^${f}:`).join('|');
  const regex = new RegExp(`^${fieldName}:\\s*\\|?\\s*([\\s\\S]*?)(?=${nextPattern}|$)`, 'm');
  const match = yaml.match(regex);
  return match ? match[1].trim() : '';
}

function extractListField(yaml: string, fieldName: string, nextFields: string[]): string[] {
  const content = extractField(yaml, fieldName, nextFields);
  if (!content) return [];
  
  return content.split('\n')
    .map(line => line.replace(/^\s*[-\d.]+\s*/, '').trim())
    .filter(line => line.length > 0 && !line.startsWith('---') && !line.startsWith('```'));
}

function buildFullDescription(card: CardData): any {
  const yaml = card.fullYamlContent;
  const content: any[] = [];
  
  // Config menu disclaimer panel
  if (card.hasDisclaimer) {
    content.push({
      type: 'panel',
      attrs: { panelType: 'warning' },
      content: [{
        type: 'paragraph',
        content: [{ 
          type: 'text', 
          text: '⚠️ CARD RELACIONADO AO MENU DE CONFIGURAÇÕES',
          marks: [{ type: 'strong' }]
        }]
      }]
    });
  }
  
  // Status panel
  const statusMatch = yaml.match(/^Status:\s*(.+)$/m);
  const status = statusMatch ? statusMatch[1].trim() : '🔧 A desenvolver';
  content.push({
    type: 'panel',
    attrs: { panelType: status.includes('Pronto') ? 'success' : 'info' },
    content: [{
      type: 'paragraph',
      content: [{ type: 'text', text: `Status: ${status}` }]
    }]
  });
  
  // Metadata table
  const tipo = yaml.match(/^Tipo:\s*(.+)$/m)?.[1]?.trim() || '';
  const sprint = yaml.match(/^Sprint:\s*(.+)$/m)?.[1]?.trim() || '';
  const pontos = yaml.match(/^Pontos:\s*(\d+)/m)?.[1] || '';
  const prioridade = yaml.match(/^Prioridade:\s*(.+)$/m)?.[1]?.trim() || '';
  const epic = yaml.match(/^Epic:\s*(.+)$/m)?.[1]?.trim() || '';
  
  content.push({
    type: 'table',
    attrs: { isNumberColumnEnabled: false, layout: 'default' },
    content: [
      {
        type: 'tableRow',
        content: [
          { type: 'tableHeader', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Tipo' }] }] },
          { type: 'tableHeader', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Sprint' }] }] },
          { type: 'tableHeader', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Pontos' }] }] },
          { type: 'tableHeader', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Prioridade' }] }] },
          { type: 'tableHeader', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Epic' }] }] }
        ]
      },
      {
        type: 'tableRow',
        content: [
          { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: tipo }] }] },
          { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: sprint }] }] },
          { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: pontos }] }] },
          { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: prioridade }] }] },
          { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: epic }] }] }
        ]
      }
    ]
  });
  
  // Helper to add section
  const addSection = (title: string, text: string, isCode: boolean = false) => {
    if (!text) return;
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: title }]
    });
    if (isCode) {
      content.push({
        type: 'codeBlock',
        attrs: { language: 'yaml' },
        content: [{ type: 'text', text: text }]
      });
    } else {
      content.push({
        type: 'paragraph',
        content: [{ type: 'text', text: text }]
      });
    }
  };
  
  const addListSection = (title: string, items: string[], ordered: boolean = false) => {
    if (!items.length) return;
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: title }]
    });
    content.push({
      type: ordered ? 'orderedList' : 'bulletList',
      content: items.map(item => ({
        type: 'listItem',
        content: [{ type: 'paragraph', content: [{ type: 'text', text: item }] }]
      }))
    });
  };
  
  // Extract and add all sections
  const nextFields = ['Historia de Usuario', 'Regras de Negocio', 'Requisitos Tecnicos', 
    'Integracoes Externas', 'Design & Componentes', 'Referencias de Design', 
    'Comportamento de UI', 'Criterios de Aceite', 'Definition of Done'];
  
  const descricao = extractField(yaml, 'Descricao', nextFields);
  addSection('Descrição', descricao.replace(/\n\s+/g, ' '));
  
  const historia = extractField(yaml, 'Historia de Usuario', nextFields);
  addSection('História de Usuário', historia.replace(/\n\s+/g, ' '));
  
  const regras = extractListField(yaml, 'Regras de Negocio', nextFields);
  addListSection('Regras de Negócio', regras, true);
  
  const requisitos = extractField(yaml, 'Requisitos Tecnicos', nextFields);
  addSection('Requisitos Técnicos', requisitos, true);
  
  const integracoes = extractField(yaml, 'Integracoes Externas', nextFields);
  addSection('Integrações Externas', integracoes, true);
  
  const design = extractField(yaml, 'Design & Componentes', nextFields);
  addSection('Design & Componentes', design, true);
  
  const referencias = extractField(yaml, 'Referencias de Design', nextFields);
  addSection('Referências de Design', referencias);
  
  const comportamento = extractField(yaml, 'Comportamento de UI', nextFields);
  addSection('Comportamento de UI', comportamento, true);
  
  const criterios = extractListField(yaml, 'Criterios de Aceite', nextFields);
  addListSection('Critérios de Aceite', criterios);
  
  const dod = extractListField(yaml, 'Definition of Done', nextFields);
  if (dod.length > 0) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Definition of Done' }]
    });
    content.push({
      type: 'taskList',
      attrs: { localId: 'dod-list' },
      content: dod.map(item => ({
        type: 'taskItem',
        attrs: { state: 'TODO', localId: Math.random().toString(36).substr(2, 9) },
        content: [{ type: 'paragraph', content: [{ type: 'text', text: item }] }]
      }))
    });
  }
  
  return { version: 1, type: 'doc', content };
}

async function getTransitions(issueKey: string) {
  const result = await jiraRequest(`/issue/${issueKey}/transitions`);
  return result.transitions || [];
}

async function moveToToDo(issueKey: string) {
  try {
    const transitions = await getTransitions(issueKey);
    const todoTransition = transitions.find(
      (t: any) => t.name?.toLowerCase().includes('to do') ||
                  t.name?.toLowerCase().includes('todo') ||
                  t.name?.toLowerCase() === 'a fazer' ||
                  t.to?.name?.toLowerCase().includes('to do')
    );
    
    if (todoTransition) {
      await jiraRequest(`/issue/${issueKey}/transitions`, 'POST', {
        transition: { id: todoTransition.id }
      });
      return true;
    }
    return false;
  } catch (error) {
    return false;
  }
}

async function createIssue(projectKey: string, card: CardData, issueTypeId: string) {
  const yaml = card.fullYamlContent;
  
  // Extract metadata for labels
  const sprint = yaml.match(/^Sprint:\s*(.+)$/m)?.[1]?.trim() || '0';
  const tipo = yaml.match(/^Tipo:\s*(.+)$/m)?.[1]?.trim() || 'Feature';
  const status = yaml.match(/^Status:\s*(.+)$/m)?.[1]?.trim() || '';
  const titulo = yaml.match(/^Titulo:\s*(.+)$/m)?.[1]?.trim() || card.name;
  
  const labels = ['lia-mvp', `sprint-${sprint}`, tipo.toLowerCase().replace(/\s+/g, '-')];
  if (card.hasDisclaimer) labels.push('config-menu');
  if (status.includes('Pronto')) labels.push('implemented');
  if (card.id.startsWith('INT-')) labels.push('integrations');
  
  const summary = `[${card.id}] ${titulo}`.substring(0, 255);
  
  const issueData = {
    fields: {
      project: { key: projectKey },
      summary,
      description: buildFullDescription(card),
      issuetype: { id: issueTypeId },
      labels
    }
  };

  try {
    const result = await jiraRequest('/issue', 'POST', issueData);
    return result.key;
  } catch (error: any) {
    console.error(`❌ Failed: ${card.id} - ${error.message.substring(0, 100)}`);
    return null;
  }
}

async function main() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  JIRA IMPORT - LIA MVP CARDS (COMPLETE)                    ║');
  console.log('║  Project: wedotalent tasks 2026 (WT)                       ║');
  console.log('║  Target Column: TO DO                                      ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');
  
  const docPath = path.join(__dirname, '../../docs/lia-mvp-cards-jira.md');
  console.log(`📄 Reading: ${docPath}\n`);
  
  const content = fs.readFileSync(docPath, 'utf-8');
  const cards = parseAllCards(content);
  
  console.log(`📊 Found ${cards.length} cards to import\n`);
  
  // Group by prefix
  const byPrefix: Record<string, number> = {};
  cards.forEach(card => {
    const prefix = card.id.split('-')[0];
    byPrefix[prefix] = (byPrefix[prefix] || 0) + 1;
  });
  console.log('Cards by prefix:');
  Object.entries(byPrefix).sort((a, b) => b[1] - a[1]).forEach(([prefix, count]) => {
    console.log(`  ${prefix}: ${count}`);
  });
  console.log('');

  await initializeJiraConnection();
  
  const projectKey = 'WT';
  const project = await jiraRequest(`/project/${projectKey}`);
  console.log(`\n📁 Project: ${project.name} (${project.key})\n`);

  const issueTypes = project.issueTypes || [];
  console.log('Issue types:', issueTypes.map((t: any) => t.name).join(', '));
  
  const taskType = issueTypes.find((t: any) => 
    t.name.toLowerCase() === 'task' || t.name.toLowerCase() === 'tarefa'
  );
  
  if (!taskType) {
    console.error('No suitable issue type found');
    return;
  }
  console.log(`Using: ${taskType.name} (${taskType.id})\n`);

  let created = 0, failed = 0, movedToTodo = 0;
  const results: any[] = [];

  console.log('Creating issues...\n');
  
  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    const progress = `[${String(i + 1).padStart(3, '0')}/${cards.length}]`;
    
    const issueKey = await createIssue(projectKey, card, taskType.id);
    
    if (issueKey) {
      created++;
      
      // Try to move to TO DO
      const moved = await moveToToDo(issueKey);
      if (moved) movedToTodo++;
      
      console.log(`${progress} ✅ ${issueKey} - ${card.id}: ${card.name.substring(0, 40)}...${moved ? ' → TO DO' : ''}`);
      results.push({ card: card.id, status: 'created', issueKey, name: card.name, movedToTodo: moved });
    } else {
      failed++;
      console.log(`${progress} ❌ ${card.id}: ${card.name.substring(0, 40)}...`);
      results.push({ card: card.id, status: 'failed', name: card.name });
    }
    
    // Rate limiting
    await new Promise(resolve => setTimeout(resolve, 350));
  }

  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║  IMPORT SUMMARY                                            ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log(`  Total cards processed: ${cards.length}`);
  console.log(`  Successfully created:  ${created}`);
  console.log(`  Moved to TO DO:        ${movedToTodo}`);
  console.log(`  Failed:                ${failed}`);
  console.log(`  Success rate:          ${((created / cards.length) * 100).toFixed(1)}%`);
  
  if (failed > 0) {
    console.log('\n  Failed cards:');
    results.filter(r => r.status === 'failed').forEach(r => {
      console.log(`    - ${r.card}: ${r.name}`);
    });
  }

  // Get issue key range
  const createdIssues = results.filter(r => r.issueKey).map(r => r.issueKey);
  if (createdIssues.length > 0) {
    console.log(`\n  Jira Keys: ${createdIssues[0]} to ${createdIssues[createdIssues.length - 1]}`);
  }

  // Save report
  const reportPath = path.join(__dirname, 'complete-import-report.json');
  fs.writeFileSync(reportPath, JSON.stringify({ 
    timestamp: new Date().toISOString(),
    project: projectKey,
    document: 'lia-mvp-cards-jira.md',
    total: cards.length,
    created,
    movedToTodo,
    failed,
    successRate: `${((created / cards.length) * 100).toFixed(1)}%`,
    issueKeyRange: createdIssues.length > 0 ? `${createdIssues[0]} - ${createdIssues[createdIssues.length - 1]}` : null,
    byPrefix,
    results 
  }, null, 2));
  
  console.log(`\n  Report saved: ${reportPath}`);
}

main().catch(console.error);
