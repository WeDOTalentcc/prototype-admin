import * as fs from 'fs';

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
  const conn = (connData as any).items?.[0];
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

  const resources = await resourcesResponse.json() as any[];
  const cloudId = resources[0].id;
  const baseUrl = `https://api.atlassian.com/ex/jira/${cloudId}`;

  return { accessToken, cloudId, baseUrl };
}

async function main() {
  const auth = await getJiraAuth();
  console.log('✅ Auth OK, cloudId:', auth.cloudId);

  // 1. Get all fields to find Sprint and Start Date
  console.log('\n📋 Buscando campos do projeto...');
  const fieldsRes = await fetch(`${auth.baseUrl}/rest/api/3/field`, {
    headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
  });
  const fields = await fieldsRes.json() as any[];
  
  const interestingFields = fields.filter((f: any) => {
    const name = (f.name || '').toLowerCase();
    return name.includes('sprint') || name.includes('start') || name.includes('story point') || 
           name.includes('pontos') || name.includes('team') || name.includes('epic');
  });
  
  console.log('\n🔍 Campos relevantes encontrados:');
  interestingFields.forEach((f: any) => {
    console.log(`  - ${f.id}: ${f.name} (${f.schema?.type || 'N/A'}, custom: ${f.schema?.custom || 'N/A'})`);
  });

  // 2. Get all boards to find sprint IDs
  console.log('\n📋 Buscando boards...');
  const boardsRes = await fetch(`${auth.baseUrl}/rest/agile/1.0/board?projectKeyOrId=WT`, {
    headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
  });
  const boardsData = await boardsRes.json() as any;
  console.log('Boards:', JSON.stringify(boardsData.values?.map((b: any) => ({ id: b.id, name: b.name })), null, 2));

  // 3. Get sprints from each board
  if (boardsData.values?.length > 0) {
    for (const board of boardsData.values) {
      console.log(`\n📋 Sprints do board ${board.name} (${board.id}):`);
      const sprintsRes = await fetch(`${auth.baseUrl}/rest/agile/1.0/board/${board.id}/sprint?state=active,future`, {
        headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
      });
      const sprintsData = await sprintsRes.json() as any;
      console.log(JSON.stringify(sprintsData.values?.map((s: any) => ({ id: s.id, name: s.name, state: s.state, startDate: s.startDate, endDate: s.endDate })), null, 2));
    }
  }

  // 4. Get existing epics
  console.log('\n📋 Buscando Epics existentes...');
  const epicsRes = await fetch(`${auth.baseUrl}/rest/api/3/search?jql=${encodeURIComponent('project = WT AND issuetype = Epic ORDER BY key ASC')}&maxResults=50&fields=key,summary,status`, {
    headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
  });
  const epicsData = await epicsRes.json() as any;
  console.log('Total epics:', epicsData.total);
  const epicMap: Record<string, string> = {};
  epicsData.issues?.forEach((e: any) => {
    console.log(`  ${e.key}: ${e.fields.summary}`);
    epicMap[e.fields.summary] = e.key;
  });

  // 5. Check a sample existing card to see all fields
  console.log('\n📋 Campos de um card existente (WT-963 = KAN-001)...');
  const sampleRes = await fetch(`${auth.baseUrl}/rest/api/3/issue/WT-963`, {
    headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
  });
  const sampleData = await sampleRes.json() as any;
  const fieldKeys = Object.keys(sampleData.fields || {});
  const sampleFields: Record<string, any> = {};
  for (const key of fieldKeys) {
    const val = sampleData.fields[key];
    if (val !== null && val !== undefined && val !== '' && !(Array.isArray(val) && val.length === 0)) {
      sampleFields[key] = val;
    }
  }
  
  console.log('\nCampos preenchidos:');
  for (const [key, val] of Object.entries(sampleFields)) {
    const field = fields.find((f: any) => f.id === key);
    const name = field?.name || key;
    if (typeof val === 'object' && val !== null) {
      console.log(`  ${key} (${name}): ${JSON.stringify(val).substring(0, 200)}`);
    } else {
      console.log(`  ${key} (${name}): ${val}`);
    }
  }

  // Save discovery results
  const results = {
    relevantFields: interestingFields.map((f: any) => ({ id: f.id, name: f.name, type: f.schema?.type, custom: f.schema?.custom })),
    boards: boardsData.values?.map((b: any) => ({ id: b.id, name: b.name })),
    epics: epicsData.issues?.map((e: any) => ({ key: e.key, summary: e.fields.summary })),
    sampleCardFields: Object.entries(sampleFields).map(([key, val]) => {
      const field = fields.find((f: any) => f.id === key);
      return { id: key, name: field?.name || key, value: typeof val === 'object' ? JSON.stringify(val).substring(0, 300) : val };
    })
  };

  fs.writeFileSync('scripts/jira-sync/discovery-results.json', JSON.stringify(results, null, 2));
  console.log('\n✅ Resultados salvos em scripts/jira-sync/discovery-results.json');
}

main().catch(console.error);
