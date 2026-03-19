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
  console.log('Connected to Jira:', siteUrl);
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
  title: string;
  type: string;
  sprint: string;
  status: string;
  description: string;
  userStory: string;
  businessRules: string[];
  technicalRequirements: string;
  isConfigMenu: boolean;
}

function parseIntegrationCards(content: string): CardData[] {
  const cards: CardData[] = [];
  const cardRegex = /### CARD (INT-[A-Z]+-\d+): (.+?)\n\n```yaml\n([\s\S]*?)```/g;
  let match;
  
  while ((match = cardRegex.exec(content)) !== null) {
    const cardId = match[1];
    const cardName = match[2];
    const yaml = match[3];
    
    const titleMatch = yaml.match(/^Titulo:\s*(.+)$/m);
    const title = titleMatch ? titleMatch[1].trim() : `[${cardId}] ${cardName}`;
    
    const typeMatch = yaml.match(/^Tipo:\s*(.+)$/m);
    const type = typeMatch ? typeMatch[1].trim() : 'Integração';
    
    const sprintMatch = yaml.match(/^Sprint:\s*(.+)$/m);
    const sprint = sprintMatch ? sprintMatch[1].trim() : '0';

    const statusMatch = yaml.match(/^Status:\s*(.+)$/m);
    const status = statusMatch ? statusMatch[1].trim() : '🔧 A desenvolver';

    const descriptionMatch = yaml.match(/^Descricao:\s*\|?\s*([\s\S]*?)(?=^Historia de Usuario:|^Regras de Negocio:|^Requisitos Tecnicos:|$)/m);
    const description = descriptionMatch ? descriptionMatch[1].trim().replace(/\n\s+/g, ' ') : '';

    const userStoryMatch = yaml.match(/^Historia de Usuario:\s*\|?\s*([\s\S]*?)(?=^Regras de Negocio:|^Requisitos Tecnicos:|$)/m);
    const userStory = userStoryMatch ? userStoryMatch[1].trim().replace(/\n\s+/g, ' ') : '';

    const rulesMatch = yaml.match(/^Regras de Negocio:\s*([\s\S]*?)(?=^Requisitos Tecnicos:|^Estrutura|^Integracoes|^Design|^Comportamento|^Referencias|^Criterios|$)/m);
    const businessRules = rulesMatch ? 
      rulesMatch[1].split('\n')
        .map(line => line.replace(/^\s*\d+\.\s*/, '').trim())
        .filter(line => line.length > 0 && !line.startsWith('---')) : [];

    const techMatch = yaml.match(/^Requisitos Tecnicos:\s*([\s\S]*?)(?=^Integracoes|^Design|^Comportamento|^Referencias|^Criterios|$)/m);
    const technicalRequirements = techMatch ? techMatch[1].trim() : '';

    const cardSection = content.substring(
      content.indexOf(`### CARD ${cardId}:`),
      content.indexOf(`### CARD ${cardId}:`) + 3000
    );
    const isConfigMenu = cardSection.includes('DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES');

    cards.push({
      id: cardId, title, type, sprint, status, description, userStory, 
      businessRules, technicalRequirements, isConfigMenu
    });
  }
  
  return cards;
}

function buildAtlassianDoc(card: CardData): any {
  const content: any[] = [];
  
  if (card.isConfigMenu) {
    content.push({
      type: 'panel', attrs: { panelType: 'warning' },
      content: [{ type: 'paragraph', content: [{ 
        type: 'text', 
        text: '⚠️ CARD RELACIONADO AO MENU DE CONFIGURAÇÕES',
        marks: [{ type: 'strong' }]
      }]}]
    });
  }

  content.push({
    type: 'panel',
    attrs: { panelType: card.status.includes('Pronto') ? 'success' : 'info' },
    content: [{ type: 'paragraph', content: [{ type: 'text', text: `Status: ${card.status}` }]}]
  });
  
  content.push({
    type: 'heading', attrs: { level: 2 },
    content: [{ type: 'text', text: 'Descrição' }]
  });
  
  if (card.description) {
    content.push({ type: 'paragraph', content: [{ type: 'text', text: card.description }]});
  }
  
  if (card.userStory) {
    content.push({
      type: 'heading', attrs: { level: 2 },
      content: [{ type: 'text', text: 'História de Usuário' }]
    });
    content.push({ type: 'paragraph', content: [{ type: 'text', text: card.userStory }]});
  }
  
  if (card.businessRules.length > 0) {
    content.push({
      type: 'heading', attrs: { level: 2 },
      content: [{ type: 'text', text: 'Regras de Negócio' }]
    });
    content.push({
      type: 'orderedList',
      content: card.businessRules.map(rule => ({
        type: 'listItem',
        content: [{ type: 'paragraph', content: [{ type: 'text', text: rule }]}]
      }))
    });
  }
  
  if (card.technicalRequirements) {
    content.push({
      type: 'heading', attrs: { level: 2 },
      content: [{ type: 'text', text: 'Requisitos Técnicos' }]
    });
    content.push({
      type: 'codeBlock', attrs: { language: 'yaml' },
      content: [{ type: 'text', text: card.technicalRequirements }]
    });
  }
  
  return { version: 1, type: 'doc', content };
}

async function createIssue(projectKey: string, card: CardData, issueTypeId: string) {
  const labels = ['mvp', 'integrations', `sprint-${card.sprint}`, card.type.toLowerCase().replace(/\s+/g, '-')];
  if (card.isConfigMenu) labels.push('config-menu');
  if (card.status.includes('Pronto')) labels.push('implemented');

  const summary = `[${card.id}] ${card.title}`.substring(0, 255);
  
  const issueData = {
    fields: {
      project: { key: projectKey },
      summary,
      description: buildAtlassianDoc(card),
      issuetype: { id: issueTypeId },
      labels
    }
  };

  try {
    const result = await jiraRequest('/issue', 'POST', issueData);
    console.log(`✅ Created: ${result.key} - ${card.id}: ${card.title.substring(0, 50)}...`);
    return result.key;
  } catch (error: any) {
    console.error(`❌ Failed: ${card.id} - ${error.message.substring(0, 100)}`);
    return null;
  }
}

async function main() {
  console.log('========================================');
  console.log('Jira Import - Integration Cards (INT-*)');
  console.log('========================================\n');
  
  const docPath = path.join(__dirname, '../../docs/lia-mvp-cards-jira.md');
  const content = fs.readFileSync(docPath, 'utf-8');
  const cards = parseIntegrationCards(content);
  
  console.log(`Found ${cards.length} integration cards to import\n`);

  await initializeJiraConnection();
  
  const projectKey = 'WT';
  const project = await jiraRequest(`/project/${projectKey}`);
  console.log(`Project: ${project.name}\n`);

  const issueTypes = project.issueTypes || [];
  const taskType = issueTypes.find((t: any) => 
    t.name.toLowerCase() === 'task' || t.name.toLowerCase() === 'tarefa'
  );
  
  if (!taskType) {
    console.error('No suitable issue type found');
    return;
  }
  console.log(`Using issue type: ${taskType.name}\n`);

  let created = 0, failed = 0;
  const results: any[] = [];

  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    console.log(`[${i + 1}/${cards.length}] Processing ${card.id}...`);
    
    const issueKey = await createIssue(projectKey, card, taskType.id);
    
    if (issueKey) {
      created++;
      results.push({ card: card.id, status: 'created', issueKey, title: card.title });
    } else {
      failed++;
      results.push({ card: card.id, status: 'failed', title: card.title });
    }
    
    await new Promise(resolve => setTimeout(resolve, 300));
  }

  console.log('\n========================================');
  console.log('Import Summary - Integration Cards');
  console.log('========================================');
  console.log(`Total: ${cards.length} | Created: ${created} | Failed: ${failed}`);

  const reportPath = path.join(__dirname, 'integration-cards-import-report.json');
  fs.writeFileSync(reportPath, JSON.stringify({ 
    timestamp: new Date().toISOString(),
    total: cards.length, created, failed, results 
  }, null, 2));
  console.log(`\nReport saved: ${reportPath}`);
}

main().catch(console.error);
