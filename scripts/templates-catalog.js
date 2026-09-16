/* ==========================================================
   Templates de Comunicação — WEDO-3931

   Duas telas sobre o MESMO conjunto de textos, em escopos diferentes:

     global   Catálogo da WeDO. É o padrão que todo cliente herda.
              Editar aqui alcança na hora todo cliente que não
              ajustou aquela comunicação.
     cliente  Dentro do cliente. Ajusta o texto só para ele. Ao
              salvar, aquela comunicação para de acompanhar o
              padrão até alguém voltar ao padrão.

   No produto a resolução tem três camadas: cliente, catálogo
   global, e o texto do código como última defesa (comunicação
   nova que ainda não tem linha no catálogo).
   ========================================================== */

const CURRENT_CLIENT = 'iFood Talentos';
let catScope = 'cliente';
let catSelected = null;
let catDraft = null;

const catFilterState = {
  global:  { tipo: 'todos', canal: 'todos', categoria: 'todas', origem: 'todas', busca: '' },
  cliente: { tipo: 'todos', canal: 'todos', categoria: 'todas', origem: 'todas', busca: '' },
};

/* Os tres tipos fechados na reuniao de 16/09 com o Paulo e o Jader. */
const CAT_KIND = {
  modal:      { texto: 'Modal',      bg: 'rgba(152,96,209,.14)', cor: '#6D3FA0',
                ajuda: 'O recrutador escolhe este texto na hora de mover o candidato no Kanban.' },
  automatica: { texto: 'Automática', bg: 'rgba(96,190,209,.14)', cor: '#2B7A8C',
                ajuda: 'Dispara sozinha: o recrutador não escolhe, mas o texto é configurável.' },
  alerta:     { texto: 'Alerta',     bg: 'rgba(209,153,96,.16)', cor: '#8A5A20',
                ajuda: 'Notificação da plataforma ao recrutador. Texto único da WeDO: não é personalizado por cliente nesta fase.' },
};

/* Quanto do texto o cliente ja consegue mudar hoje, antes da migracao.
   Responde a divergencia da reuniao: o convite de triagem respeita o config,
   mas so no paragrafo de abertura (custom_message_html, WEDO-3394). */
const CAT_CONFIG_REACH = {
  nenhum:   '<span style="color:#B91C1C;">não alcança nada: o texto vem todo do código</span>',
  abertura: '<span style="color:#9A3412;">alcança só o parágrafo de abertura e o assunto</span>',
  total:    '<span style="color:#166534;">já alcança o corpo inteiro</span>',
};

const CAT_CHANNEL = {
  email:    { texto: 'E-mail',   bg: 'rgba(96,190,209,.14)', cor: '#2B7A8C' },
  whatsapp: { texto: 'WhatsApp', bg: 'rgba(93,164,122,.14)', cor: '#3D7A56' },
};

/* ---------------------------------------------------------------- helpers */

function catEscape(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function catHighlightVariables(s) {
  return catEscape(s).replace(/\{\{(\w+)\}\}/g,
    '<span style="background:rgba(96,190,209,.18); color:#1F6B7D; border-radius:4px; padding:1px 4px; font-weight:600;">{{$1}}</span>');
}

function catEl(suffix, escopo) {
  return document.getElementById('cat-' + suffix + '-' + (escopo || catScope));
}

function catF() { return catFilterState[catScope]; }

/* Quem, no total, deixou de seguir o padrão desta comunicação. */
function catOffDefault(t) {
  return t.otherClients.concat(t.customized ? [CURRENT_CLIENT] : []);
}

/* Texto que vale no escopo aberto. */
function catCurrentText(t) {
  return catScope === 'global'
    ? { subject: t.defaultSubject, body: t.defaultBody }
    : { subject: t.subject, body: t.body };
}

/* --------------------------------------------------------------- listagem */

function catFilteredList() {
  const f = catF();
  const b = f.busca.trim().toLowerCase();
  return CATALOGO.filter(t => {
    if (f.tipo !== 'todos' && t.type !== f.tipo) return false;
    if (f.canal !== 'todos' && t.channel !== f.canal) return false;
    if (f.categoria !== 'todas' && t.category !== f.categoria) return false;
    if (catScope === 'cliente') {
      if (f.origem === 'personalizados' && !t.customized) return false;
      if (f.origem === 'padrao' && t.customized) return false;
    } else {
      if (f.origem === 'personalizados' && !catOffDefault(t).length) return false;
      if (f.origem === 'padrao' && catOffDefault(t).length) return false;
    }
    if (!b) return true;
    return (t.name + ' ' + t.key + ' ' + t.subject + ' ' + t.defaultSubject + ' ' + t.trigger + ' ' + t.source)
      .toLowerCase().includes(b);
  });
}

function catRenderFilters() {
  const f = catF();
  const categorias = [...new Set(CATALOGO.map(t => t.category))].sort();
  const select = (suffix, campo, opcoes) =>
    `<select onchange="catSetFilter('${campo}', this.value)" style="padding:7px 10px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#374151; background:white; font-family:inherit; cursor:pointer;">
       ${opcoes.map(o => `<option value="${o[0]}"${f[campo] === o[0] ? ' selected' : ''}>${o[1]}</option>`).join('')}
     </select>`;
  const tipos = [['todos', 'Todos os tipos'], ['modal', 'Modal'], ['automatica', 'Automática'], ['alerta', 'Alerta']];
  const origens = catScope === 'global'
    ? [['todas', 'Todos'], ['padrao', 'Sem cliente fora do padrão'], ['personalizados', 'Com cliente fora do padrão']]
    : [['todas', 'Padrão e personalizados'], ['padrao', 'Só os que seguem o padrão'], ['personalizados', 'Só os personalizados']];

  catEl('filtros').innerHTML = `
    <div style="position:relative; flex:1; min-width:200px;">
      <i data-lucide="search" style="width:14px;height:14px;position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#9CA3AF;"></i>
      <input id="cat-busca-${catScope}" value="${catEscape(f.busca)}" oninput="catSetFilter('busca', this.value)"
             placeholder="Buscar por nome, assunto ou gatilho"
             style="width:100%; padding:7px 10px 7px 30px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#374151; font-family:inherit;">
    </div>
    ${select('tipo', 'tipo', tipos)}
    ${select('canal', 'canal', [['todos', 'Todos os canais'], ['email', 'E-mail'], ['whatsapp', 'WhatsApp']])}
    ${select('cat', 'categoria', [['todas', 'Todas as categorias']].concat(categorias.map(c => [c, c[0].toUpperCase() + c.slice(1)])))}
    ${select('origem', 'origem', origens)}
  `;
  if (window.lucide) lucide.createIcons();
}

function catSetFilter(campo, valor) {
  catF()[campo] = valor;
  catRenderTable();
  if (campo !== 'busca') catRenderFilters();
}

function catOriginBadge(t) {
  if (catScope === 'global') {
    if (!t.clientEditable) {
      return `<span style="background:rgba(209,153,96,.16); color:#8A5A20; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Não personalizável</span>`;
    }
    const n = catOffDefault(t).length;
    return n
      ? `<span title="${catEscape(catOffDefault(t).join(', '))}" style="background:#FEF3C7; color:#92400E; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${n} fora do padrão</span>`
      : `<span style="background:#DCFCE7; color:#166534; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Todos inheriting</span>`;
  }
  if (!t.clientEditable) {
    return `<span title="Texto único da plataforma" style="background:rgba(209,153,96,.16); color:#8A5A20; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Texto da WeDO</span>`;
  }
  return t.customized
    ? `<span style="background:#FEF3C7; color:#92400E; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Personalizado</span>`
    : `<span style="background:#F3F4F6; color:#6B7280; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Padrão da WeDO</span>`;
}

function catRenderTable() {
  const lista = catFilteredList();
  const corpo = catEl('tbody');
  if (!corpo) return;

  if (catScope === 'global') {
    const n = CATALOGO.filter(t => catOffDefault(t).length).length;
    catEl('contagem').innerHTML = `${lista.length} ${lista.length === 1 ? 'comunicação' : 'comunicações'} · <span style="color:#92400E;">${n} com pelo menos um cliente fora do padrão</span>`;
  } else {
    const n = CATALOGO.filter(t => t.customized).length;
    catEl('contagem').innerHTML = `${lista.length} ${lista.length === 1 ? 'comunicação' : 'comunicações'} · <span style="color:#92400E;">${n} personalizada(s) neste cliente</span>`;
  }

  if (!lista.length) {
    corpo.innerHTML = `<tr><td colspan="5" style="padding:48px 20px; text-align:center;">
      <i data-lucide="search-x" style="width:28px;height:28px;color:#D1D5DB;"></i>
      <p style="font-size:13px; color:#6B7280; margin:10px 0 0 0;">Nenhuma comunicação bate com esse filtro.</p>
      <button onclick="catClearFilters()" style="margin-top:10px; padding:6px 12px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:12px; color:#374151; cursor:pointer; font-family:inherit;">Limpar filtros</button>
    </td></tr>`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  corpo.innerHTML = lista.map((t, i) => {
    const channelMeta = CAT_CHANNEL[t.channel];
    const kindMeta = CAT_KIND[t.type];
    const currentSubject = catScope === 'global' ? t.defaultSubject : t.subject;
    const ultima = catScope === 'global'
      ? (catOffDefault(t).length ? catEscape(catOffDefault(t).join(', ')) : 'nenhum')
      : (t.customized ? catEscape(t.customizedAt) : 'segue o padrão');
    return `
    <tr onclick="catOpen('${t.key}','${t.channel}')" style="border-top:1px solid #F3F4F6; cursor:pointer; ${i % 2 ? 'background:#F9FAFB;' : ''}"
        onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='${i % 2 ? '#F9FAFB' : 'white'}'">
      <td style="padding:13px 20px;">
        <div style="font-size:13px; font-weight:600; color:#111827;">${catEscape(t.name)}</div>
        <div style="font-size:12px; color:#6B7280; margin-top:2px;">${currentSubject ? catEscape(currentSubject) : '<span style="color:#9CA3AF;">mensagem direta, sem assunto</span>'}</div>
      </td>
      <td style="padding:13px 12px;">
        <span title="${catEscape(kindMeta.ajuda)}" style="background:${kindMeta.bg}; color:${kindMeta.cor}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${kindMeta.texto}</span>
        <div style="font-size:11px; color:#6B7280; margin-top:4px;">${channelMeta.texto} · <span style="text-transform:capitalize;">${catEscape(t.audience)}</span></div>
      </td>
      <td style="padding:13px 12px; font-size:12px; color:#6B7280; max-width:280px;">${catEscape(t.trigger)}</td>
      <td style="padding:13px 12px; text-align:center;">${catOriginBadge(t)}</td>
      <td style="padding:13px 20px; text-align:right; font-size:11px; color:#9CA3AF; max-width:180px;">${ultima}</td>
    </tr>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

function catClearFilters() {
  Object.assign(catF(), { tipo: 'todos', canal: 'todos', categoria: 'todas', origem: 'todas', busca: '' });
  catRenderFilters(); catRenderTable();
}

/* --------------------------------------------------------- painel lateral */

function catOpen(chave, canal) {
  catSelected = CATALOGO.find(t => t.key === chave && t.channel === canal);
  if (!catSelected) return;
  catDraft = Object.assign({}, catCurrentText(catSelected));
  document.getElementById('cat-drawer').style.transform = 'translateX(0)';
  document.getElementById('cat-drawer-backdrop').style.display = 'block';
  catRenderDrawer();
  catTab('conteudo');
}

function catClose() {
  const d = document.getElementById('cat-drawer');
  if (!d) return;
  d.style.transform = 'translateX(100%)';
  document.getElementById('cat-drawer-backdrop').style.display = 'none';
  catSelected = null;
}

function catRenderDrawer() {
  const t = catSelected;
  const channelMeta = CAT_CHANNEL[t.channel];
  document.getElementById('cat-drawer-titulo').textContent = t.name;
  document.getElementById('cat-drawer-escopo').innerHTML = catScope === 'global'
    ? '<span style="background:rgba(152,96,209,.14); color:#6D3FA0; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">Padrão da WeDO</span>'
    : `<span style="background:rgba(96,190,209,.14); color:#2B7A8C; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">${catEscape(CURRENT_CLIENT)}</span>`;
  document.getElementById('cat-drawer-sub').innerHTML =
    `<span style="font-family:monospace;">${catEscape(t.key)}</span> ·
     <span style="color:${channelMeta.cor}; font-weight:600;">${channelMeta.texto}</span> ·
     <span style="text-transform:capitalize;">${catEscape(t.audience)}</span>`;
  const btnSalvar = document.getElementById('cat-btn-salvar');
  btnSalvar.textContent = catScope === 'global' ? 'Publicar o padrão' : 'Salvar para este cliente';
  const readOnly = catReadOnly();
  btnSalvar.style.display = readOnly ? 'none' : 'inline-block';
  document.getElementById('cat-btn-descartar').style.display = readOnly ? 'none' : 'inline-block';
  document.getElementById('cat-aba-padrao').style.display =
    (catScope === 'global' || !catSelected.clientEditable) ? 'none' : 'block';
  catRenderContent();
  if (catScope === 'cliente') catRenderDefault();
  catRenderHistory();
}

function catScopeBanner(t) {
  if (catScope === 'cliente' && !t.clientEditable) {
    return `<div style="background:#FFF7ED; border:1px solid #FED7AA; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#9A3412;">
      <strong>Alerta da plataforma, com texto único da WeDO.</strong>
      O Paulo e o Jader decidiram em 16/09 que alerta não é personalizado por cliente nesta fase. Para mudar este texto, edite no catálogo global: a mudança vale para todos.
      ${t.defaultEnabled === false ? ' Este alerta nasce desligado no cliente.' : ''}
    </div>`;
  }
  if (catScope === 'global' && !t.clientEditable) {
    return `<div style="background:#F5F3FF; border:1px solid #DDD6FE; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#5B21B6;">
      <strong>Alerta da plataforma.</strong>
      Texto único: publicar propaga para todos os clientes, e nenhum cliente pode fugir dele nesta fase.
      Alerta nasce desligado em cliente novo, até a copy ser revisada.
    </div>`;
  }
  if (catScope === 'global') {
    const fora = catOffDefault(t);
    const inheriting = 6 - fora.length;
    return `<div style="background:#F5F3FF; border:1px solid #DDD6FE; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#5B21B6;">
      <strong>Você está editando o padrão da WeDO.</strong>
      Publicar propaga para os ${inheriting} cliente(s) que ainda inheriting esta comunicação.
      ${fora.length ? `Não alcança ${catEscape(fora.join(', '))}, que ajustaram o texto por conta.` : 'Nenhum cliente fugiu do padrão nesta comunicação.'}
    </div>`;
  }
  if (t.customized) {
    return `<div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:8px; padding:11px 13px; margin-bottom:16px; display:flex; align-items:center; justify-content:space-between; gap:12px;">
      <div style="font-size:12px; color:#92400E;">
        <strong>Texto personalizado para este cliente.</strong><br>
        Ajustado por ${catEscape(t.customizedBy)} em ${catEscape(t.customizedAt)}. Revisões do padrão da WeDO não chegam mais aqui.
      </div>
      <button onclick="catResetToDefault()" style="padding:6px 11px; border:1px solid #FECACA; background:#FEF2F2; color:#B91C1C; border-radius:6px; font-size:12px; cursor:pointer; font-family:inherit; white-space:nowrap;">Voltar ao padrão</button>
    </div>`;
  }
  return `<div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#6B7280;">
    <strong style="color:#374151;">Segue o padrão da WeDO.</strong>
    Enquanto for assim, este cliente recebe as revisões do padrão sozinho. Se você salvar uma alteração, este cliente passa a ter a versão dele e para de acompanhar o padrão.
  </div>`;
}

function catReadOnly() {
  return catScope === 'cliente' && !catSelected.clientEditable;
}

function catRenderContent() {
  const t = catSelected;
  const readOnly = catReadOnly();
  const vars = t.variables.length ? t.variables : ['candidate_name', 'job_title'];
  document.getElementById('cat-painel-conteudo').innerHTML = `
    ${catScopeBanner(t)}
    ${t.note ? `<div style="background:#FFF7ED; border:1px solid #FED7AA; border-radius:8px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:#9A3412;">${catEscape(t.note)}</div>` : ''}
    ${!t.defaultBody ? `<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:#B91C1C;">O texto desta comunicação não está numa view de e-mail: ele é montado em <code style="background:none;">${catEscape(t.source)}</code>. Precisa ser extraído de lá na migração.</div>` : ''}

    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Assunto</label>
    <input id="cat-in-subject" value="${catEscape(catDraft.subject)}" oninput="catEdit('subject', this.value)"
           ${t.channel === 'whatsapp' ? 'disabled placeholder="WhatsApp não tem assunto"' : (readOnly ? 'disabled' : '')}
           style="width:100%; padding:9px 11px; border:1px solid #D1D5DB; border-radius:8px; font-size:13px; color:#111827; font-family:inherit; margin-bottom:18px; ${(t.channel === 'whatsapp' || readOnly) ? 'background:#F3F4F6; color:#9CA3AF;' : ''}">

    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
      <label style="font-size:12px; font-weight:600; color:#374151;">Corpo da mensagem</label>
      <span style="font-size:11px; color:#9CA3AF;">clique numa variável para inserir no cursor</span>
    </div>
    <div style="display:flex; flex-wrap:wrap; gap:5px; margin-bottom:8px;">
      ${vars.map(v => `<button onclick="catInsertVariable('${v}')" style="padding:3px 8px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:11px; color:#1F6B7D; font-family:monospace; cursor:pointer;" onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='white'">{{${v}}}</button>`).join('')}
    </div>
    <textarea id="cat-in-body" oninput="catEdit('body', this.value)" rows="12" ${readOnly ? 'disabled' : ''}
      style="width:100%; ${readOnly ? 'background:#F3F4F6; color:#6B7280;' : ''} padding:11px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#111827; font-family:inherit; line-height:1.6; resize:vertical;">${catEscape(catDraft.body)}</textarea>

    <div style="margin-top:14px; padding-top:12px; border-top:1px solid #F3F4F6; display:grid; grid-template-columns:110px 1fr; gap:6px 10px; font-size:11px; color:#6B7280;">
      <span style="color:#9CA3AF;">Remetente</span><span><code style="background:#F3F4F6; padding:1px 5px; border-radius:4px;">${catEscape(t.sender)}</code></span>
      <span style="color:#9CA3AF;">Hoje o config</span><span>${CAT_CONFIG_REACH[t.configToday]}</span>
      <span style="color:#9CA3AF;">No código</span><span><code style="background:#F3F4F6; padding:1px 5px; border-radius:4px;">${catEscape(t.source)}</code></span>
    </div>
    ${t.hasText ? `<p style="font-size:11px; color:#9A3412; margin-top:8px;">Esta comunicação também tem versão em texto puro, que precisa acompanhar a edição.</p>` : ''}
  `;
}

function catEdit(campo, valor) {
  catDraft[campo] = valor;
  catRefreshDirty();
  if (document.getElementById('cat-painel-preview').style.display !== 'none') catRenderPreview();
}

function catIsDirty() {
  const currentSubject = catCurrentText(catSelected);
  return catDraft.subject !== currentSubject.subject || catDraft.body !== currentSubject.body;
}

function catRefreshDirty() {
  const sujo = catIsDirty();
  const btn = document.getElementById('cat-btn-salvar');
  btn.disabled = !sujo;
  btn.style.opacity = sujo ? '1' : '0.45';
  btn.style.cursor = sujo ? 'pointer' : 'not-allowed';
  document.getElementById('cat-sujo').style.display = sujo ? 'inline' : 'none';
}

function catInsertVariable(v) {
  const ta = document.getElementById('cat-in-body');
  const start = ta.selectionStart, end = ta.selectionEnd;
  ta.value = ta.value.slice(0, start) + '{{' + v + '}}' + ta.value.slice(end);
  ta.focus();
  ta.selectionStart = ta.selectionEnd = start + v.length + 4;
  catEdit('body', ta.value);
}

function catTab(aba) {
  ['conteudo', 'preview', 'padrao', 'historico'].forEach(a => {
    const painel = document.getElementById('cat-painel-' + a);
    const botao = document.getElementById('cat-aba-' + a);
    const ativo = a === aba;
    painel.style.display = ativo ? 'block' : 'none';
    botao.style.color = ativo ? '#111827' : '#6B7280';
    botao.style.borderBottom = ativo ? '2px solid #C74446' : '2px solid transparent';
    botao.style.fontWeight = ativo ? '600' : '500';
  });
  if (aba === 'preview') catRenderPreview();
}

function catEmailCard(assunto, corpo) {
  const remetente = catScope === 'global' ? 'Empresa do cliente' : CURRENT_CLIENT;
  return `
    <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:20px;">
      <div style="max-width:560px; margin:0 auto; background:#fff; border:1px solid #E5E7EB; border-radius:12px; overflow:hidden;">
        <div style="padding:18px 24px; border-bottom:1px solid #F3F4F6; display:flex; align-items:center; justify-content:space-between;">
          <span style="font-size:13px; font-weight:600; color:#6B7280;">${catEscape(remetente)}</span>
          <span style="width:8px;height:8px;border-radius:50%;background:#60BED1;display:inline-block;"></span>
        </div>
        <div style="padding:22px 24px;">
          <p style="margin:0 0 14px 0; font-size:11px; color:#9CA3AF; text-transform:uppercase; letter-spacing:.05em;">Assunto</p>
          <p style="margin:0 0 18px 0; font-size:15px; font-weight:600; color:#111827;">${catHighlightVariables(assunto) || '<span style="color:#9CA3AF;">sem assunto</span>'}</p>
          <div style="font-size:13px; color:#374151; line-height:1.65;">${catHighlightVariables(corpo).replace(/\n/g, '<br>') || '<span style="color:#9CA3AF;">Sem corpo definido.</span>'}</div>
        </div>
        <div style="background:#0d0d0d; padding:20px 24px;">
          <span style="display:inline-block; background:#1f1f1f; border-radius:4px; padding:6px 10px; font-size:12px; font-weight:700; color:#e5e7eb;">WeDO Talent</span>
          <p style="margin:10px 0 0 0; font-size:11px; color:#9ca3af;">Tecnologia avançada para o RH do futuro.</p>
        </div>
      </div>
    </div>`;
}

function catWhatsappBubble(corpo) {
  return `
    <div style="background:#ECE5DD; border-radius:12px; padding:18px;">
      <div style="background:#fff; border-radius:8px 8px 8px 2px; padding:10px 12px; max-width:85%; box-shadow:0 1px 1px rgba(0,0,0,.08); font-size:13px; color:#111827; line-height:1.5;">
        ${catHighlightVariables(corpo).replace(/\n/g, '<br>') || '<span style="color:#9CA3AF;">Sem corpo definido.</span>'}
        <div style="text-align:right; font-size:10px; color:#9CA3AF; margin-top:4px;">agora</div>
      </div>
    </div>`;
}

function catRenderPreview() {
  const t = catSelected;
  document.getElementById('cat-painel-preview').innerHTML = t.channel === 'whatsapp'
    ? `<p style="font-size:11px; color:#9CA3AF; margin:0 0 10px 0;">como chega no WhatsApp do candidato</p>${catWhatsappBubble(catDraft.body)}`
    : `<p style="font-size:11px; color:#9CA3AF; margin:0 0 10px 0;">como chega na caixa de entrada, dentro do layout do produto</p>${catEmailCard(catDraft.subject, catDraft.body)}`;
}

/* Aba Padrão: só existe dentro do cliente, para comparar com o catálogo. */
function catRenderDefault() {
  const t = catSelected;
  document.getElementById('cat-painel-padrao').innerHTML = `
    <p style="font-size:12px; color:#6B7280; margin:0 0 14px 0;">
      ${t.customized
        ? 'Texto do catálogo da WeDO, para comparar com o que está valendo neste cliente.'
        : 'Este cliente está usando exatamente o texto do catálogo da WeDO.'}
    </p>
    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Assunto padrão</label>
    <div style="padding:9px 11px; border:1px solid #E5E7EB; background:#F9FAFB; border-radius:8px; font-size:13px; color:#374151; margin-bottom:16px;">${catHighlightVariables(t.defaultSubject) || '<span style="color:#9CA3AF;">sem assunto</span>'}</div>
    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Corpo padrão</label>
    <div style="padding:11px; border:1px solid #E5E7EB; background:#F9FAFB; border-radius:8px; font-size:12px; color:#374151; line-height:1.6; white-space:pre-wrap;">${catHighlightVariables(t.defaultBody) || '<span style="color:#9CA3AF;">Sem corpo definido.</span>'}</div>
    ${t.customized ? `<button onclick="catResetToDefault()" style="margin-top:14px; padding:8px 14px; border:1px solid #FECACA; background:#FEF2F2; color:#B91C1C; border-radius:8px; font-size:13px; cursor:pointer; font-family:inherit;">Voltar ao padrão neste cliente</button>` : ''}
  `;
}

function catRenderHistory() {
  const t = catSelected;
  const linhas = catScope === 'global'
    ? [['12/09/2026', 'Paulo Moraes', 'Revisou a copy do padrão'],
       ['16/06/2026', 'Sistema', 'Importado do código na criação do catálogo']]
    : (t.customized
        ? [[t.customizedAt, t.customizedBy, 'Ajustou o texto para este cliente'],
           ['16/06/2026', 'Sistema', 'Cliente provisionado seguindo o padrão da WeDO']]
        : [['16/06/2026', 'Sistema', 'Cliente provisionado seguindo o padrão da WeDO']]);
  document.getElementById('cat-painel-historico').innerHTML = `
    <p style="font-size:12px; color:#6B7280; margin:0 0 14px 0;">Toda alteração fica registrada na trilha de auditoria, com autor e texto anterior.</p>
    ${linhas.map(([q, quem, what]) => `
      <div style="display:flex; gap:12px; padding:11px 0; border-bottom:1px solid #F3F4F6;">
        <div style="width:100px; flex-shrink:0; font-size:11px; color:#9CA3AF;">${catEscape(q)}</div>
        <div>
          <div style="font-size:12px; font-weight:600; color:#111827;">${catEscape(quem)}</div>
          <div style="font-size:12px; color:#6B7280; margin-top:2px;">${catEscape(what)}</div>
        </div>
      </div>`).join('')}`;
}

/* ------------------------------------------------------------------ ações */

function catSave() {
  if (!catIsDirty()) return;
  const t = catSelected;

  if (catScope === 'global') {
    const wasInheriting = !t.customized;
    t.defaultSubject = catDraft.subject;
    t.defaultBody = catDraft.body;
    if (wasInheriting) { t.subject = t.defaultSubject; t.body = t.defaultBody; }
    const fora = catOffDefault(t);
    catToast(`Padrão publicado e propagado para ${6 - fora.length} cliente(s) que ainda inheriting.` +
             (fora.length ? ` ${fora.join(', ')} seguem com o texto próprio.` : ''));
  } else {
    const wasDefault = !t.customized;
    t.subject = catDraft.subject;
    t.body = catDraft.body;
    t.customized = true;
    t.customizedBy = 'Rodrigo Alfieri';
    t.customizedAt = 'hoje';
    catToast(wasDefault
      ? 'Salvo. Este cliente passa a ter a versão dele e não acompanha mais o padrão desta comunicação.'
      : 'Salvo para este cliente.');
  }

  catDraft = Object.assign({}, catCurrentText(t));
  catRenderDrawer();
  catRefreshDirty();
  catRenderTable();
}

function catResetToDefault() {
  const t = catSelected;
  if (!t.customized) return;
  if (!confirm('Voltar ao padrão descarta o texto ajustado para este cliente. Confirmar?')) return;
  t.subject = t.defaultSubject;
  t.body = t.defaultBody;
  t.customized = false;
  t.customizedBy = null;
  t.customizedAt = null;
  catDraft = Object.assign({}, catCurrentText(t));
  catRenderDrawer();
  catRefreshDirty();
  catRenderTable();
  catToast('Voltou ao padrão da WeDO. Este cliente volta a receber as revisões do padrão.');
}

function catDiscard() {
  catDraft = Object.assign({}, catCurrentText(catSelected));
  catRenderContent();
  catRefreshDirty();
}

function catToast(message) {
  const el = document.getElementById('cat-toast');
  el.textContent = message;
  el.style.display = 'block';
  el.style.opacity = '1';
  clearTimeout(window._catToast);
  window._catToast = setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.style.display = 'none', 250); }, 4200);
}

function catRenderDeadList() {
  const el = catEl('mortos');
  if (!el) return;
  el.innerHTML = CATALOGO_MORTOS.map(d => `
    <div style="display:flex; gap:10px; padding:9px 0; border-bottom:1px solid #F3F4F6;">
      <code style="font-size:11px; color:#6B7280; background:#F3F4F6; padding:2px 6px; border-radius:4px; height:fit-content; white-space:nowrap;">${catEscape(d.source)}</code>
      <span style="font-size:12px; color:#6B7280;">${catEscape(d.reason)}</span>
    </div>`).join('');
}

/* -------------------------------------------------------------- navegação */

function catGoTo(escopo) {
  catScope = escopo;
  catClose();
  showScreen(escopo === 'global' ? 'screen-templates-globais' : 'screen-client-templates');
  catRenderScreen();
}

function catRenderScreen() {
  if (!catEl('tbody')) return;
  catRenderFilters();
  catRenderTable();
  catRenderDeadList();
}

function catInit() {
  ['cliente', 'global'].forEach(e => { catScope = e; catRenderScreen(); });
  catScope = 'cliente';
}

document.addEventListener('DOMContentLoaded', catInit);
document.addEventListener('keydown', e => { if (e.key === 'Escape' && catSelected) catClose(); });
