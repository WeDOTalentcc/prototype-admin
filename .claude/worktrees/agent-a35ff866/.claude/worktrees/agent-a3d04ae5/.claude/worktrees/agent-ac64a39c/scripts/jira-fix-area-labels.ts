interface JiraAuth {
  accessToken: string;
  cloudId: string;
  baseUrl: string;
}

async function getJiraAuth(): Promise<JiraAuth> {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken || !hostname) {
    throw new Error('Variáveis de ambiente Replit não encontradas');
  }

  const connResponse = await fetch(
    `https://${hostname}/api/v2/connection?include_secrets=true&connector_names=jira`,
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  );

  const connData = await connResponse.json();
  const conn = connData.items?.[0];
  const accessToken = conn?.settings?.access_token;

  if (!accessToken) {
    throw new Error('Token Jira não encontrado');
  }

  const resourcesResponse = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json'
    }
  });

  if (!resourcesResponse.ok) {
    throw new Error('Erro ao obter recursos Atlassian');
  }

  const resources = await resourcesResponse.json() as any[];
  if (resources.length === 0) {
    throw new Error('Nenhum site Jira encontrado');
  }

  const cloudId = resources[0].id;
  const baseUrl = `https://api.atlassian.com/ex/jira/${cloudId}`;

  return { accessToken, cloudId, baseUrl };
}

async function addLabelsToIssue(auth: JiraAuth, jiraKey: string, labelsToAdd: string[]): Promise<boolean> {
  const getResponse = await fetch(`${auth.baseUrl}/rest/api/3/issue/${jiraKey}?fields=labels`, {
    headers: {
      'Authorization': `Bearer ${auth.accessToken}`,
      'Accept': 'application/json'
    }
  });

  if (!getResponse.ok) {
    console.error(`   Erro ao ler ${jiraKey}: ${getResponse.status}`);
    return false;
  }

  const issueData = await getResponse.json() as any;
  const currentLabels: string[] = issueData.fields?.labels || [];
  const mergedLabels = [...new Set([...currentLabels, ...labelsToAdd])];

  const updateResponse = await fetch(`${auth.baseUrl}/rest/api/3/issue/${jiraKey}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${auth.accessToken}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      fields: { labels: mergedLabels }
    })
  });

  if (!updateResponse.ok) {
    const errorText = await updateResponse.text();
    console.error(`   Erro ao atualizar labels ${jiraKey}: ${updateResponse.status} - ${errorText.substring(0, 200)}`);
    return false;
  }

  return true;
}

async function main() {
  console.log('🏷️  Corrigindo labels de área nos cards do Épico 3\n');

  const auth = await getJiraAuth();
  console.log(`✅ Autenticação OK\n`);

  const updates: { key: string; code: string; areaLabel: string }[] = [
    { key: 'WT-906', code: 'MAP-002', areaLabel: 'area-backend' },
    { key: 'WT-907', code: 'MAP-003', areaLabel: 'area-fullstack' },
    { key: 'WT-1280', code: 'MAP-007', areaLabel: 'area-backend' },
    { key: 'WT-1281', code: 'MAP-008', areaLabel: 'area-frontend' },
    { key: 'WT-1282', code: 'MAP-009', areaLabel: 'area-backend' },
    { key: 'WT-1283', code: 'MAP-010', areaLabel: 'area-backend' },
    { key: 'WT-1284', code: 'MAP-011', areaLabel: 'area-backend' },
    { key: 'WT-1285', code: 'MAP-012', areaLabel: 'area-frontend' },
    { key: 'WT-1286', code: 'MAP-013', areaLabel: 'area-frontend' },
  ];

  for (const update of updates) {
    console.log(`🏷️  ${update.key} (${update.code}): adicionando ${update.areaLabel}...`);
    const success = await addLabelsToIssue(auth, update.key, [update.areaLabel]);
    if (success) {
      console.log(`   ✅ OK`);
    } else {
      console.log(`   ❌ Falhou`);
    }
    await new Promise(resolve => setTimeout(resolve, 300));
  }

  console.log('\n✅ Labels de área corrigidas!');
}

main().catch(console.error);
