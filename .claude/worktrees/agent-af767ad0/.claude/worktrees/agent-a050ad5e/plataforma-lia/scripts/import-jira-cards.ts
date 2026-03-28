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
  console.log('Settings keys:', Object.keys(connectionSettings?.settings || {}));
  
  if (connectionSettings?.settings?.oauth) {
    console.log('OAuth keys:', Object.keys(connectionSettings.settings.oauth));
    if (connectionSettings.settings.oauth.credentials) {
      console.log('OAuth credentials keys:', Object.keys(connectionSettings.settings.oauth.credentials));
    }
  }

  accessToken = connectionSettings?.settings?.access_token || 
                connectionSettings?.settings?.oauth?.credentials?.access_token ||
                connectionSettings?.settings?.oauth?.access_token;
  siteUrl = connectionSettings?.settings?.site_url;
  
  const expiresAt = connectionSettings?.settings?.expires_at || 
                    connectionSettings?.settings?.oauth?.credentials?.expires_at;
  if (expiresAt) {
    const expiresDate = typeof expiresAt === 'number' ? new Date(expiresAt * 1000) : new Date(expiresAt);
    console.log('Token expires at:', expiresDate.toISOString());
    console.log('Current time:', new Date().toISOString());
    console.log('Token expired:', expiresDate.getTime() < Date.now());
  }
  
  console.log('OAuth expires_in:', connectionSettings?.settings?.oauth?.credentials?.expires_in);
  console.log('OAuth expires_at raw:', connectionSettings?.settings?.oauth?.credentials?.expires_at);

  if (!accessToken || !siteUrl) {
    console.log('Full settings:', JSON.stringify(connectionSettings?.settings, null, 2));
    throw new Error('Jira not connected - missing credentials');
  }

  console.log('Connected to Jira:', siteUrl);
  console.log('Token preview:', accessToken.substring(0, 20) + '...');
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
    const text = await response.text();
    console.log('Failed to get cloud ID:', response.status, text);
    throw new Error('Failed to get cloud ID');
  }
  
  const resources = await response.json();
  console.log('Accessible resources:', resources.map((r: any) => ({ id: r.id, name: r.name, url: r.url })));
  
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
  description: string;
  userStory: string;
  businessRules: string[];
  technicalRequirements: string;
  acceptanceCriteria: string[];
  definitionOfDone: string[];
}

function parseCardsFromMarkdown(content: string): CardData[] {
  const cards: CardData[] = [];
  const cardRegex = /### CARD ([A-Z]+-\d+): (.+?)\n\n```yaml\n([\s\S]*?)```/g;
  let match;
  
  while ((match = cardRegex.exec(content)) !== null) {
    const cardId = match[1];
    const cardName = match[2];
    const yamlContent = match[3];
    
    if (yamlContent.includes('ARQUIVADO')) {
      console.log(`Skipping archived card: ${cardId}`);
      continue;
    }
    
    const card = parseYamlCard(cardId, cardName, yamlContent);
    if (card) {
      cards.push(card);
    }
  }
  
  return cards;
}

function parseYamlCard(id: string, name: string, yaml: string): CardData | null {
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

  const descriptionMatch = yaml.match(/^Descricao:\s*\|?\s*([\s\S]*?)(?=^Historia de Usuario:|^Regras de Negocio:|^Requisitos Tecnicos:|$)/m);
  const description = descriptionMatch ? descriptionMatch[1].trim().replace(/\n\s+/g, ' ') : '';

  const userStoryMatch = yaml.match(/^Historia de Usuario:\s*\|?\s*([\s\S]*?)(?=^Regras de Negocio:|^Requisitos Tecnicos:|$)/m);
  const userStory = userStoryMatch ? userStoryMatch[1].trim().replace(/\n\s+/g, ' ') : '';

  const rulesMatch = yaml.match(/^Regras de Negocio:\s*([\s\S]*?)(?=^Requisitos Tecnicos:|^Estrutura|^Integracoes|^Design|^Comportamento|^Criterios de Aceite:|$)/m);
  const businessRules = rulesMatch ? 
    rulesMatch[1].split('\n')
      .map(line => line.replace(/^\s*\d+\.\s*/, '').trim())
      .filter(line => line.length > 0 && !line.startsWith('---')) : [];

  const techMatch = yaml.match(/^Requisitos Tecnicos:\s*([\s\S]*?)(?=^Integracoes|^Design|^Comportamento|^Criterios de Aceite:|$)/m);
  const technicalRequirements = techMatch ? techMatch[1].trim() : '';

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

  return {
    id, title, type, sprint, points, priority, epic,
    description, userStory, businessRules, technicalRequirements,
    acceptanceCriteria, definitionOfDone
  };
}

function buildAtlassianDoc(card: CardData): any {
  const content: any[] = [];
  
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
  
  if (card.businessRules.length > 0) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Regras de Negócio' }]
    });
    content.push({
      type: 'orderedList',
      content: card.businessRules.slice(0, 20).map(rule => ({
        type: 'listItem',
        content: [{
          type: 'paragraph',
          content: [{ type: 'text', text: rule.substring(0, 500) }]
        }]
      }))
    });
  }
  
  if (card.technicalRequirements) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Requisitos Técnicos' }]
    });
    content.push({
      type: 'codeBlock',
      attrs: { language: 'yaml' },
      content: [{ type: 'text', text: card.technicalRequirements.substring(0, 3000) }]
    });
  }
  
  if (card.acceptanceCriteria.length > 0) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Critérios de Aceite' }]
    });
    content.push({
      type: 'bulletList',
      content: card.acceptanceCriteria.slice(0, 15).map(ac => ({
        type: 'listItem',
        content: [{
          type: 'paragraph',
          content: [{ type: 'text', text: ac.substring(0, 300) }]
        }]
      }))
    });
  }
  
  if (card.definitionOfDone.length > 0) {
    content.push({
      type: 'heading',
      attrs: { level: 2 },
      content: [{ type: 'text', text: 'Definition of Done' }]
    });
    content.push({
      type: 'bulletList',
      content: card.definitionOfDone.slice(0, 10).map(dod => ({
        type: 'listItem',
        content: [{
          type: 'paragraph',
          content: [{ type: 'text', text: dod.substring(0, 300) }]
        }]
      }))
    });
  }

  content.push({
    type: 'rule'
  });
  
  content.push({
    type: 'paragraph',
    content: [
      { type: 'text', text: 'Epic: ', marks: [{ type: 'strong' }] },
      { type: 'text', text: card.epic }
    ]
  });
  
  content.push({
    type: 'paragraph',
    content: [
      { type: 'text', text: 'ID Original: ', marks: [{ type: 'strong' }] },
      { type: 'text', text: card.id },
      { type: 'text', text: ' | ' },
      { type: 'text', text: 'Pontos: ', marks: [{ type: 'strong' }] },
      { type: 'text', text: String(card.points) },
      { type: 'text', text: ' | ' },
      { type: 'text', text: 'Sprint: ', marks: [{ type: 'strong' }] },
      { type: 'text', text: card.sprint }
    ]
  });

  return {
    type: 'doc',
    version: 1,
    content
  };
}

async function getProject(projectKey: string) {
  try {
    return await jiraRequest(`/project/${projectKey}`);
  } catch (error) {
    console.error('Error getting project:', error);
    throw error;
  }
}

async function getIssueTypes(projectKey: string) {
  try {
    const meta = await jiraRequest(`/issue/createmeta?projectKeys=${projectKey}&expand=projects.issuetypes`);
    return meta.projects?.[0]?.issuetypes || [];
  } catch (error) {
    console.error('Error getting issue types:', error);
    return [];
  }
}

async function createIssue(projectKey: string, card: CardData, issueTypeId: string): Promise<string | null> {
  try {
    const description = buildAtlassianDoc(card);
    
    const epicPrefix = card.epic.split('(')[0].trim().replace(/[^\w-]/g, '-');
    const cardPrefix = card.id.split('-')[0];
    
    const issueData = {
      fields: {
        project: { key: projectKey },
        summary: `[${card.id}] ${card.title}`,
        description,
        issuetype: { id: issueTypeId },
        labels: ['menu-config', epicPrefix, cardPrefix]
      }
    };

    const result = await jiraRequest('/issue', 'POST', issueData);
    console.log(`Created: ${result.key} - [${card.id}] ${card.title.substring(0, 50)}...`);
    return result.key;
  } catch (error: any) {
    console.error(`Failed ${card.id}:`, error.message?.substring(0, 100));
    return null;
  }
}

async function getTransitions(issueKey: string) {
  try {
    const result = await jiraRequest(`/issue/${issueKey}/transitions`);
    return result.transitions || [];
  } catch (error) {
    return [];
  }
}

async function moveToColumn(issueKey: string, columnName: string) {
  try {
    const transitions = await getTransitions(issueKey);
    const targetTransition = transitions.find(
      (t: any) => t.name?.toLowerCase().includes(columnName.toLowerCase()) ||
                  t.to?.name?.toLowerCase().includes(columnName.toLowerCase())
    );
    
    if (targetTransition) {
      await jiraRequest(`/issue/${issueKey}/transitions`, 'POST', {
        transition: { id: targetTransition.id }
      });
      return true;
    }
    return false;
  } catch (error) {
    return false;
  }
}

async function main() {
  console.log('========================================');
  console.log('Jira Cards Import - WeDo Talent LIA');
  console.log('========================================\n');
  
  const docPath = path.join(__dirname, '../../docs/configuracoes-admin-cards-jira.md');
  console.log(`Reading cards from: ${docPath}`);
  
  const content = fs.readFileSync(docPath, 'utf-8');
  const cards = parseCardsFromMarkdown(content);
  
  console.log(`\nFound ${cards.length} cards to import (excluding archived)\n`);
  
  const epicCounts: Record<string, number> = {};
  cards.forEach(card => {
    const epicName = card.epic.split('(')[0].trim();
    epicCounts[epicName] = (epicCounts[epicName] || 0) + 1;
  });
  console.log('Cards by Epic:');
  Object.entries(epicCounts).forEach(([epic, count]) => {
    console.log(`  ${epic}: ${count} cards`);
  });
  console.log('');

  await initializeJiraConnection();
  
  const projectKey = 'WT';
  const project = await getProject(projectKey);
  console.log(`Project: ${project.name} (${project.key})\n`);

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
  const results: { card: string; status: string; issueKey?: string }[] = [];

  console.log('Creating issues...\n');
  
  for (const card of cards) {
    const issueKey = await createIssue(projectKey, card, taskType.id);
    
    if (issueKey) {
      created++;
      results.push({ card: card.id, status: 'created', issueKey });
      
      const moved = await moveToColumn(issueKey, 'menu config');
      if (moved) {
        console.log(`  -> Moved to "menu config"`);
      }
    } else {
      failed++;
      results.push({ card: card.id, status: 'failed' });
    }
    
    await new Promise(resolve => setTimeout(resolve, 300));
  }

  console.log('\n========================================');
  console.log('Import Summary');
  console.log('========================================');
  console.log(`Total cards: ${cards.length}`);
  console.log(`Created: ${created}`);
  console.log(`Failed: ${failed}`);
  
  if (failed > 0) {
    console.log('\nFailed cards:');
    results.filter(r => r.status === 'failed').forEach(r => {
      console.log(`  - ${r.card}`);
    });
  }

  const reportPath = path.join(__dirname, 'jira-import-report.json');
  fs.writeFileSync(reportPath, JSON.stringify({ 
    timestamp: new Date().toISOString(),
    project: projectKey,
    total: cards.length,
    created,
    failed,
    results 
  }, null, 2));
  console.log(`\nReport saved: ${reportPath}`);
}

main().catch(console.error);
