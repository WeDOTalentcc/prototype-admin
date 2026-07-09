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
    'screen-client-detail':         'nav-client-overview',
    'screen-client-users':          'nav-client-users',
    'screen-billing':               'nav-billing',
    'screen-llm-config':            'nav-llm-config',
    'screen-lia-persona':           'nav-lia-persona',
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
    'screen-client-detail':         'iFood Talentos',
    'screen-client-users':          'Usuários — iFood Talentos',
    'screen-billing':               'Faturamento — iFood Talentos',
    'screen-llm-config':            'Configuração LLM — iFood Talentos',
    'screen-lia-persona':           'Persona da LIA — iFood Talentos',
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
   Audit Log Drawer
   ---------------------------------------------------------- */
function openDrawer(rowData) {
  const drawer = document.getElementById('audit-drawer');
  const content = document.getElementById('audit-drawer-content');
  if (!drawer || !content) return;
  content.textContent = JSON.stringify(rowData, null, 2);
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
