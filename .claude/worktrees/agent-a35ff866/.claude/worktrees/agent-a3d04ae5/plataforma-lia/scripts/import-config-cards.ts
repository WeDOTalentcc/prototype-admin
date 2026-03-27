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
    throw new Error(`API error ${response.status}: ${errorText.substring(0, 200)}`);
  }
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

async function moveToMenuConfig(issueKey: string): Promise<boolean> {
  try {
    const result = await jiraApi(`/issue/${issueKey}/transitions`);
    const menuConfigTransition = result.transitions?.find(
      (t: any) => t.name?.toLowerCase().includes('menu config') || 
                  t.to?.name?.toLowerCase().includes('menu config') ||
                  t.to?.id === '10006'
    );
    if (menuConfigTransition) {
      await jiraApi(`/issue/${issueKey}/transitions`, 'POST', { transition: { id: menuConfigTransition.id } });
      return true;
    }
    // Try direct status update
    const todoTransition = result.transitions?.find((t: any) => t.to?.id === '10006');
    if (todoTransition) {
      await jiraApi(`/issue/${issueKey}/transitions`, 'POST', { transition: { id: todoTransition.id } });
      return true;
    }
    return false;
  } catch (e) { 
    console.log(`  Warning: Could not transition ${issueKey}: ${(e as Error).message.substring(0, 50)}`);
    return false; 
  }
}

function parseCardContent(yaml: string): any {
  const get = (key: string) => {
    const match = yaml.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'));
    return match?.[1]?.trim() || '';
  };
  
  const getMultiLine = (key: string): string => {
    const pattern = new RegExp(`^${key}:\\s*\\|\\s*\\n([\\s\\S]*?)(?=^[A-Za-z_]+:|$)`, 'm');
    const match = yaml.match(pattern);
    if (!match) return '';
    return match[1].split('\n').map(l => l.trim()).filter(Boolean).join(' ');
  };
  
  const getSection = (key: string): string[] => {
    const pattern = new RegExp(`^${key}:\\s*\\n([\\s\\S]*?)(?=^[A-Za-z_]+:|$)`, 'm');
    const match = yaml.match(pattern);
    if (!match) return [];
    return match[1].split('\n')
      .filter(line => line.trim().startsWith('-'))
      .map(line => line.replace(/^\s*-\s*/, '').replace(/^["']|["']$/g, '').trim())
      .filter(Boolean);
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
    descricao: get('Descricao') || getMultiLine('Descricao'),
    userStory: get('Historia_Usuario') || getMultiLine('Historia_Usuario'),
    regrasNegocio: getSection('Regras_Negocio'),
    requisitos: getSection('Requisitos_Tecnicos'),
    integracoes: getSection('Integracoes'),
    design: get('Design_Componentes'),
    designRef: getSection('Design_References'),
    uiBehavior: getSection('UI_Behavior'),
    criteriosAceite: getSection('Criterios_Aceite'),
    definitionOfDone: getSection('Definition_of_Done'),
    dependencies: getSection('Dependencies'),
    testCases: getSection('Test_Cases'),
    apiEndpoints: getSection('API_Endpoints'),
    securityReq: getSection('Security_Requirements'),
    accessibilityReq: getSection('Accessibility_Requirements')
  };
}

function buildDescription(card: any): any {
  const content: any[] = [];
  
  // Status panel
  const statusType = card.status?.includes('✅') ? 'success' : card.status?.includes('🔄') ? 'note' : 'info';
  content.push({
    type: 'panel', attrs: { panelType: statusType },
    content: [{ type: 'paragraph', content: [{ type: 'text', text: `Status: ${card.status || '🔧 A desenvolver'}` }] }]
  });

  // Metadata table with Hub/Subsecao
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
  
  addRow('Tipo', card.tipo || 'Feature');
  addRow('Hub', card.hub);
  addRow('Subseção', card.subsecao);
  addRow('Sprint', card.sprint || '0');
  addRow('Pontos', card.pontos || '0');
  addRow('Prioridade', card.prioridade || 'Medium');
  addRow('Epic', card.epic);
  
  content.push({ type: 'table', attrs: {}, content: rows });

  // Description
  if (card.descricao) {
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: '📝 Descrição' }] });
    content.push({ type: 'paragraph', content: [{ type: 'text', text: card.descricao }] });
  }

  // User Story
  if (card.userStory) {
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: '👤 História de Usuário' }] });
    content.push({ type: 'blockquote', content: [{ type: 'paragraph', content: [{ type: 'text', text: card.userStory }] }] });
  }

  // Helper for bullet lists
  const addList = (title: string, items: string[], emoji: string) => {
    if (!items || items.length === 0) return;
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: `${emoji} ${title}` }] });
    content.push({
      type: 'bulletList',
      content: items.map(item => ({
        type: 'listItem',
        content: [{ type: 'paragraph', content: [{ type: 'text', text: item }] }]
      }))
    });
  };

  addList('Regras de Negócio', card.regrasNegocio, '📏');
  addList('Requisitos Técnicos', card.requisitos, '⚙️');
  addList('Integrações', card.integracoes, '🔗');
  addList('API Endpoints', card.apiEndpoints, '🌐');
  
  if (card.design) {
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: '🎨 Design & Componentes' }] });
    content.push({ type: 'paragraph', content: [{ type: 'text', text: card.design }] });
  }
  
  addList('Design References', card.designRef, '🖼️');
  addList('Comportamento de UI', card.uiBehavior, '🖥️');
  addList('Critérios de Aceite', card.criteriosAceite, '✅');
  addList('Definition of Done', card.definitionOfDone, '🏁');
  addList('Test Cases', card.testCases, '🧪');
  addList('Security Requirements', card.securityReq, '🔒');
  addList('Accessibility Requirements', card.accessibilityReq, '♿');
  addList('Dependências', card.dependencies, '🔄');

  return { version: 1, type: 'doc', content };
}

async function main() {
  console.log('=== Import Config Cards to Jira (MENU CONFIG) ===\n');
  
  const docPath = path.join(__dirname, '../../docs/configuracoes-admin-cards-jira.md');
  const content = fs.readFileSync(docPath, 'utf-8');
  
  // Match card pattern: XXX-NNN (SET, EMP, REC, COM, INT, PLA, BUS, etc.)
  const cardRegex = /### CARD ([A-Z]+-\d+): ([^\n]+)\n\n```yaml\n([\s\S]*?)```/g;
  const cards: any[] = [];
  let match;
  
  while ((match = cardRegex.exec(content)) !== null) {
    cards.push({ 
      id: match[1], 
      name: match[2].trim(), 
      yaml: match[3] 
    });
  }
  
  console.log(`Found ${cards.length} config cards\n`);

  await initializeJira();
  
  const project = await jiraApi('/project/WT');
  const taskType = project.issueTypes?.find((t: any) => 
    t.name.toLowerCase() === 'task' || t.name.toLowerCase() === 'tarefa'
  );
  if (!taskType) throw new Error('No task type found');
  console.log(`Using issue type: ${taskType.name}\n`);

  let created = 0, failed = 0, movedToMenuConfig = 0;
  const results: any[] = [];

  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    const parsed = parseCardContent(card.yaml);
    
    const labels = ['config-admin', 'menu-config', `sprint-${parsed.sprint || '0'}`];
    if (parsed.hub) labels.push(`hub-${parsed.hub.toLowerCase().replace(/[^a-z0-9]/g, '-')}`);
    if (parsed.status?.includes('✅')) labels.push('implemented');
    
    try {
      const result = await jiraApi('/issue', 'POST', {
        fields: {
          project: { key: 'WT' },
          summary: `[${card.id}] ${parsed.titulo || card.name}`.substring(0, 255),
          description: buildDescription(parsed),
          issuetype: { id: taskType.id },
          labels
        }
      });
      
      created++;
      const moved = await moveToMenuConfig(result.key);
      if (moved) movedToMenuConfig++;
      
      console.log(`[${i+1}/${cards.length}] ✅ ${result.key} - ${card.id}${moved ? ' → MENU CONFIG' : ''}`);
      results.push({ card: card.id, issueKey: result.key, moved, status: 'success' });
    } catch (error: any) {
      failed++;
      console.log(`[${i+1}/${cards.length}] ❌ ${card.id}: ${error.message.substring(0, 80)}`);
      results.push({ card: card.id, status: 'failed', error: error.message.substring(0, 100) });
    }
    
    await new Promise(r => setTimeout(r, 300));
  }

  console.log(`\n=== Summary ===`);
  console.log(`Created: ${created} | Moved to MENU CONFIG: ${movedToMenuConfig} | Failed: ${failed}`);
  
  const keys = results.filter(r => r.issueKey).map(r => r.issueKey);
  if (keys.length > 0) {
    console.log(`Jira Keys: ${keys[0]} - ${keys[keys.length-1]}`);
  }

  fs.writeFileSync(path.join(__dirname, 'config-import-report.json'), JSON.stringify({ 
    timestamp: new Date().toISOString(),
    total: cards.length,
    created,
    movedToMenuConfig,
    failed,
    results 
  }, null, 2));
  
  console.log('\nReport saved to scripts/config-import-report.json');
}

main().catch(console.error);
