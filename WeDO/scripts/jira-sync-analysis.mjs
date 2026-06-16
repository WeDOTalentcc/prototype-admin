import { readFileSync, writeFileSync } from 'fs';

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
    { headers: { 'Accept': 'application/json', 'X_REPLIT_TOKEN': xReplitToken } }
  ).then(r => r.json());
  const conn = data.items?.[0];
  return conn?.settings?.access_token || conn?.settings?.oauth?.credentials?.access_token;
}

async function jiraGet(path, token) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Authorization': `Bearer ${token}`, 'Accept': 'application/json' }
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`GET ${path} → ${res.status}: ${txt.substring(0, 300)}`);
  }
  return res.json();
}

async function fetchAllIssues(token, projectKey) {
  const all = [];
  let nextPageToken = null;
  const fields = ['summary','status','duedate','customfield_10015','issuetype','customfield_10014','sprint','labels','priority','customfield_10016','parent'];
  
  while (true) {
    const jql = `project = "${projectKey}" ORDER BY created ASC`;
    const body = { jql, maxResults: 100, fields };
    if (nextPageToken) body.nextPageToken = nextPageToken;
    
    const res = await fetch(`${BASE_URL}/search/jql`, {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`, 
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`POST /search/jql → ${res.status}: ${txt.substring(0, 300)}`);
    }
    const data = await res.json();
    const issues = data.issues || [];
    all.push(...issues);
    const total = data.total || all.length;
    console.log(`  Fetched ${all.length}/${total}`);
    
    nextPageToken = data.nextPageToken;
    if (!nextPageToken || issues.length === 0) break;
  }
  return all;
}

async function main() {
  const token = await getAccessToken();
  console.log('Fetching all WT issues...');
  
  const issues = await fetchAllIssues(token, 'WT');
  console.log(`\nTotal issues fetched: ${issues.length}`);
  
  const processed = issues.map(issue => {
    const f = issue.fields;
    
    let sprintName = null;
    const sprintField = f.sprint || f.customfield_10016;
    if (sprintField) {
      if (typeof sprintField === 'object' && sprintField.name) {
        sprintName = sprintField.name;
      } else if (typeof sprintField === 'string') {
        const m = sprintField.match(/name=([^,\]]+)/);
        if (m) sprintName = m[1];
      }
    }
    
    let epicKey = null;
    let epicName = null;
    if (f.parent) {
      epicKey = f.parent.key;
      if (f.parent.fields && f.parent.fields.summary) {
        epicName = f.parent.fields.summary;
      }
    }
    if (f.customfield_10014) {
      epicKey = f.customfield_10014;
    }
    
    let sprintFromLabels = null;
    if (f.labels && f.labels.length > 0) {
      const sprintLabel = f.labels.find(l => l.match(/semana-?\d/i) || l.match(/sprint-?\d/i));
      if (sprintLabel) sprintFromLabels = sprintLabel;
    }
    
    return {
      key: issue.key,
      summary: f.summary,
      status: f.status?.name,
      statusCategory: f.status?.statusCategory?.name,
      type: f.issuetype?.name,
      startDate: f.customfield_10015,
      dueDate: f.duedate,
      sprint: sprintName,
      sprintFromLabels,
      labels: f.labels || [],
      epicKey,
      epicName,
      priority: f.priority?.name,
    };
  });
  
  writeFileSync('/tmp/jira_all_issues.json', JSON.stringify(processed, null, 2));
  console.log(`\nSaved ${processed.length} issues to /tmp/jira_all_issues.json`);
  
  const types = {};
  const statuses = {};
  const epics = {};
  processed.forEach(i => {
    types[i.type] = (types[i.type] || 0) + 1;
    statuses[i.status] = (statuses[i.status] || 0) + 1;
    const ep = i.epicKey || i.epicName || 'NO_EPIC';
    epics[ep] = (epics[ep] || 0) + 1;
  });
  
  console.log('\nBy Type:', JSON.stringify(types));
  console.log('By Status:', JSON.stringify(statuses));
  console.log('\nBy Epic:');
  Object.entries(epics).sort((a,b) => b[1]-a[1]).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
  
  console.log('\nSample issues:');
  processed.slice(0, 5).forEach(i => {
    console.log(`  ${i.key}: "${i.summary}" | start=${i.startDate} due=${i.dueDate} | epic=${i.epicKey} | sprint=${i.sprint} | labels=${i.labels.join(',')}`);
  });
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
