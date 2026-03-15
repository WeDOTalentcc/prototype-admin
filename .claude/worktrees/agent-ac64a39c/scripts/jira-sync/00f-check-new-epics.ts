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
  
  // Scan WT-1287 to WT-1310 for the newly created epics
  for (let i = 1287; i <= 1310; i++) {
    try {
      const res = await fetch(`${auth.baseUrl}/rest/api/3/issue/WT-${i}?fields=summary,issuetype,status`, {
        headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json() as any;
        console.log(`WT-${i}: ${data.fields?.summary} [${data.fields?.issuetype?.name}] [${data.fields?.status?.name}]`);
      }
    } catch (e) {}
  }
}

main().catch(console.error);
