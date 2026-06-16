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

async function searchJql(jql: string, fields: string[] = ['key', 'summary']): Promise<any[]> {
  const url = `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/search/jql?jql=${encodeURIComponent(jql)}&maxResults=200&fields=${fields.join(',')}`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json', 'Authorization': `Bearer ${accessToken}` }
  });
  const result = await response.json();
  return result.issues || [];
}

async function transitionTo(issueKey: string, statusName: string): Promise<boolean> {
  try {
    const result = await jiraApi(`/issue/${issueKey}/transitions`);
    const transition = result.transitions?.find(
      (t: any) => t.name?.toLowerCase().includes(statusName.toLowerCase()) || 
                  t.to?.name?.toLowerCase().includes(statusName.toLowerCase())
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
    return match[1].split('\n')
      .filter(line => /^\s*\d+\./.test(line))
      .map(line => line.replace(/^\s*\d+\.\s*/, '').trim())
      .filter(Boolean);
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
    descricao: getMultiline('Descricao'),
    userStory: getMultiline('Historia de Usuario') || getMultiline('Historia_Usuario'),
    regrasNegocio: getNumberedList('Regras de Negocio') || getList('Regras_Negocio'),
    requisitos: getNestedSection('Requisitos Tecnicos') || getNestedSection('Requisitos_Tecnicos'),
    integracoes: getList('Integracoes'),
    design: getNestedSection('Design & Componentes') || getNestedSection('Design_Componentes'),
    uiBehavior: getNestedSection('Comportamento de UI') || getNestedSection('UI_Behavior'),
    criteriosAceite: getList('Criterios de Aceite') || getList('Criterios_Aceite'),
    definitionOfDone: getList('Definition of Done') || getList('Definition_of_Done'),
    dependencies: getList('Dependencies') || getList('Dependencias'),
    references: getNestedSection('Referencias de Design')
  };
}

function buildFullDescription(card: any, cardId: string, hasDisclaimer: boolean): any {
  const content: any[] = [];
  
  // Disclaimer if applicable
  if (hasDisclaimer) {
    content.push({
      type: 'panel', attrs: { panelType: 'warning' },
      content: [{ type: 'paragraph', content: [{ type: 'text', text: '⚠️ CARD RELACIONADO AO MENU DE CONFIGURAÇÕES - Este card integra funcionalidades do menu de configurações da empresa.', marks: [{ type: 'strong' }] }] }]
    });
  }

  // Status panel
  const statusType = card.status?.includes('✅') ? 'success' : card.status?.includes('🔄') ? 'note' : 'info';
  content.push({
    type: 'panel', attrs: { panelType: statusType },
    content: [{ type: 'paragraph', content: [{ type: 'text', text: `Status: ${card.status || '🔧 A desenvolver'}` }] }]
  });

  // Metadata table
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
  addRow('Sprint', card.sprint || '0');
  addRow('Pontos', card.pontos || '0');
  addRow('Prioridade', card.prioridade || 'Medium');
  addRow('Epic', card.epic || '-');
  
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

  // Bullet list helper
  const addBulletList = (title: string, items: string[], emoji: string) => {
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

  // Code block helper for nested sections
  const addCodeSection = (title: string, text: string, emoji: string) => {
    if (!text) return;
    content.push({ type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: `${emoji} ${title}` }] });
    content.push({ type: 'codeBlock', attrs: { language: 'yaml' }, content: [{ type: 'text', text: text }] });
  };

  addBulletList('Regras de Negócio', card.regrasNegocio, '📏');
  addCodeSection('Requisitos Técnicos', card.requisitos, '⚙️');
  addBulletList('Integrações', card.integracoes, '🔗');
  addCodeSection('Design & Componentes', card.design, '🎨');
  addCodeSection('Comportamento de UI', card.uiBehavior, '🖥️');
  addBulletList('Critérios de Aceite', card.criteriosAceite, '✅');
  addBulletList('Definition of Done', card.definitionOfDone, '🏁');
  addBulletList('Dependências', card.dependencies, '🔄');
  addCodeSection('Referências de Design', card.references, '🖼️');

  return { version: 1, type: 'doc', content };
}

async function main() {
  console.log('=== Update MVP Cards with Full Content ===\n');
  
  const docPath = path.join(__dirname, '../../docs/lia-mvp-cards-jira.md');
  const content = fs.readFileSync(docPath, 'utf-8');
  
  // Parse all cards from document
  const cardRegex = /### CARD ([A-Z]+-(?:[A-Z]+-)?[0-9]+): ([^\n]+)\n\n```yaml\n([\s\S]*?)```/g;
  const docCards: Map<string, any> = new Map();
  let match;
  
  while ((match = cardRegex.exec(content)) !== null) {
    const id = match[1];
    const name = match[2].trim();
    const yaml = match[3];
    const cardSection = content.substring(Math.max(0, match.index - 500), match.index + 500);
    const hasDisclaimer = cardSection.includes('DISCLAIMER: CARD RELACIONADO AO MENU DE CONFIGURAÇÕES');
    docCards.set(id, { id, name, yaml, hasDisclaimer });
  }
  
  console.log(`Found ${docCards.size} cards in document\n`);

  await initializeJira();
  
  // Get all lia-mvp cards from Jira
  const jiraCards = await searchJql('project = WT AND labels = lia-mvp ORDER BY key ASC', ['key', 'summary', 'status', 'labels']);
  console.log(`Found ${jiraCards.length} lia-mvp cards in Jira\n`);
  
  // Build mapping from card ID to Jira key
  const cardToJira: Map<string, string> = new Map();
  for (const issue of jiraCards) {
    const match = issue.fields?.summary?.match(/\[([A-Z]+-(?:[A-Z]+-)?[0-9]+)\]/);
    if (match) {
      cardToJira.set(match[1], issue.key);
    }
  }
  
  console.log(`Mapped ${cardToJira.size} cards\n`);
  
  // Get project info for issue type
  const project = await jiraApi('/project/WT');
  const taskType = project.issueTypes?.find((t: any) => 
    t.name.toLowerCase() === 'task' || t.name.toLowerCase() === 'tarefa'
  );
  
  let updated = 0, created = 0, failed = 0;
  const results: any[] = [];

  // Process each card from document
  for (const [cardId, cardData] of docCards) {
    const parsed = parseFullCard(cardData.yaml);
    const jiraKey = cardToJira.get(cardId);
    
    // Build labels
    const labels = ['lia-mvp', `sprint-${parsed.sprint || '0'}`];
    if (cardData.hasDisclaimer) labels.push('config-menu');
    if (parsed.status?.includes('✅')) labels.push('implemented');
    if (cardId.startsWith('INT-')) labels.push('integrations');
    if (parsed.tipo) labels.push(`tipo-${parsed.tipo.toLowerCase().replace(/[^a-z0-9]/g, '-')}`);
    if (parsed.epic) labels.push(`epic-${parsed.epic.toLowerCase().replace(/[^a-z0-9]/g, '-')}`);
    if (parsed.prioridade) labels.push(`priority-${parsed.prioridade.toLowerCase().replace(/[^a-z0-9]/g, '-')}`);
    
    const description = buildFullDescription(parsed, cardId, cardData.hasDisclaimer);
    const summary = `[${cardId}] ${parsed.titulo || cardData.name}`.substring(0, 255);
    
    try {
      if (jiraKey) {
        // Update existing card
        await jiraApi(`/issue/${jiraKey}`, 'PUT', {
          fields: {
            summary,
            description,
            labels
          }
        });
        updated++;
        
        // Transition to TO DO if needed
        await transitionTo(jiraKey, 'to do');
        
        console.log(`[${updated + created}/${docCards.size}] 📝 Updated ${jiraKey} - ${cardId}`);
        results.push({ card: cardId, issueKey: jiraKey, action: 'updated' });
      } else {
        // Create new card
        const result = await jiraApi('/issue', 'POST', {
          fields: {
            project: { key: 'WT' },
            summary,
            description,
            issuetype: { id: taskType.id },
            labels
          }
        });
        created++;
        await transitionTo(result.key, 'to do');
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
  
  fs.writeFileSync(path.join(__dirname, 'update-mvp-report.json'), JSON.stringify({ 
    timestamp: new Date().toISOString(),
    total: docCards.size,
    updated,
    created,
    failed,
    results 
  }, null, 2));
  
  console.log('\nReport saved to scripts/update-mvp-report.json');
}

main().catch(console.error);
