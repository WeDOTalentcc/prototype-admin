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
  console.log('Connected to Jira - Cloud ID:', cloudId);
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

async function moveToToDo(issueKey: string): Promise<boolean> {
  try {
    const result = await jiraApi(`/issue/${issueKey}/transitions`);
    const todoTransition = result.transitions?.find(
      (t: any) => t.name?.toLowerCase().includes('to do') || t.to?.name?.toLowerCase().includes('to do')
    );
    if (todoTransition) {
      await jiraApi(`/issue/${issueKey}/transitions`, 'POST', { transition: { id: todoTransition.id } });
      return true;
    }
    return false;
  } catch { return false; }
}

function parseCardContent(yaml: string): any {
  const get = (key: string) => {
    const match = yaml.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'));
    return match?.[1]?.trim() || '';
  };
  
  const getSection = (key: string): string[] => {
    const pattern = new RegExp(`^${key}:\\s*\\n([\\s\\S]*?)(?=^[A-Za-z_]+:|$)`, 'm');
    const match = yaml.match(pattern);
    if (!match) return [];
    return match[1].split('\n')
      .filter(line => line.trim().startsWith('-'))
      .map(line => line.replace(/^\s*-\s*/, '').trim())
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
    descricao: get('Descricao'),
    userStory: get('Historia_Usuario'),
    regrasNegocio: getSection('Regras_Negocio'),
    requisitos: getSection('Requisitos_Tecnicos'),
    integracoes: getSection('Integracoes'),
    design: get('Design_Componentes'),
    uiBehavior: getSection('UI_Behavior'),
    criteriosAceite: getSection('Criterios_Aceite'),
    definitionOfDone: getSection('Definition_of_Done'),
    dependencies: getSection('Dependencies')
  };
}

function buildDescription(card: any, hasDisclaimer: boolean): any {
  const content: any[] = [];
  
  if (hasDisclaimer) {
    content.push({
      type: 'panel', attrs: { panelType: 'warning' },
      content: [{ type: 'paragraph', content: [{ type: 'text', text: '⚠️ CARD RELACIONADO AO MENU DE CONFIGURAÇÕES', marks: [{ type: 'strong' }] }] }]
    });
  }

  const statusType = card.status?.includes('✅') ? 'success' : card.status?.includes('🔄') ? 'note' : 'info';
  content.push({
    type: 'panel', attrs: { panelType: statusType },
    content: [{ type: 'paragraph', content: [{ type: 'text', text: `Status: ${card.status || '🔧 A desenvolver'}` }] }]
  });

  content.push({
    type: 'heading', attrs: { level: 2 },
    content: [{ type: 'text', text: '📋 Metadados' }]
  });
  content.push({
    type: 'table', attrs: {},
    content: [
      { type: 'tableRow', content: [
        { type: 'tableHeader', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Campo' }] }] },
        { type: 'tableHeader', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Valor' }] }] }
      ]},
      { type: 'tableRow', content: [
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Tipo' }] }] },
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: card.tipo || 'Feature' }] }] }
      ]},
      { type: 'tableRow', content: [
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Sprint' }] }] },
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: card.sprint || '0' }] }] }
      ]},
      { type: 'tableRow', content: [
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Pontos' }] }] },
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: card.pontos || '0' }] }] }
      ]},
      { type: 'tableRow', content: [
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Prioridade' }] }] },
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: card.prioridade || 'Medium' }] }] }
      ]},
      { type: 'tableRow', content: [
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Epic' }] }] },
        { type: 'tableCell', attrs: {}, content: [{ type: 'paragraph', content: [{ type: 'text', text: card.epic || '-' }] }] }
      ]}
    ]
  });

  if (card.descricao) {
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: '📝 Descrição' }] });
    content.push({ type: 'paragraph', content: [{ type: 'text', text: card.descricao }] });
  }

  if (card.userStory) {
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: '👤 História de Usuário' }] });
    content.push({ type: 'blockquote', content: [{ type: 'paragraph', content: [{ type: 'text', text: card.userStory }] }] });
  }

  const addBulletList = (title: string, items: string[], emoji: string = '📌') => {
    if (items.length === 0) return;
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: `${emoji} ${title}` }] });
    content.push({
      type: 'bulletList',
      content: items.map(item => ({
        type: 'listItem',
        content: [{ type: 'paragraph', content: [{ type: 'text', text: item }] }]
      }))
    });
  };

  addBulletList('Regras de Negócio', card.regrasNegocio, '📏');
  addBulletList('Requisitos Técnicos', card.requisitos, '⚙️');
  addBulletList('Integrações', card.integracoes, '🔗');
  
  if (card.design) {
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: '🎨 Design & Componentes' }] });
    content.push({ type: 'paragraph', content: [{ type: 'text', text: card.design }] });
  }

  addBulletList('Comportamento de UI', card.uiBehavior, '🖥️');
  addBulletList('Critérios de Aceite', card.criteriosAceite, '✅');
  addBulletList('Definition of Done', card.definitionOfDone, '🏁');
  addBulletList('Dependências', card.dependencies, '🔄');

  return { version: 1, type: 'doc', content };
}

async function main() {
  console.log('=== Import All Cards to Jira ===\n');
  
  const docPath = path.join(__dirname, '../../docs/lia-mvp-cards-jira.md');
  const content = fs.readFileSync(docPath, 'utf-8');
  
  // Match all card patterns
  const cardRegex = /### CARD ([A-Z]+-(?:[A-Z]+-)?[0-9]+): ([^\n]+)\n\n```yaml\n([\s\S]*?)```/g;
  const cards: any[] = [];
  let match;
  
  while ((match = cardRegex.exec(content)) !== null) {
    const id = match[1];
    const name = match[2].trim();
    const yaml = match[3];
    const cardSection = content.substring(Math.max(0, match.index - 500), match.index + 500);
    const hasDisclaimer = cardSection.includes('DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES');
    cards.push({ id, name, yaml, hasDisclaimer });
  }
  
  console.log(`Found ${cards.length} cards in document\n`);

  await initializeJira();
  
  const project = await jiraApi('/project/WT');
  const taskType = project.issueTypes?.find((t: any) => 
    t.name.toLowerCase() === 'task' || t.name.toLowerCase() === 'tarefa'
  );
  if (!taskType) throw new Error('No task type found');
  console.log(`Using issue type: ${taskType.name}\n`);

  let created = 0, failed = 0;
  const results: any[] = [];

  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    const parsed = parseCardContent(card.yaml);
    
    const labels = ['lia-mvp', `sprint-${parsed.sprint || '0'}`];
    if (card.hasDisclaimer) labels.push('config-menu');
    if (parsed.status?.includes('✅')) labels.push('implemented');
    if (card.id.startsWith('INT-')) labels.push('integrations');
    
    try {
      const result = await jiraApi('/issue', 'POST', {
        fields: {
          project: { key: 'WT' },
          summary: `[${card.id}] ${parsed.titulo || card.name}`.substring(0, 255),
          description: buildDescription(parsed, card.hasDisclaimer),
          issuetype: { id: taskType.id },
          labels
        }
      });
      
      created++;
      const moved = await moveToToDo(result.key);
      console.log(`[${i+1}/${cards.length}] ✅ ${result.key} - ${card.id}${moved ? ' → TO DO' : ''}`);
      results.push({ card: card.id, issueKey: result.key, moved, status: 'success' });
    } catch (error: any) {
      failed++;
      console.log(`[${i+1}/${cards.length}] ❌ ${card.id}: ${error.message.substring(0, 80)}`);
      results.push({ card: card.id, status: 'failed', error: error.message.substring(0, 100) });
    }
    
    await new Promise(r => setTimeout(r, 300));
  }

  console.log(`\n=== Summary ===`);
  console.log(`Created: ${created} | Failed: ${failed}`);
  
  const keys = results.filter(r => r.issueKey).map(r => r.issueKey);
  if (keys.length > 0) {
    console.log(`Jira Keys: ${keys[0]} - ${keys[keys.length-1]}`);
  }

  fs.writeFileSync(path.join(__dirname, 'import-report.json'), JSON.stringify({ 
    timestamp: new Date().toISOString(),
    total: cards.length,
    created,
    failed,
    results 
  }, null, 2));
  
  console.log('\nReport saved to scripts/import-report.json');
}

main().catch(console.error);
