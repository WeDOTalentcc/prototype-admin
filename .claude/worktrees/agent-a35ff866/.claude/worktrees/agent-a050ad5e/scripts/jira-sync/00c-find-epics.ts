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

  // Try multiple JQL queries to find epic-like issues
  const queries = [
    'project = WT AND summary ~ "EPIC-" ORDER BY key ASC',
    'project = WT AND issuetype = Epic ORDER BY key ASC',
    'project = WT AND key >= WT-1240 AND key <= WT-1270 ORDER BY key ASC',
  ];

  for (const jql of queries) {
    console.log(`\n--- JQL: ${jql} ---`);
    const res = await fetch(`${auth.baseUrl}/rest/api/3/search`, {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${auth.accessToken}`, 
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        jql,
        maxResults: 50,
        fields: ['key', 'summary', 'issuetype', 'status', 'parent']
      })
    });
    const data = await res.json() as any;
    console.log(`Total: ${data.total}`);
    data.issues?.forEach((i: any) => {
      const parent = i.fields.parent ? `parent: ${i.fields.parent.key}` : 'no parent';
      console.log(`  ${i.key}: ${i.fields.summary} [${i.fields.issuetype?.name}] [${parent}]`);
    });
  }

  // Also get the parent of WT-963 to understand the epic structure
  console.log('\n--- Parent chain of WT-963 ---');
  const parentRes = await fetch(`${auth.baseUrl}/rest/api/3/issue/WT-1256?fields=key,summary,issuetype,parent,status`, {
    headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
  });
  const parentData = await parentRes.json() as any;
  console.log(`WT-1256: ${parentData.fields?.summary} [${parentData.fields?.issuetype?.name}]`);
  if (parentData.fields?.parent) {
    console.log(`  parent: ${parentData.fields.parent.key} - ${parentData.fields.parent.fields?.summary}`);
  }

  // Get all issues with parent that has EPIC in name
  console.log('\n--- Issues that are EPIC parents (range WT-1240 to WT-1280) ---');
  const rangeRes = await fetch(`${auth.baseUrl}/rest/api/3/search`, {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${auth.accessToken}`, 
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      jql: 'project = WT AND summary ~ "EPIC" ORDER BY key ASC',
      maxResults: 50,
      fields: ['key', 'summary', 'issuetype', 'status']
    })
  });
  const rangeData = await rangeRes.json() as any;
  console.log(`Total: ${rangeData.total}`);
  rangeData.issues?.forEach((i: any) => {
    console.log(`  ${i.key}: ${i.fields.summary} [${i.fields.issuetype?.name}] [${i.fields.status?.name}]`);
  });
}

main().catch(console.error);
