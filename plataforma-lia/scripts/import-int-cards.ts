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
  console.log('Connected to Jira');
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

async function moveToToDo(issueKey: string) {
  try {
    const result = await jiraRequest(`/issue/${issueKey}/transitions`);
    const todoTransition = result.transitions?.find(
      (t: any) => t.name?.toLowerCase().includes('to do') || t.to?.name?.toLowerCase().includes('to do')
    );
    if (todoTransition) {
      await jiraRequest(`/issue/${issueKey}/transitions`, 'POST', { transition: { id: todoTransition.id } });
      return true;
    }
    return false;
  } catch { return false; }
}

function buildDescription(yaml: string, hasDisclaimer: boolean): any {
  const content: any[] = [];
  
  if (hasDisclaimer) {
    content.push({
      type: 'panel', attrs: { panelType: 'warning' },
      content: [{ type: 'paragraph', content: [{ type: 'text', text: '⚠️ CARD RELACIONADO AO MENU DE CONFIGURAÇÕES', marks: [{ type: 'strong' }] }] }]
    });
  }

  const status = yaml.match(/^Status:\s*(.+)$/m)?.[1]?.trim() || '🔧 A desenvolver';
  content.push({
    type: 'panel', attrs: { panelType: status.includes('Pronto') ? 'success' : 'info' },
    content: [{ type: 'paragraph', content: [{ type: 'text', text: `Status: ${status}` }] }]
  });

  // Add full YAML as code block for complete content
  content.push({
    type: 'heading', attrs: { level: 2 },
    content: [{ type: 'text', text: 'Especificação Completa' }]
  });
  content.push({
    type: 'codeBlock', attrs: { language: 'yaml' },
    content: [{ type: 'text', text: yaml }]
  });

  return { version: 1, type: 'doc', content };
}

async function main() {
  console.log('Import INT-* Cards to Jira\n');
  
  const docPath = path.join(__dirname, '../../docs/lia-mvp-cards-jira.md');
  const content = fs.readFileSync(docPath, 'utf-8');
  
  // Match INT-XXX-NNN pattern
  const cardRegex = /### CARD (INT-[A-Z]+-\d+): ([^\n]+)\n\n```yaml\n([\s\S]*?)```/g;
  const cards: any[] = [];
  let match;
  
  while ((match = cardRegex.exec(content)) !== null) {
    const id = match[1];
    const name = match[2].trim();
    const yaml = match[3];
    const cardSection = content.substring(match.index, match.index + 4000);
    const hasDisclaimer = cardSection.includes('DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES');
    cards.push({ id, name, yaml, hasDisclaimer });
  }
  
  console.log(`Found ${cards.length} INT-* cards\n`);

  await initializeJiraConnection();
  
  const project = await jiraRequest('/project/WT');
  const taskType = project.issueTypes?.find((t: any) => t.name.toLowerCase() === 'task' || t.name.toLowerCase() === 'tarefa');
  if (!taskType) { console.error('No task type'); return; }
  console.log(`Using: ${taskType.name}\n`);

  let created = 0, failed = 0;
  const results: any[] = [];

  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    const titulo = card.yaml.match(/^Titulo:\s*(.+)$/m)?.[1]?.trim() || card.name;
    const sprint = card.yaml.match(/^Sprint:\s*(.+)$/m)?.[1]?.trim() || '0';
    
    const labels = ['lia-mvp', 'integrations', `sprint-${sprint}`];
    if (card.hasDisclaimer) labels.push('config-menu');
    if (card.yaml.includes('Status: ✅')) labels.push('implemented');
    
    try {
      const result = await jiraRequest('/issue', 'POST', {
        fields: {
          project: { key: 'WT' },
          summary: `[${card.id}] ${titulo}`.substring(0, 255),
          description: buildDescription(card.yaml, card.hasDisclaimer),
          issuetype: { id: taskType.id },
          labels
        }
      });
      
      created++;
      const moved = await moveToToDo(result.key);
      console.log(`[${i+1}/${cards.length}] ✅ ${result.key} - ${card.id}${moved ? ' → TO DO' : ''}`);
      results.push({ card: card.id, issueKey: result.key, moved });
    } catch (error: any) {
      failed++;
      console.log(`[${i+1}/${cards.length}] ❌ ${card.id}: ${error.message.substring(0, 60)}`);
      results.push({ card: card.id, status: 'failed' });
    }
    
    await new Promise(r => setTimeout(r, 350));
  }

  console.log(`\n=== Summary ===`);
  console.log(`Created: ${created} | Failed: ${failed}`);
  
  if (results.length > 0) {
    const keys = results.filter(r => r.issueKey).map(r => r.issueKey);
    if (keys.length > 0) console.log(`Keys: ${keys[0]} - ${keys[keys.length-1]}`);
  }

  fs.writeFileSync(path.join(__dirname, 'int-cards-report.json'), JSON.stringify({ 
    timestamp: new Date().toISOString(), total: cards.length, created, failed, results 
  }, null, 2));
}

main().catch(console.error);
