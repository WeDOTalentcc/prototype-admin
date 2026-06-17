import * as fs from 'fs';
import * as path from 'path';

let connectionSettings: any;
let accessToken: string;
let siteUrl: string;

async function initializeJiraConnection() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('X_REPLIT_TOKEN not found');
  }

  const url = 'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=jira';
  
  const response = await fetch(url, {
    headers: {
      'Accept': 'application/json',
      'X_REPLIT_TOKEN': xReplitToken
    }
  });
  
  const data = await response.json();
  connectionSettings = data.items?.[0];
  
  console.log('Connection status:', connectionSettings?.status);

  accessToken = connectionSettings?.settings?.access_token || 
                connectionSettings?.settings?.oauth?.credentials?.access_token ||
                connectionSettings?.settings?.oauth?.access_token;
  siteUrl = connectionSettings?.settings?.site_url;
  
  if (!accessToken || !siteUrl) {
    throw new Error('Jira not connected - missing credentials');
  }

  console.log('Connected to Jira:', siteUrl);
  return { accessToken, siteUrl };
}

async function getCloudId(): Promise<string> {
  const response = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to get cloud ID');
  }
  
  const resources = await response.json();
  const site = resources.find((r: any) => r.url === siteUrl || r.url.includes('wedotalent'));
  if (!site) {
    throw new Error('Site not found in accessible resources');
  }
  
  return site.id;
}

let cloudId: string;

async function jiraRequest(endpoint: string, method: string = 'GET', body?: any) {
  if (!cloudId) {
    cloudId = await getCloudId();
    console.log('Cloud ID:', cloudId);
  }
  
  const url = `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3${endpoint}`;
  
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  };

  const options: RequestInit = { method, headers };
  if (body) {
    options.body = JSON.stringify(body);
  }

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
  points: number;
  priority: string;
  epic: string;
  status: string;
  description: string;
  userStory: string;
  businessRules: string[];
  technicalRequirements: string;
  integrations: string;
  designComponents: string;
  designReferences: string;
  uiBehavior: string;
  acceptanceCriteria: string[];
  definitionOfDone: string[];
  isConfigMenu: boolean;
}

function parseCardsFromMarkdown(content: string): CardData[] {
  const cards: CardData[] = [];
  const cardRegex = /### CARD ([A-Z]+-\d+): (.+?)\n\n```yaml\n([\s\S]*?)```/g;
  let match;
  
  while ((match = cardRegex.exec(content)) !== null) {
    const cardId = match[1];
    const cardName = match[2];
    const yamlContent = match[3];
    
    if (yamlContent.includes('ARQUIVADO') || yamlContent.includes('OBSOLETO')) {
      console.log(`Skipping archived/obsolete card: ${cardId}`);
      continue;
    }
    
    const card = parseYamlCard(cardId, cardName, yamlContent, content);
    if (card) {
      cards.push(card);
    }
  }
  
  return cards;
}

function parseYamlCard(id: string, name: string, yaml: string, fullContent: string): CardData | null {
  const titleMatch = yaml.match(/^Titulo:\s*(.+)$/m);
  const title = titleMatch ? titleMatch[1].trim() : `[${id}] ${name}`;
  
  const typeMatch = yaml.match(/^Tipo:\s*(.+)$/m);
  const type = typeMatch ? typeMatch[1].trim() : 'Feature';
  
  const sprintMatch = yaml.match(/^Sprint:\s*(.+)$/m);
  const sprint = sprintMatch ? sprintMatch[1].trim() : '1';
  
  const pointsMatch = yaml.match(/^Pontos:\s*(\d+)/m);
  const points = pointsMatch ? parseInt(pointsMatch[1]) : 5;
  
  const priorityMatch = yaml.match(/^Prioridade:\s*(.+)$/m);
  const priority = priorityMatch ? priorityMatch[1].trim() : 'Medium';
  
  const epicMatch = yaml.match(/^Epic:\s*(.+)$/m);
  const epic = epicMatch ? epicMatch[1].trim() : '';

  const statusMatch = yaml.match(/^Status:\s*(.+)$/m);
  const status = statusMatch ? statusMatch[1].trim() : '🔧 A desenvolver';

  const descriptionMatch = yaml.match(/^Descricao:\s*\|?\s*([\s\S]*?)(?=^Historia de Usuario:|^Regras de Negocio:|^Requisitos Tecnicos:|$)/m);
  const description = descriptionMatch ? descriptionMatch[1].trim().replace(/\n\s+/g, ' ') : '';

  const userStoryMatch = yaml.match(/^Historia de Usuario:\s*\|?\s*([\s\S]*?)(?=^Regras de Negocio:|^Requisitos Tecnicos:|$)/m);
  const userStory = userStoryMatch ? userStoryMatch[1].trim().replace(/\n\s+/g, ' ') : '';

  const rulesMatch = yaml.match(/^Regras de Negocio:\s*([\s\S]*?)(?=^Requisitos Tecnicos:|^Estrutura|^Integracoes|^Design|^Comportamento|^Referencias|^Criterios de Aceite:|$)/m);
  const businessRules = rulesMatch ? 
    rulesMatch[1].split('\n')
      .map(line => line.replace(/^\s*\d+\.\s*/, '').trim())
      .filter(line => line.length > 0 && !line.startsWith('---')) : [];

  const techMatch = yaml.match(/^Requisitos Tecnicos:\s*([\s\S]*?)(?=^Integracoes|^Design|^Comportamento|^Referencias|^Criterios de Aceite:|$)/m);
  const technicalRequirements = techMatch ? techMatch[1].trim() : '';

  const intMatch = yaml.match(/^Integracoes Externas:\s*([\s\S]*?)(?=^Design|^Comportamento|^Referencias|^Criterios de Aceite:|$)/m);
  const integrations = intMatch ? intMatch[1].trim() : '';

  const designMatch = yaml.match(/^Design & Componentes:\s*([\s\S]*?)(?=^Referencias de Design:|^Comportamento|^Criterios de Aceite:|$)/m);
  const designComponents = designMatch ? designMatch[1].trim() : '';

  const refMatch = yaml.match(/^Referencias de Design:\s*([\s\S]*?)(?=^Comportamento|^Criterios de Aceite:|$)/m);
  const designReferences = refMatch ? refMatch[1].trim() : '';

  const uiMatch = yaml.match(/^Comportamento de UI:\s*([\s\S]*?)(?=^Criterios de Aceite:|^Definition of Done:|$)/m);
  const uiBehavior = uiMatch ? uiMatch[1].trim() : '';

  const acMatch = yaml.match(/^Criterios de Aceite:\s*([\s\S]*?)(?=^Definition of Done:|$)/m);
  const acceptanceCriteria = acMatch ?
    acMatch[1].split('\n')
      .map(line => line.replace(/^\s*[-\d.]+\s*/, '').trim())
      .filter(line => line.length > 0 && !line.startsWith('---')) : [];

  const dodMatch = yaml.match(/^Definition of Done:\s*([\s\S]*?)(?=^[A-Z][a-z_]+:|```|$)/m);
  const definitionOfDone = dodMatch ?
    dodMatch[1].split('\n')
      .map(line => line.replace(/^\s*[-\d.]+\s*/, '').trim())
      .filter(line => line.length > 0 && !line.startsWith('---')) : [];

  // Check if this card has the config menu disclaimer
  const cardSection = fullContent.substring(
    fullContent.indexOf(`### CARD ${id}:`),
    fullContent.indexOf(`### CARD ${id}:`) + 3000
  );
  const isConfigMenu = cardSection.includes('DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES');

  return {
    id, title, type, sprint, points, priority, epic, status,
    description, userStory, businessRules, technicalRequirements,
    integrations, designComponents, designReferences, uiBehavior,
    acceptanceCriteria, definitionOfDone, isConfigMenu
  };
}

function buildAtlassianDoc(card: CardData): any {
  const content: any[] = [];
  
  // Config menu disclaimer if applicable
  if (card.isConfigMenu) {
    content.push({
      type: 'panel',
      attrs: { panelType: 'warning' },
      content: [{
        type: 'paragraph',
        content: [{ 
          type: 'text', 
          text: '⚠️ CARD RELACIONADO AO MENU DE CONFIGURAÇÕES - Consulte também: docs/configuracoes-admin-cards-jira.md',
          marks: [{ type: 'strong' }]
        }]
      }]
    });
  }

  // Status badge
  content.push({
    type: 'panel',
    attrs: { panelType: card.status.includes('Pronto') ? 'success' : 'info' },
    content: [{
      type: 'paragraph',
      content: [{ type: 'text', text: `Status: ${card.status}` }]
    }]
  });
  
  // Description
  content.push({
    type: 'heading',
    attrs: { level: 2 },
    content: [{ type: 'text', text: 'Descrição' }]
  });
  
  if (card.description) {
    content.push({
      type: 'paragraph',
      content: [{ type: 'text', text: card.description }]
    });
  }
  
  // User Story
  if (card.userStory) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'História de Usuário' }]
    });
    content.push({
      type: 'paragraph',
      content: [{ type: 'text', text: card.userStory }]
    });
  }
  
  // Business Rules
  if (card.businessRules.length > 0) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Regras de Negócio' }]
    });
    content.push({
      type: 'orderedList',
      content: card.businessRules.map(rule => ({
        type: 'listItem',
        content: [{
          type: 'paragraph',
          content: [{ type: 'text', text: rule }]
        }]
      }))
    });
  }
  
  // Technical Requirements
  if (card.technicalRequirements) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Requisitos Técnicos' }]
    });
    content.push({
      type: 'codeBlock',
      attrs: { language: 'yaml' },
      content: [{ type: 'text', text: card.technicalRequirements }]
    });
  }

  // Integrations
  if (card.integrations) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Integrações Externas' }]
    });
    content.push({
      type: 'codeBlock',
      attrs: { language: 'yaml' },
      content: [{ type: 'text', text: card.integrations }]
    });
  }

  // Design & Components
  if (card.designComponents) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Design & Componentes' }]
    });
    content.push({
      type: 'codeBlock',
      attrs: { language: 'yaml' },
      content: [{ type: 'text', text: card.designComponents }]
    });
  }

  // Design References
  if (card.designReferences) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Referências de Design' }]
    });
    content.push({
      type: 'paragraph',
      content: [{ type: 'text', text: card.designReferences }]
    });
  }

  // UI Behavior
  if (card.uiBehavior) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Comportamento de UI' }]
    });
    content.push({
      type: 'codeBlock',
      attrs: { language: 'yaml' },
      content: [{ type: 'text', text: card.uiBehavior }]
    });
  }
  
  // Acceptance Criteria
  if (card.acceptanceCriteria.length > 0) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Critérios de Aceite' }]
    });
    content.push({
      type: 'bulletList',
      content: card.acceptanceCriteria.map(ac => ({
        type: 'listItem',
        content: [{
          type: 'paragraph',
          content: [{ type: 'text', text: ac }]
        }]
      }))
    });
  }
  
  // Definition of Done
  if (card.definitionOfDone.length > 0) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Definition of Done' }]
    });
    content.push({
      type: 'taskList',
      attrs: { localId: 'dod' },
      content: card.definitionOfDone.map(item => ({
        type: 'taskItem',
        attrs: { state: 'TODO', localId: Math.random().toString(36).substr(2, 9) },
        content: [{
          type: 'paragraph',
          content: [{ type: 'text', text: item }]
        }]
      }))
    });
  }
  
  return {
    version: 1,
    type: 'doc',
    content
  };
}

async function getProject(projectKey: string) {
  return jiraRequest(`/project/${projectKey}`);
}

async function getIssueTypes(projectKey: string) {
  const project = await jiraRequest(`/project/${projectKey}`);
  return project.issueTypes || [];
}

async function createIssue(projectKey: string, card: CardData, issueTypeId: string) {
  const labels = [`mvp`, `sprint-${card.sprint}`, card.type.toLowerCase().replace(/\s+/g, '-')];
  if (card.isConfigMenu) {
    labels.push('config-menu');
  }
  if (card.status.includes('Pronto')) {
    labels.push('implemented');
  }

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
  console.log('Jira Import - LIA MVP Cards');
  console.log('WeDo Talent - wedotalent tasks 2026');
  console.log('========================================\n');
  
  const docPath = path.join(__dirname, '../../docs/lia-mvp-cards-jira.md');
  console.log(`Reading cards from: ${docPath}`);
  
  const content = fs.readFileSync(docPath, 'utf-8');
  const cards = parseCardsFromMarkdown(content);
  
  console.log(`\nFound ${cards.length} cards to import\n`);
  
  // Summary by epic
  const epicCounts: Record<string, number> = {};
  const statusCounts: Record<string, number> = {};
  let configMenuCount = 0;
  
  cards.forEach(card => {
    const epicName = card.epic.split('(')[0].trim() || 'Sem Epic';
    epicCounts[epicName] = (epicCounts[epicName] || 0) + 1;
    
    const statusKey = card.status.includes('Pronto') ? '✅ Pronto' : '🔧 A desenvolver';
    statusCounts[statusKey] = (statusCounts[statusKey] || 0) + 1;
    
    if (card.isConfigMenu) configMenuCount++;
  });
  
  console.log('Cards by Epic:');
  Object.entries(epicCounts).sort((a, b) => b[1] - a[1]).forEach(([epic, count]) => {
    console.log(`  ${epic}: ${count} cards`);
  });
  
  console.log('\nCards by Status:');
  Object.entries(statusCounts).forEach(([status, count]) => {
    console.log(`  ${status}: ${count} cards`);
  });
  
  console.log(`\nConfig Menu Cards: ${configMenuCount}`);
  console.log('');

  await initializeJiraConnection();
  
  const projectKey = 'WT';
  const project = await getProject(projectKey);
  console.log(`\nProject: ${project.name} (${project.key})\n`);

  const issueTypes = await getIssueTypes(projectKey);
  console.log('Available issue types:', issueTypes.map((t: any) => t.name).join(', '));
  
  const taskType = issueTypes.find((t: any) => 
    t.name.toLowerCase() === 'task' || 
    t.name.toLowerCase() === 'tarefa' ||
    t.name.toLowerCase() === 'story'
  );
  
  if (!taskType) {
    console.error('No suitable issue type found');
    return;
  }
  console.log(`Using issue type: ${taskType.name} (${taskType.id})\n`);

  let created = 0;
  let failed = 0;
  const results: { card: string; status: string; issueKey?: string; title: string }[] = [];

  console.log('Creating issues...\n');
  
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
    
    // Rate limiting - 300ms between requests
    await new Promise(resolve => setTimeout(resolve, 300));
  }

  console.log('\n========================================');
  console.log('Import Summary');
  console.log('========================================');
  console.log(`Total cards processed: ${cards.length}`);
  console.log(`Successfully created: ${created}`);
  console.log(`Failed: ${failed}`);
  console.log(`Success rate: ${((created / cards.length) * 100).toFixed(1)}%`);
  
  if (failed > 0) {
    console.log('\nFailed cards:');
    results.filter(r => r.status === 'failed').forEach(r => {
      console.log(`  - ${r.card}: ${r.title}`);
    });
  }

  // Save report
  const reportPath = path.join(__dirname, 'lia-mvp-import-report.json');
  fs.writeFileSync(reportPath, JSON.stringify({ 
    timestamp: new Date().toISOString(),
    project: projectKey,
    document: 'lia-mvp-cards-jira.md',
    total: cards.length,
    created,
    failed,
    successRate: `${((created / cards.length) * 100).toFixed(1)}%`,
    epicCounts,
    statusCounts,
    configMenuCount,
    results 
  }, null, 2));
  
  console.log(`\nReport saved: ${reportPath}`);
  
  // Create markdown summary
  const summaryPath = path.join(__dirname, 'lia-mvp-import-summary.md');
  const summaryContent = `# LIA MVP Cards - Jira Import Summary

**Date**: ${new Date().toISOString()}
**Project**: wedotalent tasks 2026 (WT)
**Document**: docs/lia-mvp-cards-jira.md

## Results

| Metric | Value |
|--------|-------|
| Total Cards | ${cards.length} |
| Created | ${created} |
| Failed | ${failed} |
| Success Rate | ${((created / cards.length) * 100).toFixed(1)}% |

## Cards by Epic

${Object.entries(epicCounts).sort((a, b) => b[1] - a[1]).map(([epic, count]) => `- **${epic}**: ${count} cards`).join('\n')}

## Created Issues

| Card ID | Jira Key | Title |
|---------|----------|-------|
${results.filter(r => r.status === 'created').map(r => `| ${r.card} | ${r.issueKey} | ${r.title.substring(0, 50)}... |`).join('\n')}

${failed > 0 ? `
## Failed Cards

${results.filter(r => r.status === 'failed').map(r => `- ${r.card}: ${r.title}`).join('\n')}
` : ''}
`;
  
  fs.writeFileSync(summaryPath, summaryContent);
  console.log(`Summary saved: ${summaryPath}`);
}

main().catch(console.error);
