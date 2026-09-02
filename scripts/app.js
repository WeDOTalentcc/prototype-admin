/* ==========================================================
   WeDOTalent Admin Console — Prototype App Logic
   WEDO-640 a WEDO-648
   ========================================================== */

// App State
let currentScreen = 'screen-dashboard';
let sidebarExpanded = true;
let selectedClient = null;
let activeModal = null;
let currentWizardStep = 1;

/* ----------------------------------------------------------
   Screen Navigation
   ---------------------------------------------------------- */
function showScreen(screenId) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const target = document.getElementById(screenId);
  if (target) target.classList.add('active');
  currentScreen = screenId;
  updateSidebarActive(screenId);
  updateTopbarContext(screenId);
}

function setActivePage(page) {
  const map = {
    dashboard: 'screen-dashboard',
    clients:   'screen-clients',
  };
  showScreen(map[page] || 'screen-dashboard');
}

function updateSidebarActive(screenId) {
  document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
  const map = {
    'screen-dashboard':             'nav-dashboard',
    'screen-saas-metrics':          'nav-saas-metrics',
    'screen-clients':               'nav-clients',
    'screen-clients-empty':         'nav-clients',
    'screen-clients-search-empty':  'nav-clients',
    'screen-onboarding':                  'nav-onboarding',
    'screen-onboarding-portal-global':    'nav-onboarding-portal',
    'screen-onboarding-client':           'nav-client-onboarding',
    'screen-ai-monitoring':         'nav-ai-monitoring',
    'screen-audit-logs':            'nav-audit-logs',
    'screen-assisted-access':         'nav-assisted-access',
    'screen-assisted-access-empty':   'nav-assisted-access',
    'screen-assisted-access-loading': 'nav-assisted-access',
    'screen-assisted-access-error':   'nav-assisted-access',
    'screen-client-detail':         'nav-client-overview',
    'screen-client-users':          'nav-client-users',
    'screen-billing':               'nav-billing',
    'screen-llm-config':            'nav-llm-config',
    'screen-lia-persona':           'nav-lia-persona',
    'screen-whatsapp-templates':    'nav-wa-templates',
    'screen-fairness-policies':     'nav-fairness-policies',
    'screen-feature-flags':         'nav-feature-flags',
    'screen-plans':                 'nav-plans',
    'screen-global-flags':          'nav-global-flags',
    'screen-email-templates':       'nav-email-templates',
    'screen-contracts':             'nav-contracts',
    'screen-settings':              'nav-settings',
    'screen-global-integrations':   'nav-global-integrations',
    'screen-lia-global':            'nav-lia-global',
    'screen-notifications':         'nav-notifications',
    'screen-cat-geo':               'nav-cat-geo',
    'screen-cat-talents':           'nav-cat-talents',
    'screen-cat-job':               'nav-cat-job',
    'screen-cat-comp':              'nav-cat-comp',
    'screen-cat-pipeline':          'nav-cat-pipeline',
    'screen-client-refdata-structure': 'nav-client-refdata-structure',
    'screen-client-refdata-talents':   'nav-client-refdata-talents',
  };
  const activeId = map[screenId];
  if (activeId) {
    const el = document.getElementById(activeId);
    if (el) el.classList.add('active');
  }
}

function updateTopbarContext(screenId) {
  const ctx = document.getElementById('topbar-context');
  if (!ctx) return;
  const labels = {
    'screen-dashboard':             'Dashboard',
    'screen-saas-metrics':          'SaaS Metrics',
    'screen-clients':               'Clientes',
    'screen-clients-empty':         'Clientes',
    'screen-clients-search-empty':  'Clientes',
    'screen-onboarding':                 'Provisionamentos',
    'screen-onboarding-portal-global':   'Onboarding Portal',
    'screen-onboarding-client':          'Onboarding — iFood Talentos',
    'screen-ai-monitoring':         'Monitoramento de Agentes IA',
    'screen-audit-logs':            'Logs & Auditoria',
    'screen-assisted-access':         'Acessos Assistidos',
    'screen-assisted-access-empty':   'Acessos Assistidos',
    'screen-assisted-access-loading': 'Acessos Assistidos',
    'screen-assisted-access-error':   'Acessos Assistidos',
    'screen-client-detail':         'iFood Talentos',
    'screen-client-users':          'Usuários — iFood Talentos',
    'screen-billing':               'Faturamento — iFood Talentos',
    'screen-llm-config':            'Configuração LLM — iFood Talentos',
    'screen-lia-persona':           'Persona da LIA — iFood Talentos',
    'screen-whatsapp-templates':    'WhatsApp & Templates — iFood Talentos',
    'screen-fairness-policies':     'Políticas de Fairness — iFood Talentos',
    'screen-feature-flags':         'Feature Flags — iFood Talentos',
    'screen-plans':                 'Planos & Preços',
    'screen-global-flags':          'Feature Flags Globais',
    'screen-email-templates':       'Templates de E-mail',
    'screen-contracts':             'Contratos',
    'screen-settings':              'Configurações da Plataforma',
    'screen-global-integrations':   'Integrações Globais',
    'screen-lia-global':            'LIA Global',
    'screen-notifications':         'Notificações',
    'screen-cat-geo':               'Catálogo Geográfico',
    'screen-cat-talents':           'Idiomas & Setores',
    'screen-cat-job':               'Atributos de Vaga',
    'screen-cat-comp':              'Remuneração & Qualificação',
    'screen-cat-pipeline':          'Pipeline & Diversidade',
    'screen-client-refdata-structure': 'Dados de Referência — Estrutura & Processo',
    'screen-client-refdata-talents':   'Dados de Referência — Talentos',
  };
  ctx.textContent = labels[screenId] || '';
}

/* ----------------------------------------------------------
   Sidebar Toggle
   ---------------------------------------------------------- */
function toggleSidebar() {
  sidebarExpanded = !sidebarExpanded;
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content');
  const topbar = document.getElementById('topbar');

  if (sidebarExpanded) {
    sidebar.classList.remove('collapsed');
    if (mainContent) mainContent.style.left = 'var(--sidebar-width-expanded)';
    if (topbar) topbar.style.left = 'var(--sidebar-width-expanded)';
  } else {
    sidebar.classList.add('collapsed');
    if (mainContent) mainContent.style.left = 'var(--sidebar-width-collapsed)';
    if (topbar) topbar.style.left = 'var(--sidebar-width-collapsed)';
  }
}

/* ----------------------------------------------------------
   Scope Dropdown
   ---------------------------------------------------------- */
function toggleScopeDropdown() {
  const dd = document.getElementById('scope-dropdown');
  if (!dd) return;
  dd.style.display = dd.style.display === 'block' ? 'none' : 'block';
}

function closeScopeDropdown() {
  const dd = document.getElementById('scope-dropdown');
  if (dd) dd.style.display = 'none';
}

function selectScopeGlobal() {
  clearClientContext();
  closeScopeDropdown();
}

function selectScopeClient(clientId, name, plan) {
  selectedClient = clientId;
  const globalSidebar = document.getElementById('sidebar-global');
  const clientSidebar = document.getElementById('sidebar-client');
  if (globalSidebar) globalSidebar.style.display = 'none';
  if (clientSidebar) clientSidebar.style.display = 'block';

  const scopeBtn = document.getElementById('scope-btn');
  if (scopeBtn) {
    const badge = plan === 'Alpha'
      ? `<span style="background:rgba(17,24,39,0.08);color:#374151;font-size:11px;padding:1px 6px;border-radius:99px;font-weight:600;">Alpha</span>`
      : `<span style="background:rgba(96,190,209,0.15);color:#0E7490;font-size:11px;padding:1px 6px;border-radius:99px;font-weight:600;">${plan}</span>`;
    scopeBtn.innerHTML = `<span class="scope-dot" style="background:var(--wedo-green)"></span>${name}${badge}<i data-lucide="chevron-down"></i>`;
    lucide.createIcons({ nodes: [scopeBtn] });
  }
  showScreen('screen-client-detail');
  closeScopeDropdown();
}

/* ----------------------------------------------------------
   Client Context
   ---------------------------------------------------------- */
function setClientContext(clientId) {
  selectedClient = clientId;
  const globalSidebar = document.getElementById('sidebar-global');
  const clientSidebar = document.getElementById('sidebar-client');
  if (globalSidebar) globalSidebar.style.display = 'none';
  if (clientSidebar) clientSidebar.style.display = 'block';

  const scopeBtn = document.getElementById('scope-btn');
  if (scopeBtn) {
    scopeBtn.innerHTML = `<span class="scope-dot" style="background:var(--wedo-green)"></span>
      iFood Talentos
      <span style="background:rgba(96,190,209,0.15);color:#0E7490;font-size:11px;padding:1px 6px;border-radius:99px;font-weight:600;">PRO</span>
      <i data-lucide="chevron-down"></i>`;
    lucide.createIcons({ nodes: [scopeBtn] });
  }
}

function clearClient() { clearClientContext(); }

function clearClientContext() {
  selectedClient = null;
  const globalSidebar = document.getElementById('sidebar-global');
  const clientSidebar = document.getElementById('sidebar-client');
  if (globalSidebar) globalSidebar.style.display = 'block';
  if (clientSidebar) clientSidebar.style.display = 'none';

  const scopeBtn = document.getElementById('scope-btn');
  if (scopeBtn) {
    scopeBtn.innerHTML = `<span class="scope-dot"></span>
      Visão Global — Todos os Clientes
      <i data-lucide="chevron-down"></i>`;
    lucide.createIcons({ nodes: [scopeBtn] });
  }

  const clientScreens = ['screen-client-detail','screen-client-users','screen-billing','screen-llm-config','screen-feature-flags','screen-onboarding-client'];
  if (clientScreens.includes(currentScreen)) {
    showScreen('screen-clients');
  }
}

/* ----------------------------------------------------------
   Modal Management
   ---------------------------------------------------------- */
function openModal(modalId) {
  closeModal();
  const overlay = document.getElementById('overlay-' + modalId);
  if (overlay) {
    overlay.style.display = 'flex';
    activeModal = modalId;
    const modal = overlay.querySelector('.modal');
    if (modal) {
      modal.style.opacity = '0';
      modal.style.transform = 'scale(0.95) translateY(-8px)';
      requestAnimationFrame(() => {
        modal.style.transition = 'opacity 200ms ease, transform 200ms ease';
        modal.style.opacity = '1';
        modal.style.transform = 'scale(1) translateY(0)';
      });
    }
  }
}

function closeModal() {
  document.querySelectorAll('.modal-overlay').forEach(o => o.style.display = 'none');
  activeModal = null;
}

function handleOverlayClick(event) {
  if (event.target === event.currentTarget) {
    if (activeModal === 'new-client') {
      closeModal();
    } else {
      closeModal();
    }
  }
}

/* ----------------------------------------------------------
   Plan Card Selection
   ---------------------------------------------------------- */
function selectPlan(card) {
  const container = card.parentElement;
  container.querySelectorAll('div[onclick]').forEach(sib => {
    sib.classList.remove('plan-selected');
    sib.style.border = '1px solid #E5E7EB';
    sib.style.background = '';
  });
  card.classList.add('plan-selected');
  card.style.border = '2px solid #C74446';
  card.style.background = 'rgba(199,68,70,0.02)';
}

/* ----------------------------------------------------------
   Feature Toggle Switch
   ---------------------------------------------------------- */
function toggleFeature(el) {
  const isOn = el.dataset.on === 'true';
  el.dataset.on = isOn ? 'false' : 'true';
  el.style.background = isOn ? '#D1D5DB' : '#60BED1';
  const circle = el.querySelector('.toggle-circle');
  if (circle) circle.style.left = isOn ? '2px' : '22px';
}

/* ----------------------------------------------------------
   Persona — seleção de tom (single-select entre os cards)
   ---------------------------------------------------------- */
function selectPersonaTone(el) {
  const group = el.parentElement;
  group.querySelectorAll('.provider-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
}

/* ----------------------------------------------------------
   Wizard Navigation (Onboarding)
   ---------------------------------------------------------- */
function wizardStep(n) {
  // Clamp between 1 and 5
  n = Math.max(1, Math.min(5, n));
  currentWizardStep = n;

  // Hide all panels
  document.querySelectorAll('.wizard-panel').forEach(p => p.style.display = 'none');
  const active = document.getElementById('wizard-panel-' + n);
  if (active) active.style.display = 'block';

  // Update step indicators
  document.querySelectorAll('.wizard-step').forEach((s, i) => {
    const stepNum = i + 1;
    s.classList.remove('current', 'completed', 'pending');
    if (stepNum < n) s.classList.add('completed');
    else if (stepNum === n) s.classList.add('current');
    else s.classList.add('pending');
  });
}

/* ----------------------------------------------------------
   Tab Switching
   ---------------------------------------------------------- */
function switchTab(groupId, tabId) {
  // Deactivate all tabs in group
  document.querySelectorAll('[data-tab-group="' + groupId + '"]').forEach(btn => {
    btn.classList.remove('active');
  });
  // Activate clicked tab
  const activeBtn = document.querySelector('[data-tab-group="' + groupId + '"][data-tab="' + tabId + '"]');
  if (activeBtn) activeBtn.classList.add('active');

  // Hide all panels in group
  document.querySelectorAll('[data-tab-panel-group="' + groupId + '"]').forEach(panel => {
    panel.style.display = 'none';
  });
  // Show active panel
  const activePanel = document.querySelector('[data-tab-panel-group="' + groupId + '"][data-tab-panel="' + tabId + '"]');
  if (activePanel) activePanel.style.display = 'block';
}

/* ----------------------------------------------------------
   Políticas de Fairness — seletor de domínio (WEDO-1559)
   Protótipo: o domínio "screening" (triagem) está totalmente modelado;
   os demais reusam a mesma estrutura por domínio.
   ---------------------------------------------------------- */
function fairSetDomain(domain) {
  const ctx = document.getElementById('topbar-context');
  if (ctx) ctx.textContent = 'Políticas de Fairness — iFood Talentos · ' + domain;
}

/* ----------------------------------------------------------
   Audit Log Drawer
   ---------------------------------------------------------- */
const AUDIT_SEVERITY_COLORS = {
  info: { bg: '#EFF6FF', fg: '#1D4ED8' },
  warning: { bg: '#FEF3C7', fg: '#B45309' },
  critical: { bg: '#FEE2E2', fg: '#B91C1C' }
};

const AUDIT_FIELD_LABELS = {
  id: 'ID do evento', type: 'Tipo', timestamp: 'Timestamp', tenant: 'Tenant',
  actor: 'Agente / Usuário', action: 'Ação', resource: 'Recurso',
  old_value: 'Valor anterior', new_value: 'Novo valor', ip: 'IP de origem',
  candidate_id: 'Candidato', score: 'Score', approved: 'Aprovado',
  fairness_passed: 'FairnessGuard', subject_cpf: 'CPF do titular',
  requester: 'Solicitante', purpose: 'Finalidade', job_id: 'Vaga'
};

// Campos de rastreabilidade/integridade (ADR-004) renderizados em bloco próprio.
const AUDIT_TRACE_FIELDS = ['correlation_id', 'decision_category', 'hash', 'prev_hash', 'payload_uri', 'chain_verified'];

function auditFmtValue(v) {
  if (v === true) return 'Sim';
  if (v === false) return 'Não';
  if (v === null || v === undefined || v === '') return '—';
  return String(v);
}

function auditRow(label, valueHtml) {
  return '<div style="display:flex; gap:12px; padding:10px 0; border-top:1px solid #F3F4F6;">'
    + '<div style="flex:0 0 150px; font-size:12px; color:#6B7280;">' + label + '</div>'
    + '<div style="flex:1; font-size:13px; color:#111827; word-break:break-word;">' + valueHtml + '</div>'
    + '</div>';
}

function openDrawer(rowData) {
  const drawer = document.getElementById('audit-drawer');
  const content = document.getElementById('audit-drawer-content');
  if (!drawer || !content) return;

  const sev = (rowData.severity || 'info').toLowerCase();
  const sevColor = AUDIT_SEVERITY_COLORS[sev] || AUDIT_SEVERITY_COLORS.info;
  const isDecision = rowData.type === 'ai_decision';
  const category = rowData.decision_category || (isDecision ? 'business' : null);
  const catColor = category === 'compliance' ? { bg: '#F5F3FF', fg: '#6D28D9' } : { bg: '#ECFDF5', fg: '#047857' };

  let html = '';
  // Cabeçalho
  html += '<div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">'
    + '<span style="font-family:ui-monospace,monospace; font-size:13px; font-weight:600; color:#111827;">' + auditFmtValue(rowData.action || rowData.type) + '</span>'
    + '<span style="padding:2px 8px; border-radius:6px; font-size:11px; font-weight:600; background:' + sevColor.bg + '; color:' + sevColor.fg + ';">' + sev.toUpperCase() + '</span>'
    + (category ? '<span style="padding:2px 8px; border-radius:6px; font-size:11px; font-weight:600; background:' + catColor.bg + '; color:' + catColor.fg + ';">' + category + '</span>' : '')
    + '</div>';
  html += '<div style="font-size:12px; color:#6B7280; margin-bottom:16px;">' + auditFmtValue(rowData.timestamp) + '</div>';

  // Detalhes gerais
  html += '<div style="margin-bottom:20px;">';
  Object.keys(rowData).forEach(k => {
    if (k === 'severity' || k === 'timestamp' || k === 'action' || AUDIT_TRACE_FIELDS.indexOf(k) !== -1) return;
    const label = AUDIT_FIELD_LABELS[k] || k;
    let val = auditFmtValue(rowData[k]);
    if (k === 'fairness_passed') {
      val = rowData[k]
        ? '<span style="color:#047857; font-weight:600;">✓ Aprovado</span>'
        : '<span style="color:#B91C1C; font-weight:600;">✗ Bloqueado</span>';
    }
    html += auditRow(label, val);
  });
  html += '</div>';

  // Bloco de integridade & rastreabilidade (ADR-004) — trilha imutável append-only + hash-chain
  const hasTrace = AUDIT_TRACE_FIELDS.some(f => rowData[f] !== undefined) || isDecision;
  if (hasTrace) {
    const verified = rowData.chain_verified !== false; // default verificado na referência
    const corr = rowData.correlation_id || 'req_' + (rowData.id || 'na');
    html += '<div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:14px 16px;">';
    html += '<div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">'
      + '<i data-lucide="shield-check" style="width:15px; height:15px; color:' + (verified ? '#047857' : '#B91C1C') + ';"></i>'
      + '<span style="font-size:12px; font-weight:700; color:#111827;">Integridade & Rastreabilidade</span>'
      + '<span style="margin-left:auto; padding:2px 8px; border-radius:6px; font-size:11px; font-weight:600; background:' + (verified ? '#ECFDF5' : '#FEE2E2') + '; color:' + (verified ? '#047857' : '#B91C1C') + ';">'
      + (verified ? 'hash-chain verificada' : 'integridade comprometida') + '</span>'
      + '</div>';
    html += auditRow('correlation_id', '<span style="font-family:ui-monospace,monospace; font-size:12px;">' + corr + '</span>');
    if (rowData.hash) html += auditRow('hash (SHA-256)', '<span style="font-family:ui-monospace,monospace; font-size:11px; color:#6B7280;">' + rowData.hash + '</span>');
    if (rowData.prev_hash) html += auditRow('hash anterior', '<span style="font-family:ui-monospace,monospace; font-size:11px; color:#6B7280;">' + rowData.prev_hash + '</span>');
    html += auditRow('payload', rowData.payload_uri
      ? '<a href="#" onclick="return false" style="color:#2563EB; text-decoration:none; font-size:12px;">object storage ↗ <span style="color:#9CA3AF;">(' + rowData.payload_uri + ')</span></a>'
      : '<span style="color:#6B7280; font-size:12px;">inline (metadata store)</span>');
    html += '<div style="margin-top:10px; font-size:11px; color:#9CA3AF; line-height:1.5;">Registro append-only imutável (não editável/removível). LGPD · EU AI Act.</div>';
    html += '</div>';
  }

  content.innerHTML = html;
  if (window.lucide) lucide.createIcons();
  drawer.classList.add('open');
}

function closeDrawer() {
  const drawer = document.getElementById('audit-drawer');
  if (drawer) drawer.classList.remove('open');
}

/* ----------------------------------------------------------
   Period Selector (SaaS Metrics)
   ---------------------------------------------------------- */
function selectPeriod(days) {
  [30, 60, 90].forEach(d => {
    const btn = document.getElementById('period-' + d);
    if (!btn) return;
    if (d === days) {
      btn.style.background = '#111827';
      btn.style.color = 'white';
      btn.style.fontWeight = '600';
    } else {
      btn.style.background = 'white';
      btn.style.color = '#374151';
      btn.style.fontWeight = '400';
    }
  });
}

/* ----------------------------------------------------------
   Notification Dropdown
   ---------------------------------------------------------- */
let unreadNotifCount = 3;

function toggleNotifDropdown() {
  const dd = document.getElementById('notif-dropdown');
  if (!dd) return;
  dd.style.display = dd.style.display === 'block' ? 'none' : 'block';
}

function closeNotifDropdown() {
  const dd = document.getElementById('notif-dropdown');
  if (dd) dd.style.display = 'none';
}

function markAllNotifsRead() {
  unreadNotifCount = 0;
  const badge = document.getElementById('notif-badge');
  if (badge) badge.style.display = 'none';
  document.querySelectorAll('.notif-item').forEach(item => {
    item.style.background = 'white';
    item.onmouseover = function() { this.style.background = '#F9FAFB'; };
    item.onmouseout = function() { this.style.background = 'white'; };
    const dot = item.querySelector('div[style*="background:#C74446"]');
    if (dot) dot.style.display = 'none';
  });
}

/* ----------------------------------------------------------
   User Dropdown
   ---------------------------------------------------------- */
function toggleUserDropdown() {
  const dd = document.getElementById('user-dropdown');
  if (!dd) return;
  dd.style.display = dd.style.display === 'block' ? 'none' : 'block';
}

function closeUserDropdown() {
  const dd = document.getElementById('user-dropdown');
  if (dd) dd.style.display = 'none';
}

/* ----------------------------------------------------------
   Keyboard Shortcuts & Outside-click Handlers
   ---------------------------------------------------------- */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeModal();
    closeDrawer();
    aaCloseDetail();
    closeScopeDropdown();
    closeNotifDropdown();
    closeUserDropdown();
  }
});

document.addEventListener('click', e => {
  const scopeWrapper = document.getElementById('scope-wrapper');
  if (scopeWrapper && !scopeWrapper.contains(e.target)) closeScopeDropdown();

  const notifWrapper = document.getElementById('notif-wrapper');
  if (notifWrapper && !notifWrapper.contains(e.target)) closeNotifDropdown();

  const userWrapper = document.getElementById('user-wrapper');
  if (userWrapper && !userWrapper.contains(e.target)) closeUserDropdown();
});

/* ----------------------------------------------------------
   Init
   ---------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  const hash = (location.hash || '').replace('#', '');
  if (hash && document.getElementById(hash)) {
    // Telas de contexto de cliente precisam da sidebar de cliente
    if (hash.indexOf('screen-client-') === 0 && typeof setClientContext === 'function') {
      setClientContext('ifood');
    }
    showScreen(hash);
  } else {
    showScreen('screen-dashboard');
  }
  // Deep-link opcional para abrir um modal: ?cf=<key>&mode=novo|editar  ou  ?modal=<id>
  try {
    const q = new URLSearchParams(location.search);
    if (q.get('tab') && typeof showCatTab === 'function') {
      const scr = document.querySelector('.screen.active');
      if (scr) {
        const btns = [...scr.querySelectorAll('.cat-tab')];
        const b = btns.find(x => (x.getAttribute('onclick')||'').indexOf("'" + q.get('tab') + "'") !== -1);
        if (b) b.click();
      }
    }
    if (q.get('pipe') && typeof openPipelineEditor === 'function') {
      openPipelineEditor(q.get('pipe'));
    }
    if (q.get('cf') && typeof openCatForm === 'function') {
      openCatForm(q.get('cf'), q.get('mode') || 'novo');
    } else if (q.get('modal') && typeof openModal === 'function') {
      openModal(q.get('modal'));
    }
  } catch (e) {}
});

/* ----------------------------------------------------------
   Onboarding Portal — Tab navigation
   ---------------------------------------------------------- */
const ONB_TABS = ['visao','checklist','respostas','delegacoes','arquivos','mensagens','implementacao'];

function onbSwitchTab(tab) {
  ONB_TABS.forEach(t => {
    const panel = document.getElementById('onb-panel-' + t);
    const btn   = document.getElementById('onb-tab-' + t);
    if (!panel || !btn) return;
    if (t === tab) {
      panel.style.display = '';
      btn.style.color = '#C74446';
      btn.style.fontWeight = '600';
      btn.style.borderBottom = '2px solid #C74446';
    } else {
      panel.style.display = 'none';
      btn.style.color = '#6B7280';
      btn.style.fontWeight = '500';
      btn.style.borderBottom = '2px solid transparent';
    }
  });
}

/* ----------------------------------------------------------
   Onboarding Portal — Checklist section toggle
   ---------------------------------------------------------- */
function onbToggleSection(secId) {
  const body = document.getElementById('onb-' + secId + '-body');
  const icon = document.getElementById('onb-' + secId + '-icon');
  if (!body) return;
  const isOpen = body.style.display !== 'none';
  body.style.display = isOpen ? 'none' : '';
  if (icon) {
    icon.setAttribute('data-lucide', isOpen ? 'chevron-right' : 'chevron-down');
    lucide.createIcons({ nodes: [icon] });
  }
}

/* ----------------------------------------------------------
   Onboarding Portal — Global filter pills
   ---------------------------------------------------------- */
function opgFilterPill(selected) {
  ['all','andamento','atrasado','aguardando','concluido'].forEach(p => {
    const el = document.getElementById('opg-pill-' + p);
    if (!el) return;
    if (p === selected) {
      el.style.background = '#111827';
      el.style.borderColor = '#111827';
      el.querySelectorAll('span,strong').forEach(s => { s.style.color = 'white'; });
    } else {
      el.style.background = 'white';
      el.style.borderColor = '#E5E7EB';
      el.querySelectorAll('span,strong').forEach(s => { s.style.color = ''; });
    }
  });
}


/* ----------------------------------------------------------
   Catálogos — troca de abas (Dados de Referência)
   ---------------------------------------------------------- */
function showCatTab(screenId, tabKey, btn) {
  const screen = document.getElementById(screenId);
  if (!screen) return;
  screen.querySelectorAll('.cat-panel').forEach(p => p.style.display = 'none');
  const panel = screen.querySelector('.cat-panel[data-tab="' + tabKey + '"]');
  if (panel) panel.style.display = 'block';
  screen.querySelectorAll('.cat-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  if (window.lucide && lucide.createIcons) lucide.createIcons();
}


/* ----------------------------------------------------------
   Dados de Referência — modais de CRUD (Novo/Editar/Excluir)
   ---------------------------------------------------------- */
const CAT_LABELS = {"paises": {"n": "Novo País", "e": "Editar País"}, "estados": {"n": "Novo Estado", "e": "Editar Estado"}, "cidades": {"n": "Nova Cidade", "e": "Editar Cidade"}, "idiomas": {"n": "Novo Idioma", "e": "Editar Idioma"}, "setores": {"n": "Novo Setor", "e": "Editar Setor"}, "senioridade": {"n": "Novo Nível", "e": "Editar Nível"}, "contrato": {"n": "Novo Tipo", "e": "Editar Tipo"}, "modelo": {"n": "Novo Modelo", "e": "Editar Modelo"}, "prioridade": {"n": "Nova Prioridade", "e": "Editar Prioridade"}, "urgencia": {"n": "Novo Nível", "e": "Editar Nível"}, "moedas": {"n": "Nova Moeda", "e": "Editar Moeda"}, "escolaridade": {"n": "Novo Nível", "e": "Editar Nível"}, "experiencia": {"n": "Nova Faixa", "e": "Editar Faixa"}, "niveis-skill": {"n": "Novo Nível", "e": "Editar Nível"}, "proficiencia": {"n": "Novo Nível", "e": "Editar Nível"}, "reprovacao": {"n": "Novo Motivo", "e": "Editar Motivo"}, "recusa": {"n": "Novo Motivo", "e": "Editar Motivo"}, "origem": {"n": "Nova Origem", "e": "Editar Origem"}, "afirmativo": {"n": "Novo Grupo", "e": "Editar Grupo"}, "departamentos": {"n": "Novo Departamento", "e": "Editar Departamento"}, "status-vaga": {"n": "Novo Status", "e": "Editar Status"}, "jornadas": {"n": "Nova Jornada", "e": "Editar Jornada"}, "beneficios": {"n": "Novo Benefício", "e": "Editar Benefício"}, "cat-skill": {"n": "Nova Categoria", "e": "Editar Categoria"}, "skills": {"n": "Nova Skill", "e": "Editar Skill"}, "comportamentais": {"n": "Nova Competência", "e": "Editar Competência"}, "ocupacoes": {"n": "Nova Ocupação", "e": "Editar Ocupação"}, "instituicoes": {"n": "Nova Instituição", "e": "Editar Instituição"}, "areas-estudo": {"n": "Nova Área", "e": "Editar Área"}};
function openCatForm(key, mode) {
  const meta = CAT_LABELS[key]; if (!meta) return;
  const t = document.getElementById('cf-' + key + '-title');
  if (t) t.textContent = (mode === 'editar' ? meta.e : meta.n);
  const del = document.getElementById('cf-' + key + '-del');
  if (del) del.style.display = (mode === 'editar' ? 'inline-flex' : 'none');
  openModal('cf-' + key);
}
function openCatDelete(name) {
  const el = document.getElementById('cat-delete-name');
  if (el) el.textContent = name || 'este item';
  openModal('cat-delete');
}


/* Pipeline/Jornada — labels extra + DnD + toggles */
Object.assign(CAT_LABELS, {"etapa": {"n": "Nova Etapa", "e": "Editar Etapa"}, "substatus": {"n": "Novo Sub-status", "e": "Editar Sub-status"}, "template": {"n": "Novo Template de Jornada", "e": "Editar Template"}, "secao": {"n": "Nova Seção", "e": "Editar Seção"}});
function toggleStageSub(idx, btn){
  const el=document.getElementById('sub-'+idx); if(!el) return;
  const open = el.style.display!=='none';
  el.style.display = open ? 'none' : 'block';
  const ic = btn.querySelector('i');
  if(ic){ ic.setAttribute('data-lucide', open?'chevron-right':'chevron-down'); if(window.lucide) lucide.createIcons(); }
}
function _dndAfter(list, y){
  const els=[...list.querySelectorAll(':scope > .dnd-row[draggable="true"]:not(.dnd-dragging)')];
  let best={o:-Infinity,el:null};
  for(const c of els){ const b=c.getBoundingClientRect(); const off=y-b.top-b.height/2; if(off<0 && off>best.o) best={o:off,el:c}; }
  return best.el;
}
function initDnd(){
  document.querySelectorAll('[data-sortable]').forEach(list=>{
    if(list.__dnd) return; list.__dnd=true;
    list.addEventListener('dragstart', e=>{ const r=e.target.closest('.dnd-row[draggable="true"]'); if(!r||!list.contains(r))return; r.classList.add('dnd-dragging'); e.dataTransfer.effectAllowed='move'; });
    list.addEventListener('dragend', e=>{ const r=list.querySelector('.dnd-dragging'); if(r) r.classList.remove('dnd-dragging'); });
    list.addEventListener('dragover', e=>{ e.preventDefault(); const drag=list.querySelector('.dnd-dragging'); if(!drag)return; const after=_dndAfter(list, e.clientY); if(after==null) list.appendChild(drag); else list.insertBefore(drag, after); });
  });
}
document.addEventListener('DOMContentLoaded', initDnd);


/* Pipeline — navegação lista <-> editor + confirmação genérica */
function openPipelineEditor(name){
  var l=document.getElementById('pipe-list'), ed=document.getElementById('pipe-editor');
  if(l) l.style.display='none';
  if(ed) ed.style.display='block';
  var n=document.getElementById('pipe-editor-name'); if(n) n.textContent=name;
  if(window.lucide) lucide.createIcons();
}
function backToTemplates(){
  var l=document.getElementById('pipe-list'), ed=document.getElementById('pipe-editor');
  if(ed) ed.style.display='none';
  if(l) l.style.display='block';
}
function openConfirmAction(title, msg, label){
  var t=document.getElementById('confirm-action-title'); if(t) t.textContent=title||'Confirmar';
  var m=document.getElementById('confirm-action-msg'); if(m) m.textContent=msg||'';
  var b=document.getElementById('confirm-action-btn'); if(b) b.textContent=label||'Confirmar';
  if(typeof openModal==='function') openModal('confirm-action');
}


/* ----------------------------------------------------------
   Pipeline do cliente — bloqueio, visibilidade e exclusão de etapa
   O admin decide o que fica travado em cada cliente: o cadeado
   comanda arraste, edição, ocultação e exclusão da etapa.
   ---------------------------------------------------------- */
function _stageIcon(el, name) {
  if (!el) return;
  el.innerHTML = '';
  var i = document.createElement('i');
  i.setAttribute('data-lucide', name);
  i.style.width = '14px'; i.style.height = '14px';
  el.appendChild(i);
  if (window.lucide) lucide.createIcons({ nodes: [i] });
}

function _stageBadge(text, color, bg) {
  return '<span style="display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;color:' +
    color + ';background:' + bg + ';white-space:nowrap;">' + text + '</span>';
}

function _stageRefresh(row) {
  var locked = row.dataset.locked === '1';
  var hidden = row.dataset.hidden === '1';
  var kind = row.dataset.kind;
  var name = row.dataset.stage;

  var lockBtn = row.querySelector('[data-role="lock"]');
  if (lockBtn) {
    _stageIcon(lockBtn, locked ? 'lock' : 'lock-open');
    var ic = lockBtn.querySelector('i');
    if (ic) { ic.style.width = '13px'; ic.style.height = '13px'; ic.style.color = locked ? '#C74446' : '#9CA3AF'; }
    lockBtn.style.borderColor = locked ? '#F0D2D2' : '#E5E7EB';
    lockBtn.style.background = locked ? 'rgba(199,68,70,0.06)' : 'white';
    lockBtn.title = locked
      ? 'Etapa travada. Clique para liberar renomear, arrastar, ocultar e excluir.'
      : 'Etapa livre. Clique para travar.';
  }

  var grip = row.querySelector('[data-role="grip"]');
  if (grip) grip.style.visibility = locked ? 'hidden' : 'visible';
  if (locked) row.removeAttribute('draggable'); else row.setAttribute('draggable', 'true');

  var lockBadge = row.querySelector('[data-role="lock-badge"]');
  if (lockBadge) lockBadge.innerHTML = locked
    ? _stageBadge('Travada', '#C74446', 'rgba(199,68,70,0.10)')
    : _stageBadge('Livre', '#5DA47A', 'rgba(93,164,122,0.12)');

  var hiddenBadge = row.querySelector('[data-role="hidden-badge"]');
  if (hiddenBadge) hiddenBadge.style.display = hidden ? 'inline' : 'none';

  var hideBtn = row.querySelector('[data-role="hide"]');
  if (hideBtn) {
    _stageIcon(hideBtn, hidden ? 'eye' : 'eye-off');
    hideBtn.disabled = locked && !hidden;
    hideBtn.style.opacity = hideBtn.disabled ? '0.35' : '';
    hideBtn.style.cursor = hideBtn.disabled ? 'not-allowed' : 'pointer';
    hideBtn.title = hidden
      ? 'Reexibir etapa no processo'
      : (locked ? 'Etapa travada não pode ser ocultada' : 'Ocultar etapa do processo, sem apagar o histórico');
  }

  var delBtn = row.querySelector('[data-role="del"]');
  if (delBtn) {
    delBtn.disabled = locked;
    delBtn.style.opacity = locked ? '0.35' : '';
    delBtn.style.cursor = locked ? 'not-allowed' : 'pointer';
    delBtn.title = locked ? 'Etapa travada não pode ser excluída' : 'Excluir etapa';
    delBtn.setAttribute('onclick', "openStageDelete('" + name + "','" + kind + "')");
  }

  row.style.opacity = hidden ? '0.55' : '';
  row.style.background = hidden ? '#FAFAFA' : 'white';
}

function toggleStageLock(btn) {
  var row = btn.closest('.dnd-row');
  if (!row) return;
  row.dataset.locked = row.dataset.locked === '1' ? '0' : '1';
  _stageRefresh(row);
}

function toggleStageHidden(btn) {
  var row = btn.closest('.dnd-row');
  if (!row || btn.disabled) return;
  row.dataset.hidden = row.dataset.hidden === '1' ? '0' : '1';
  _stageRefresh(row);
  _stageHiddenCount();
  var cb = document.getElementById('pipe-show-hidden');
  if (cb) toggleHiddenStages(cb);
}

function _stageHiddenCount() {
  var list = document.getElementById('pipeline-stages');
  var el = document.getElementById('pipe-hidden-count');
  if (!list || !el) return;
  var n = list.querySelectorAll('.dnd-row[data-hidden="1"]').length;
  el.textContent = '(' + n + ')';
}

function toggleHiddenStages(cb) {
  var list = document.getElementById('pipeline-stages');
  if (!list) return;
  list.querySelectorAll('.dnd-row[data-hidden="1"]').forEach(function (row) {
    row.style.display = cb.checked ? '' : 'none';
  });
}

/* Etapa estrutural exclui igual, mas com aviso reforçado do que ela ancora. */
var STAGE_DELETE_WARNINGS = {
  system: 'Esta é a etapa de <strong>Triagem</strong>: ela ancora a triagem automática da LIA e é onde entram as candidaturas vindas do site. Sem ela, o candidato passa a entrar na primeira etapa do pipeline.',
  standard: 'Esta é uma etapa <strong>estrutural</strong> do processo. Relatórios e contadores que a usam como referência passam a mostrar zero para este cliente.'
};

function openStageDelete(name, kind) {
  var n = document.getElementById('stage-delete-name');
  if (n) n.textContent = name || 'esta etapa';
  var box = document.getElementById('stage-delete-warning');
  var txt = document.getElementById('stage-delete-warning-text');
  var warning = STAGE_DELETE_WARNINGS[kind];
  if (box) box.style.display = warning ? 'block' : 'none';
  if (txt) txt.innerHTML = warning || '';
  if (typeof openModal === 'function') openModal('stage-delete');
  if (window.lucide) lucide.createIcons();
}

document.addEventListener('DOMContentLoaded', _stageHiddenCount);

/* ----------------------------------------------------------
   Acesso Assistido: abertura da sessão e histórico
   O acesso é total: a contenção é o registro, a confirmação
   em ação irreversível e o prazo curto da sessão.
   ---------------------------------------------------------- */

// Cada cliente carrega o estado que libera ou barra a abertura:
//   ok        -> pode abrir
//   disabled  -> o cliente desligou o acesso assistido em contrato
//   suspended -> conta suspensa, ninguém entra
// Usuários com acesso global da WeDO nunca entram nesta lista.
const AA_CLIENTS = {
  ifood: {
    name: 'iFood Talentos', initials: 'IF', color: 'var(--lia-brand-primary)', state: 'ok',
    users: [
      { id: 'u-101', name: 'Ana Beatriz Ramos', email: 'ana.ramos@ifoodtalentos.com.br', role: 'admin do cliente' },
      { id: 'u-102', name: 'Carlos Menezes',    email: 'carlos.menezes@ifoodtalentos.com.br', role: 'recrutador' },
      { id: 'u-103', name: 'Juliana Torres',    email: 'juliana.torres@ifoodtalentos.com.br', role: 'recrutadora' },
      { id: 'u-104', name: 'Pedro Sales',       email: 'pedro.sales@ifoodtalentos.com.br', role: 'recrutador' }
    ]
  },
  nubank: {
    name: 'Nubank Recrutamento', initials: 'NR', color: 'var(--wedo-cyan)', state: 'ok',
    users: [
      { id: 'u-201', name: 'Fernanda Lima', email: 'fernanda.lima@nubankrecrutamento.com.br', role: 'admin do cliente' },
      { id: 'u-202', name: 'Diego Barros',  email: 'diego.barros@nubankrecrutamento.com.br', role: 'recrutador' }
    ]
  },
  vega: {
    name: 'Vega Recruit', initials: 'VG', color: 'var(--wedo-orange)', state: 'disabled',
    blockedTitle: 'Acesso assistido desligado para este cliente',
    blockedText: 'Vega Recruit exigiu autorização prévia em contrato e mantém o acesso assistido desligado. Para abrir uma sessão, o cliente precisa religar a chave nas configurações da conta.',
    users: []
  },
  globalhire: {
    name: 'GlobalHire Co.', initials: 'GH', color: 'var(--lia-text-tertiary)', state: 'suspended',
    blockedTitle: 'Conta suspensa',
    blockedText: 'GlobalHire Co. está com a conta suspensa desde março de 2026. Nenhuma sessão pode ser aberta enquanto a conta não for reativada.',
    users: []
  }
};

let aaClientKey = null;
let aaSelectedUser = null;
let aaDuration = 30;

const AA_REASON_MIN = 10;

function aaOpenModal(clientKey) {
  const client = AA_CLIENTS[clientKey];
  if (!client) return;

  aaClientKey = clientKey;
  aaSelectedUser = null;
  aaDuration = 30;

  const avatar = document.getElementById('aa-client-avatar');
  if (avatar) {
    avatar.textContent = client.initials;
    avatar.style.backgroundColor = client.color;
  }
  const nameEl = document.getElementById('aa-client-name');
  if (nameEl) nameEl.textContent = client.name;

  const blocked = client.state !== 'ok';
  const blockedBox = document.getElementById('aa-blocked');
  const form = document.getElementById('aa-form');
  const opening = document.getElementById('aa-opening');
  const footer = document.getElementById('aa-footer');
  const submit = document.getElementById('aa-submit');

  if (opening) opening.style.display = 'none';
  if (footer) footer.style.display = 'flex';
  if (form) form.style.display = blocked ? 'none' : 'block';
  if (blockedBox) blockedBox.style.display = blocked ? 'flex' : 'none';
  if (submit) submit.style.display = blocked ? 'none' : 'inline-flex';

  if (blocked) {
    const t = document.getElementById('aa-blocked-title');
    const x = document.getElementById('aa-blocked-text');
    if (t) t.textContent = client.blockedTitle;
    if (x) x.textContent = client.blockedText;
  } else {
    const reason = document.getElementById('aa-reason');
    if (reason) reason.value = '';
    const search = document.getElementById('aa-user-search');
    if (search) search.value = '';
    document.querySelectorAll('#aa-duration button').forEach(b => {
      b.classList.toggle('selected', b.textContent.trim() === '30 min');
    });
    aaRenderUsers('');
    aaValidate();
  }

  openModal('assisted-access');
  if (window.lucide) lucide.createIcons();
}

function aaRenderUsers(query) {
  const list = document.getElementById('aa-user-list');
  const client = AA_CLIENTS[aaClientKey];
  if (!list || !client) return;

  const q = (query || '').trim().toLowerCase();
  const users = client.users.filter(u =>
    !q || u.name.toLowerCase().indexOf(q) !== -1 || u.email.toLowerCase().indexOf(q) !== -1
  );

  if (!users.length) {
    list.innerHTML = '<div class="text-sm text-secondary" style="padding:14px 12px; text-align:center;">Nenhum usuário ativo corresponde à busca.</div>';
    return;
  }

  list.innerHTML = users.map(u =>
    '<button type="button" class="aa-user-option' + (aaSelectedUser === u.id ? ' selected' : '') + '"'
    + ' onclick="aaSelectUser(\'' + u.id + '\', this)">'
    + '<span class="avatar avatar-sm" style="background-color:var(--lia-bg-tertiary); color:var(--lia-text-secondary);">'
    + u.name.split(' ')[0].charAt(0) + u.name.split(' ').slice(-1)[0].charAt(0) + '</span>'
    + '<span class="flex-1 min-w-0">'
    + '<span class="block text-base font-medium text-primary truncate">' + u.name + '</span>'
    + '<span class="block text-sm text-secondary truncate">' + u.email + '</span>'
    + '</span>'
    + '<span class="badge badge-gray badge-sm">' + u.role + '</span>'
    + '</button>'
  ).join('');
}

function aaFilterUsers(query) {
  aaRenderUsers(query);
}

function aaSelectUser(userId, el) {
  aaSelectedUser = userId;
  document.querySelectorAll('#aa-user-list .aa-user-option').forEach(b => b.classList.remove('selected'));
  if (el) el.classList.add('selected');
  aaValidate();
}

function aaSetDuration(minutes, btn) {
  aaDuration = minutes;
  document.querySelectorAll('#aa-duration button').forEach(b => b.classList.remove('selected'));
  if (btn) btn.classList.add('selected');
}

function aaValidate() {
  const reason = document.getElementById('aa-reason');
  const counter = document.getElementById('aa-reason-counter');
  const submit = document.getElementById('aa-submit');
  const length = reason ? reason.value.trim().length : 0;
  const reasonOk = length >= AA_REASON_MIN;

  if (counter) {
    counter.textContent = reasonOk
      ? length + ' caracteres'
      : length + '/' + AA_REASON_MIN + ' caracteres';
    counter.classList.toggle('invalid', !reasonOk);
  }
  if (reason) reason.classList.toggle('error', length > 0 && !reasonOk);
  if (submit) submit.disabled = !(reasonOk && aaSelectedUser);
}

function aaSubmit() {
  const form = document.getElementById('aa-form');
  const opening = document.getElementById('aa-opening');
  const footer = document.getElementById('aa-footer');
  if (form) form.style.display = 'none';
  if (footer) footer.style.display = 'none';
  if (opening) opening.style.display = 'block';
}

function aaConfirmRevoke(clientName, adminName) {
  const c = document.getElementById('aa-revoke-client');
  const a = document.getElementById('aa-revoke-admin');
  if (c) c.textContent = clientName;
  if (a) a.textContent = adminName;
  openModal('assisted-revoke');
  if (window.lucide) lucide.createIcons();
}

function aaExport(btn) {
  if (!btn) return;
  const original = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="loader"></i>Gerando arquivo...';
  if (window.lucide) lucide.createIcons({ nodes: [btn] });
  setTimeout(() => {
    btn.innerHTML = original;
    btn.disabled = false;
    if (window.lucide) lucide.createIcons({ nodes: [btn] });
  }, 1600);
}

/* ----------------------------------------------------------
   Acesso Assistido: trilha de ações da sessão
   Ação sensível (irreversível ou visível para terceiro) sai
   em destaque: é o que a auditoria procura primeiro.
   ---------------------------------------------------------- */
const AA_SESSIONS = {
  s1: {
    client: 'iFood Talentos', targetUser: 'Ana Beatriz Ramos', targetRole: 'admin do cliente',
    admin: 'Marina Vasconcelos', status: 'Ativa', statusClass: 'aa-live-tag',
    started: '02/09/2026 14:52', ends: '02/09/2026 15:22', duration: 'em curso',
    reason: 'Cliente relatou que a triagem da LIA não pontua candidatos da vaga de Analista Fiscal.',
    ip: '177.22.4.89',
    actions: [
      { at: '14:52', label: 'Entrou na plataforma do cliente', detail: 'Sessão iniciada como Ana Beatriz Ramos' },
      { at: '14:54', label: 'Abriu a vaga Analista Fiscal Sênior', detail: 'Leitura: não conta como atividade do cliente' },
      { at: '14:57', label: 'Alterou o filtro de triagem da vaga', detail: 'Nota mínima: 7,0 para 6,0' },
      { at: '15:02', label: 'Reenviou convite de entrevista ao candidato', detail: 'Candidato cand-9281 · e-mail entregue', sensitive: 'Comunicação ao candidato' },
      { at: '15:05', label: 'Exportou a lista de candidatos da vaga', detail: '48 candidatos · arquivo CSV', sensitive: 'Exportação de base' }
    ]
  },
  s2: {
    client: 'Nubank Recrutamento', targetUser: 'Diego Barros', targetRole: 'recrutador',
    admin: 'Rafael Antunes', status: 'Ativa', statusClass: 'aa-live-tag',
    started: '02/09/2026 15:04', ends: '02/09/2026 15:19', duration: 'em curso',
    reason: 'Investigar o erro ao publicar vaga relatado no chamado 4821.',
    ip: '191.5.88.201',
    actions: [
      { at: '15:04', label: 'Entrou na plataforma do cliente', detail: 'Sessão iniciada como Diego Barros' },
      { at: '15:06', label: 'Abriu o formulário da vaga Engenheiro de Dados', detail: 'Leitura: não conta como atividade do cliente' },
      { at: '15:09', label: 'Publicou a vaga Engenheiro de Dados', detail: 'Vaga visível no site de carreiras', sensitive: 'Publicação de vaga' }
    ]
  },
  s3: {
    client: 'TechAlpha Ltda', targetUser: 'Marcos Vinícius Aguiar', targetRole: 'admin do cliente',
    admin: 'Camila Prado', status: 'Encerrada', statusClass: 'badge badge-gray',
    started: '02/09/2026 11:18', ends: '02/09/2026 11:30', duration: '12 min (saída pelo botão)',
    reason: 'Conferir o mapeamento de etapas do processo seletivo junto com o cliente.',
    ip: '201.44.10.7',
    actions: [
      { at: '11:18', label: 'Entrou na plataforma do cliente', detail: 'Sessão iniciada como Marcos Vinícius Aguiar' },
      { at: '11:21', label: 'Abriu o editor do processo seletivo', detail: 'Leitura: não conta como atividade do cliente' },
      { at: '11:26', label: 'Renomeou a etapa Entrevista Técnica', detail: 'Novo nome: Entrevista Técnica (time de dados)' },
      { at: '11:30', label: 'Saiu do acesso assistido', detail: 'Encerramento manual' }
    ]
  },
  s4: {
    client: 'RH Solutions', targetUser: 'Letícia Furtado', targetRole: 'recrutadora',
    admin: 'Marina Vasconcelos', status: 'Expirada', statusClass: 'badge badge-yellow',
    started: '01/09/2026 17:40', ends: '01/09/2026 18:10', duration: '30 min (prazo esgotado)',
    reason: 'Validar o envio de WhatsApp depois da mudança de template.',
    ip: '177.22.4.89',
    actions: [
      { at: '17:40', label: 'Entrou na plataforma do cliente', detail: 'Sessão iniciada como Letícia Furtado' },
      { at: '17:44', label: 'Abriu a triagem por WhatsApp da vaga Consultor Comercial', detail: 'Leitura: não conta como atividade do cliente' },
      { at: '17:52', label: 'Enviou mensagem de WhatsApp ao candidato', detail: 'Candidato cand-7734 · template de convite', sensitive: 'Comunicação ao candidato' },
      { at: '18:10', label: 'Sessão expirada pelo prazo', detail: 'Encerramento automático, sem ação do operador' }
    ]
  },
  s5: {
    client: 'iFood Talentos', targetUser: 'Carlos Menezes', targetRole: 'recrutador',
    admin: 'Rafael Antunes', status: 'Revogada', statusClass: 'badge badge-red',
    started: '01/09/2026 09:12', ends: '01/09/2026 09:16', duration: '4 min (revogada por Camila Prado)',
    reason: 'Reproduzir a falha do funil relatada por telefone.',
    ip: '191.5.88.201',
    actions: [
      { at: '09:12', label: 'Entrou na plataforma do cliente', detail: 'Sessão iniciada como Carlos Menezes' },
      { at: '09:14', label: 'Abriu o funil de talentos', detail: 'Leitura: não conta como atividade do cliente' },
      { at: '09:16', label: 'Sessão revogada pelo painel interno', detail: 'Revogada por Camila Prado: acesso aberto na conta errada' }
    ]
  },
  s6: {
    client: 'Nubank Recrutamento', targetUser: 'Fernanda Lima', targetRole: 'admin do cliente',
    admin: 'Camila Prado', status: 'Encerrada', statusClass: 'badge badge-gray',
    started: '29/08/2026 16:03', ends: '29/08/2026 16:25', duration: '22 min (saída pelo botão)',
    reason: 'Ajustar a configuração de triagem junto com o cliente durante a reunião.',
    ip: '201.44.10.7',
    actions: [
      { at: '16:03', label: 'Entrou na plataforma do cliente', detail: 'Sessão iniciada como Fernanda Lima' },
      { at: '16:08', label: 'Alterou o peso das competências na triagem', detail: 'Competências técnicas: 40% para 55%' },
      { at: '16:19', label: 'Reprovou candidato no processo', detail: 'Candidato cand-5512 · motivo: fora do perfil', sensitive: 'Desfecho de candidato' },
      { at: '16:25', label: 'Saiu do acesso assistido', detail: 'Encerramento manual' }
    ]
  }
};

function aaDetailRow(label, value) {
  return '<div style="display:flex; gap:12px; padding:10px 0; border-top:1px solid var(--lia-border-subtle);">'
    + '<div style="flex:0 0 130px;" class="text-sm text-secondary">' + label + '</div>'
    + '<div class="flex-1 text-base text-primary" style="word-break:break-word;">' + value + '</div>'
    + '</div>';
}

function aaOpenDetail(sessionId) {
  const drawer = document.getElementById('assisted-drawer');
  const content = document.getElementById('assisted-drawer-content');
  const session = AA_SESSIONS[sessionId];
  if (!drawer || !content || !session) return;

  const isLive = session.status === 'Ativa';
  const statusHtml = isLive
    ? '<span class="aa-live-tag"><span class="aa-live-pulse"></span>Ativa</span>'
    : '<span class="' + session.statusClass + '">' + session.status + '</span>';

  const sensitiveCount = session.actions.filter(a => a.sensitive).length;

  let html = '';

  html += '<div class="flex items-center gap-8 mb-4 flex-wrap">'
    + '<span class="text-md font-semibold text-primary">' + session.client + '</span>'
    + statusHtml
    + '</div>';
  html += '<div class="text-sm text-secondary mb-16">'
    + session.admin + ' (WeDO) atuando como ' + session.targetUser
    + '</div>';

  html += '<div class="aa-callout mb-16">'
    + '<i data-lucide="quote"></i>'
    + '<div><strong>Motivo informado na abertura</strong><div class="mt-4">' + session.reason + '</div></div>'
    + '</div>';

  html += '<div class="mb-20">';
  html += aaDetailRow('Usuário do cliente', session.targetUser + ' <span class="badge badge-gray badge-sm">' + session.targetRole + '</span>');
  html += aaDetailRow('Quem acessou', session.admin + ' <span class="badge badge-gray badge-sm">acesso global WeDO</span>');
  html += aaDetailRow('Início', session.started);
  html += aaDetailRow(isLive ? 'Expira em' : 'Fim', session.ends);
  html += aaDetailRow('Duração', session.duration);
  html += aaDetailRow('IP de origem', '<span class="font-inter text-sm">' + session.ip + '</span>');
  html += '</div>';

  html += '<div class="flex items-center justify-between mb-8">'
    + '<span class="text-base font-semibold text-primary">Ações executadas na sessão</span>'
    + (sensitiveCount
        ? '<span class="aa-badge-sensitive"><i data-lucide="alert-triangle"></i>' + sensitiveCount + ' sensíveis</span>'
        : '')
    + '</div>';

  html += session.actions.map(a =>
    '<div class="aa-action-row' + (a.sensitive ? ' sensitive' : '') + '">'
    + '<div class="font-inter text-sm text-secondary" style="flex:0 0 44px;">' + a.at + '</div>'
    + '<div class="flex-1 min-w-0">'
    + '<div class="text-base ' + (a.sensitive ? 'font-semibold' : 'font-medium') + ' text-primary">' + a.label + '</div>'
    + '<div class="text-sm text-secondary mt-4">' + a.detail + '</div>'
    + (a.sensitive
        ? '<div class="mt-8"><span class="aa-badge-sensitive"><i data-lucide="alert-triangle"></i>' + a.sensitive + '</span></div>'
        : '')
    + '</div>'
    + '</div>'
  ).join('');

  html += '<div class="text-sm text-secondary mt-16" style="line-height:1.6;">'
    + 'Toda ação acima está registrada no nome de ' + session.admin + ', não no nome do usuário do cliente. '
    + 'A leitura de tela durante a sessão não altera notificação, último acesso nem métrica de uso do cliente.'
    + '</div>';

  if (isLive) {
    html += '<button class="btn btn-danger w-full mt-16" onclick="aaConfirmRevoke(\'' + session.client + '\',\'' + session.admin + '\')">'
      + '<i data-lucide="power"></i>Revogar esta sessão</button>';
  }

  content.innerHTML = html;
  if (window.lucide) lucide.createIcons();
  drawer.classList.add('open');
}

function aaCloseDetail() {
  const drawer = document.getElementById('assisted-drawer');
  if (drawer) drawer.classList.remove('open');
}
