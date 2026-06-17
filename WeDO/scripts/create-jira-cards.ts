import * as fs from 'fs';
import * as path from 'path';

interface JiraCard {
  id: string;
  title: string;
  type: string;
  sprint?: string;
  points?: number;
  priority: string;
  epic: string;
  status: string;
  dependencies?: string;
  description: string;
  labels: string[];
}

const JIRA_CONFIG = {
  projectKey: 'WT',
  cloudId: '8cf762f8-6a44-47de-8915-6b3dc0cd2715',
  apiBaseUrl: 'https://api.atlassian.com/ex/jira/8cf762f8-6a44-47de-8915-6b3dc0cd2715'
};

async function getAccessToken(): Promise<string> {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('X_REPLIT_TOKEN not found');
  }

  const resp = await fetch(
    `https://${hostname}/api/v2/connection?include_secrets=true&connector_names=jira`,
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  );
  const data = await resp.json();
  const settings = data.items?.[0]?.settings;
  return settings?.access_token || settings?.oauth?.credentials?.access_token;
}

function parseMarkdownCards(content: string): JiraCard[] {
  const cards: JiraCard[] = [];
  
  // Updated pattern to match INT-TWI-001 style IDs
  const cardPattern = /### CARD ([A-Z]+-[A-Z]*-?\d+): (.+?)\n\n```yaml\n([\s\S]+?)```/g;
  let match;
  
  while ((match = cardPattern.exec(content)) !== null) {
    const cardId = match[1];
    const cardTitle = match[2];
    const yamlContent = match[3];
    
    const card = parseYamlCard(cardId, cardTitle, yamlContent);
    if (card) {
      cards.push(card);
    }
  }
  
  return cards;
}

function parseYamlCard(id: string, title: string, yamlContent: string): JiraCard | null {
  const lines = yamlContent.split('\n');
  const data: Record<string, string> = {};
  let currentKey = '';
  let currentValue = '';
  let inMultiline = false;
  
  for (const line of lines) {
    if (line.match(/^[A-Za-z_]+:/)) {
      if (currentKey) {
        data[currentKey] = currentValue.trim();
      }
      const colonIndex = line.indexOf(':');
      currentKey = line.substring(0, colonIndex).trim().toLowerCase().replace(/\s+/g, '_');
      const value = line.substring(colonIndex + 1).trim();
      if (value === '|') {
        inMultiline = true;
        currentValue = '';
      } else {
        inMultiline = false;
        currentValue = value;
      }
    } else if (inMultiline || currentKey) {
      currentValue += '\n' + line;
    }
  }
  if (currentKey) {
    data[currentKey] = currentValue.trim();
  }

  const fullTitle = data.titulo || `[${data.tipo || 'Feature'}] ${title}`;
  
  let fullDescription = '';
  
  if (data.descricao) {
    fullDescription += `h2. Descrição\n${data.descricao}\n\n`;
  }
  
  if (data.historia_de_usuario) {
    fullDescription += `h2. História de Usuário\n${data.historia_de_usuario}\n\n`;
  }
  
  if (data.regras_de_negocio) {
    fullDescription += `h2. Regras de Negócio\n${data.regras_de_negocio}\n\n`;
  }
  
  if (data.requisitos_tecnicos) {
    fullDescription += `h2. Requisitos Técnicos\n${data.requisitos_tecnicos}\n\n`;
  }
  
  if (data.integracoes_externas) {
    fullDescription += `h2. Integrações Externas\n${data.integracoes_externas}\n\n`;
  }
  
  if (data['design_&_componentes'] || data.design_e_componentes) {
    fullDescription += `h2. Design & Componentes\n${data['design_&_componentes'] || data.design_e_componentes}\n\n`;
  }
  
  if (data.comportamento_de_ui) {
    fullDescription += `h2. Comportamento de UI\n${data.comportamento_de_ui}\n\n`;
  }
  
  if (data.dod) {
    fullDescription += `h2. Definition of Done\n${data.dod}\n\n`;
  }
  
  if (data.criterios_de_aceitacao) {
    fullDescription += `h2. Critérios de Aceitação\n${data.criterios_de_aceitacao}\n\n`;
  }

  const labels: string[] = ['MVP'];
  
  const tipo = data.tipo?.toLowerCase() || '';
  if (tipo.includes('frontend')) labels.push('frontend');
  if (tipo.includes('backend')) labels.push('backend');
  if (tipo.includes('full-stack') || tipo.includes('fullstack')) labels.push('fullstack');
  if (tipo.includes('integra')) labels.push('integration');
  if (tipo.includes('ai')) labels.push('ai');

  const epicMatch = id.match(/^([A-Z]+)/);
  if (epicMatch) {
    labels.push(`epic-${epicMatch[1].toLowerCase()}`);
  }

  let priority = 'Medium';
  const prioridadeRaw = data.prioridade?.toLowerCase() || '';
  if (prioridadeRaw.includes('crítica') || prioridadeRaw.includes('critica')) priority = 'Highest';
  else if (prioridadeRaw.includes('alta')) priority = 'High';
  else if (prioridadeRaw.includes('média') || prioridadeRaw.includes('media')) priority = 'Medium';
  else if (prioridadeRaw.includes('baixa')) priority = 'Low';

  return {
    id,
    title: fullTitle,
    type: data.tipo || 'Feature',
    sprint: data.sprint,
    points: data.pontos ? parseInt(data.pontos) : undefined,
    priority,
    epic: data.epic || '',
    status: data.status || '',
    dependencies: data.dependencias,
    description: fullDescription || `Card ${id}: ${title}`,
    labels
  };
}

async function createJiraIssue(accessToken: string, card: JiraCard): Promise<{ key: string; success: boolean; error?: string }> {
  const fields: Record<string, any> = {
    project: { key: JIRA_CONFIG.projectKey },
    summary: `[${card.id}] ${card.title}`,
    description: {
      type: 'doc',
      version: 1,
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              text: card.description
            }
          ]
        }
      ]
    },
    issuetype: { name: 'Task' },
    labels: card.labels
  };

  try {
    const response = await fetch(`${JIRA_CONFIG.apiBaseUrl}/rest/api/3/issue`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ fields })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { 
        key: '', 
        success: false, 
        error: errorData.errorMessages?.join(', ') || `HTTP ${response.status}` 
      };
    }

    const data = await response.json();
    return { key: data.key, success: true };
  } catch (error: any) {
    return { key: '', success: false, error: error.message };
  }
}

async function main() {
  console.log('Reading MVP cards file...');
  const filePath = path.join(__dirname, '..', 'docs', 'lia-mvp-cards-jira.md');
  const content = fs.readFileSync(filePath, 'utf-8');
  
  console.log('Parsing cards...');
  const cards = parseMarkdownCards(content);
  console.log(`Found ${cards.length} cards to create`);
  
  console.log('Getting Jira access token...');
  const accessToken = await getAccessToken();
  
  const results = {
    created: [] as string[],
    failed: [] as { id: string; error: string }[]
  };
  
  // Cards already created (skip these) - all 95 from previous runs
  const alreadyCreated = new Set([
    'AUTH-001', 'AUTH-002', 'AUTH-003', 'AUTH-004',
    'WIZ-001', 'WIZ-002', 'WIZ-003', 'WIZ-004', 'WIZ-005', 'WIZ-006', 'WIZ-007', 'WIZ-008',
    'MAP-001', 'MAP-002', 'MAP-003', 'MAP-004', 'MAP-005', 'MAP-006',
    'WSI-001', 'WSI-002', 'WSI-003', 'WSI-004', 'WSI-005',
    'TRI-001', 'TRI-002', 'TRI-003', 'TRI-004', 'TRI-005', 'TRI-006', 'TRI-007', 'TRI-008', 'TRI-009', 'TRI-010',
    'SCO-001', 'SCO-002', 'SCO-003', 'SCO-004', 'SCO-005', 'SCO-006', 'SCO-007', 'SCO-008',
    'GAT-001', 'GAT-002', 'GAT-003', 'GAT-004', 'GAT-005', 'GAT-006', 'GAT-007',
    'TPL-001', 'TPL-002', 'TPL-003', 'TPL-004', 'TPL-005', 'TPL-006', 'TPL-007',
    'AGE-001', 'AGE-002', 'AGE-003', 'AGE-004', 'AGE-005', 'AGE-006', 'AGE-007', 'AGE-008',
    'NOT-001', 'NOT-002', 'NOT-003', 'NOT-004', 'NOT-005', 'NOT-006',
    'KAN-001', 'KAN-002', 'KAN-003', 'KAN-004', 'KAN-005', 'KAN-006', 'KAN-007', 'KAN-008',
    'TAB-001', 'TAB-002', 'TAB-003', 'TAB-004', 'TAB-005',
    'PRV-001', 'PRV-002', 'PRV-003', 'PRV-004', 'PRV-005',
    'VAG-001', 'VAG-002', 'VAG-003', 'VAG-004', 'VAG-005', 'VAG-006', 'VAG-007', 'VAG-008'
  ]);
  
  const cardsToCreate = cards.filter(c => !alreadyCreated.has(c.id));
  console.log(`Skipping ${alreadyCreated.size} already created cards`);
  console.log(`Creating ${cardsToCreate.length} remaining cards...`);
  
  for (let i = 0; i < cardsToCreate.length; i++) {
    const card = cardsToCreate[i];
    console.log(`[${i + 1}/${cardsToCreate.length}] Creating ${card.id}...`);
    
    const result = await createJiraIssue(accessToken, card);
    
    if (result.success) {
      results.created.push(result.key);
      console.log(`  ✓ Created: ${result.key}`);
    } else {
      results.failed.push({ id: card.id, error: result.error || 'Unknown error' });
      console.log(`  ✗ Failed: ${result.error}`);
    }
    
    await new Promise(resolve => setTimeout(resolve, 300));
  }
  
  console.log('\n=== SUMMARY ===');
  console.log(`Created: ${results.created.length}`);
  console.log(`Failed: ${results.failed.length}`);
  
  if (results.failed.length > 0) {
    console.log('\nFailed cards:');
    results.failed.forEach(f => console.log(`  - ${f.id}: ${f.error}`));
  }
  
  fs.writeFileSync('jira-creation-results.json', JSON.stringify(results, null, 2));
  console.log('\nResults saved to jira-creation-results.json');
}

main().catch(console.error);
