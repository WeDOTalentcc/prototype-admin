import { writeFileSync } from 'fs';

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
    const text = await res.text();
    throw new Error(`GET ${path} → ${res.status}: ${text.substring(0, 300)}`);
  }
  return res.json();
}

async function fetchAllIssues(token, projectKey) {
  const all = [];
  let startAt = 0;
  while (true) {
    const jql = encodeURIComponent(`project="${projectKey}" ORDER BY key ASC`);
    const data = await jiraGet(
      `/search/jql?jql=${jql}&startAt=${startAt}&maxResults=100&fields=summary,status,issuetype,duedate,customfield_10015,labels,customfield_10020,customfield_10135,description,parent,priority,customfield_10014`,
      token
    );
    all.push(...(data.issues || []));
    const total = data.total || 0;
    console.log(`  ${projectKey}: fetched ${all.length}/${total}`);
    if (all.length >= total || (data.issues || []).length === 0) break;
    startAt += 100;
  }
  return all;
}

function extractTextFromADF(node) {
  if (!node) return '';
  if (typeof node === 'string') return node;
  if (node.type === 'text') return node.text || '';
  if (node.content) return node.content.map(extractTextFromADF).join('');
  return '';
}

async function main() {
  const token = await getAccessToken();
  console.log("Fetching all issues with full details...\n");

  const wtIssues = await fetchAllIssues(token, 'WT');
  const cwafIssues = await fetchAllIssues(token, 'CWAF');

  console.log("\nFetching epics...");
  let epics = {};
  try {
    const jql = encodeURIComponent(`issuetype = Epic ORDER BY key ASC`);
    const epicData = await jiraGet(`/search/jql?jql=${jql}&maxResults=200&fields=summary,key`, token);
    for (const e of (epicData.issues || [])) {
      epics[e.id] = { key: e.key, name: e.fields?.summary || '' };
    }
    console.log(`  Found ${Object.keys(epics).length} epics`);
  } catch (e) {
    console.log(`  Epic fetch error: ${e.message.substring(0, 100)}`);
  }

  const allIssues = [...wtIssues, ...cwafIssues];
  const result = [];

  for (const issue of allIssues) {
    const f = issue.fields || {};
    
    const sprint10020 = f.customfield_10020;
    const sprint10135 = f.customfield_10135;
    let sprintInfo = null;
    const sprintField = sprint10020 || sprint10135;
    if (Array.isArray(sprintField) && sprintField.length > 0) {
      const s = sprintField[sprintField.length - 1];
      sprintInfo = {
        name: s.name || s,
        state: s.state || null,
        id: s.id || null,
      };
    }

    let epicKey = null;
    let epicName = null;
    if (f.parent) {
      epicKey = f.parent.key || null;
      epicName = f.parent.fields?.summary || null;
    }
    if (f.customfield_10014) {
      const epicId = f.customfield_10014;
      if (epics[epicId]) {
        epicKey = epics[epicId].key;
        epicName = epics[epicId].name;
      } else {
        epicKey = epicId;
      }
    }

    let descText = '';
    if (f.description) {
      descText = extractTextFromADF(f.description).substring(0, 500);
    }

    result.push({
      key: issue.key,
      summary: f.summary || '',
      status: f.status?.name || '',
      type: f.issuetype?.name || '',
      priority: f.priority?.name || '',
      startDate: f.customfield_10015 || null,
      dueDate: f.duedate || null,
      labels: f.labels || [],
      sprint: sprintInfo,
      epicKey,
      epicName,
      description: descText,
    });
  }

  writeFileSync('/tmp/jira_full_details.json', JSON.stringify(result, null, 2));
  console.log(`\nSaved ${result.length} issues to /tmp/jira_full_details.json`);

  for (const r of result) {
    const labels = r.labels.length > 0 ? r.labels.join(',') : '-';
    const sprint = r.sprint ? r.sprint.name : '-';
    const epic = r.epicName ? `${r.epicKey}:${r.epicName.substring(0, 30)}` : '-';
    const start = r.startDate || '-';
    const due = r.dueDate || '-';
    console.log(`${r.key.padEnd(10)} | ${r.summary.substring(0, 55).padEnd(55)} | Labels: ${labels.substring(0, 30).padEnd(30)} | Sprint: ${sprint.substring(0, 20).padEnd(20)} | Epic: ${epic.substring(0, 35).padEnd(35)} | ${start} → ${due}`);
  }
}

main().catch(console.error);
