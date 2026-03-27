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

  // Try fetching known epic key ranges (WT-1240 to WT-1270)
  const epicCandidates = [];
  for (let i = 1240; i <= 1270; i++) {
    try {
      const res = await fetch(`${auth.baseUrl}/rest/api/3/issue/WT-${i}?fields=key,summary,issuetype`, {
        headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json() as any;
        if (data.fields?.summary?.includes('EPIC') || data.fields?.issuetype?.name === 'Epic') {
          epicCandidates.push({ key: data.key, summary: data.fields.summary, type: data.fields.issuetype?.name });
          console.log(`✅ ${data.key}: ${data.fields.summary} [${data.fields.issuetype?.name}]`);
        }
      }
    } catch (e) {}
  }
  
  // Also check WT-893 parent chain
  const knownCards = ['WT-893', 'WT-897', 'WT-905', 'WT-911', 'WT-916', 'WT-927', 'WT-935', 'WT-942', 'WT-949', 'WT-957', 'WT-963', 'WT-971', 'WT-976', 'WT-981', 'WT-1121', 'WT-1126', 'WT-1131', 'WT-1132', 'WT-1135', 'WT-1136', 'WT-1137', 'WT-1138', 'WT-1228', 'WT-1230'];
  
  console.log('\n--- Parents of known cards ---');
  const epicMap: Record<string, { key: string, summary: string }> = {};
  for (const key of knownCards) {
    try {
      const res = await fetch(`${auth.baseUrl}/rest/api/3/issue/${key}?fields=parent,summary`, {
        headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json() as any;
        if (data.fields?.parent) {
          const parentKey = data.fields.parent.key;
          const parentSummary = data.fields.parent.fields?.summary;
          if (!epicMap[parentKey]) {
            epicMap[parentKey] = { key: parentKey, summary: parentSummary };
            console.log(`  ${key} (${data.fields.summary?.substring(0,40)}) → parent: ${parentKey}: ${parentSummary}`);
          }
        }
      }
    } catch (e) {}
  }

  console.log('\n=== EPIC MAP ===');
  console.log(JSON.stringify(epicMap, null, 2));
}

main().catch(console.error);
