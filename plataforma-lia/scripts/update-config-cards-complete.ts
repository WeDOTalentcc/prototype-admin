import * as fs from 'fs';
import * as path from 'path';

let accessToken: string;
let cloudId: string;

async function initializeJira() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY ? 'repl ' + process.env.REPL_IDENTITY : null;
  if (!xReplitToken) throw new Error('Token not found');

  const url = 'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=jira';
  const response = await fetch(url, { headers: { 'Accept': 'application/json', 'X_REPLIT_TOKEN': xReplitToken } });
  const data = await response.json();
  accessToken = data.items?.[0]?.settings?.access_token;
  
  const cloudResponse = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: { 'Accept': 'application/json', 'Authorization': `Bearer ${accessToken}` }
  });
  const resources = await cloudResponse.json();
  cloudId = resources.find((r: any) => r.url.includes('wedotalent'))?.id;
  console.log('Connected to Jira');
}

async function jiraApi(endpoint: string, method: string = 'GET', body?: any) {
  const url = `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3${endpoint}`;
  const options: RequestInit = {
    method,
    headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': `Bearer ${accessToken}` }
  };
  if (body) options.body = JSON.stringify(body);
  const response = await fetch(url, options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error ${response.status}: ${errorText.substring(0, 200)}`);
  }
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

async function searchJql(jql: string): Promise<any[]> {
  const url = `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/search/jql?jql=${encodeURIComponent(jql)}&maxResults=200&fields=key,summary`;
  const response = await fetch(url, { headers: { 'Accept': 'application/json', 'Authorization': `Bearer ${accessToken}` } });
  const result = await response.json();
  return result.issues || [];
}

async function transitionTo(issueKey: string, statusName: string): Promise<boolean> {
  try {
    const result = await jiraApi(`/issue/${issueKey}/transitions`);
    const transition = result.transitions?.find(
      (t: any) => t.name?.toLowerCase().includes(statusName.toLowerCase()) || t.to?.name?.toLowerCase().includes(statusName.toLowerCase())
    );
    if (transition) {
      await jiraApi(`/issue/${issueKey}/transitions`, 'POST', { transition: { id: transition.id } });
      return true;
    }
    return false;
  } catch { return false; }
}

function parseFullCard(yaml: string): any {
  const get = (key: string): string => {
    const match = yaml.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'));
    return match?.[1]?.trim().replace(/^["']|["']$/g, '') || '';
  };
  
  const getMultiline = (key: string): string => {
    const pattern = new RegExp(`^${key}:\\s*\\|\\s*\\n([\\s\\S]*?)(?=^\\w+:|^\\s*$)`, 'm');
    const match = yaml.match(pattern);
    if (!match) return get(key);
    return match[1].split('\n').map(l => l.trim()).filter(Boolean).join(' ');
  };
  
  const getList = (key: string): string[] => {
    const pattern = new RegExp(`^${key}:\\s*\\n([\\s\\S]*?)(?=^[A-Za-z_]+:|$)`, 'm');
    const match = yaml.match(pattern);
    if (!match) return [];
    const lines = match[1].split('\n');
    const items: string[] = [];
    let currentItem = '';
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('-')) {
        if (currentItem) items.push(currentItem);
        currentItem = trimmed.replace(/^-\s*/, '').replace(/^["']|["']$/g, '');
      } else if (trimmed && currentItem) {
        currentItem += ' ' + trimmed;
      }
    }
    if (currentItem) items.push(currentItem);
    return items.filter(Boolean);
  };
  
  const getNumberedList = (key: string): string[] => {
    const pattern = new RegExp(`^${key}:\\s*\\n([\\s\\S]*?)(?=^[A-Za-z_]+:|$)`, 'm');
    const match = yaml.match(pattern);
    if (!match) return [];
    return match[1].split('\n').filter(line => /^\s*\d+\./.test(line)).map(line => line.replace(/^\s*\d+\.\s*/, '').trim()).filter(Boolean);
  };
  
  const getNestedSection = (key: string): string => {
    const pattern = new RegExp(`^${key}:\\s*\\n([\\s\\S]*?)(?=^[A-Za-z_]+:|^---|\$)`, 'm');
    const match = yaml.match(pattern);
    if (!match) return '';
    return match[1].trim();
  };

  return {
    titulo: get('Titulo'),
    tipo: get('Tipo'),
    sprint: get('Sprint'),
    pontos: get('Pontos'),
    prioridade: get('Prioridade'),
    epic: get('Epic'),
    status: get('Status'),
    hub: get('Hub'),
    subsecao: get('Subsecao'),
    descricao: getMultiline('Descricao'),
    userStory: getMultiline('Historia de Usuario') || getMultiline('Historia_Usuario'),
    regrasNegocio: getNumberedList('Regras de Negocio') || getList('Regras_Negocio'),
    requisitos: getNestedSection('Requisitos Tecnicos') || getNestedSection('Requisitos_Tecnicos'),
    integracoes: getList('Integracoes') || getList('Integracoes_Externas'),
    design: getNestedSection('Design & Componentes') || getNestedSection('Design_Componentes'),
    uiBehavior: getNestedSection('Comportamento de UI') || getNestedSection('UI_Behavior'),
    criteriosAceite: getList('Criterios de Aceite') || getList('Criterios_Aceite'),
    definitionOfDone: getList('Definition of Done') || getList('Definition_of_Done'),
    dependencies: getList('Dependencies') || getList('Dependencias'),
    apiEndpoints: getList('API_Endpoints') || getList('Endpoints'),
    securityReq: getList('Security_Requirements') || getList('Seguranca'),
    accessibilityReq: getList('Accessibility_Requirements') || getList('Acessibilidade'),
    testCases: getList('Test_Cases') || getList('Testes'),
    references: getNestedSection('Referencias de Design') || getNestedSection('Design_References')
  };
}

function buildFullDescription(card: any, cardId: string): any {
  const content: any[] = [];
  
  const statusType = card.status?.includes('✅') ? 'success' : card.status?.includes('🔄') ? 'note' : 'info';
  content.push({
    type: 'panel', attrs: { panelType: statusType },
    content: [{ type: 'paragraph', content: [{ type: 'text', text: `Status: ${card.status || '🔧 A desenvolver'}` }] }]
  });

  content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: '📋 Metadados' }] });
  const rows: any[] = [
    { type: 'tableRow', content: [
      { type: 'tableHeader', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Campo' }] }] },
      { type: 'tableHeader', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Valor' }] }] }
    ]}
  ];
  
  const addRow = (label: string, value: string) => {
    if (!value) return;
    rows.push({ type: 'tableRow', content: [
      { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: label }] }] },
      { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: value }] }] }
    ]});
  };
  
  addRow('Card ID', cardId);
  addRow('Tipo', card.tipo || 'Feature');
  addRow('Hub', card.hub);
  addRow('Subseção', card.subsecao);
  addRow('Sprint', card.sprint || '0');
  addRow('Pontos', card.pontos || '0');
  addRow('Prioridade', card.prioridade || 'Medium');
  addRow('Epic', card.epic);
  
  content.push({ type: 'table', attrs: {}, content: rows });

  if (card.descricao) {
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: '📝 Descrição' }] });
    content.push({ type: 'paragraph', content: [{ type: 'text', text: card.descricao }] });
  }

  if (card.userStory) {
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: '👤 História de Usuário' }] });
    content.push({ type: 'blockquote', content: [{ type: 'paragraph', content: [{ type: 'text', text: card.userStory }] }] });
  }

  const addBulletList = (title: string, items: string[], emoji: string) => {
    if (!items || items.length === 0) return;
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: `${emoji} ${title}` }] });
    content.push({ type: 'bulletList', content: items.map(item => ({ type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: item }] }] })) });
  };

  const addCodeSection = (title: string, text: string, emoji: string) => {
    if (!text) return;
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: `${emoji} ${title}` }] });
    content.push({ type: 'codeBlock', attrs: { language: 'yaml' }, content: [{ type: 'text', text: text }] });
  };

  addBulletList('Regras de Negócio', card.regrasNegocio, '📏');
  addCodeSection('Requisitos Técnicos', card.requisitos, '⚙️');
  addBulletList('Integrações', card.integracoes, '🔗');
  addBulletList('API Endpoints', card.apiEndpoints, '🌐');
  addCodeSection('Design & Componentes', card.design, '🎨');
  addCodeSection('Comportamento de UI', card.uiBehavior, '🖥️');
  addBulletList('Critérios de Aceite', card.criteriosAceite, '✅');
  addBulletList('Definition of Done', card.definitionOfDone, '🏁');
  addBulletList('Test Cases', card.testCases, '🧪');
  addBulletList('Security Requirements', card.securityReq, '🔒');
  addBulletList('Accessibility', card.accessibilityReq, '♿');
  addBulletList('Dependências', card.dependencies, '🔄');
  addCodeSection('Referências de Design', card.references, '🖼️');

  return { version: 1, type: 'doc', content };
}

async function main() {
  console.log('=== Update Config Cards with Full Content ===\n');
  
  const docPath = path.join(__dirname, '../../docs/configuracoes-admin-cards-jira.md');
  const content = fs.readFileSync(docPath, 'utf-8');
  
  const cardRegex = /### CARD ([A-Z]+-[0-9]+): ([^\n]+)\n\n```yaml\n([\s\S]*?)```/g;
  const docCards: Map<string, any> = new Map();
  let match;
  
  while ((match = cardRegex.exec(content)) !== null) {
    docCards.set(match[1], { id: match[1], name: match[2].trim(), yaml: match[3] });
  }
  
  console.log(`Found ${docCards.size} cards in document\n`);

  await initializeJira();
  
  const jiraCards = await searchJql('project = WT AND labels = config-admin ORDER BY key ASC');
  console.log(`Found ${jiraCards.length} config-admin cards in Jira\n`);
  
  const cardToJira: Map<string, string> = new Map();
  for (const issue of jiraCards) {
    const match = issue.fields?.summary?.match(/\[([A-Z]+-[0-9]+)\]/);
    if (match) cardToJira.set(match[1], issue.key);
  }
  
  const project = await jiraApi('/project/WT');
  const taskType = project.issueTypes?.find((t: any) => t.name.toLowerCase() === 'task' || t.name.toLowerCase() === 'tarefa');
  
  let updated = 0, created = 0, failed = 0;
  const results: any[] = [];

  for (const [cardId, cardData] of docCards) {
    const parsed = parseFullCard(cardData.yaml);
    const jiraKey = cardToJira.get(cardId);
    
    const labels = ['config-admin', 'menu-config', `sprint-${parsed.sprint || '0'}`];
    if (parsed.hub) labels.push(`hub-${parsed.hub.toLowerCase().replace(/[^a-z0-9]/g, '-')}`);
    if (parsed.tipo) labels.push(`tipo-${parsed.tipo.toLowerCase().replace(/[^a-z0-9]/g, '-')}`);
    if (parsed.epic) labels.push(`epic-${parsed.epic.toLowerCase().replace(/[^a-z0-9]/g, '-')}`);
    if (parsed.prioridade) labels.push(`priority-${parsed.prioridade.toLowerCase().replace(/[^a-z0-9]/g, '-')}`);
    if (parsed.status?.includes('✅')) labels.push('implemented');
    
    const description = buildFullDescription(parsed, cardId);
    const summary = `[${cardId}] ${parsed.titulo || cardData.name}`.substring(0, 255);
    
    try {
      if (jiraKey) {
        await jiraApi(`/issue/${jiraKey}`, 'PUT', { fields: { summary, description, labels } });
        updated++;
        await transitionTo(jiraKey, 'menu config');
        console.log(`[${updated + created}/${docCards.size}] 📝 Updated ${jiraKey} - ${cardId}`);
        results.push({ card: cardId, issueKey: jiraKey, action: 'updated' });
      } else {
        const result = await jiraApi('/issue', 'POST', {
          fields: { project: { key: 'WT' }, summary, description, issuetype: { id: taskType.id }, labels }
        });
        created++;
        await transitionTo(result.key, 'menu config');
        console.log(`[${updated + created}/${docCards.size}] ✅ Created ${result.key} - ${cardId}`);
        results.push({ card: cardId, issueKey: result.key, action: 'created' });
      }
    } catch (error: any) {
      failed++;
      console.log(`[${updated + created + failed}/${docCards.size}] ❌ ${cardId}: ${error.message.substring(0, 60)}`);
      results.push({ card: cardId, action: 'failed', error: error.message.substring(0, 100) });
    }
    
    await new Promise(r => setTimeout(r, 250));
  }

  console.log(`\n=== Summary ===`);
  console.log(`Updated: ${updated} | Created: ${created} | Failed: ${failed}`);
  
  fs.writeFileSync(path.join(__dirname, 'update-config-report.json'), JSON.stringify({ 
    timestamp: new Date().toISOString(), total: docCards.size, updated, created, failed, results 
  }, null, 2));
  
  console.log('\nReport saved to scripts/update-config-report.json');
}

main().catch(console.error);
