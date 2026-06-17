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
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}: ${(await res.text()).substring(0, 200)}`);
  return res.json();
}

async function fetchAllIssues(token, projectKey) {
  const all = [];
  let startAt = 0;
  while (true) {
    const jql = encodeURIComponent(`project="${projectKey}" ORDER BY key ASC`);
    const data = await jiraGet(`/search/jql?jql=${jql}&startAt=${startAt}&maxResults=100&fields=summary,status,duedate,customfield_10015,issuetype`, token);
    all.push(...(data.issues || []));
    const total = data.total || 0;
    console.log(`  ${projectKey}: fetched ${all.length}/${total}`);
    if (all.length >= total || (data.issues || []).length === 0) break;
    startAt += 100;
  }
  return all;
}

function normalize(str) {
  return str.toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

async function main() {
  const token = await getAccessToken();
  console.log("=== FULL JIRA ANALYSIS ===\n");

  console.log("Step 1: Fetching ALL Jira issues...");
  const wtIssues = await fetchAllIssues(token, 'WT');
  const cwafIssues = await fetchAllIssues(token, 'CWAF');
  const allJira = [...wtIssues, ...cwafIssues];
  console.log(`\nTotal Jira issues: ${allJira.length} (WT: ${wtIssues.length}, CWAF: ${cwafIssues.length})\n`);

  const jiraList = allJira.map(issue => ({
    key: issue.key,
    summary: issue.fields?.summary || '',
    status: issue.fields?.status?.name || '',
    type: issue.fields?.issuetype?.name || '',
    startDate: issue.fields?.customfield_10015 || null,
    dueDate: issue.fields?.duedate || null,
  }));

  writeFileSync('/tmp/jira_all_issues.json', JSON.stringify(jiraList, null, 2));

  console.log("Step 2: Loading document cards...");
  const docCards = JSON.parse(readFileSync('/tmp/doc_cards.json', 'utf-8'));
  console.log(`Document cards: ${docCards.length}\n`);

  console.log("Step 3: Matching...\n");

  const mapping = [];
  const unmatchedDoc = [];
  const usedJiraKeys = new Set();

  for (const card of docCards) {
    let match = null;
    let matchMethod = '';

    // Method 1: Exact code match in summary [CODE]
    for (const j of jiraList) {
      if (usedJiraKeys.has(j.key)) continue;
      const codePattern = new RegExp(`\\[${card.code.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]`, 'i');
      if (codePattern.test(j.summary)) {
        match = j;
        matchMethod = 'exact_code';
        break;
      }
    }

    // Method 2: Code without brackets at start of summary
    if (!match) {
      for (const j of jiraList) {
        if (usedJiraKeys.has(j.key)) continue;
        if (j.summary.startsWith(card.code + ':') || j.summary.startsWith(card.code + ' ')) {
          match = j;
          matchMethod = 'code_prefix';
          break;
        }
      }
    }

    // Method 3: Title similarity match (normalized)
    if (!match) {
      const docTitleNorm = normalize(card.title_yaml || card.title_header);
      const docWords = docTitleNorm.split(' ').filter(w => w.length > 3);
      
      let bestScore = 0;
      let bestMatch = null;
      
      for (const j of jiraList) {
        if (usedJiraKeys.has(j.key)) continue;
        const jiraNorm = normalize(j.summary);
        
        // Count matching words
        let matchingWords = 0;
        for (const word of docWords) {
          if (jiraNorm.includes(word)) matchingWords++;
        }
        
        const score = docWords.length > 0 ? matchingWords / docWords.length : 0;
        
        if (score > bestScore && score >= 0.6) {
          bestScore = score;
          bestMatch = j;
        }
      }
      
      if (bestMatch) {
        match = bestMatch;
        matchMethod = `title_similarity(${Math.round(bestScore * 100)}%)`;
      }
    }

    if (match) {
      usedJiraKeys.add(match.key);
      mapping.push({
        docCode: card.code,
        docTitle: card.title_yaml || card.title_header,
        jiraKey: match.key,
        jiraSummary: match.summary,
        matchMethod,
        sprint: card.sprint,
        removed: card.removed,
        postmvp: card.postmvp,
        docStart: card.start,
        docEnd: card.end,
        jiraStart: match.startDate,
        jiraDue: match.dueDate,
      });
    } else {
      unmatchedDoc.push(card);
    }
  }

  const unmatchedJira = jiraList.filter(j => !usedJiraKeys.has(j.key));

  console.log("=== MATCHING RESULTS ===");
  console.log(`  Matched: ${mapping.length}`);
  console.log(`  Unmatched doc cards: ${unmatchedDoc.length}`);
  console.log(`  Unmatched Jira issues: ${unmatchedJira.length}`);

  console.log("\n=== ALL MATCHES ===");
  for (const m of mapping) {
    const status = m.removed ? '❌REM' : (m.postmvp ? '⏸️POST' : `S${m.sprint}`);
    const dateOk = m.docStart === m.jiraStart && m.docEnd === m.jiraDue;
    console.log(`  ${status.padEnd(6)} ${m.docCode.padEnd(15)} → ${m.jiraKey.padEnd(8)} | ${dateOk ? '✅' : '❌'} dates | ${m.matchMethod}`);
    if (!dateOk) {
      console.log(`         Doc: ${m.docStart} → ${m.docEnd} | Jira: ${m.jiraStart || 'null'} → ${m.jiraDue || 'null'}`);
    }
  }

  if (unmatchedDoc.length > 0) {
    console.log("\n=== UNMATCHED DOCUMENT CARDS ===");
    for (const c of unmatchedDoc) {
      const status = c.removed ? '❌REM' : (c.postmvp ? '⏸️POST' : `S${c.sprint}`);
      console.log(`  ${status.padEnd(6)} ${c.code.padEnd(15)} | ${(c.title_yaml || c.title_header).substring(0, 70)}`);
    }
  }

  if (unmatchedJira.length > 0) {
    console.log("\n=== UNMATCHED JIRA ISSUES ===");
    for (const j of unmatchedJira) {
      console.log(`  ${j.key.padEnd(8)} | ${j.summary.substring(0, 80)}`);
    }
  }

  writeFileSync('/tmp/jira_mapping.json', JSON.stringify({ mapping, unmatchedDoc, unmatchedJira }, null, 2));
  console.log("\n✅ Full mapping saved to /tmp/jira_mapping.json");
}

main().catch(console.error);
