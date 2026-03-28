const CLOUD_ID = '8cf762f8-6a44-47de-8915-6b3dc0cd2715';
const BASE_URL = `https://api.atlassian.com/ex/jira/${CLOUD_ID}/rest/api/3`;

async function getAccessToken() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  const data = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=jira',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  ).then(res => res.json());
  
  const conn = data.items?.[0];
  return conn?.settings?.access_token || conn?.settings?.oauth?.credentials?.access_token;
}

async function jiraGet(path, token) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json'
    }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Jira API ${res.status}: ${text.substring(0, 200)}`);
  }
  return res.json();
}

async function main() {
  const token = await getAccessToken();
  console.log("=== JIRA CONNECTION OK ===\n");
  
  const projects = await jiraGet('/project/search?maxResults=50', token);
  console.log("Projects:", projects.values?.length);
  for (const p of (projects.values || [])) {
    console.log(`  - ${p.key}: ${p.name}`);
  }
  
  for (const p of (projects.values || [])) {
    console.log(`\n=== PROJECT: ${p.key} ===`);
    const jql = encodeURIComponent(`project="${p.key}" ORDER BY created ASC`);
    const issues = await jiraGet(`/search/jql?jql=${jql}&maxResults=5&fields=summary,status,issuetype,duedate,customfield_10015`, token);
    console.log(`Total issues: ${issues.total}`);
    for (const issue of (issues.issues || [])) {
      console.log(`  ${issue.key}: ${issue.fields?.summary}`);
      console.log(`    Type: ${issue.fields?.issuetype?.name}, Status: ${issue.fields?.status?.name}`);
      console.log(`    Due: ${issue.fields?.duedate}, Start: ${issue.fields?.customfield_10015 || 'N/A'}`);
    }
  }
  
  console.log("\n=== DATE/SPRINT FIELDS ===");
  const fields = await jiraGet('/field', token);
  const relevant = fields.filter(f => 
    f.name?.toLowerCase().includes('date') || 
    f.name?.toLowerCase().includes('start') || 
    f.name?.toLowerCase().includes('due') ||
    f.name?.toLowerCase().includes('sprint') ||
    f.name?.toLowerCase().includes('inicio') ||
    f.name?.toLowerCase().includes('target') ||
    f.name?.toLowerCase().includes('end')
  );
  for (const f of relevant) {
    console.log(`  ${f.id}: "${f.name}" (type: ${f.schema?.type || 'N/A'})`);
  }
}

main().catch(console.error);
