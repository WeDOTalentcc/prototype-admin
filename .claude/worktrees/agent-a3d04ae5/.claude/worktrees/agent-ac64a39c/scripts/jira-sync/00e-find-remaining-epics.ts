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

  // Check parents of AUTH and WIZ cards
  const checkCards = [
    'WT-893', // AUTH-001
    'WT-897', // WIZ-001
    'WT-971', // TAB-001
    'WT-976', // PRV-001
    'WT-981', // VAG-001
    'WT-1121', // JD-001
    'WT-1125', // WIZ-011
    'WT-1126', // CFG-001
    'WT-1131', // IMP-001
    'WT-1132', // AGT-001
    'WT-1135', // TRI-011
    'WT-1136', // DAT-001
    'WT-1137', // ENT-001
    'WT-1138', // KAN-009
    'WT-1229', // KAN-010
    'WT-1233', // INT-MSG-001
    'WT-1228', // INT-MSG-005
  ];
  
  const epicMap: Record<string, { key: string, summary: string }> = {};
  
  for (const key of checkCards) {
    try {
      const res = await fetch(`${auth.baseUrl}/rest/api/3/issue/${key}?fields=parent,summary`, {
        headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json() as any;
        const parentKey = data.fields?.parent?.key;
        const parentSummary = data.fields?.parent?.fields?.summary;
        if (parentKey && !epicMap[parentKey]) {
          epicMap[parentKey] = { key: parentKey, summary: parentSummary };
        }
        console.log(`${key} (${data.fields?.summary?.substring(0,50)}) → ${parentKey || 'NO PARENT'}: ${parentSummary || ''}`);
      }
    } catch (e) {}
  }

  // Also scan range WT-1250 to WT-1290 for more epics
  console.log('\n--- Scanning WT-1270 to WT-1300 for epics ---');
  for (let i = 1265; i <= 1300; i++) {
    try {
      const res = await fetch(`${auth.baseUrl}/rest/api/3/issue/WT-${i}?fields=summary,issuetype`, {
        headers: { 'Authorization': `Bearer ${auth.accessToken}`, 'Accept': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json() as any;
        if (data.fields?.issuetype?.name === 'Epic') {
          console.log(`  ✅ WT-${i}: ${data.fields.summary} [Epic]`);
          epicMap[`WT-${i}`] = { key: `WT-${i}`, summary: data.fields.summary };
        }
      }
    } catch (e) {}
  }

  console.log('\n=== COMPLETE EPIC MAP ===');
  console.log(JSON.stringify(epicMap, null, 2));
}

main().catch(console.error);
