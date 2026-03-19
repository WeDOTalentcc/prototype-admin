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
    const txt = await res.text();
    throw new Error(`PUT ${path} → ${res.status}: ${txt.substring(0, 500)}`);
  }
  return res.status;
}

async function jiraPost(path, token, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
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
    throw new Error(`POST ${path} → ${res.status}: ${txt.substring(0, 500)}`);
  }
  return res.json().catch(() => ({}));
}

async function jiraGet(path, token) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Authorization': `Bearer ${token}`, 'Accept': 'application/json' }
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`GET ${path} → ${res.status}: ${txt.substring(0, 500)}`);
  }
  return res.json();
}

async function getTransitions(issueKey, token) {
  return jiraGet(`/issue/${issueKey}/transitions`, token);
}

async function transitionIssue(issueKey, transitionId, token) {
  return jiraPost(`/issue/${issueKey}/transitions`, token, {
    transition: { id: transitionId }
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function executePhase1(plan, token, dryRun = false) {
  const items = plan.phase1_dates;
  console.log(`\n${'='.repeat(60)}`);
  console.log(`FASE 1: CORREÇÃO DE DATAS — ${items.length} cards`);
  console.log(`${'='.repeat(60)}`);

  let success = 0, errors = 0, skipped = 0;
  const errorLog = [];

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const fields = {};

    if (item.new_start) fields.customfield_10015 = item.new_start;
    if (item.new_due) fields.duedate = item.new_due;

    if (Object.keys(fields).length === 0) {
      skipped++;
      continue;
    }

    const label = `[${i+1}/${items.length}] ${item.code} (${item.jira_key})`;

    if (dryRun) {
      console.log(`  DRY-RUN ${label}: start=${item.new_start}, due=${item.new_due}`);
      success++;
      continue;
    }

    try {
      await jiraPut(`/issue/${item.jira_key}`, token, { fields });
      console.log(`  ✓ ${label}`);
      success++;
    } catch (e) {
      console.log(`  ✗ ${label}: ${e.message.substring(0, 120)}`);
      errorLog.push({ ...item, error: e.message });
      errors++;
    }

    if (i % 10 === 9) await sleep(500);
  }

  console.log(`\nFase 1 concluída: ${success} OK, ${errors} erros, ${skipped} pulados`);
  return { success, errors, skipped, errorLog };
}

async function executePhase2(plan, token, dryRun = false) {
  const items = plan.phase2_sprints;
  console.log(`\n${'='.repeat(60)}`);
  console.log(`FASE 2: CORREÇÃO DE SPRINT LABELS — ${items.length} cards`);
  console.log(`${'='.repeat(60)}`);

  let success = 0, errors = 0;
  const errorLog = [];

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const label = `[${i+1}/${items.length}] ${item.code} (${item.jira_key})`;

    if (dryRun) {
      console.log(`  DRY-RUN ${label}: ${item.old_sprint} → ${item.new_sprint}`);
      success++;
      continue;
    }

    try {
      await jiraPut(`/issue/${item.jira_key}`, token, {
        fields: { labels: item.new_labels }
      });
      console.log(`  ✓ ${label}: ${item.old_sprint} → ${item.new_sprint}`);
      success++;
    } catch (e) {
      console.log(`  ✗ ${label}: ${e.message.substring(0, 120)}`);
      errorLog.push({ ...item, error: e.message });
      errors++;
    }

    if (i % 10 === 9) await sleep(500);
  }

  console.log(`\nFase 2 concluída: ${success} OK, ${errors} erros`);
  return { success, errors, errorLog };
}

async function executePhase4(plan, token, dryRun = false) {
  const items = plan.phase4_duplicates;
  console.log(`\n${'='.repeat(60)}`);
  console.log(`FASE 4: MARCAR ${items.length} DUPLICADOS`);
  console.log(`${'='.repeat(60)}`);

  let success = 0, errors = 0, alreadyClosed = 0;
  const errorLog = [];

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const label = `[${i+1}/${items.length}] ${item.jira_key} [${item.code}]`;

    if (item.status === 'Done' || item.status === 'Cancelled') {
      console.log(`  ⊘ ${label}: já ${item.status}, apenas adicionando label`);
      alreadyClosed++;
    }

    if (dryRun) {
      console.log(`  DRY-RUN ${label}: add label 'duplicate'`);
      success++;
      continue;
    }

    try {
      const currentIssue = await jiraGet(`/issue/${item.jira_key}?fields=labels`, token);
      const currentLabels = currentIssue.fields?.labels || [];

      if (!currentLabels.includes('duplicate')) {
        const newLabels = [...currentLabels, 'duplicate'];
        await jiraPut(`/issue/${item.jira_key}`, token, {
          fields: { labels: newLabels }
        });
      }

      if (item.status !== 'Done' && item.status !== 'Cancelled') {
        try {
          const transitions = await getTransitions(item.jira_key, token);
          const cancelTransition = transitions.transitions?.find(t =>
            t.name.toLowerCase().includes('cancel') ||
            t.name.toLowerCase().includes('done') ||
            t.name.toLowerCase().includes('conclu')
          );

          if (cancelTransition) {
            await transitionIssue(item.jira_key, cancelTransition.id, token);
            console.log(`  ✓ ${label}: labeled + transitioned to ${cancelTransition.name}`);
          } else {
            console.log(`  ✓ ${label}: labeled (no cancel/done transition found)`);
          }
        } catch (te) {
          console.log(`  ⚠ ${label}: labeled but transition failed: ${te.message.substring(0, 80)}`);
        }
      } else {
        console.log(`  ✓ ${label}: labeled`);
      }

      success++;
    } catch (e) {
      console.log(`  ✗ ${label}: ${e.message.substring(0, 120)}`);
      errorLog.push({ ...item, error: e.message });
      errors++;
    }

    if (i % 5 === 4) await sleep(500);
  }

  console.log(`\nFase 4 concluída: ${success} OK, ${errors} erros, ${alreadyClosed} já fechados`);
  return { success, errors, alreadyClosed, errorLog };
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const phase = args.find(a => a.startsWith('--phase='))?.split('=')[1] || 'all';

  console.log(`\n${'#'.repeat(60)}`);
  console.log(`# JIRA SYNC EXECUTION ${dryRun ? '(DRY-RUN)' : '(LIVE)'}`);
  console.log(`# Phase: ${phase}`);
  console.log(`${'#'.repeat(60)}`);

  const plan = JSON.parse(readFileSync('/tmp/execution_plan.json', 'utf8'));
  const token = await getAccessToken();
  const results = {};

  if (phase === 'all' || phase === '1') {
    results.phase1 = await executePhase1(plan, token, dryRun);
  }

  if (phase === 'all' || phase === '2') {
    results.phase2 = await executePhase2(plan, token, dryRun);
  }

  if (phase === 'all' || phase === '4') {
    results.phase4 = await executePhase4(plan, token, dryRun);
  }

  console.log(`\n${'#'.repeat(60)}`);
  console.log(`# RESUMO FINAL`);
  console.log(`${'#'.repeat(60)}`);
  for (const [p, r] of Object.entries(results)) {
    console.log(`  ${p}: ${r.success} OK, ${r.errors} erros${r.skipped ? `, ${r.skipped} pulados` : ''}`);
  }

  writeFileSync('/tmp/execution_results.json', JSON.stringify(results, null, 2));
  console.log('\nResultados salvos em /tmp/execution_results.json');
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
