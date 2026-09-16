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

const CLIENTE_ATUAL = 'iFood Talentos';
let catEscopo = 'cliente';
let catSelecionado = null;
let catRascunho = null;

const catFiltro = {
  global:  { tipo: 'todos', canal: 'todos', categoria: 'todas', origem: 'todas', busca: '' },
  cliente: { tipo: 'todos', canal: 'todos', categoria: 'todas', origem: 'todas', busca: '' },
};

/* Os tres tipos fechados na reuniao de 16/09 com o Paulo e o Jader. */
const CAT_TIPO = {
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
const CAT_CONFIG_HOJE = {
  nenhum:   '<span style="color:#B91C1C;">não alcança nada: o texto vem todo do código</span>',
  abertura: '<span style="color:#9A3412;">alcança só o parágrafo de abertura e o assunto</span>',
  total:    '<span style="color:#166534;">já alcança o corpo inteiro</span>',
};

const CAT_CANAL = {
  email:    { texto: 'E-mail',   bg: 'rgba(96,190,209,.14)', cor: '#2B7A8C' },
  whatsapp: { texto: 'WhatsApp', bg: 'rgba(93,164,122,.14)', cor: '#3D7A56' },
};

/* ---------------------------------------------------------------- helpers */

function catEscapar(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function catRealcarVars(s) {
  return catEscapar(s).replace(/\{\{(\w+)\}\}/g,
    '<span style="background:rgba(96,190,209,.18); color:#1F6B7D; border-radius:4px; padding:1px 4px; font-weight:600;">{{$1}}</span>');
}

function catEl(sufixo, escopo) {
  return document.getElementById('cat-' + sufixo + '-' + (escopo || catEscopo));
}

function catF() { return catFiltro[catEscopo]; }

/* Quem, no total, deixou de seguir o padrão desta comunicação. */
function catForaDoPadrao(t) {
  return t.otherClients.concat(t.customized ? [CLIENTE_ATUAL] : []);
}

/* Texto que vale no escopo aberto. */
function catTextoVigente(t) {
  return catEscopo === 'global'
    ? { subject: t.defaultSubject, body: t.defaultBody }
    : { subject: t.subject, body: t.body };
}

/* --------------------------------------------------------------- listagem */

function catListaFiltrada() {
  const f = catF();
  const b = f.busca.trim().toLowerCase();
  return CATALOGO.filter(t => {
    if (f.tipo !== 'todos' && t.type !== f.tipo) return false;
    if (f.canal !== 'todos' && t.channel !== f.canal) return false;
    if (f.categoria !== 'todas' && t.category !== f.categoria) return false;
    if (catEscopo === 'cliente') {
      if (f.origem === 'personalizados' && !t.customized) return false;
      if (f.origem === 'padrao' && t.customized) return false;
    } else {
      if (f.origem === 'personalizados' && !catForaDoPadrao(t).length) return false;
      if (f.origem === 'padrao' && catForaDoPadrao(t).length) return false;
    }
    if (!b) return true;
    return (t.name + ' ' + t.key + ' ' + t.subject + ' ' + t.defaultSubject + ' ' + t.trigger + ' ' + t.source)
      .toLowerCase().includes(b);
  });
}

function catRenderFiltros() {
  const f = catF();
  const categorias = [...new Set(CATALOGO.map(t => t.category))].sort();
  const sel = (sufixo, campo, opcoes) =>
    `<select onchange="catSetFiltro('${campo}', this.value)" style="padding:7px 10px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#374151; background:white; font-family:inherit; cursor:pointer;">
       ${opcoes.map(o => `<option value="${o[0]}"${f[campo] === o[0] ? ' selected' : ''}>${o[1]}</option>`).join('')}
     </select>`;
  const tipos = [['todos', 'Todos os tipos'], ['modal', 'Modal'], ['automatica', 'Automática'], ['alerta', 'Alerta']];
  const origens = catEscopo === 'global'
    ? [['todas', 'Todos'], ['padrao', 'Sem cliente fora do padrão'], ['personalizados', 'Com cliente fora do padrão']]
    : [['todas', 'Padrão e personalizados'], ['padrao', 'Só os que seguem o padrão'], ['personalizados', 'Só os personalizados']];

  catEl('filtros').innerHTML = `
    <div style="position:relative; flex:1; min-width:200px;">
      <i data-lucide="search" style="width:14px;height:14px;position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#9CA3AF;"></i>
      <input id="cat-busca-${catEscopo}" value="${catEscapar(f.busca)}" oninput="catSetFiltro('busca', this.value)"
             placeholder="Buscar por nome, assunto ou gatilho"
             style="width:100%; padding:7px 10px 7px 30px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#374151; font-family:inherit;">
    </div>
    ${sel('tipo', 'tipo', tipos)}
    ${sel('canal', 'canal', [['todos', 'Todos os canais'], ['email', 'E-mail'], ['whatsapp', 'WhatsApp']])}
    ${sel('cat', 'categoria', [['todas', 'Todas as categorias']].concat(categorias.map(c => [c, c[0].toUpperCase() + c.slice(1)])))}
    ${sel('origem', 'origem', origens)}
  `;
  if (window.lucide) lucide.createIcons();
}

function catSetFiltro(campo, valor) {
  catF()[campo] = valor;
  catRenderTabela();
  if (campo !== 'busca') catRenderFiltros();
}

function catSeloOrigem(t) {
  if (catEscopo === 'global') {
    if (!t.clientEditable) {
      return `<span style="background:rgba(209,153,96,.16); color:#8A5A20; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Não personalizável</span>`;
    }
    const n = catForaDoPadrao(t).length;
    return n
      ? `<span title="${catEscapar(catForaDoPadrao(t).join(', '))}" style="background:#FEF3C7; color:#92400E; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${n} fora do padrão</span>`
      : `<span style="background:#DCFCE7; color:#166534; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Todos herdam</span>`;
  }
  if (!t.clientEditable) {
    return `<span title="Texto único da plataforma" style="background:rgba(209,153,96,.16); color:#8A5A20; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Texto da WeDO</span>`;
  }
  return t.customized
    ? `<span style="background:#FEF3C7; color:#92400E; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Personalizado</span>`
    : `<span style="background:#F3F4F6; color:#6B7280; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">Padrão da WeDO</span>`;
}

function catRenderTabela() {
  const lista = catListaFiltrada();
  const corpo = catEl('tbody');
  if (!corpo) return;

  if (catEscopo === 'global') {
    const n = CATALOGO.filter(t => catForaDoPadrao(t).length).length;
    catEl('contagem').innerHTML = `${lista.length} ${lista.length === 1 ? 'comunicação' : 'comunicações'} · <span style="color:#92400E;">${n} com pelo menos um cliente fora do padrão</span>`;
  } else {
    const n = CATALOGO.filter(t => t.customized).length;
    catEl('contagem').innerHTML = `${lista.length} ${lista.length === 1 ? 'comunicação' : 'comunicações'} · <span style="color:#92400E;">${n} personalizada(s) neste cliente</span>`;
  }

  if (!lista.length) {
    corpo.innerHTML = `<tr><td colspan="5" style="padding:48px 20px; text-align:center;">
      <i data-lucide="search-x" style="width:28px;height:28px;color:#D1D5DB;"></i>
      <p style="font-size:13px; color:#6B7280; margin:10px 0 0 0;">Nenhuma comunicação bate com esse filtro.</p>
      <button onclick="catLimparFiltros()" style="margin-top:10px; padding:6px 12px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:12px; color:#374151; cursor:pointer; font-family:inherit;">Limpar filtros</button>
    </td></tr>`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  corpo.innerHTML = lista.map((t, i) => {
    const ca = CAT_CANAL[t.channel];
    const ti = CAT_TIPO[t.type];
    const vig = catEscopo === 'global' ? t.defaultSubject : t.subject;
    const ultima = catEscopo === 'global'
      ? (catForaDoPadrao(t).length ? catEscapar(catForaDoPadrao(t).join(', ')) : 'nenhum')
      : (t.customized ? catEscapar(t.customizedAt) : 'segue o padrão');
    return `
    <tr onclick="catAbrir('${t.key}','${t.channel}')" style="border-top:1px solid #F3F4F6; cursor:pointer; ${i % 2 ? 'background:#F9FAFB;' : ''}"
        onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='${i % 2 ? '#F9FAFB' : 'white'}'">
      <td style="padding:13px 20px;">
        <div style="font-size:13px; font-weight:600; color:#111827;">${catEscapar(t.name)}</div>
        <div style="font-size:12px; color:#6B7280; margin-top:2px;">${vig ? catEscapar(vig) : '<span style="color:#9CA3AF;">mensagem direta, sem assunto</span>'}</div>
      </td>
      <td style="padding:13px 12px;">
        <span title="${catEscapar(ti.ajuda)}" style="background:${ti.bg}; color:${ti.cor}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${ti.texto}</span>
        <div style="font-size:11px; color:#6B7280; margin-top:4px;">${ca.texto} · <span style="text-transform:capitalize;">${catEscapar(t.audience)}</span></div>
      </td>
      <td style="padding:13px 12px; font-size:12px; color:#6B7280; max-width:280px;">${catEscapar(t.trigger)}</td>
      <td style="padding:13px 12px; text-align:center;">${catSeloOrigem(t)}</td>
      <td style="padding:13px 20px; text-align:right; font-size:11px; color:#9CA3AF; max-width:180px;">${ultima}</td>
    </tr>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

function catLimparFiltros() {
  Object.assign(catF(), { tipo: 'todos', canal: 'todos', categoria: 'todas', origem: 'todas', busca: '' });
  catRenderFiltros(); catRenderTabela();
}

/* --------------------------------------------------------- painel lateral */

function catAbrir(chave, canal) {
  catSelecionado = CATALOGO.find(t => t.key === chave && t.channel === canal);
  if (!catSelecionado) return;
  catRascunho = Object.assign({}, catTextoVigente(catSelecionado));
  document.getElementById('cat-drawer').style.transform = 'translateX(0)';
  document.getElementById('cat-drawer-backdrop').style.display = 'block';
  catRenderDrawer();
  catAba('conteudo');
}

function catFechar() {
  const d = document.getElementById('cat-drawer');
  if (!d) return;
  d.style.transform = 'translateX(100%)';
  document.getElementById('cat-drawer-backdrop').style.display = 'none';
  catSelecionado = null;
}

function catRenderDrawer() {
  const t = catSelecionado;
  const ca = CAT_CANAL[t.channel];
  document.getElementById('cat-drawer-titulo').textContent = t.name;
  document.getElementById('cat-drawer-escopo').innerHTML = catEscopo === 'global'
    ? '<span style="background:rgba(152,96,209,.14); color:#6D3FA0; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">Padrão da WeDO</span>'
    : `<span style="background:rgba(96,190,209,.14); color:#2B7A8C; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">${catEscapar(CLIENTE_ATUAL)}</span>`;
  document.getElementById('cat-drawer-sub').innerHTML =
    `<span style="font-family:monospace;">${catEscapar(t.key)}</span> ·
     <span style="color:${ca.cor}; font-weight:600;">${ca.texto}</span> ·
     <span style="text-transform:capitalize;">${catEscapar(t.audience)}</span>`;
  const btnSalvar = document.getElementById('cat-btn-salvar');
  btnSalvar.textContent = catEscopo === 'global' ? 'Publicar o padrão' : 'Salvar para este cliente';
  const ro = catSomenteLeitura();
  btnSalvar.style.display = ro ? 'none' : 'inline-block';
  document.getElementById('cat-btn-descartar').style.display = ro ? 'none' : 'inline-block';
  document.getElementById('cat-aba-padrao').style.display =
    (catEscopo === 'global' || !catSelecionado.clientEditable) ? 'none' : 'block';
  catRenderConteudo();
  if (catEscopo === 'cliente') catRenderPadrao();
  catRenderHistorico();
}

function catFaixaEscopo(t) {
  if (catEscopo === 'cliente' && !t.clientEditable) {
    return `<div style="background:#FFF7ED; border:1px solid #FED7AA; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#9A3412;">
      <strong>Alerta da plataforma, com texto único da WeDO.</strong>
      O Paulo e o Jader decidiram em 16/09 que alerta não é personalizado por cliente nesta fase. Para mudar este texto, edite no catálogo global: a mudança vale para todos.
      ${t.defaultEnabled === false ? ' Este alerta nasce desligado no cliente.' : ''}
    </div>`;
  }
  if (catEscopo === 'global' && !t.clientEditable) {
    return `<div style="background:#F5F3FF; border:1px solid #DDD6FE; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#5B21B6;">
      <strong>Alerta da plataforma.</strong>
      Texto único: publicar vale para todos os clientes, e nenhum cliente pode fugir dele nesta fase.
      Alerta nasce desligado em cliente novo, até a copy ser revisada.
    </div>`;
  }
  if (catEscopo === 'global') {
    const fora = catForaDoPadrao(t);
    const herdam = 6 - fora.length;
    return `<div style="background:#F5F3FF; border:1px solid #DDD6FE; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#5B21B6;">
      <strong>Você está editando o padrão da WeDO.</strong>
      Publicar alcança na hora os ${herdam} cliente(s) que herdam esta comunicação.
      ${fora.length ? `Não alcança ${catEscapar(fora.join(', '))}, que ajustaram o texto por conta.` : 'Nenhum cliente fugiu do padrão nesta comunicação.'}
    </div>`;
  }
  if (t.customized) {
    return `<div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:8px; padding:11px 13px; margin-bottom:16px; display:flex; align-items:center; justify-content:space-between; gap:12px;">
      <div style="font-size:12px; color:#92400E;">
        <strong>Texto personalizado para este cliente.</strong><br>
        Ajustado por ${catEscapar(t.customizedBy)} em ${catEscapar(t.customizedAt)}. Revisões do padrão da WeDO não chegam mais aqui.
      </div>
      <button onclick="catVoltarPadrao()" style="padding:6px 11px; border:1px solid #FECACA; background:#FEF2F2; color:#B91C1C; border-radius:6px; font-size:12px; cursor:pointer; font-family:inherit; white-space:nowrap;">Voltar ao padrão</button>
    </div>`;
  }
  return `<div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#6B7280;">
    <strong style="color:#374151;">Segue o padrão da WeDO.</strong>
    Enquanto for assim, uma revisão do padrão chega aqui sozinha. Se você salvar uma alteração, este cliente passa a ter a versão dele e para de acompanhar o padrão.
  </div>`;
}

function catSomenteLeitura() {
  return catEscopo === 'cliente' && !catSelecionado.clientEditable;
}

function catRenderConteudo() {
  const t = catSelecionado;
  const ro = catSomenteLeitura();
  const vars = t.variables.length ? t.variables : ['candidate_name', 'job_title'];
  document.getElementById('cat-painel-conteudo').innerHTML = `
    ${catFaixaEscopo(t)}
    ${t.note ? `<div style="background:#FFF7ED; border:1px solid #FED7AA; border-radius:8px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:#9A3412;">${catEscapar(t.note)}</div>` : ''}
    ${!t.defaultBody ? `<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:#B91C1C;">O texto desta comunicação não está numa view de e-mail: ele é montado em <code style="background:none;">${catEscapar(t.source)}</code>. Precisa ser extraído de lá na migração.</div>` : ''}

    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Assunto</label>
    <input id="cat-in-subject" value="${catEscapar(catRascunho.subject)}" oninput="catEditar('subject', this.value)"
           ${t.channel === 'whatsapp' ? 'disabled placeholder="WhatsApp não tem assunto"' : (ro ? 'disabled' : '')}
           style="width:100%; padding:9px 11px; border:1px solid #D1D5DB; border-radius:8px; font-size:13px; color:#111827; font-family:inherit; margin-bottom:18px; ${(t.channel === 'whatsapp' || ro) ? 'background:#F3F4F6; color:#9CA3AF;' : ''}">

    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
      <label style="font-size:12px; font-weight:600; color:#374151;">Corpo da mensagem</label>
      <span style="font-size:11px; color:#9CA3AF;">clique numa variável para inserir no cursor</span>
    </div>
    <div style="display:flex; flex-wrap:wrap; gap:5px; margin-bottom:8px;">
      ${vars.map(v => `<button onclick="catInserirVar('${v}')" style="padding:3px 8px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:11px; color:#1F6B7D; font-family:monospace; cursor:pointer;" onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='white'">{{${v}}}</button>`).join('')}
    </div>
    <textarea id="cat-in-body" oninput="catEditar('body', this.value)" rows="12" ${ro ? 'disabled' : ''}
      style="width:100%; ${ro ? 'background:#F3F4F6; color:#6B7280;' : ''} padding:11px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#111827; font-family:inherit; line-height:1.6; resize:vertical;">${catEscapar(catRascunho.body)}</textarea>

    <div style="margin-top:14px; padding-top:12px; border-top:1px solid #F3F4F6; display:grid; grid-template-columns:110px 1fr; gap:6px 10px; font-size:11px; color:#6B7280;">
      <span style="color:#9CA3AF;">Remetente</span><span><code style="background:#F3F4F6; padding:1px 5px; border-radius:4px;">${catEscapar(t.sender)}</code></span>
      <span style="color:#9CA3AF;">Hoje o config</span><span>${CAT_CONFIG_HOJE[t.configToday]}</span>
      <span style="color:#9CA3AF;">No código</span><span><code style="background:#F3F4F6; padding:1px 5px; border-radius:4px;">${catEscapar(t.source)}</code></span>
    </div>
    ${t.hasText ? `<p style="font-size:11px; color:#9A3412; margin-top:8px;">Esta comunicação também tem versão em texto puro, que precisa acompanhar a edição.</p>` : ''}
  `;
}

function catEditar(campo, valor) {
  catRascunho[campo] = valor;
  catMarcarSujo();
  if (document.getElementById('cat-painel-preview').style.display !== 'none') catRenderPreview();
}

function catSujo() {
  const vig = catTextoVigente(catSelecionado);
  return catRascunho.subject !== vig.subject || catRascunho.body !== vig.body;
}

function catMarcarSujo() {
  const sujo = catSujo();
  const btn = document.getElementById('cat-btn-salvar');
  btn.disabled = !sujo;
  btn.style.opacity = sujo ? '1' : '0.45';
  btn.style.cursor = sujo ? 'pointer' : 'not-allowed';
  document.getElementById('cat-sujo').style.display = sujo ? 'inline' : 'none';
}

function catInserirVar(v) {
  const ta = document.getElementById('cat-in-body');
  const ini = ta.selectionStart, fim = ta.selectionEnd;
  ta.value = ta.value.slice(0, ini) + '{{' + v + '}}' + ta.value.slice(fim);
  ta.focus();
  ta.selectionStart = ta.selectionEnd = ini + v.length + 4;
  catEditar('body', ta.value);
}

function catAba(aba) {
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

function catCartaoEmail(assunto, corpo) {
  const remetente = catEscopo === 'global' ? 'Empresa do cliente' : CLIENTE_ATUAL;
  return `
    <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:20px;">
      <div style="max-width:560px; margin:0 auto; background:#fff; border:1px solid #E5E7EB; border-radius:12px; overflow:hidden;">
        <div style="padding:18px 24px; border-bottom:1px solid #F3F4F6; display:flex; align-items:center; justify-content:space-between;">
          <span style="font-size:13px; font-weight:600; color:#6B7280;">${catEscapar(remetente)}</span>
          <span style="width:8px;height:8px;border-radius:50%;background:#60BED1;display:inline-block;"></span>
        </div>
        <div style="padding:22px 24px;">
          <p style="margin:0 0 14px 0; font-size:11px; color:#9CA3AF; text-transform:uppercase; letter-spacing:.05em;">Assunto</p>
          <p style="margin:0 0 18px 0; font-size:15px; font-weight:600; color:#111827;">${catRealcarVars(assunto) || '<span style="color:#9CA3AF;">sem assunto</span>'}</p>
          <div style="font-size:13px; color:#374151; line-height:1.65;">${catRealcarVars(corpo).replace(/\n/g, '<br>') || '<span style="color:#9CA3AF;">Sem corpo definido.</span>'}</div>
        </div>
        <div style="background:#0d0d0d; padding:20px 24px;">
          <span style="display:inline-block; background:#1f1f1f; border-radius:4px; padding:6px 10px; font-size:12px; font-weight:700; color:#e5e7eb;">WeDO Talent</span>
          <p style="margin:10px 0 0 0; font-size:11px; color:#9ca3af;">Tecnologia avançada para o RH do futuro.</p>
        </div>
      </div>
    </div>`;
}

function catBalaoWhatsapp(corpo) {
  return `
    <div style="background:#ECE5DD; border-radius:12px; padding:18px;">
      <div style="background:#fff; border-radius:8px 8px 8px 2px; padding:10px 12px; max-width:85%; box-shadow:0 1px 1px rgba(0,0,0,.08); font-size:13px; color:#111827; line-height:1.5;">
        ${catRealcarVars(corpo).replace(/\n/g, '<br>') || '<span style="color:#9CA3AF;">Sem corpo definido.</span>'}
        <div style="text-align:right; font-size:10px; color:#9CA3AF; margin-top:4px;">agora</div>
      </div>
    </div>`;
}

function catRenderPreview() {
  const t = catSelecionado;
  document.getElementById('cat-painel-preview').innerHTML = t.channel === 'whatsapp'
    ? `<p style="font-size:11px; color:#9CA3AF; margin:0 0 10px 0;">como chega no WhatsApp do candidato</p>${catBalaoWhatsapp(catRascunho.body)}`
    : `<p style="font-size:11px; color:#9CA3AF; margin:0 0 10px 0;">como chega na caixa de entrada, dentro do layout do produto</p>${catCartaoEmail(catRascunho.subject, catRascunho.body)}`;
}

/* Aba Padrão: só existe dentro do cliente, para comparar com o catálogo. */
function catRenderPadrao() {
  const t = catSelecionado;
  document.getElementById('cat-painel-padrao').innerHTML = `
    <p style="font-size:12px; color:#6B7280; margin:0 0 14px 0;">
      ${t.customized
        ? 'Texto do catálogo da WeDO, para comparar com o que está valendo neste cliente.'
        : 'Este cliente está usando exatamente o texto do catálogo da WeDO.'}
    </p>
    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Assunto padrão</label>
    <div style="padding:9px 11px; border:1px solid #E5E7EB; background:#F9FAFB; border-radius:8px; font-size:13px; color:#374151; margin-bottom:16px;">${catRealcarVars(t.defaultSubject) || '<span style="color:#9CA3AF;">sem assunto</span>'}</div>
    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Corpo padrão</label>
    <div style="padding:11px; border:1px solid #E5E7EB; background:#F9FAFB; border-radius:8px; font-size:12px; color:#374151; line-height:1.6; white-space:pre-wrap;">${catRealcarVars(t.defaultBody) || '<span style="color:#9CA3AF;">Sem corpo definido.</span>'}</div>
    ${t.customized ? `<button onclick="catVoltarPadrao()" style="margin-top:14px; padding:8px 14px; border:1px solid #FECACA; background:#FEF2F2; color:#B91C1C; border-radius:8px; font-size:13px; cursor:pointer; font-family:inherit;">Voltar ao padrão neste cliente</button>` : ''}
  `;
}

function catRenderHistorico() {
  const t = catSelecionado;
  const linhas = catEscopo === 'global'
    ? [['12/09/2026', 'Paulo Moraes', 'Revisou a copy do padrão'],
       ['16/06/2026', 'Sistema', 'Importado do código na criação do catálogo']]
    : (t.customized
        ? [[t.customizedAt, t.customizedBy, 'Ajustou o texto para este cliente'],
           ['16/06/2026', 'Sistema', 'Cliente provisionado seguindo o padrão da WeDO']]
        : [['16/06/2026', 'Sistema', 'Cliente provisionado seguindo o padrão da WeDO']]);
  document.getElementById('cat-painel-historico').innerHTML = `
    <p style="font-size:12px; color:#6B7280; margin:0 0 14px 0;">Toda alteração fica registrada na trilha de auditoria, com autor e texto anterior.</p>
    ${linhas.map(([q, quem, oque]) => `
      <div style="display:flex; gap:12px; padding:11px 0; border-bottom:1px solid #F3F4F6;">
        <div style="width:100px; flex-shrink:0; font-size:11px; color:#9CA3AF;">${catEscapar(q)}</div>
        <div>
          <div style="font-size:12px; font-weight:600; color:#111827;">${catEscapar(quem)}</div>
          <div style="font-size:12px; color:#6B7280; margin-top:2px;">${catEscapar(oque)}</div>
        </div>
      </div>`).join('')}`;
}

/* ------------------------------------------------------------------ ações */

function catSalvar() {
  if (!catSujo()) return;
  const t = catSelecionado;

  if (catEscopo === 'global') {
    const herdava = !t.customized;
    t.defaultSubject = catRascunho.subject;
    t.defaultBody = catRascunho.body;
    if (herdava) { t.subject = t.defaultSubject; t.body = t.defaultBody; }
    const fora = catForaDoPadrao(t);
    catAviso(`Padrão publicado. ${6 - fora.length} cliente(s) recebem o texto novo agora.` +
             (fora.length ? ` ${fora.join(', ')} seguem com o texto próprio.` : ''));
  } else {
    const eraPadrao = !t.customized;
    t.subject = catRascunho.subject;
    t.body = catRascunho.body;
    t.customized = true;
    t.customizedBy = 'Rodrigo Alfieri';
    t.customizedAt = 'hoje';
    catAviso(eraPadrao
      ? 'Salvo. Este cliente passa a ter a versão dele e não acompanha mais o padrão desta comunicação.'
      : 'Salvo para este cliente.');
  }

  catRascunho = Object.assign({}, catTextoVigente(t));
  catRenderDrawer();
  catMarcarSujo();
  catRenderTabela();
}

function catVoltarPadrao() {
  const t = catSelecionado;
  if (!t.customized) return;
  if (!confirm('Voltar ao padrão descarta o texto ajustado para este cliente. Confirmar?')) return;
  t.subject = t.defaultSubject;
  t.body = t.defaultBody;
  t.customized = false;
  t.customizedBy = null;
  t.customizedAt = null;
  catRascunho = Object.assign({}, catTextoVigente(t));
  catRenderDrawer();
  catMarcarSujo();
  catRenderTabela();
  catAviso('Voltou ao padrão da WeDO. Revisões do padrão voltam a chegar aqui sozinhas.');
}

function catDescartar() {
  catRascunho = Object.assign({}, catTextoVigente(catSelecionado));
  catRenderConteudo();
  catMarcarSujo();
}

function catAviso(msg) {
  const el = document.getElementById('cat-toast');
  el.textContent = msg;
  el.style.display = 'block';
  el.style.opacity = '1';
  clearTimeout(window._catToast);
  window._catToast = setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.style.display = 'none', 250); }, 4200);
}

function catRenderMortos() {
  const el = catEl('mortos');
  if (!el) return;
  el.innerHTML = CATALOGO_MORTOS.map(d => `
    <div style="display:flex; gap:10px; padding:9px 0; border-bottom:1px solid #F3F4F6;">
      <code style="font-size:11px; color:#6B7280; background:#F3F4F6; padding:2px 6px; border-radius:4px; height:fit-content; white-space:nowrap;">${catEscapar(d.source)}</code>
      <span style="font-size:12px; color:#6B7280;">${catEscapar(d.reason)}</span>
    </div>`).join('');
}

/* -------------------------------------------------------------- navegação */

function catIr(escopo) {
  catEscopo = escopo;
  catFechar();
  showScreen(escopo === 'global' ? 'screen-templates-globais' : 'screen-client-templates');
  catRender();
}

function catRender() {
  if (!catEl('tbody')) return;
  catRenderFiltros();
  catRenderTabela();
  catRenderMortos();
}

function catIniciar() {
  ['cliente', 'global'].forEach(e => { catEscopo = e; catRender(); });
  catEscopo = 'cliente';
}

document.addEventListener('DOMContentLoaded', catIniciar);
document.addEventListener('keydown', e => { if (e.key === 'Escape' && catSelecionado) catFechar(); });
