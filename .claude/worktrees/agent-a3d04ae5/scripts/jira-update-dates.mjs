import { readFileSync } from 'fs';

const CLOUD_ID = '8cf762f8-6a44-47de-8915-6b3dc0cd2715';
const BASE_URL = `https://api.atlassian.com/ex/jira/${CLOUD_ID}/rest/api/3`;

const DATE_MAP = {
  '1': { start: '2026-02-09', end: '2026-02-13' },
  '2': { start: '2026-02-16', end: '2026-02-20' },
  '3': { start: '2026-02-23', end: '2026-02-27' },
};

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
      headers: { 'Accept': 'application/json', 'X_REPLIT_TOKEN': xReplitToken }
    }
  ).then(res => res.json());
  
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

async function jiraPut(path, token, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PUT ${path} → ${res.status}: ${text.substring(0, 300)}`);
  }
  return res.status === 204 ? null : res.json();
}

async function fetchAllIssues(token, projectKey) {
  const allIssues = [];
  let startAt = 0;
  const maxResults = 100;
  
  while (true) {
    const jql = encodeURIComponent(`project="${projectKey}" ORDER BY created ASC`);
    const data = await jiraGet(
      `/search/jql?jql=${jql}&startAt=${startAt}&maxResults=${maxResults}&fields=summary,status,duedate,customfield_10015`,
      token
    );
    
    const issues = data.issues || [];
    allIssues.push(...issues);
    
    const total = data.total || allIssues.length;
    console.log(`  Fetched ${allIssues.length}/${total} issues from ${projectKey}...`);
    
    if (allIssues.length >= total || issues.length === 0) break;
    startAt += maxResults;
  }
  
  return allIssues;
}

function loadWeekMapping() {
  const raw = readFileSync('/tmp/week_mapping.json', 'utf-8');
  return JSON.parse(raw);
}

function extractCardCode(summary) {
  const match = summary.match(/\[([A-Z]+-(?:[A-Z]+-)?[\d]+)\]/);
  return match ? match[1] : null;
}

async function main() {
  const token = await getAccessToken();
  console.log("=== JIRA DATE UPDATE SCRIPT ===\n");

  const weekMapping = loadWeekMapping();
  console.log(`Loaded ${Object.keys(weekMapping).length} cards from week mapping\n`);

  console.log("Step 1: Fetching all issues from Jira...");
  const wtIssues = await fetchAllIssues(token, 'WT');
  const cwafIssues = await fetchAllIssues(token, 'CWAF');
  const allIssues = [...wtIssues, ...cwafIssues];
  console.log(`\nTotal Jira issues: ${allIssues.length}\n`);

  console.log("Step 2: Mapping card codes to Jira issues...");
  const issueMap = {};
  const unmappedIssues = [];
  
  for (const issue of allIssues) {
    const summary = issue.fields?.summary || '';
    const cardCode = extractCardCode(summary);
    if (cardCode) {
      issueMap[cardCode] = {
        key: issue.key,
        summary: summary,
        currentStart: issue.fields?.customfield_10015,
        currentDue: issue.fields?.duedate
      };
    } else {
      unmappedIssues.push(`${issue.key}: ${summary}`);
    }
  }

  console.log(`  Mapped: ${Object.keys(issueMap).length} issues`);
  console.log(`  Unmapped: ${unmappedIssues.length} issues`);

  console.log("\nStep 3: Cross-referencing with week mapping...");
  const toUpdate = [];
  const notFound = [];
  const alreadyCorrect = [];
  
  for (const [cardCode, [week, , ]] of Object.entries(weekMapping)) {
    const dates = DATE_MAP[week];
    if (!dates) {
      console.log(`  ⚠️ No dates for week ${week} (card ${cardCode})`);
      continue;
    }
    
    const jiraIssue = issueMap[cardCode];
    if (!jiraIssue) {
      notFound.push(cardCode);
      continue;
    }
    
    if (jiraIssue.currentStart === dates.start && jiraIssue.currentDue === dates.end) {
      alreadyCorrect.push(cardCode);
      continue;
    }
    
    toUpdate.push({
      cardCode,
      issueKey: jiraIssue.key,
      summary: jiraIssue.summary,
      startDate: dates.start,
      dueDate: dates.end,
      week
    });
  }

  console.log(`\n  To update: ${toUpdate.length}`);
  console.log(`  Already correct: ${alreadyCorrect.length}`);
  console.log(`  Not found in Jira: ${notFound.length}`);
  
  if (notFound.length > 0) {
    console.log(`\n  Cards NOT found in Jira:`);
    for (const c of notFound.sort()) {
      console.log(`    - ${c}`);
    }
  }

  if (toUpdate.length === 0) {
    console.log("\n✅ Nothing to update - all dates are already correct!");
    return;
  }

  console.log(`\nStep 4: Updating ${toUpdate.length} issues in Jira...`);
  let success = 0;
  let errors = 0;
  
  for (let i = 0; i < toUpdate.length; i++) {
    const item = toUpdate[i];
    try {
      await jiraPut(`/issue/${item.issueKey}`, token, {
        fields: {
          customfield_10015: item.startDate,
          duedate: item.dueDate
        }
      });
      success++;
      if ((i + 1) % 10 === 0 || i === toUpdate.length - 1) {
        console.log(`  Progress: ${i + 1}/${toUpdate.length} (${success} ok, ${errors} err)`);
      }
    } catch (err) {
      errors++;
      console.log(`  ❌ ${item.issueKey} (${item.cardCode}): ${err.message.substring(0, 150)}`);
    }
    
    if ((i + 1) % 5 === 0) {
      await new Promise(r => setTimeout(r, 200));
    }
  }

  console.log(`\n=== RESULTS ===`);
  console.log(`  ✅ Updated: ${success}`);
  console.log(`  ❌ Errors: ${errors}`);
  console.log(`  ⏭️ Already correct: ${alreadyCorrect.length}`);
  console.log(`  ⚠️ Not in Jira: ${notFound.length}`);
  console.log(`  📊 Total cards in mapping: ${Object.keys(weekMapping).length}`);
}

main().catch(console.error);
