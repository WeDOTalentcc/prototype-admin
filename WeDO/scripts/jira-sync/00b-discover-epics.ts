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
  const conn = (connData as any).items?.[0];
  const accessToken = conn?.settings?.access_token;
  const resourcesResponse = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: { 'Authorization': `Bearer ${accessToken}`, 'Accept': 'application/json' }
  });
  const resources = await resourcesResponse.json() as any[];
  const cloudId = resources[0].id;
  return { accessToken, cloudId, baseUrl: `https://api.atlassian.com/ex/jira/${cloudId}` };
}

async function main() {
  const auth = await getJiraAuth();

  // Search for epics
  const jql = 'project = WT AND summary ~ "EPIC" ORDER BY key ASC';
  const res = await fetch(`${auth.baseUrl}/rest/api/3/search?jql=${encodeURIComponent(jql)}&maxResults=100&fields=key,summary,issuetype,parent,status`, {
    headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
  });
  const data = await res.json() as any;
  console.log(`Total issues com EPIC no nome: ${data.total}`);
  data.issues?.forEach((i: any) => {
    console.log(`  ${i.key}: ${i.fields.summary} [type: ${i.fields.issuetype?.name}, status: ${i.fields.status?.name}]`);
  });

  // Also check boards using Agile API
  console.log('\n--- Boards ---');
  const boardRes = await fetch(`${auth.baseUrl}/rest/agile/1.0/board?projectKeyOrId=WT&maxResults=50`, {
    headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
  });
  const boardData = await boardRes.json() as any;
  console.log('Board response:', JSON.stringify(boardData, null, 2).substring(0, 1000));

  // Check issue types
  console.log('\n--- Issue Types ---');
  const typesRes = await fetch(`${auth.baseUrl}/rest/api/3/issuetype`, {
    headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
  });
  const types = await typesRes.json() as any[];
  types.forEach((t: any) => {
    console.log(`  ${t.id}: ${t.name} (subtask: ${t.subtask})`);
  });

  // Check SPRINT custom field (customfield_10135) - what values does it accept?
  console.log('\n--- SPRINT field (customfield_10135) on WT-963 ---');
  const cardRes = await fetch(`${auth.baseUrl}/rest/api/3/issue/WT-963?fields=customfield_10135,customfield_10020,customfield_10015,customfield_10016,customfield_10057`, {
    headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
  });
  const cardData = await cardRes.json() as any;
  console.log('customfield_10135 (SPRINT):', JSON.stringify(cardData.fields?.customfield_10135));
  console.log('customfield_10020 (Sprint agile):', JSON.stringify(cardData.fields?.customfield_10020));
  console.log('customfield_10015 (Start date):', JSON.stringify(cardData.fields?.customfield_10015));
  console.log('customfield_10016 (Story points):', JSON.stringify(cardData.fields?.customfield_10016));
  console.log('customfield_10057 (Story Points):', JSON.stringify(cardData.fields?.customfield_10057));
}

main().catch(console.error);
