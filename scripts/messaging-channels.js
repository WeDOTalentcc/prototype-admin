/* ==========================================================
   Canais de mensagem por cliente — WEDO-4145 e WEDO-4146

   Duas telas:

     screen-client-communication   Comunicação do cliente, com três
                                   abas: Textos (o catálogo do
                                   cliente, e-mail e WhatsApp juntos),
                                   Canais (os números) e Modelos na
                                   Meta (o estado de aprovação, por
                                   conta WABA).
     screen-channels-health        Saúde de todos os canais da
                                   plataforma, por ambiente.

   A regra de escolha do canal espelha o desenho em
   _docs/arquitetura/canais-de-mensagem: o recorte mais específico
   vence (marca e finalidade, marca, finalidade, padrão), e dentro
   dele o papel decide (principal, reserva, excedente). Sem canal,
   nada sai.
   ========================================================== */

const MC_CLIENT = 'iFood Talentos';

const MC_KIND = {
  whatsapp: { texto: 'WhatsApp', icone: 'message-circle', bg: 'rgba(93,164,122,.14)', cor: '#3D7A56' },
  voice:    { texto: 'Voz',      icone: 'phone',          bg: 'rgba(96,190,209,.14)', cor: '#2B7A8C' },
  sms:      { texto: 'SMS',      icone: 'message-square', bg: 'rgba(152,96,209,.14)', cor: '#6D3FA0' },
};

const MC_STATUS = {
  active:       { texto: 'Ativo',             bg: '#DCFCE7', cor: '#166534', icone: 'circle-check' },
  degraded:     { texto: 'Degradado',         bg: '#FEF3C7', cor: '#92400E', icone: 'triangle-alert' },
  provisioning: { texto: 'Em provisionamento', bg: '#DBEAFE', cor: '#1E40AF', icone: 'loader' },
  suspended:    { texto: 'Suspenso',          bg: '#FEE2E2', cor: '#991B1B', icone: 'circle-pause' },
  revoked:      { texto: 'Revogado',          bg: '#F3F4F6', cor: '#6B7280', icone: 'ban' },
};

const MC_QUALITY = {
  high:   { texto: 'Alta',  bg: '#DCFCE7', cor: '#166534' },
  medium: { texto: 'Média', bg: '#FEF3C7', cor: '#92400E' },
  low:    { texto: 'Baixa', bg: '#FEE2E2', cor: '#991B1B' },
};

const MC_ROLE = {
  primary:  { texto: 'Principal', ajuda: 'É o número escolhido para este recorte enquanto estiver ativo.' },
  standby:  { texto: 'Reserva',   ajuda: 'Fica parado no dia a dia e assume quando o principal é suspenso ou cai abaixo do piso de qualidade.' },
  overflow: { texto: 'Excedente', ajuda: 'Divide a carga quando o principal esgota o limite de envio da janela.' },
};

const MC_PURPOSE = {
  processo:     'Processo seletivo',
  acesso:       'Acesso e códigos',
  notificacoes: 'Avisos',
};

const MC_BRANDS = ['iFood Talentos', 'iFood Pago'];

/* Contas externas do cliente. A aprovação de modelo é por WABA, e não
   por número: os quatro números da conta principal dividem os mesmos
   modelos aprovados. */
const MC_ACCOUNTS = {
  'waba-talentos': { provider: 'meta', nome: 'iFood Talentos', id: '1182••••4410', numeros: 4 },
  'waba-pago':     { provider: 'meta', nome: 'iFood Pago Carreiras', id: '2231••••0087', numeros: 1 },
  'sub-ifood':     { provider: 'twilio', nome: 'Subconta ifood-talentos', id: 'AC9f••••21e4', numeros: 2 },
};

let MC_CHANNELS = [
  {
    id: 'wa-principal', kind: 'whatsapp', provider: 'meta', account: 'waba-talentos',
    phone: '+55 11 4003-1234', displayName: 'iFood Talentos', displayNameStatus: 'Aprovado',
    numberId: '7731••••0192', status: 'active', quality: 'high', trend: 'estável',
    limit: 10000, used: 3412, failed: 9,
    bindings: [{ purpose: null, brand: null, role: 'primary' }],
    credential: 'Cifrada · rotacionada em 01/09/2026 · token de integração do cliente, sem validade',
    history: [
      ['02/09/2026', 'Sistema', 'Limite de envio subiu de 1.000 para 10.000 conversas por dia'],
      ['12/08/2026', 'Rodrigo Alfieri', 'Canal ativado depois da aprovação do nome de exibição'],
    ],
  },
  {
    id: 'wa-volume', kind: 'whatsapp', provider: 'meta', account: 'waba-talentos',
    phone: '+55 11 4003-3456', displayName: 'iFood Talentos', displayNameStatus: 'Aprovado',
    numberId: '7731••••2210', status: 'active', quality: 'high', trend: 'estável',
    limit: 1000, used: 212, failed: 1,
    bindings: [{ purpose: null, brand: null, role: 'overflow', weight: 40 }],
    credential: 'Cifrada · rotacionada em 01/09/2026 · mesmo token da conta principal',
    history: [['05/09/2026', 'Rodrigo Alfieri', 'Adicionado como excedente para os picos de convite de triagem']],
  },
  {
    id: 'wa-reserva', kind: 'whatsapp', provider: 'meta', account: 'waba-talentos',
    phone: '+55 11 4003-9012', displayName: 'iFood Talentos', displayNameStatus: 'Aprovado',
    numberId: '7731••••8841', status: 'active', quality: 'high', trend: 'estável',
    limit: 1000, used: 0, failed: 0,
    bindings: [{ purpose: null, brand: null, role: 'standby' }],
    credential: 'Cifrada · rotacionada em 01/09/2026 · mesmo token da conta principal',
    history: [['12/08/2026', 'Rodrigo Alfieri', 'Adicionado como reserva do número principal']],
  },
  {
    id: 'wa-avisos', kind: 'whatsapp', provider: 'meta', account: 'waba-talentos',
    phone: '+55 11 4003-7777', displayName: 'iFood Talentos Avisos', displayNameStatus: 'Em análise pela Meta',
    numberId: '7731••••5530', status: 'provisioning', quality: null, trend: null,
    limit: 250, used: 0, failed: 0,
    bindings: [{ purpose: 'notificacoes', brand: null, role: 'primary' }],
    credential: 'Cifrada · recebida na autorização de 16/09/2026',
    steps: [
      ['Autorização do cliente na Meta', 'done', '16/09 · pelo painel, sem abrir o Business Manager'],
      ['Verificação do negócio', 'done', 'já verificado na conta principal'],
      ['Registro do número', 'done', '16/09 · código confirmado por SMS'],
      ['Nome de exibição', 'current', 'em análise pela Meta desde 17/09'],
      ['Webhook assinado', 'todo', 'acontece quando o nome for aprovado'],
      ['Catálogo padrão submetido', 'todo', 'nesta conta os modelos já estão aprovados, então só confere'],
    ],
    history: [['16/09/2026', 'Rodrigo Alfieri', 'Provisionamento iniciado para os avisos do processo']],
  },
  {
    id: 'wa-pago', kind: 'whatsapp', provider: 'meta', account: 'waba-pago',
    phone: '+55 11 4003-5678', displayName: 'iFood Pago Carreiras', displayNameStatus: 'Aprovado',
    numberId: '8810••••4127', status: 'active', quality: 'medium', trend: 'caindo',
    limit: 1000, used: 612, failed: 23,
    bindings: [{ purpose: null, brand: 'iFood Pago', role: 'primary' }],
    credential: 'Cifrada · rotacionada em 10/09/2026 · token de integração do cliente, sem validade',
    history: [
      ['15/09/2026', 'Meta (webhook)', 'Qualidade caiu de Alta para Média'],
      ['10/09/2026', 'Jader Ota', 'Canal ativado para as vagas da marca iFood Pago'],
    ],
  },
  {
    id: 'voz-principal', kind: 'voice', provider: 'twilio', account: 'sub-ifood',
    phone: '+55 11 4040-3098', displayName: null, displayNameStatus: null,
    numberId: 'PN4c••••a91f', status: 'active', quality: null, trend: null,
    limit: null, used: 38, failed: 2,
    bindings: [{ purpose: null, brand: null, role: 'primary' }],
    credential: 'Cifrada · auth token da subconta, rotacionado em 01/09/2026',
    history: [['12/08/2026', 'Rodrigo Alfieri', 'Número comprado na subconta com documentação regulatória aprovada']],
  },
  {
    id: 'sms-acesso', kind: 'sms', provider: 'twilio', account: 'sub-ifood',
    phone: '+55 11 4040-7788', displayName: null, displayNameStatus: null,
    numberId: 'PN77••••0c3d', status: 'suspended', quality: null, trend: null,
    limit: null, used: 0, failed: 0,
    bindings: [{ purpose: 'acesso', brand: null, role: 'primary' }],
    credential: 'Cifrada · auth token da subconta, rotacionado em 01/09/2026',
    suspendedReason: 'Suspenso pelo time WeDO: aguardando o registro do remetente de SMS na operadora.',
    history: [['11/09/2026', 'Paulo Moraes', 'Suspendeu: registro do remetente ainda não aprovado pela operadora']],
  },
];

/* Estado de cada texto de WhatsApp na Meta, por conta. O texto vem do
   catálogo; aqui é só a aprovação. */
const MC_META_REJECTED_REASON =
  'Categoria incorreta: a Meta classificou o conteúdo como marketing, porque o texto fala de "novas oportunidades". ' +
  'Reescreva como mensagem do processo em andamento, sem convite a outras vagas, e publique de novo em Textos.';

function mcMetaStatus(account, key) {
  if (account === 'waba-talentos') {
    if (key === 'rejection_feedback') return { s: 'rejected', quando: 'hoje, 09:12' };
    if (key === 'screening_reminder' || key === 'job_reactivated') return { s: 'pending', quando: 'há 3 horas' };
    if (key === 'cadence_followup_whatsapp') return { s: 'not_submitted', quando: '—' };
    return { s: 'approved', quando: 'há 2 horas' };
  }
  if (account === 'waba-pago') {
    if (key === 'rejection_feedback') return { s: 'rejected', quando: 'ontem, 18:40' };
    if (['interview_reminder', 'interview_reminder_urgent', 'offer_deadline_reminder', 'no_show_first',
         'no_show_final', 'job_paused', 'job_reactivated'].includes(key)) return { s: 'pending', quando: 'há 20 horas' };
    if (key === 'cadence_followup_whatsapp') return { s: 'not_submitted', quando: '—' };
    return { s: 'approved', quando: 'há 20 horas' };
  }
  return { s: 'not_submitted', quando: '—' };
}

const MC_META_STATE = {
  approved:      { texto: 'Aprovado',       bg: '#DCFCE7', cor: '#166534' },
  pending:       { texto: 'Em análise',     bg: '#DBEAFE', cor: '#1E40AF' },
  rejected:      { texto: 'Reprovado',      bg: '#FEE2E2', cor: '#991B1B' },
  not_submitted: { texto: 'Não submetido',  bg: '#FEF9C3', cor: '#854D0E' },
};

let mcKindFilter = 'todos';
let mcMetaAccount = 'waba-talentos';
let mcSim = { kind: 'whatsapp', purpose: 'processo', brand: 'iFood Talentos', primaryDown: false, limitOut: false };
let mcWiz = null;
let mcHealthEnv = 'production';
let mcPendingAction = null;

/* ---------------------------------------------------------------- helpers */

function mcEsc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function mcBadge(meta, extra) {
  if (!meta) return '<span style="font-size:12px; color:#9CA3AF;">—</span>';
  return `<span style="display:inline-flex; align-items:center; gap:4px; background:${meta.bg}; color:${meta.cor}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${meta.icone ? `<i data-lucide="${meta.icone}" style="width:11px;height:11px;"></i>` : ''}${mcEsc(meta.texto)}${extra || ''}</span>`;
}

function mcIcons() { if (window.lucide) lucide.createIcons(); }

function mcToast(msg) {
  if (typeof catToast === 'function') catToast(msg);
}

function mcFmt(n) { return n == null ? '—' : n.toLocaleString('pt-BR'); }

function mcBindingLabel(b) {
  const partes = [];
  if (b.brand) partes.push('Marca ' + b.brand);
  if (b.purpose) partes.push(MC_PURPOSE[b.purpose]);
  if (!partes.length) partes.push('Padrão');
  return partes.join(' · ');
}

function mcBindingChip(b) {
  const role = MC_ROLE[b.role];
  const papelCor = b.role === 'primary' ? '#111827' : (b.role === 'standby' ? '#6B7280' : '#2B7A8C');
  return `<span title="${mcEsc(role.ajuda)}" style="display:inline-flex; align-items:center; gap:5px; border:1px solid #E5E7EB; background:#F9FAFB; font-size:11px; color:#374151; padding:2px 8px; border-radius:6px; white-space:nowrap;">
    ${mcEsc(mcBindingLabel(b))}<span style="color:#D1D5DB;">|</span><strong style="color:${papelCor}; font-weight:600;">${role.texto}${b.weight ? ' · peso ' + b.weight : ''}</strong></span>`;
}

function mcLimitBar(c) {
  if (c.limit == null) {
    return `<div style="font-size:12px; color:#374151;">${mcFmt(c.used)} <span style="color:#9CA3AF;">${c.kind === 'voice' ? 'ligações' : 'envios'} em 24h</span></div>
            <div style="font-size:11px; color:#9CA3AF; margin-top:2px;">sem limite da Meta</div>`;
  }
  const pct = Math.min(100, Math.round((c.used / c.limit) * 100));
  const cor = pct >= 90 ? '#DC2626' : pct >= 70 ? '#D97706' : '#5DA47A';
  return `<div style="font-size:12px; color:#374151;">${mcFmt(c.used)} <span style="color:#9CA3AF;">de ${mcFmt(c.limit)}</span></div>
    <div style="height:5px; background:#F3F4F6; border-radius:99px; margin-top:5px; width:120px; overflow:hidden;">
      <div style="height:100%; width:${pct}%; background:${cor}; border-radius:99px;"></div>
    </div>`;
}

/* ------------------------------------------------------ regra de escolha */

/* Espelha Messaging::ChannelResolver. O que o simulador pode forçar é
   o estado do principal, para ver a reserva e o excedente trabalhando. */
function mcResolve(sim) {
  const trilha = [];
  const efetivo = c => {
    const ehPrincipalPadrao = c.bindings.some(b => b.role === 'primary' && !b.purpose && !b.brand)
      || c.bindings.some(b => b.role === 'primary' && b.brand === sim.brand && !b.purpose);
    if (sim.primaryDown && ehPrincipalPadrao && c.kind === sim.kind) return 'suspended';
    return c.status;
  };
  const elegivel = c => c.kind === sim.kind && ['active', 'degraded'].includes(efetivo(c));

  const doTipo = MC_CHANNELS.filter(c => c.kind === sim.kind);
  const foraDaEscolha = doTipo.filter(c => !elegivel(c));
  foraDaEscolha.forEach(c => trilha.push(`${c.phone} fica de fora: está ${MC_STATUS[efetivo(c)].texto.toLowerCase()}.`));

  const vinculos = [];
  MC_CHANNELS.filter(elegivel).forEach(c => c.bindings.forEach(b => vinculos.push({ c, b })));

  const niveis = [
    ['marca e finalidade', v => v.b.brand === sim.brand && v.b.purpose === sim.purpose],
    ['marca', v => v.b.brand === sim.brand && !v.b.purpose],
    ['finalidade', v => !v.b.brand && v.b.purpose === sim.purpose],
    ['padrão', v => !v.b.brand && !v.b.purpose],
  ];

  for (const [nome, casa] of niveis) {
    const grupo = vinculos.filter(casa);
    if (!grupo.length) { trilha.push(`Nenhum vínculo por ${nome}.`); continue; }
    trilha.push(`Recorte por ${nome}: ${grupo.length} ${grupo.length === 1 ? 'número elegível' : 'números elegíveis'}.`);

    const principal = grupo.find(v => v.b.role === 'primary');
    const excedente = grupo.filter(v => v.b.role === 'overflow');
    const reserva = grupo.find(v => v.b.role === 'standby');

    if (principal && sim.limitOut && excedente.length) {
      trilha.push(`O principal ${principal.c.phone} esgotou o limite da janela: o excedente divide a carga.`);
      return { canal: excedente[0].c, papel: 'overflow', nivel: nome, trilha };
    }
    if (principal) {
      if (sim.limitOut) trilha.push('O principal esgotou o limite, mas não há excedente neste recorte: segue no principal, respeitando o ritmo.');
      return { canal: principal.c, papel: 'primary', nivel: nome, trilha };
    }
    if (reserva) {
      trilha.push('Sem principal elegível neste recorte: a reserva assume.');
      return { canal: reserva.c, papel: 'standby', nivel: nome, trilha };
    }
    if (excedente.length) {
      trilha.push('Sem principal e sem reserva: sai pelo excedente.');
      return { canal: excedente[0].c, papel: 'overflow', nivel: nome, trilha };
    }
  }
  trilha.push('Nenhum recorte tem número elegível.');
  return { canal: null, trilha };
}

/* ------------------------------------------------------------- navegação */

function commGoTo(aba) {
  if (typeof catClose === 'function') catClose();
  mcCloseDrawer();
  if (typeof setClientContext === 'function' && !selectedClient) setClientContext('ifood');
  if (typeof catScope !== 'undefined') catScope = 'cliente';
  showScreen('screen-client-communication');
  commTab(aba || 'textos');
}

function commTab(aba) {
  switchTab('comm-tabs', aba);
  if (typeof catScope !== 'undefined') catScope = 'cliente';
  if (aba === 'textos' && typeof catRenderScreen === 'function') catRenderScreen();
  if (aba === 'canais') mcRenderChannels();
  if (aba === 'modelos') mcRenderMeta();
  mcRenderTabCounts();
}

function mcRenderTabCounts() {
  const nCanais = document.getElementById('comm-count-canais');
  if (nCanais) nCanais.textContent = MC_CHANNELS.filter(c => c.status !== 'revoked').length;
  const nRep = document.getElementById('comm-count-modelos');
  if (nRep) {
    const rep = mcWhatsappTexts().reduce((n, t) =>
      n + mcMetaAccounts().filter(a => mcMetaStatus(a, t.key).s === 'rejected').length, 0);
    nRep.style.display = rep ? 'inline-block' : 'none';
    nRep.textContent = rep + (rep === 1 ? ' reprovado' : ' reprovados');
  }
}

/* ---------------------------------------------------------- aba: canais */

function mcSetKindFilter(k) { mcKindFilter = k; mcRenderChannels(); }

function mcRenderChannels() {
  const alvo = document.getElementById('mc-canais');
  if (!alvo) return;
  const lista = MC_CHANNELS.filter(c => mcKindFilter === 'todos' || c.kind === mcKindFilter);
  const pill = (k, rot) => {
    const ativo = mcKindFilter === k;
    const n = k === 'todos' ? MC_CHANNELS.length : MC_CHANNELS.filter(c => c.kind === k).length;
    return `<button onclick="mcSetKindFilter('${k}')" style="padding:6px 12px; border-radius:99px; font-size:12px; font-weight:${ativo ? 600 : 500}; cursor:pointer; font-family:inherit; border:1px solid ${ativo ? '#111827' : '#D1D5DB'}; background:${ativo ? '#111827' : 'white'}; color:${ativo ? 'white' : '#374151'};">${rot} <span style="opacity:.6;">${n}</span></button>`;
  };

  alvo.innerHTML = `
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:18px;">
      <div style="display:flex; gap:10px; align-items:flex-start; background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px; padding:12px 14px;">
        <i data-lucide="badge-check" style="width:18px;height:18px;color:#166534;flex-shrink:0;margin-top:1px;"></i>
        <div style="font-size:12.5px; color:#14532D; line-height:1.5;"><strong>Negócio verificado na Meta.</strong> iFood Talentos Ltda, verificado em 02/09/2026. É o que libera a ativação de número novo nas contas deste cliente.</div>
      </div>
      <div style="display:flex; gap:10px; align-items:flex-start; background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px; padding:12px 14px;">
        <i data-lucide="building-2" style="width:18px;height:18px;color:#166534;flex-shrink:0;margin-top:1px;"></i>
        <div style="font-size:12.5px; color:#14532D; line-height:1.5;"><strong>Subconta Twilio ativa.</strong> Documentação regulatória aprovada (CNPJ e endereço no Brasil). Uso e fatura de voz e SMS separados dos outros clientes.</div>
      </div>
    </div>

    <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px; flex-wrap:wrap;">
      <div style="display:flex; gap:6px;">${pill('todos', 'Todos')}${pill('whatsapp', 'WhatsApp')}${pill('voice', 'Voz')}${pill('sms', 'SMS')}</div>
      <button onclick="mcOpenWizard()" style="display:flex; align-items:center; gap:6px; padding:8px 14px; background:#C74446; color:white; border:none; border-radius:8px; font-size:13px; font-weight:600; cursor:pointer; font-family:inherit;" onmouseover="this.style.background='#B23B3D'" onmouseout="this.style.background='#C74446'"><i data-lucide="plus" style="width:14px;height:14px;"></i> Adicionar canal</button>
    </div>

    <div style="background:white; border:1px solid #E5E7EB; border-radius:12px; overflow:hidden; margin-bottom:20px;">
      <table style="width:100%; border-collapse:collapse;">
        <thead><tr style="background:#F9FAFB; border-bottom:1px solid #E5E7EB;">
          <th style="padding:10px 20px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Canal</th>
          <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Usado para</th>
          <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Estado</th>
          <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Qualidade</th>
          <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Últimas 24h</th>
          <th style="padding:10px 20px; text-align:right; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Ações</th>
        </tr></thead>
        <tbody>
          ${lista.length ? lista.map((c, i) => mcChannelRow(c, i)).join('') : `
            <tr><td colspan="6" style="padding:44px 20px; text-align:center;">
              <i data-lucide="radio-tower" style="width:28px;height:28px;color:#D1D5DB;"></i>
              <p style="font-size:13px; color:#6B7280; margin:10px 0 0;">Nenhum canal deste tipo. Sem canal, este cliente não envia por aqui: a plataforma não cai no número de outro cliente.</p>
            </td></tr>`}
        </tbody>
      </table>
    </div>

    ${mcSimulatorHtml()}

    <div style="display:flex; gap:10px; align-items:flex-start; background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:12px 14px; margin-top:20px;">
      <i data-lucide="lock" style="width:15px;height:15px;color:#6B7280;flex-shrink:0;margin-top:2px;"></i>
      <div style="font-size:12px; color:#6B7280; line-height:1.55;">Nenhuma credencial aparece nesta tela: só o estado e a data da última rotação. O token fica cifrado no banco com a chave mestra no KMS, e não vai para log. Toda ação de suspender, reativar ou revogar fica na trilha de auditoria, com autor e data.</div>
    </div>
  `;
  mcIcons();
}

function mcChannelRow(c, i) {
  const k = MC_KIND[c.kind];
  const acc = MC_ACCOUNTS[c.account];
  const st = MC_STATUS[c.status];
  let estado = mcBadge(st);
  if (c.status === 'provisioning' && c.steps) {
    const feitos = c.steps.filter(s => s[1] === 'done').length;
    estado += `<div style="font-size:11px; color:#1E40AF; margin-top:4px;">${feitos} de ${c.steps.length} etapas</div>`;
  }
  if (c.status === 'suspended') estado += `<div style="font-size:11px; color:#991B1B; margin-top:4px; max-width:180px;">aguardando operadora</div>`;
  const q = c.quality ? mcBadge(MC_QUALITY[c.quality]) + (c.trend === 'caindo'
    ? '<div style="display:flex; align-items:center; gap:3px; font-size:11px; color:#92400E; margin-top:4px;"><i data-lucide="trending-down" style="width:12px;height:12px;"></i>caindo</div>' : '')
    : '<span style="font-size:11px; color:#9CA3AF;">não se aplica</span>';

  const acoes = [`<button onclick="event.stopPropagation(); mcOpenDrawer('${c.id}')" style="padding:5px 10px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:12px; color:#374151; cursor:pointer; font-family:inherit; white-space:nowrap;">Detalhes</button>`];

  return `
    <tr onclick="mcOpenDrawer('${c.id}')" style="border-top:1px solid #F3F4F6; cursor:pointer; ${i % 2 ? 'background:#F9FAFB;' : ''} ${c.status === 'revoked' ? 'opacity:.55;' : ''}"
        onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='${i % 2 ? '#F9FAFB' : 'white'}'">
      <td style="padding:13px 20px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <div style="width:32px; height:32px; border-radius:8px; background:${k.bg}; display:flex; align-items:center; justify-content:center; flex-shrink:0;"><i data-lucide="${k.icone}" style="width:16px;height:16px;color:${k.cor};"></i></div>
          <div style="min-width:0;">
            <div style="font-size:13px; font-weight:600; color:#111827; white-space:nowrap;">${mcEsc(c.phone)}</div>
            <div style="font-size:12px; color:#6B7280; margin-top:1px; white-space:nowrap;">${c.displayName ? mcEsc(c.displayName) + ' · ' : ''}${k.texto} · ${c.provider === 'meta' ? 'Meta' : 'Twilio'}</div>
            <div style="font-size:11px; color:#9CA3AF; margin-top:1px; white-space:nowrap;">${mcEsc(acc.nome)}</div>
          </div>
        </div>
      </td>
      <td style="padding:13px 12px;"><div style="display:flex; flex-direction:column; gap:4px; align-items:flex-start;">${c.bindings.map(mcBindingChip).join('')}</div></td>
      <td style="padding:13px 12px;">${estado}</td>
      <td style="padding:13px 12px;">${q}</td>
      <td style="padding:13px 12px;">${mcLimitBar(c)}</td>
      <td style="padding:13px 20px;"><div style="display:flex; gap:6px; justify-content:flex-end;">${acoes.join('')}</div></td>
    </tr>`;
}

/* ------------------------------------------------------------ simulador */

function mcSetSim(campo, valor) { mcSim[campo] = valor; mcRenderSimulator(); }

function mcSimulatorHtml() {
  return `<div id="mc-simulador" style="background:white; border:1px solid #E5E7EB; border-radius:12px; padding:20px 22px;">${mcSimulatorInner()}</div>`;
}

function mcRenderSimulator() {
  const el = document.getElementById('mc-simulador');
  if (!el) return;
  el.innerHTML = mcSimulatorInner();
  mcIcons();
}

function mcSimulatorInner() {
  const r = mcResolve(mcSim);
  const sel = (campo, opcoes) => `<select onchange="mcSetSim('${campo}', this.value)" style="padding:7px 10px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#374151; background:white; font-family:inherit; cursor:pointer;">
      ${opcoes.map(o => `<option value="${o[0]}"${mcSim[campo] === o[0] ? ' selected' : ''}>${o[1]}</option>`).join('')}</select>`;
  const chk = (campo, rot) => `<label style="display:flex; align-items:center; gap:6px; font-size:12px; color:#374151; cursor:pointer;">
      <input type="checkbox" ${mcSim[campo] ? 'checked' : ''} onchange="mcSetSim('${campo}', this.checked)" style="accent-color:#C74446;"> ${rot}</label>`;

  const resultado = r.canal
    ? `<div style="display:flex; align-items:center; gap:12px; background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px; padding:12px 14px;">
         <i data-lucide="send" style="width:18px;height:18px;color:#166534;flex-shrink:0;"></i>
         <div>
           <div style="font-size:13px; color:#14532D;">Sai por <strong>${mcEsc(r.canal.phone)}</strong>${r.canal.displayName ? ' (' + mcEsc(r.canal.displayName) + ')' : ''}</div>
           <div style="font-size:12px; color:#166534; margin-top:2px;">recorte por ${r.nivel} · papel ${MC_ROLE[r.papel].texto.toLowerCase()}</div>
         </div>
       </div>`
    : `<div style="display:flex; align-items:center; gap:12px; background:#FEF2F2; border:1px solid #FECACA; border-radius:10px; padding:12px 14px;">
         <i data-lucide="octagon-x" style="width:18px;height:18px;color:#991B1B;flex-shrink:0;"></i>
         <div>
           <div style="font-size:13px; color:#7F1D1D;"><strong>Nada sai.</strong> Este cliente não tem número elegível para este envio.</div>
           <div style="font-size:12px; color:#991B1B; margin-top:2px;">O pedido fica como falha visível e o monitoramento é avisado. A plataforma não usa o número de outro cliente, nem de outro ambiente.</div>
         </div>
       </div>`;

  return `
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;"><i data-lucide="route" style="width:16px;height:16px;color:#374151;"></i><span style="font-size:14px; font-weight:700; color:#111827;">Qual número sai?</span></div>
    <p style="font-size:12px; color:#6B7280; margin:0 0 14px;">Simula a regra de escolha: o recorte mais específico vence (marca e finalidade, marca, finalidade, padrão), e dentro dele o papel decide.</p>
    <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:12px;">
      ${sel('kind', [['whatsapp', 'WhatsApp'], ['voice', 'Voz'], ['sms', 'SMS']])}
      ${sel('purpose', [['processo', 'Processo seletivo'], ['acesso', 'Acesso e códigos'], ['notificacoes', 'Avisos']])}
      ${sel('brand', MC_BRANDS.map(b => [b, 'Vaga da marca ' + b]))}
      <span style="width:1px; height:22px; background:#E5E7EB; margin:0 4px;"></span>
      ${chk('primaryDown', 'principal suspenso')}
      ${chk('limitOut', 'principal sem limite')}
    </div>
    ${resultado}
    <ol style="margin:12px 0 0; padding-left:18px; display:flex; flex-direction:column; gap:3px;">
      ${r.trilha.map(t => `<li style="font-size:12px; color:#6B7280;">${mcEsc(t)}</li>`).join('')}
    </ol>`;
}

/* --------------------------------------------------------------- gaveta */

function mcOpenDrawer(id, origem) {
  const c = mcFindAny(id);
  if (!c) return;
  const k = MC_KIND[c.kind];
  document.getElementById('mc-drawer-titulo').textContent = c.phone;
  document.getElementById('mc-drawer-sub').innerHTML =
    `<span style="color:${k.cor}; font-weight:600;">${k.texto}</span> · ${c.provider === 'meta' ? 'Meta' : 'Twilio'}${c.client ? ' · ' + mcEsc(c.client) : ''}`;
  document.getElementById('mc-drawer-estado').innerHTML = mcBadge(MC_STATUS[c.status]);
  document.getElementById('mc-drawer-corpo').innerHTML = origem === 'saude' ? mcHealthDrawerBody(c) : mcDrawerBody(c);

  const rodape = document.getElementById('mc-drawer-rodape');
  if (origem === 'saude') {
    rodape.innerHTML = c.client === MC_CLIENT
      ? `<button onclick="commGoTo('canais'); mcOpenDrawer('${c.id}')" style="padding:8px 14px; border:1px solid #D1D5DB; background:white; border-radius:8px; font-size:13px; color:#374151; cursor:pointer; font-family:inherit;">Abrir no cliente</button>`
      : '<span style="font-size:12px; color:#9CA3AF;">As ações ficam na área de Comunicação do cliente.</span>';
  } else {
    const btns = [];
    if (c.status === 'active' || c.status === 'degraded') btns.push(`<button onclick="mcAsk('suspend','${c.id}')" style="padding:8px 14px; border:1px solid #D1D5DB; background:white; border-radius:8px; font-size:13px; color:#374151; cursor:pointer; font-family:inherit;">Suspender</button>`);
    if (c.status === 'suspended') btns.push(`<button onclick="mcAsk('reactivate','${c.id}')" style="padding:8px 14px; border:1px solid #BBF7D0; background:#F0FDF4; border-radius:8px; font-size:13px; color:#166534; cursor:pointer; font-family:inherit;">Reativar</button>`);
    if (c.status !== 'revoked') btns.push(`<button onclick="mcAsk('revoke','${c.id}')" style="padding:8px 14px; border:1px solid #FECACA; background:#FEF2F2; border-radius:8px; font-size:13px; color:#B91C1C; cursor:pointer; font-family:inherit;">Revogar</button>`);
    rodape.innerHTML = btns.join('');
  }

  document.getElementById('mc-drawer').style.transform = 'translateX(0)';
  document.getElementById('mc-drawer-backdrop').style.display = 'block';
  mcIcons();
}

function mcCloseDrawer() {
  const d = document.getElementById('mc-drawer');
  if (!d) return;
  d.style.transform = 'translateX(100%)';
  document.getElementById('mc-drawer-backdrop').style.display = 'none';
}

function mcSection(titulo, corpo) {
  return `<div style="margin-bottom:22px;">
    <div style="font-size:11px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.05em; margin-bottom:10px;">${titulo}</div>${corpo}</div>`;
}

function mcGrid(pares) {
  return `<div style="display:grid; grid-template-columns:150px 1fr; gap:8px 12px; font-size:12.5px;">
    ${pares.map(([a, b]) => `<span style="color:#9CA3AF;">${a}</span><span style="color:#111827;">${b}</span>`).join('')}</div>`;
}

function mcDrawerBody(c) {
  const acc = MC_ACCOUNTS[c.account];
  const partes = [];

  if (c.status === 'suspended' && c.suspendedReason) {
    partes.push(`<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:11px 13px; margin-bottom:18px; font-size:12px; color:#991B1B;">${mcEsc(c.suspendedReason)} Enquanto estiver suspenso, o resolvedor não escolhe este número.</div>`);
  }

  if (c.steps) {
    partes.push(mcSection('Provisionamento', `<div style="display:flex; flex-direction:column; gap:0;">
      ${c.steps.map(([t, s, d], i) => {
        const cor = s === 'done' ? '#166534' : s === 'current' ? '#1E40AF' : '#D1D5DB';
        const icone = s === 'done' ? 'circle-check' : s === 'current' ? 'loader' : 'circle';
        return `<div style="display:flex; gap:10px; align-items:flex-start; padding:7px 0; ${i < c.steps.length - 1 ? 'border-bottom:1px dashed #F3F4F6;' : ''}">
          <i data-lucide="${icone}" style="width:16px;height:16px;color:${cor};flex-shrink:0;margin-top:1px;"></i>
          <div><div style="font-size:12.5px; color:${s === 'todo' ? '#9CA3AF' : '#111827'}; font-weight:${s === 'current' ? 600 : 500};">${mcEsc(t)}</div>
          <div style="font-size:11.5px; color:#6B7280; margin-top:1px;">${mcEsc(d)}</div></div></div>`;
      }).join('')}</div>`));
  }

  partes.push(mcSection('Identificação', mcGrid([
    ['Número', mcEsc(c.phone)],
    ['Nome de exibição', c.displayName ? `${mcEsc(c.displayName)} <span style="color:#6B7280;">· ${mcEsc(c.displayNameStatus)}</span>` : '<span style="color:#9CA3AF;">não se aplica</span>'],
    [c.provider === 'meta' ? 'Conta (WABA)' : 'Subconta', `${mcEsc(acc.nome)} <code style="background:#F3F4F6; padding:1px 5px; border-radius:4px; font-size:11px;">${acc.id}</code>`],
    [c.provider === 'meta' ? 'Phone number ID' : 'Number SID', `<code style="background:#F3F4F6; padding:1px 5px; border-radius:4px; font-size:11px;">${c.numberId}</code>`],
    ['Ambiente', 'Produção · canal dedicado deste cliente'],
  ])));

  partes.push(mcSection('Usado para', `<div style="display:flex; flex-direction:column; gap:8px;">
    ${c.bindings.map(b => `<div style="display:flex; align-items:flex-start; gap:10px;">${mcBindingChip(b)}<span style="font-size:12px; color:#6B7280;">${mcEsc(MC_ROLE[b.role].ajuda)}</span></div>`).join('')}
  </div>`));

  if (c.kind === 'whatsapp') {
    partes.push(mcSection('Saúde', mcGrid([
      ['Qualidade', c.quality ? mcBadge(MC_QUALITY[c.quality]) + (c.trend === 'caindo' ? ' <span style="font-size:12px; color:#92400E;">caindo desde 15/09</span>' : '') : '<span style="color:#9CA3AF;">sai quando o canal ativar</span>'],
      ['Limite de envio', c.limit ? `${mcFmt(c.limit)} conversas por dia` : '—'],
      ['Últimas 24h', `${mcFmt(c.used)} enviadas · ${mcFmt(c.failed)} falhas`],
      ['Modelos aprovados', `os da conta ${mcEsc(acc.nome)} <a href="#" onclick="mcCloseDrawer(); mcMetaAccount='${c.account}'; commTab('modelos'); return false;" style="color:#C74446; font-weight:500;">ver na aba Modelos</a>`],
    ])));
  } else {
    partes.push(mcSection('Saúde', mcGrid([
      ['Últimas 24h', `${mcFmt(c.used)} ${c.kind === 'voice' ? 'ligações' : 'mensagens'} · ${mcFmt(c.failed)} falhas`],
      ['Retorno do candidato', c.kind === 'voice' ? 'ligação de volta roteada por este número para este cliente' : 'SMS de entrada roteado por este número'],
    ])));
  }

  partes.push(mcSection('Credencial', `<div style="display:flex; gap:10px; align-items:flex-start;">
    <i data-lucide="key-round" style="width:15px;height:15px;color:#6B7280;flex-shrink:0;margin-top:2px;"></i>
    <div style="font-size:12.5px; color:#374151;">${mcEsc(c.credential)}<div style="font-size:11.5px; color:#9CA3AF; margin-top:2px;">O valor nunca é exibido. Assinatura de webhook conferida com o segredo deste canal.</div></div></div>`));

  partes.push(mcSection('Histórico', c.history.map(([q, quem, o]) => `
    <div style="display:flex; gap:12px; padding:9px 0; border-bottom:1px solid #F3F4F6;">
      <div style="width:84px; flex-shrink:0; font-size:11px; color:#9CA3AF;">${mcEsc(q)}</div>
      <div><div style="font-size:12px; font-weight:600; color:#111827;">${mcEsc(quem)}</div><div style="font-size:12px; color:#6B7280; margin-top:1px;">${mcEsc(o)}</div></div>
    </div>`).join('')));

  return partes.join('');
}

/* ------------------------------------------------- suspender e revogar */

function mcAsk(acao, id) {
  const c = mcFindAny(id);
  if (!c) return;
  mcPendingAction = { acao, id };
  let titulo, texto, rotulo, cor, exigeCiencia = false;

  if (acao === 'suspend') {
    const eraPrincipal = c.bindings.some(b => b.role === 'primary');
    let quemAssume = '';
    if (eraPrincipal) {
      const b = c.bindings.find(x => x.role === 'primary');
      const sim = { kind: c.kind, purpose: b.purpose || 'processo', brand: b.brand || 'iFood Talentos', primaryDown: false, limitOut: false };
      const antes = c.status;
      c.status = 'suspended';
      const r = mcResolve(sim);
      c.status = antes;
      quemAssume = r.canal
        ? `<div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:10px 12px; font-size:12.5px; color:#14532D; margin-top:12px;">Quem assume: <strong>${mcEsc(r.canal.phone)}</strong> (${MC_ROLE[r.papel].texto.toLowerCase()}, recorte por ${r.nivel}).</div>`
        : `<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:10px 12px; font-size:12.5px; color:#991B1B; margin-top:12px;"><strong>Ninguém assume.</strong> Este cliente para de enviar por ${MC_KIND[c.kind].texto} neste recorte até o número voltar ou outro ser provisionado.</div>`;
    }
    titulo = 'Suspender ' + c.phone + '?';
    texto = `O número sai da escolha automática e para de enviar. As conversas abertas continuam registradas, e dá para reativar depois.${quemAssume}`;
    rotulo = 'Suspender'; cor = '#C74446';
  } else if (acao === 'reactivate') {
    titulo = 'Reativar ' + c.phone + '?';
    texto = 'O número volta para a escolha automática no papel que ele tinha. Confira antes que o motivo da suspensão foi resolvido.';
    rotulo = 'Reativar'; cor = '#166534';
  } else {
    titulo = 'Revogar ' + c.phone + '?';
    const vizinhos = MC_CHANNELS.filter(x => x.account === c.account && x.id !== c.id && x.status !== 'revoked').length;
    const acesso = vizinhos
      ? `O acesso da WeDO à conta ${mcEsc(MC_ACCOUNTS[c.account].nome)} continua, porque ${vizinhos} outro(s) número(s) dela seguem em uso.`
      : `Como é o último número da conta ${mcEsc(MC_ACCOUNTS[c.account].nome)}, o acesso da WeDO a ela${c.provider === 'meta' ? ' na Meta' : ' na Twilio'} também é desligado.`;
    texto = `Revogar interrompe os envios por este número. ${acesso} O histórico de conversas continua guardado.
      <div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:10px 12px; font-size:12.5px; color:#991B1B; margin-top:12px;">Não dá para desfazer. Para voltar a usar este número, é preciso provisionar de novo, e o cliente autoriza de novo.</div>`;
    rotulo = 'Revogar'; cor = '#B91C1C'; exigeCiencia = true;
  }

  document.getElementById('mc-confirm-titulo').textContent = titulo;
  document.getElementById('mc-confirm-texto').innerHTML = texto + (exigeCiencia
    ? `<label style="display:flex; gap:8px; align-items:center; margin-top:14px; font-size:12.5px; color:#374151; cursor:pointer;"><input id="mc-confirm-ciencia" type="checkbox" onchange="mcConfirmToggle()" style="accent-color:#B91C1C;"> Entendo que isto não pode ser desfeito</label>` : '');
  const btn = document.getElementById('mc-confirm-btn');
  btn.textContent = rotulo;
  btn.style.background = cor;
  btn.disabled = exigeCiencia;
  btn.style.opacity = exigeCiencia ? '0.45' : '1';
  btn.style.cursor = exigeCiencia ? 'not-allowed' : 'pointer';
  openModal('mc-confirm');
  mcIcons();
}

function mcConfirmToggle() {
  const ok = document.getElementById('mc-confirm-ciencia').checked;
  const btn = document.getElementById('mc-confirm-btn');
  btn.disabled = !ok;
  btn.style.opacity = ok ? '1' : '0.45';
  btn.style.cursor = ok ? 'pointer' : 'not-allowed';
}

function mcConfirm() {
  if (!mcPendingAction) return;
  const c = mcFindAny(mcPendingAction.id);
  const quem = 'Rodrigo Alfieri';
  if (mcPendingAction.acao === 'suspend') {
    c.status = 'suspended';
    c.suspendedReason = 'Suspenso pelo time WeDO.';
    c.history.unshift(['hoje', quem, 'Suspendeu o canal']);
    mcToast(`${c.phone} suspenso. Ele saiu da escolha automática.`);
  } else if (mcPendingAction.acao === 'reactivate') {
    c.status = 'active';
    c.suspendedReason = null;
    c.history.unshift(['hoje', quem, 'Reativou o canal']);
    mcToast(`${c.phone} reativado.`);
  } else {
    c.status = 'revoked';
    c.history.unshift(['hoje', quem, 'Revogou o canal e o acesso da WeDO à conta']);
    mcToast(`${c.phone} revogado. Os envios por ele pararam; o histórico continua guardado.`);
  }
  mcPendingAction = null;
  closeModal();
  mcCloseDrawer();
  mcRenderChannels();
  mcRenderTabCounts();
  mcRenderHealth();
}

/* ------------------------------------------------- adicionar canal */

function mcOpenWizard() {
  mcWiz = { passo: 1, kind: null, autorizado: false, numero: '+55 11 4040-5521', role: 'primary', purpose: '', brand: '' };
  mcRenderWizard();
  openModal('mc-new');
}

function mcWizSet(campo, valor) { mcWiz[campo] = valor; mcRenderWizard(); }

function mcWizGo(passo) { mcWiz.passo = passo; mcRenderWizard(); }

function mcRenderWizard() {
  const w = mcWiz;
  const passos = ['Tipo', 'Conexão', 'Uso', 'Revisão'];
  document.getElementById('mc-wiz-passos').innerHTML = passos.map((p, i) => {
    const n = i + 1, feito = n < w.passo, atual = n === w.passo;
    return `<div style="display:flex; align-items:center; gap:8px; ${i < passos.length - 1 ? 'flex:1;' : ''}">
      <span style="width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; background:${feito ? '#166534' : atual ? '#C74446' : '#F3F4F6'}; color:${feito || atual ? 'white' : '#9CA3AF'};">${feito ? '✓' : n}</span>
      <span style="font-size:12px; font-weight:${atual ? 600 : 500}; color:${atual ? '#111827' : '#6B7280'};">${p}</span>
      ${i < passos.length - 1 ? '<span style="flex:1; height:1px; background:#E5E7EB; margin:0 6px;"></span>' : ''}
    </div>`;
  }).join('');

  let corpo = '', podeSeguir = true;
  if (w.passo === 1) {
    const opc = (k, titulo, sub) => {
      const ativo = w.kind === k, m = MC_KIND[k];
      return `<button onclick="mcWizSet('kind','${k}')" style="text-align:left; padding:14px; border-radius:10px; cursor:pointer; font-family:inherit; border:${ativo ? '2px solid #C74446' : '1px solid #E5E7EB'}; background:${ativo ? 'rgba(199,68,70,0.03)' : 'white'};">
        <div style="width:30px; height:30px; border-radius:8px; background:${m.bg}; display:flex; align-items:center; justify-content:center; margin-bottom:10px;"><i data-lucide="${m.icone}" style="width:15px;height:15px;color:${m.cor};"></i></div>
        <div style="font-size:13px; font-weight:600; color:#111827;">${titulo}</div>
        <div style="font-size:12px; color:#6B7280; margin-top:3px; line-height:1.45;">${sub}</div></button>`;
    };
    corpo = `<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">
      ${opc('whatsapp', 'WhatsApp', 'Número na conta WABA do cliente, pela Meta')}
      ${opc('voice', 'Voz', 'Número de ligação na subconta Twilio do cliente')}
      ${opc('sms', 'SMS', 'Número de SMS na subconta Twilio do cliente')}
    </div>`;
    podeSeguir = !!w.kind;
  } else if (w.passo === 2 && w.kind === 'whatsapp') {
    corpo = `<p style="font-size:13px; color:#4B5563; line-height:1.55; margin:0 0 14px;">O cliente autoriza pela Meta dentro do painel, sem abrir o Business Manager. A conta e o número continuam sendo dele, e a WeDO recebe um token só desta integração.</p>
      ${w.autorizado
        ? `<div style="display:flex; gap:10px; align-items:flex-start; background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px; padding:12px 14px;">
             <i data-lucide="circle-check" style="width:18px;height:18px;color:#166534;flex-shrink:0;margin-top:1px;"></i>
             <div style="font-size:12.5px; color:#14532D; line-height:1.5;"><strong>Autorizado.</strong> Conta iFood Talentos (1182••••4410), número +55 11 4003-6060. O token foi cifrado e não aparece aqui.</div></div>`
        : `<button onclick="mcWizSet('autorizado', true)" style="display:flex; align-items:center; gap:8px; padding:10px 16px; background:#1877F2; color:white; border:none; border-radius:8px; font-size:13px; font-weight:600; cursor:pointer; font-family:inherit;"><i data-lucide="external-link" style="width:14px;height:14px;"></i> Abrir autorização da Meta</button>
           <p style="font-size:11.5px; color:#9CA3AF; margin:10px 0 0;">Erros conhecidos aparecem aqui em linguagem clara: número já em uso em outro WhatsApp, negócio ainda não verificado, nome de exibição recusado.</p>`}`;
    podeSeguir = w.autorizado;
  } else if (w.passo === 2) {
    const nums = ['+55 11 4040-5521', '+55 11 4040-6612', '+55 11 4040-8830'];
    corpo = `<p style="font-size:13px; color:#4B5563; line-height:1.55; margin:0 0 14px;">O número é comprado dentro da subconta Twilio deste cliente, que já tem a documentação regulatória aprovada. Uso e fatura ficam separados dos outros clientes.</p>
      <div style="display:flex; flex-direction:column; gap:8px;">
        ${nums.map(n => `<label style="display:flex; align-items:center; gap:10px; border:${w.numero === n ? '2px solid #C74446' : '1px solid #E5E7EB'}; border-radius:8px; padding:10px 12px; cursor:pointer;">
          <input type="radio" name="mc-num" ${w.numero === n ? 'checked' : ''} onchange="mcWizSet('numero','${n}')" style="accent-color:#C74446;">
          <span style="font-size:13px; font-weight:600; color:#111827;">${n}</span><span style="font-size:12px; color:#6B7280;">São Paulo · ${w.kind === 'voice' ? 'voz' : 'SMS'}</span></label>`).join('')}
      </div>`;
  } else if (w.passo === 3) {
    const kindAtual = w.kind;
    const sel = (campo, opcoes) => `<select onchange="mcWizSet('${campo}', this.value)" style="width:100%; padding:9px 11px; border:1px solid #D1D5DB; border-radius:8px; font-size:13px; color:#111827; background:white; font-family:inherit;">
        ${opcoes.map(o => `<option value="${o[0]}"${w[campo] === o[0] ? ' selected' : ''}>${o[1]}</option>`).join('')}</select>`;
    const conflito = w.role === 'primary' && MC_CHANNELS.find(c => c.kind === kindAtual && c.status !== 'revoked' &&
      c.bindings.some(b => b.role === 'primary' && (b.purpose || '') === w.purpose && (b.brand || '') === w.brand));
    corpo = `<p style="font-size:13px; color:#4B5563; line-height:1.55; margin:0 0 14px;">Diz para que este número é usado. Deixar finalidade e marca em branco faz dele o padrão do cliente.</p>
      <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-bottom:12px;">
        <div><label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Papel</label>${sel('role', [['primary', 'Principal'], ['standby', 'Reserva'], ['overflow', 'Excedente']])}</div>
        <div><label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Finalidade</label>${sel('purpose', [['', 'Qualquer'], ['processo', 'Processo seletivo'], ['acesso', 'Acesso e códigos'], ['notificacoes', 'Avisos']])}</div>
        <div><label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Marca</label>${sel('brand', [['', 'Qualquer']].concat(MC_BRANDS.map(b => [b, b])))}</div>
      </div>
      <p style="font-size:12px; color:#6B7280; margin:0;">${mcEsc(MC_ROLE[w.role].ajuda)}</p>
      ${conflito ? `<div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:8px; padding:10px 12px; margin-top:12px; font-size:12.5px; color:#92400E;">Já existe um principal para este recorte: <strong>${mcEsc(conflito.phone)}</strong>. Só pode haver um, e o banco recusa o segundo. Escolha reserva ou excedente, ou troque o principal depois de ativar este.</div>` : ''}`;
    podeSeguir = !conflito;
  } else {
    const b = { role: w.role, purpose: w.purpose || null, brand: w.brand || null };
    corpo = `${mcGrid([
        ['Tipo', MC_KIND[w.kind].texto + (w.kind === 'whatsapp' ? ' · Meta' : ' · Twilio')],
        ['Número', w.kind === 'whatsapp' ? '+55 11 4003-6060' : w.numero],
        ['Usado para', mcBindingChip(b)],
      ])}
      <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:8px; padding:11px 13px; margin-top:16px; font-size:12.5px; color:#1E3A8A; line-height:1.55;">
        <strong>O que acontece depois.</strong> O canal nasce em provisionamento e só entra na escolha automática quando estiver ativo.
        ${w.kind === 'whatsapp' ? 'Falta a Meta aprovar o nome de exibição; depois a plataforma assina o webhook e confere o catálogo de modelos da conta.' : 'Falta configurar a URL de atendimento do número e conferir a assinatura do webhook da subconta.'}
      </div>`;
  }

  document.getElementById('mc-wiz-corpo').innerHTML = corpo;
  const voltar = document.getElementById('mc-wiz-voltar');
  voltar.style.visibility = w.passo > 1 ? 'visible' : 'hidden';
  const seguir = document.getElementById('mc-wiz-seguir');
  seguir.textContent = w.passo === 4 ? 'Criar canal' : 'Continuar';
  seguir.disabled = !podeSeguir;
  seguir.style.opacity = podeSeguir ? '1' : '0.45';
  seguir.style.cursor = podeSeguir ? 'pointer' : 'not-allowed';
  mcIcons();
}

function mcWizNext() {
  if (mcWiz.passo < 4) { mcWizGo(mcWiz.passo + 1); return; }
  const w = mcWiz;
  const whats = w.kind === 'whatsapp';
  MC_CHANNELS.push({
    id: 'novo-' + Date.now(), kind: w.kind, provider: whats ? 'meta' : 'twilio',
    account: whats ? 'waba-talentos' : 'sub-ifood',
    phone: whats ? '+55 11 4003-6060' : w.numero,
    displayName: whats ? 'iFood Talentos' : null, displayNameStatus: whats ? 'Em análise pela Meta' : null,
    numberId: whats ? '7731••••6060' : 'PNa1••••77b0', status: 'provisioning', quality: null, trend: null,
    limit: whats ? 250 : null, used: 0, failed: 0,
    bindings: [{ purpose: w.purpose || null, brand: w.brand || null, role: w.role }],
    credential: whats ? 'Cifrada · recebida na autorização de hoje' : 'Cifrada · auth token da subconta',
    steps: whats
      ? [['Autorização do cliente na Meta', 'done', 'hoje'], ['Verificação do negócio', 'done', 'já verificado'],
         ['Registro do número', 'current', 'aguardando o código de confirmação'], ['Nome de exibição', 'todo', ''],
         ['Webhook assinado', 'todo', ''], ['Catálogo padrão submetido', 'todo', '']]
      : [['Número comprado na subconta', 'done', 'hoje'], ['URL de atendimento configurada', 'current', ''],
         ['Assinatura do webhook conferida', 'todo', '']],
    history: [['hoje', 'Rodrigo Alfieri', 'Provisionamento iniciado']],
  });
  closeModal();
  mcKindFilter = 'todos';
  mcRenderChannels();
  mcRenderTabCounts();
  mcToast('Canal criado em provisionamento. Ele entra na escolha automática quando ficar ativo.');
}

/* ------------------------------------------------ aba: modelos na Meta */

function mcWhatsappTexts() {
  return (typeof CATALOGO !== 'undefined' ? CATALOGO : []).filter(t => t.channel === 'whatsapp');
}

/* Cliente sem canal de WhatsApp configurado. E um estado real: enquanto o
   numero nao existe nao ha conta da Meta onde submeter, e oferecer o botao
   "Submeter" ali seria prometer o que nao acontece. Abre com ?conta=nenhuma. */
let mcSemCanal = false;

function mcMetaAccounts() {
  if (mcSemCanal) return [];
  return Object.keys(MC_ACCOUNTS).filter(a => MC_ACCOUNTS[a].provider === 'meta');
}

function mcSetMetaAccount(a) { mcMetaAccount = a; mcRenderMeta(); }

function mcRenderMeta() {
  const alvo = document.getElementById('mc-modelos');
  if (!alvo) return;
  const contas = mcMetaAccounts();
  if (!contas.length) return mcRenderMetaSemConta(alvo);

  const textos = mcWhatsappTexts();
  const linhas = textos.map(t => ({ t, st: mcMetaStatus(mcMetaAccount, t.key) }));
  const conta = (s) => linhas.filter(l => l.st.s === s).length;
  const numerosDaConta = MC_CHANNELS.filter(c => c.account === mcMetaAccount && ['active', 'degraded'].includes(c.status));
  const reprovados = linhas.filter(l => l.st.s === 'rejected');

  const aba = a => {
    const ativo = a === mcMetaAccount, acc = MC_ACCOUNTS[a];
    const rep = textos.filter(t => mcMetaStatus(a, t.key).s === 'rejected').length;
    return `<button onclick="mcSetMetaAccount('${a}')" style="text-align:left; padding:12px 14px; border-radius:10px; cursor:pointer; font-family:inherit; min-width:230px; border:${ativo ? '2px solid #C74446' : '1px solid #E5E7EB'}; background:${ativo ? 'rgba(199,68,70,0.03)' : 'white'};">
      <div style="font-size:13px; font-weight:600; color:#111827;">${mcEsc(acc.nome)}</div>
      <div style="font-size:11.5px; color:#6B7280; margin-top:2px;">WABA ${acc.id} · ${MC_CHANNELS.filter(c => c.account === a).length} número(s)</div>
      ${rep ? `<div style="font-size:11px; color:#991B1B; font-weight:600; margin-top:4px;">${rep} reprovado(s)</div>` : ''}</button>`;
  };

  alvo.innerHTML = `
    <div style="display:flex; gap:10px; align-items:flex-start; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:12px 14px; margin-bottom:18px;">
      <i data-lucide="info" style="width:16px;height:16px;color:#1E40AF;flex-shrink:0;margin-top:1px;"></i>
      <div style="font-size:12.5px; color:#1E3A8A; line-height:1.55;">Aqui se acompanha, não se escreve. O texto de cada comunicação vive em <a href="#" onclick="commTab('textos'); return false;" style="color:#1E40AF; font-weight:600;">Textos</a>; publicar lá submete de novo à Meta. A aprovação é <strong>por conta</strong>, e não por número: os números da mesma conta dividem os mesmos modelos aprovados.</div>
    </div>

    <div style="display:flex; gap:10px; margin-bottom:18px; flex-wrap:wrap;">${contas.map(aba).join('')}</div>

    ${reprovados.length ? `<div style="display:flex; gap:12px; align-items:flex-start; background:#FEF2F2; border:1px solid #FECACA; border-radius:10px; padding:14px 16px; margin-bottom:18px;">
      <i data-lucide="triangle-alert" style="width:18px;height:18px;color:#DC2626;flex-shrink:0;margin-top:1px;"></i>
      <div style="flex:1;"><div style="font-size:13px; font-weight:600; color:#991B1B; margin-bottom:2px;">${reprovados.map(l => mcEsc(l.t.name)).join(', ')} ${reprovados.length === 1 ? 'foi reprovado' : 'foram reprovados'} nesta conta</div>
      <div style="font-size:12.5px; color:#7F1D1D; line-height:1.5;">Fora da janela de 24 horas, esta comunicação não sai por ${numerosDaConta.map(c => mcEsc(c.phone)).join(', ')} até ser aprovada. Dentro da janela, o texto livre continua saindo.</div></div>
      <button onclick="mcOpenModel('${reprovados[0].t.key}')" style="align-self:center; padding:6px 12px; background:white; border:1px solid #FCA5A5; color:#991B1B; border-radius:7px; font-size:12px; font-weight:600; cursor:pointer; font-family:inherit; white-space:nowrap;">Ver motivo</button>
    </div>` : ''}

    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px;">
      ${[['approved', '#166534', 'Aprovados'], ['pending', '#1E40AF', 'Em análise'], ['rejected', '#991B1B', 'Reprovados'], ['not_submitted', '#854D0E', 'Não submetidos']]
        .map(([s, cor, rot]) => `<div style="background:white; border:1px solid #E5E7EB; border-radius:10px; padding:14px 16px;"><div style="font-size:22px; font-weight:700; color:${cor};">${conta(s)}</div><div style="font-size:12px; color:#6B7280; margin-top:2px;">${rot}</div></div>`).join('')}
    </div>

    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <span style="font-size:12px; color:#6B7280;">${linhas.length} comunicações de WhatsApp · limite de 250 modelos por conta, ${linhas.length} em uso</span>
      <button onclick="mcToast('Estado conferido com a Meta. Normalmente o webhook já atualiza sozinho.')" style="display:flex; align-items:center; gap:6px; padding:6px 12px; border:1px solid #D1D5DB; background:white; border-radius:7px; font-size:12px; color:#374151; cursor:pointer; font-family:inherit;"><i data-lucide="refresh-cw" style="width:13px;height:13px;"></i> Conferir com a Meta</button>
    </div>

    <div style="background:white; border:1px solid #E5E7EB; border-radius:12px; overflow:hidden;">
      <table style="width:100%; border-collapse:collapse;">
        <thead><tr style="background:#F9FAFB; border-bottom:1px solid #E5E7EB;">
          <th style="padding:10px 20px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Comunicação</th>
          <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Categoria</th>
          <th style="padding:10px 12px; text-align:center; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Idioma</th>
          <th style="padding:10px 12px; text-align:center; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Estado na Meta</th>
          <th style="padding:10px 12px; text-align:right; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Atualizado</th>
          <th style="padding:10px 20px; text-align:right; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Ações</th>
        </tr></thead>
        <tbody>
          ${linhas.map(({ t, st }, i) => {
            let acao;
            if (st.s === 'rejected') acao = `<button onclick="mcOpenModel('${t.key}')" style="padding:5px 10px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:12px; color:#374151; cursor:pointer; font-family:inherit;">Ver motivo</button><button onclick="mcFixInTexts('${t.key}')" style="padding:5px 10px; border:none; background:#C74446; border-radius:6px; font-size:12px; color:white; font-weight:600; cursor:pointer; font-family:inherit;">Corrigir em Textos</button>`;
            else if (st.s === 'not_submitted') acao = `<button onclick="mcOpenModel('${t.key}')" style="padding:5px 10px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:12px; color:#374151; cursor:pointer; font-family:inherit;">Ver</button><button onclick="mcToast('Submetido à Meta. A aprovação costuma levar de minutos a 24 horas.')" style="padding:5px 10px; border:none; background:#C74446; border-radius:6px; font-size:12px; color:white; font-weight:600; cursor:pointer; font-family:inherit;">Submeter</button>`;
            else if (st.s === 'pending') acao = `<button onclick="mcOpenModel('${t.key}')" style="padding:5px 10px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:12px; color:#374151; cursor:pointer; font-family:inherit;">Ver</button><button disabled title="Aguardando a decisão da Meta" style="padding:5px 10px; border:1px solid #E5E7EB; background:#F9FAFB; border-radius:6px; font-size:12px; color:#9CA3AF; cursor:not-allowed; font-family:inherit;">Aguardando Meta</button>`;
            else acao = `<button onclick="mcOpenModel('${t.key}')" style="padding:5px 10px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:12px; color:#374151; cursor:pointer; font-family:inherit;">Ver</button>`;
            return `<tr style="border-top:1px solid #F3F4F6; ${i % 2 ? 'background:#F9FAFB;' : ''}">
              <td style="padding:12px 20px;"><div style="font-size:13px; font-weight:600; color:#111827;">${mcEsc(t.name)}</div><div style="font-size:11.5px; color:#6B7280; margin-top:2px; font-family:monospace;">${mcEsc(t.key)}</div></td>
              <td style="padding:12px 12px;"><span style="background:#EEF2FF; color:#3730A3; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">Utility</span></td>
              <td style="padding:12px 12px; text-align:center; font-size:12px; color:#374151;">pt_BR</td>
              <td style="padding:12px 12px; text-align:center;">${mcBadge(MC_META_STATE[st.s])}</td>
              <td style="padding:12px 12px; text-align:right; font-size:12px; color:#6B7280; white-space:nowrap;">${mcEsc(st.quando)}</td>
              <td style="padding:12px 20px;"><div style="display:flex; gap:6px; justify-content:flex-end;">${acao}</div></td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;
  mcIcons();
}

/* Sem conta da Meta nao ha o que acompanhar, e o caminho e configurar o canal
   primeiro. A tabela de comunicacoes sairia inteira em "nao submetido", que e
   verdade e nao ajuda: o que falta nao e submeter, e o numero. */
function mcRenderMetaSemConta(alvo) {
  alvo.innerHTML = `
    <div style="display:flex; gap:10px; align-items:flex-start; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:12px 14px; margin-bottom:18px;">
      <i data-lucide="info" style="width:16px;height:16px;color:#1E40AF;flex-shrink:0;margin-top:1px;"></i>
      <div style="font-size:12.5px; color:#1E3A8A; line-height:1.55;">Aqui se acompanha, não se escreve. O texto de cada comunicação vive em <a href="#" onclick="commTab('textos'); return false;" style="color:#1E40AF; font-weight:600;">Textos</a>; publicar lá submete de novo à Meta. A aprovação é <strong>por conta</strong>, e não por número: os números da mesma conta dividem os mesmos modelos aprovados.</div>
    </div>

    <div style="background:white; border:1px solid #E5E7EB; border-radius:12px; padding:44px 20px; text-align:center;">
      <i data-lucide="message-circle-off" style="width:28px;height:28px;color:#D1D5DB;"></i>
      <p style="font-size:14px; font-weight:600; color:#374151; margin:12px 0 0;">Este cliente ainda não tem conta da Meta</p>
      <p style="font-size:12.5px; color:#6B7280; margin:6px auto 0; max-width:520px; line-height:1.6;">A aprovação de modelo é por conta da Meta, então não há onde submeter enquanto o canal de WhatsApp não existir. Sem canal, este cliente não envia por aqui: a plataforma não cai no número de outro cliente.</p>
      <button onclick="commTab('canais')" style="margin-top:16px; padding:8px 16px; border:none; background:#C74446; border-radius:8px; font-size:13px; color:white; font-weight:600; cursor:pointer; font-family:inherit;">Configurar canal</button>
    </div>
  `;
  mcIcons();
}

function mcFixInTexts(key) {
  closeModal();
  commTab('textos');
  if (typeof catOpen !== 'function') return;
  catOpen(key, 'whatsapp');
  const painel = document.getElementById('cat-painel-conteudo');
  if (painel) {
    painel.insertAdjacentHTML('afterbegin', `<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:11px 13px; margin-bottom:16px;">
      <div style="font-size:11px; font-weight:700; color:#991B1B; text-transform:uppercase; letter-spacing:.04em; margin-bottom:4px;">Reprovado pela Meta em ${mcEsc(MC_ACCOUNTS[mcMetaAccount].nome)}</div>
      <div style="font-size:12px; color:#7F1D1D; line-height:1.5;">${mcEsc(MC_META_REJECTED_REASON)}</div></div>`);
  }
}

function mcOpenModel(key) {
  const t = mcWhatsappTexts().find(x => x.key === key);
  if (!t) return;
  const st = mcMetaStatus(mcMetaAccount, key);
  const acc = MC_ACCOUNTS[mcMetaAccount];
  document.getElementById('mc-model-titulo').textContent = t.name;
  document.getElementById('mc-model-corpo').innerHTML = `
    <div style="display:flex; gap:8px; margin-bottom:18px; flex-wrap:wrap;">${mcBadge(MC_META_STATE[st.s])}
      <span style="background:#EEF2FF; color:#3730A3; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">Utility</span>
      <span style="background:#F3F4F6; color:#374151; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">pt_BR</span>
      <span style="background:#F3F4F6; color:#374151; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">${mcEsc(acc.nome)}</span></div>
    ${st.s === 'rejected' ? `<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:10px; padding:14px 16px; margin-bottom:18px;">
      <div style="font-size:11px; font-weight:700; color:#991B1B; text-transform:uppercase; letter-spacing:.04em; margin-bottom:6px;">Motivo da reprovação (Meta)</div>
      <div style="font-size:13px; color:#7F1D1D; line-height:1.5;">${mcEsc(MC_META_REJECTED_REASON)}</div></div>` : ''}
    <div style="font-size:11px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.04em; margin-bottom:8px;">Texto submetido</div>
    ${typeof catWhatsappBubble === 'function' ? catWhatsappBubble(t.body) : ''}
    <div style="display:grid; grid-template-columns:150px 1fr; gap:8px 12px; font-size:12px; margin-top:16px;">
      <span style="color:#9CA3AF;">Nome na Meta</span><code style="background:#F3F4F6; padding:1px 5px; border-radius:4px; width:fit-content;">${mcEsc(t.key)}</code>
      <span style="color:#9CA3AF;">Variáveis</span><span style="color:#374151;">as nomeadas do catálogo viram {{1}}, {{2}}... na ordem em que aparecem</span>
      <span style="color:#9CA3AF;">Por que Utility</span><span style="color:#374151;">mensagem de um processo em andamento; acesso e código seriam Authentication</span>
    </div>`;
  document.getElementById('mc-model-acoes').innerHTML = st.s === 'rejected'
    ? `<button onclick="closeModal()" style="padding:9px 18px; border:1px solid #D1D5DB; background:white; color:#374151; border-radius:8px; font-size:13px; font-weight:500; cursor:pointer; font-family:inherit;">Fechar</button>
       <button onclick="mcFixInTexts('${key}')" style="padding:9px 18px; background:#C74446; color:white; border:none; border-radius:8px; font-size:13px; font-weight:600; cursor:pointer; font-family:inherit;">Corrigir em Textos</button>`
    : `<button onclick="closeModal()" style="padding:9px 18px; border:1px solid #D1D5DB; background:white; color:#374151; border-radius:8px; font-size:13px; font-weight:500; cursor:pointer; font-family:inherit;">Fechar</button>`;
  openModal('mc-model');
  mcIcons();
}

/* Resumo do estado na Meta de um texto de WhatsApp, usado na aba Textos. */
function mcMetaSummary(key) {
  const contas = mcMetaAccounts();
  if (!contas.length) return `<span style="color:#6B7280;">Meta: sem canal configurado</span>`;

  const estados = contas.map(a => mcMetaStatus(a, key).s);
  const rep = estados.filter(s => s === 'rejected').length;
  const pend = estados.filter(s => s === 'pending').length;
  const nao = estados.filter(s => s === 'not_submitted').length;
  if (rep) return `<span style="color:#991B1B; font-weight:600;">Meta: reprovado em ${rep} de ${contas.length} contas</span>`;
  if (nao) return `<span style="color:#854D0E; font-weight:600;">Meta: não submetido</span>`;
  if (pend) return `<span style="color:#1E40AF;">Meta: em análise em ${pend} de ${contas.length}</span>`;
  return `<span style="color:#166534;">Meta: aprovado nas ${contas.length} contas</span>`;
}

function mcMetaAccountsLine(key) {
  return mcMetaAccounts().map(a => {
    const st = mcMetaStatus(a, key);
    return `<div style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #F3F4F6;">
      <span style="font-size:12px; color:#374151;">${mcEsc(MC_ACCOUNTS[a].nome)}</span>${mcBadge(MC_META_STATE[st.s])}</div>`;
  }).join('');
}

function mcMetaAccountCount() {
  return mcMetaAccounts().length;
}

/* -------------------------------------------------- saúde dos canais */

const MC_HEALTH = {
  production: [
    { id: 'wa-principal' }, { id: 'wa-volume' }, { id: 'wa-reserva' }, { id: 'wa-avisos' }, { id: 'wa-pago' }, { id: 'voz-principal' }, { id: 'sms-acesso' },
    { id: 'nb-wa1', client: 'Nubank RH', kind: 'whatsapp', provider: 'meta', phone: '+55 11 3003-4455', displayName: 'Nubank Carreiras',
      status: 'suspended', quality: 'low', trend: 'caindo', limit: 1000, used: 0, failed: 0, changed: 'há 5 horas',
      alert: ['MessagingChannelSuspended', 'A Meta suspendeu o número por qualidade baixa. A reserva +55 11 3003-4466 assumiu.'],
      timeline: [['hoje, 11:02', 'Suspenso pela Meta (qualidade baixa por 7 dias)'], ['12/09', 'Qualidade caiu de Média para Baixa'], ['08/09', 'Qualidade caiu de Alta para Média']] },
    { id: 'nb-wa2', client: 'Nubank RH', kind: 'whatsapp', provider: 'meta', phone: '+55 11 3003-4466', displayName: 'Nubank Carreiras',
      status: 'active', quality: 'high', trend: 'estável', limit: 1000, used: 488, failed: 4, changed: 'há 5 horas',
      timeline: [['hoje, 11:02', 'Assumiu como reserva do número suspenso']] },
    { id: 'ta-wa1', client: 'TechAlpha Ltda', kind: 'whatsapp', provider: 'meta', phone: '+55 21 3500-1200', displayName: 'TechAlpha Talentos',
      status: 'degraded', quality: 'low', trend: 'caindo', limit: 1000, used: 940, failed: 61, changed: 'há 1 dia',
      alert: ['MessagingChannelLimitReduced', 'Limite reduzido de 10.000 para 1.000 conversas por dia depois da queda de qualidade. Está a 94% do limite.'],
      timeline: [['ontem, 16:20', 'Limite reduzido de 10.000 para 1.000'], ['ontem, 16:20', 'Qualidade caiu de Alta para Baixa']] },
    { id: 'ta-voz', client: 'TechAlpha Ltda', kind: 'voice', provider: 'twilio', phone: '+55 21 4042-7700', displayName: null,
      status: 'active', quality: null, limit: null, used: 12, failed: 0, changed: 'há 20 dias', timeline: [] },
    { id: 'rh-wa1', client: 'RH Solutions', kind: 'whatsapp', provider: 'meta', phone: '+55 31 3300-9090', displayName: 'RH Solutions',
      status: 'active', quality: 'high', trend: 'estável', limit: 1000, used: 97, failed: 0, changed: 'há 3 dias',
      alert: ['MessagingChannelTokenExpiring', 'A credencial do canal expira em 6 dias. O cliente precisa autorizar de novo pela Meta.'],
      timeline: [['15/09', 'Aviso de expiração da credencial enviado ao cliente']] },
  ],
  staging: [
    { id: 'stg-wa1', client: 'Plataforma WeDO', boundTo: 'qa_homologacao', kind: 'whatsapp', provider: 'meta', phone: '+55 11 97520-5003',
      displayName: 'WeDO Staging', status: 'active', quality: 'high', trend: 'estável', limit: 1000, used: 64, failed: 2, changed: 'há 2 dias',
      openConversations: 5, busy: 1, timeline: [['16/09', 'Vínculo trocado de e2e_automation para qa_homologacao']] },
    { id: 'stg-voz', client: 'Plataforma WeDO', boundTo: 'qa_homologacao', kind: 'voice', provider: 'twilio', phone: '+55 11 4040-3099',
      displayName: null, status: 'active', quality: null, limit: null, used: 7, failed: 0, changed: 'há 2 dias', openConversations: 1, busy: 0, timeline: [] },
    { id: 'stg-wa2', slot: true, kind: 'whatsapp', phone: '2º número de WhatsApp' },
    { id: 'stg-voz2', slot: true, kind: 'voice', phone: '2º número de voz' },
  ],
  development: [
    { id: 'dev-wa1', client: 'Plataforma WeDO', boundTo: 'e2e_automation', kind: 'whatsapp', provider: 'meta', phone: '+55 11 97000-1100',
      displayName: 'WeDO Dev', status: 'active', quality: 'high', trend: 'estável', limit: 250, used: 38, failed: 5, changed: 'hoje',
      openConversations: 3, busy: 4,
      alert: ['MessagingChannelBusyRejections', '4 envios recusados hoje porque o telefone já tinha conversa aberta com outro tenant neste número. Encerre a conversa antiga ou use o 2º número quando ele existir.'],
      timeline: [['hoje, 10:14', '4 recusas por conversa ocupada']] },
    { id: 'dev-voz', client: 'Plataforma WeDO', boundTo: 'e2e_automation', kind: 'voice', provider: 'twilio', phone: '+55 11 4040-3100',
      displayName: null, status: 'active', quality: null, limit: null, used: 3, failed: 1, changed: 'há 4 dias', openConversations: 0, busy: 0, timeline: [] },
    { id: 'dev-wa2', slot: true, kind: 'whatsapp', phone: '2º número de WhatsApp' },
    { id: 'dev-voz2', slot: true, kind: 'voice', phone: '2º número de voz' },
  ],
};

function mcHealthRows(env) {
  return MC_HEALTH[env].map(h => {
    if (h.slot) return h;
    const base = MC_CHANNELS.find(c => c.id === h.id);
    if (base) {
      return Object.assign({}, base, {
        client: MC_CLIENT, changed: base.history[0] ? base.history[0][0] : '—',
        timeline: base.history.map(([q, , o]) => [q, o]),
        alert: base.id === 'wa-pago' ? ['MessagingChannelQualityDegraded', 'Qualidade caiu de Alta para Média no número da marca iFood Pago.'] : null,
      });
    }
    return h;
  });
}

function mcFindAny(id) {
  const c = MC_CHANNELS.find(x => x.id === id);
  if (c) return c;
  for (const env of Object.keys(MC_HEALTH)) {
    const r = mcHealthRows(env).find(x => x.id === id);
    if (r) return r;
  }
  return null;
}

function mcSetHealthEnv(env) { mcHealthEnv = env; mcRenderHealth(); }

function mcRenderHealth() {
  const alvo = document.getElementById('mc-saude');
  if (!alvo) return;
  const env = mcHealthEnv;
  const compartilhado = env !== 'production';
  const linhas = mcHealthRows(env);
  const reais = linhas.filter(l => !l.slot && l.status !== 'revoked');

  const nAtivos = reais.filter(l => l.status === 'active').length;
  const nAtencao = reais.filter(l => l.status !== 'suspended' && (l.status === 'degraded' || l.quality === 'medium' || l.quality === 'low')).length;
  const nSusp = reais.filter(l => l.status === 'suspended').length;
  const nRep = env === 'production' ? 2 : 0;
  const env24 = reais.reduce((n, l) => n + (l.used || 0), 0);
  const fal24 = reais.reduce((n, l) => n + (l.failed || 0), 0);
  const alertas = linhas.filter(l => l.alert);
  if (env === 'production') alertas.push({ id: 'wa-principal', client: MC_CLIENT, phone: 'Conta iFood Talentos', alert: ['Modelo reprovado', 'Feedback de reprovação foi reprovado pela Meta nas duas contas do cliente. Fora da janela de 24 horas ele não sai.'], modelo: true });

  const seg = (e, rot) => {
    const ativo = env === e;
    return `<button onclick="mcSetHealthEnv('${e}')" style="padding:7px 14px; font-size:12.5px; font-weight:${ativo ? 600 : 500}; border:none; border-radius:7px; cursor:pointer; font-family:inherit; background:${ativo ? 'white' : 'transparent'}; color:${ativo ? '#111827' : '#6B7280'}; ${ativo ? 'box-shadow:0 1px 2px rgba(0,0,0,.08);' : ''}">${rot}</button>`;
  };
  const kpi = (valor, rot, cor, icone) => `<div style="background:white; border:1px solid #E5E7EB; border-radius:10px; padding:14px 16px;">
    <div style="display:flex; align-items:center; justify-content:space-between;"><div style="font-size:22px; font-weight:700; color:${cor};">${valor}</div><i data-lucide="${icone}" style="width:16px;height:16px;color:${cor}; opacity:.7;"></i></div>
    <div style="font-size:12px; color:#6B7280; margin-top:2px;">${rot}</div></div>`;

  alvo.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; flex-wrap:wrap; gap:12px;">
      <div style="display:inline-flex; background:#F3F4F6; border-radius:9px; padding:3px; gap:2px;">
        ${seg('production', 'Produção')}${seg('staging', 'Staging')}${seg('development', 'Desenvolvimento')}
      </div>
      <span style="font-size:12px; color:#9CA3AF;">atualizado há 1 minuto · qualidade e limite vêm do webhook da Meta</span>
    </div>

    ${compartilhado ? `<div style="display:flex; gap:10px; align-items:flex-start; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:12px 14px; margin-bottom:18px;">
      <i data-lucide="share-2" style="width:16px;height:16px;color:#1E40AF;flex-shrink:0;margin-top:1px;"></i>
      <div style="font-size:12.5px; color:#1E3A8A; line-height:1.55;"><strong>Canais compartilhados da plataforma.</strong> Em ${env === 'staging' ? 'staging' : 'desenvolvimento'} os números pertencem à WeDO e ficam amarrados a um tenant de teste por vez. Compartilhar o número não compartilha a conversa: se o mesmo telefone já tem conversa aberta com outro tenant, o envio é recusado. O ambiente começa com um número de cada tipo e tem espaço para o segundo. Em produção, canal compartilhado é recusado pelo banco.</div>
    </div>` : ''}

    <div style="display:grid; grid-template-columns:repeat(6,1fr); gap:12px; margin-bottom:18px;">
      ${kpi(nAtivos, 'Canais ativos', '#166534', 'circle-check')}
      ${kpi(nAtencao, 'Pedem atenção', '#92400E', 'triangle-alert')}
      ${kpi(nSusp, 'Suspensos', '#991B1B', 'circle-pause')}
      ${kpi(nRep, 'Modelos reprovados', '#991B1B', 'file-x')}
      ${kpi(mcFmt(env24), 'Envios em 24h', '#111827', 'send')}
      ${kpi(env24 ? (fal24 / env24 * 100).toFixed(1).replace('.', ',') + '%' : '0%', 'Falhas em 24h', fal24 / Math.max(env24, 1) > 0.03 ? '#991B1B' : '#111827', 'circle-x')}
    </div>

    ${alertas.length ? `<div style="background:white; border:1px solid #E5E7EB; border-radius:12px; padding:16px 18px; margin-bottom:18px;">
      <div style="font-size:14px; font-weight:700; color:#111827; margin-bottom:10px;">Precisa de atenção</div>
      ${alertas.map(a => {
        const grave = /Suspended|Limit|reprovado/i.test(a.alert[0]);
        return `<div onclick="${a.modelo ? "commGoTo('modelos')" : `mcOpenDrawer('${a.id}','saude')`}" style="display:flex; gap:12px; align-items:flex-start; padding:10px 8px; border-top:1px solid #F3F4F6; cursor:pointer; border-radius:6px;" onmouseover="this.style.background='#F9FAFB'" onmouseout="this.style.background='white'">
          <i data-lucide="${grave ? 'octagon-alert' : 'triangle-alert'}" style="width:16px;height:16px;color:${grave ? '#DC2626' : '#D97706'};flex-shrink:0;margin-top:2px;"></i>
          <div style="flex:1;"><div style="font-size:12.5px; color:#111827;"><strong>${mcEsc(a.client)}</strong> · ${mcEsc(a.phone)} <code style="background:#F3F4F6; padding:1px 5px; border-radius:4px; font-size:10.5px; color:#6B7280; margin-left:4px;">${mcEsc(a.alert[0])}</code></div>
          <div style="font-size:12px; color:#6B7280; margin-top:2px;">${mcEsc(a.alert[1])}</div></div>
          <i data-lucide="chevron-right" style="width:14px;height:14px;color:#9CA3AF;margin-top:3px;"></i></div>`;
      }).join('')}
    </div>` : ''}

    <div style="background:white; border:1px solid #E5E7EB; border-radius:12px; overflow:hidden;">
      <table style="width:100%; border-collapse:collapse;">
        <thead><tr style="background:#F9FAFB; border-bottom:1px solid #E5E7EB;">
          <th style="padding:10px 20px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">${compartilhado ? 'Amarrado a' : 'Cliente'}</th>
          <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Canal</th>
          <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Estado</th>
          <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Qualidade</th>
          <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Uso em 24h</th>
          <th style="padding:10px 12px; text-align:right; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">Falhas</th>
          <th style="padding:10px 20px; text-align:right; font-size:11px; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em;">${compartilhado ? 'Conversas' : 'Última mudança'}</th>
        </tr></thead>
        <tbody>${linhas.map((l, i) => mcHealthRow(l, i, compartilhado)).join('')}</tbody>
      </table>
    </div>
  `;
  mcIcons();
}

function mcHealthRow(l, i, compartilhado) {
  const k = MC_KIND[l.kind];
  if (l.slot) {
    return `<tr style="border-top:1px solid #F3F4F6;">
      <td style="padding:12px 20px; font-size:12px; color:#9CA3AF;">—</td>
      <td style="padding:12px 12px;" colspan="6"><div style="display:flex; align-items:center; gap:10px;">
        <div style="width:28px; height:28px; border-radius:7px; border:1px dashed #D1D5DB; display:flex; align-items:center; justify-content:center;"><i data-lucide="${k.icone}" style="width:14px;height:14px;color:#D1D5DB;"></i></div>
        <span style="font-size:12.5px; color:#9CA3AF;">${mcEsc(l.phone)} · não provisionado. Entra quando for preciso simular dois canais no mesmo ambiente.</span></div></td></tr>`;
  }
  const falhaPct = l.used ? (l.failed / l.used) : 0;
  const falha = `<span style="font-size:12px; color:${falhaPct > 0.03 ? '#991B1B' : '#374151'}; font-weight:${falhaPct > 0.03 ? 600 : 400};">${mcFmt(l.failed)}</span>`;
  return `<tr onclick="mcOpenDrawer('${l.id}','saude')" style="border-top:1px solid #F3F4F6; cursor:pointer; ${i % 2 ? 'background:#F9FAFB;' : ''}"
      onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='${i % 2 ? '#F9FAFB' : 'white'}'">
    <td style="padding:12px 20px;">
      ${compartilhado
        ? `<div style="font-size:12.5px; font-weight:600; color:#111827; font-family:monospace;">${mcEsc(l.boundTo)}</div><div style="font-size:11px; color:#9CA3AF; margin-top:2px;">compartilhado · dono: plataforma</div>`
        : `<div style="font-size:13px; font-weight:600; color:#111827;">${mcEsc(l.client)}</div><div style="font-size:11px; color:#9CA3AF; margin-top:2px;">dedicado</div>`}
    </td>
    <td style="padding:12px 12px;"><div style="display:flex; align-items:center; gap:9px;">
      <div style="width:28px; height:28px; border-radius:7px; background:${k.bg}; display:flex; align-items:center; justify-content:center; flex-shrink:0;"><i data-lucide="${k.icone}" style="width:14px;height:14px;color:${k.cor};"></i></div>
      <div><div style="font-size:12.5px; font-weight:600; color:#111827; white-space:nowrap;">${mcEsc(l.phone)}</div><div style="font-size:11px; color:#6B7280;">${l.displayName ? mcEsc(l.displayName) + ' · ' : ''}${k.texto}</div></div></div></td>
    <td style="padding:12px 12px;">${mcBadge(MC_STATUS[l.status])}</td>
    <td style="padding:12px 12px;">${l.quality ? mcBadge(MC_QUALITY[l.quality]) + (l.trend === 'caindo' ? ' <i data-lucide="trending-down" style="width:12px;height:12px;color:#92400E;vertical-align:middle;"></i>' : '') : '<span style="font-size:11px; color:#9CA3AF;">não se aplica</span>'}</td>
    <td style="padding:12px 12px;">${mcLimitBar(l)}</td>
    <td style="padding:12px 12px; text-align:right;">${falha}</td>
    <td style="padding:12px 20px; text-align:right; font-size:11.5px; color:#6B7280; white-space:nowrap;">${compartilhado
      ? `${l.openConversations} abertas${l.busy ? `<div style="color:#92400E; margin-top:2px;">${l.busy} recusa(s) por conversa ocupada</div>` : ''}`
      : mcEsc(l.changed)}</td>
  </tr>`;
}

function mcHealthDrawerBody(l) {
  const partes = [];
  if (l.alert) {
    partes.push(`<div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:8px; padding:11px 13px; margin-bottom:18px;">
      <code style="font-size:11px; color:#92400E; font-weight:600;">${mcEsc(l.alert[0])}</code>
      <div style="font-size:12.5px; color:#78350F; margin-top:4px; line-height:1.5;">${mcEsc(l.alert[1])}</div></div>`);
  }
  partes.push(mcSection('Canal', mcGrid([
    [l.boundTo ? 'Amarrado a' : 'Cliente', l.boundTo ? `<code style="background:#F3F4F6; padding:1px 5px; border-radius:4px;">${mcEsc(l.boundTo)}</code>` : mcEsc(l.client)],
    ['Escopo', l.boundTo ? 'Compartilhado · pertence à plataforma' : 'Dedicado ao cliente'],
    ['Número', mcEsc(l.phone)],
    ['Qualidade', l.quality ? mcBadge(MC_QUALITY[l.quality]) : '<span style="color:#9CA3AF;">não se aplica</span>'],
    ['Limite', l.limit ? `${mcFmt(l.limit)} conversas por dia` : '—'],
    ['Últimas 24h', `${mcFmt(l.used)} envios · ${mcFmt(l.failed)} falhas`],
  ].concat(l.boundTo ? [['Conversas abertas', `${l.openConversations}${l.busy ? ` · ${l.busy} recusa(s) por conversa ocupada hoje` : ''}`]] : []))));
  partes.push(mcSection('Histórico de qualidade e limite', (l.timeline && l.timeline.length ? l.timeline : [['—', 'Sem mudanças recentes']]).map(([q, o]) => `
    <div style="display:flex; gap:12px; padding:9px 0; border-bottom:1px solid #F3F4F6;">
      <div style="width:84px; flex-shrink:0; font-size:11px; color:#9CA3AF;">${mcEsc(q)}</div>
      <div style="font-size:12px; color:#374151;">${mcEsc(o)}</div></div>`).join('')));
  partes.push(`<p style="font-size:11.5px; color:#9CA3AF; margin:0;">Este histórico é o que se mostra ao cliente para explicar o que aconteceu com o número.</p>`);
  return partes.join('');
}

function mcGoHealth() {
  if (typeof clearClientContext === 'function' && selectedClient) clearClientContext();
  showScreen('screen-channels-health');
  mcRenderHealth();
}

/* ------------------------------------------------------------------ init */

document.addEventListener('DOMContentLoaded', () => {
  mcRenderChannels();
  mcRenderMeta();
  mcRenderHealth();
  mcRenderTabCounts();
  try {
    const q = new URLSearchParams(location.search);
    mcSemCanal = q.get('conta') === 'nenhuma';
    if (mcSemCanal) mcRenderMeta();
    const aba = q.get('aba');
    if (aba && location.hash === '#screen-client-communication') commTab(aba);
    if (q.get('ambiente') && location.hash === '#screen-channels-health') mcSetHealthEnv(q.get('ambiente'));
  } catch (e) {}
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') mcCloseDrawer(); });
