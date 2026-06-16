import * as fs from 'fs';

interface CardMapping {
  code: string;
  titulo: string;
  area: string;
}

interface JiraResult {
  jiraKey: string;
  docCode: string;
  status: string;
}

async function getJiraAuth() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  const connResponse = await fetch(
    `https://${hostname}/api/v2/connection?include_secrets=true&connector_names=jira`,
    { headers: { 'Accept': 'application/json', 'X_REPLIT_TOKEN': xReplitToken! } }
  );
  const connData = await connResponse.json();
  const conn = connData.items?.[0];
  const accessToken = conn?.settings?.access_token;

  const resourcesResponse = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: { 'Authorization': `Bearer ${accessToken}`, 'Accept': 'application/json' }
  });
  const resources = await resourcesResponse.json();
  const cloudId = resources[0].id;
  
  return { accessToken, baseUrl: `https://api.atlassian.com/ex/jira/${cloudId}` };
}

async function addLabelToIssue(auth: any, issueKey: string, label: string): Promise<boolean> {
  const resp = await fetch(`${auth.baseUrl}/rest/api/3/issue/${issueKey}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${auth.accessToken}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      update: {
        labels: [{ add: label }]
      }
    })
  });
  
  return resp.ok;
}

async function main() {
  console.log('🏷️  ADICIONANDO LABELS DE ÁREA NOS 153 CARDS MVP\n');
  
  // Carregar mapeamentos
  const areaMapping: CardMapping[] = JSON.parse(fs.readFileSync('/tmp/cards-area-final.json', 'utf-8'));
  
  // Carregar mapeamento código -> jiraKey
  const updateResults: JiraResult[] = JSON.parse(fs.readFileSync('scripts/jira-update-result.json', 'utf-8')).results;
  const createResults: JiraResult[] = JSON.parse(fs.readFileSync('scripts/jira-create-result.json', 'utf-8')).results;
  
  const codeToJiraKey = new Map<string, string>();
  [...updateResults, ...createResults]
    .filter(r => r.status === 'success')
    .forEach(r => codeToJiraKey.set(r.docCode, r.jiraKey));
  
  console.log(`📋 Cards mapeados: ${codeToJiraKey.size}`);
  console.log(`📋 Áreas mapeadas: ${areaMapping.length}\n`);
  
  const auth = await getJiraAuth();
  
  let success = 0;
  let errors = 0;
  let notFound = 0;
  
  // Processar em batches
  const batchSize = 10;
  for (let i = 0; i < areaMapping.length; i += batchSize) {
    const batch = areaMapping.slice(i, Math.min(i + batchSize, areaMapping.length));
    
    const promises = batch.map(async (card) => {
      const jiraKey = codeToJiraKey.get(card.code);
      if (!jiraKey) {
        notFound++;
        return { code: card.code, status: 'not_found' };
      }
      
      const ok = await addLabelToIssue(auth, jiraKey, card.area);
      if (ok) {
        success++;
        return { code: card.code, jiraKey, area: card.area, status: 'success' };
      } else {
        errors++;
        return { code: card.code, jiraKey, status: 'error' };
      }
    });
    
    await Promise.all(promises);
    
    // Progresso
    const processed = Math.min(i + batchSize, areaMapping.length);
    console.log(`Processados: ${processed}/${areaMapping.length} | ✅ ${success} | ❌ ${errors} | ⚠️ ${notFound}`);
    
    // Rate limit
    await new Promise(r => setTimeout(r, 300));
  }
  
  console.log('\n═══════════════════════════════════════════════════');
  console.log('                    RESULTADO                       ');
  console.log('═══════════════════════════════════════════════════');
  console.log(`✅ Sucesso: ${success}`);
  console.log(`❌ Erros: ${errors}`);
  console.log(`⚠️ Não encontrados: ${notFound}`);
  console.log('═══════════════════════════════════════════════════');
}

main().catch(console.error);
