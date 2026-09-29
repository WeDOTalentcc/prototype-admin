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
  proprio:  '<span style="color:#166534;">escrito aqui, o painel manda em tudo</span>',
  nenhum:   '<span style="color:#B91C1C;">não alcança nada: o texto vem todo do código</span>',
  abertura: '<span style="color:#9A3412;">alcança só o parágrafo de abertura e o assunto</span>',
  total:    '<span style="color:#166534;">já alcança o corpo inteiro</span>',
};

const CAT_CHANNEL = {
  email:    { texto: 'E-mail',   bg: 'rgba(96,190,209,.14)', cor: '#2B7A8C' },
  whatsapp: { texto: 'WhatsApp', bg: 'rgba(93,164,122,.14)', cor: '#3D7A56' },
};

/* Tres remetentes por finalidade: e' o que faz o candidato nao receber convite
   de triagem com a mesma cara do aviso de senha. */
const CAT_SENDER = {
  processo:     { texto: 'Processo seletivo', endereco: 'processo@vagas.wedotalent.cc' },
  acesso:       { texto: 'Acesso e codigos',  endereco: 'acesso@conta.wedotalent.cc' },
  notificacoes: { texto: 'Avisos',            endereco: 'notificacoes@avisos.wedotalent.cc' },
};

const CAT_STATUS = {
  active:  { texto: 'Publicado',  bg: '#DCFCE7', cor: '#166534' },
  dynamic: { texto: 'Montado no codigo', bg: '#F3F4F6', cor: '#6B7280' },
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

/* Comunicacao que sai pelos dois canais: a mesma chave com linha de e-mail e de
   WhatsApp. A linha continua sendo uma por canal, porque o texto e' de cada um. */
function catBothChannels() {
  const porChave = {};
  CATALOGO.forEach(t => { (porChave[t.key] = porChave[t.key] || new Set()).add(t.channel); });
  return new Set(Object.keys(porChave).filter(k => porChave[k].size > 1));
}

/* --------------------------------------------------------------- listagem */

function catFilteredList() {
  const f = catF();
  const b = f.busca.trim().toLowerCase();
  const nosDois = catBothChannels();
  return CATALOGO.filter(t => {
    if (f.tipo !== 'todos' && t.type !== f.tipo) return false;
    if (f.canal === 'ambos' && !nosDois.has(t.key)) return false;
    if (f.canal !== 'todos' && f.canal !== 'ambos' && t.channel !== f.canal) return false;
    if (f.categoria !== 'todas' && t.category !== f.categoria) return false;
    if (catScope === 'cliente') {
      if (f.origem === 'personalizados' && !t.customized) return false;
      if (f.origem === 'padrao' && t.customized) return false;
    } else {
      if (f.origem === 'personalizados' && !catOffDefault(t).length) return false;
      if (f.origem === 'padrao' && catOffDefault(t).length) return false;
    }
    if (!b) return true;
    // Termo so' de digitos casa o id INTEIRO, e nao como pedaco de texto: com
    // `includes` a busca por 10 devolveria 10, 100 e 210 juntos, e quem digita
    // um id esta conferindo uma linha especifica.
    if (/^\d+$/.test(b)) return String(catId(t)) === b;
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
             placeholder="Buscar por id, nome, assunto ou gatilho"
             style="width:100%; padding:7px 10px 7px 30px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#374151; font-family:inherit;">
    </div>
    ${select('tipo', 'tipo', tipos)}
    ${select('canal', 'canal', [['todos', 'Todos os canais'], ['email', 'E-mail'], ['whatsapp', 'WhatsApp'], ['ambos', 'Nos dois canais']])}
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

/* O painel mostra o id da linha no banco, que e' como se confere uma
   comunicacao especifica. Aqui a posicao no catalogo faz esse papel: o que
   importa no desenho e' a coluna existir e caber no mesmo lugar. */
function catId(t) {
  return CATALOGO.indexOf(t) + 1;
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
    corpo.innerHTML = `<tr><td colspan="8" style="padding:48px 20px; text-align:center;">
      <i data-lucide="search-x" style="width:28px;height:28px;color:#D1D5DB;"></i>
      <p style="font-size:13px; color:#6B7280; margin:10px 0 0 0;">Nenhuma comunicação bate com esse filtro.</p>
      <button onclick="catClearFilters()" style="margin-top:10px; padding:6px 12px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:12px; color:#374151; cursor:pointer; font-family:inherit;">Limpar filtros</button>
    </td></tr>`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const nosDois = catBothChannels();
  corpo.innerHTML = lista.map((t, i) => {
    const channelMeta = CAT_CHANNEL[t.channel];
    const kindMeta = CAT_KIND[t.type];
    const senderMeta = CAT_SENDER[t.sender] || { texto: t.sender, endereco: '' };
    const statusMeta = CAT_STATUS[t.status] || { texto: t.status, bg: '#F3F4F6', cor: '#6B7280' };
    const currentSubject = catScope === 'global' ? t.defaultSubject : t.subject;
    const ultima = catScope === 'global'
      ? (catOffDefault(t).length ? catEscape(catOffDefault(t).join(', ')) : 'nenhum')
      : (t.customized ? catEscape(t.customizedAt) : 'segue o padrão');
    const metaNaConta = catScope === 'cliente' && t.channel === 'whatsapp' && typeof mcMetaSummary === 'function'
      ? `<div style="font-size:11px; margin-top:4px;">${mcMetaSummary(t.key)}</div>` : '';
    const foraDoPadrao = catScope === 'cliente' && t.customized;
    return `
    <tr onclick="catOpen('${t.key}','${t.channel}')" data-fora-do-padrao="${foraDoPadrao ? 'sim' : 'nao'}"
        style="border-top:1px solid #F3F4F6; cursor:pointer; ${i % 2 ? 'background:#F9FAFB;' : ''} ${foraDoPadrao ? 'border-left:4px solid #D97706;' : ''}"
        onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='${i % 2 ? '#F9FAFB' : 'white'}'">
      <td style="padding:13px 16px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11.5px; color:#6B7280;">${catId(t)}</td>
      <td style="padding:13px 20px;">
        <div style="font-size:13px; font-weight:600; color:#111827;">${catEscape(t.name)}</div>
        <div style="font-size:12px; color:#6B7280; margin-top:2px;">${currentSubject ? catEscape(currentSubject) : '<span style="color:#9CA3AF;">mensagem direta, sem assunto</span>'}</div>
      </td>
      <td style="padding:13px 12px;">
        <span style="background:${channelMeta.bg}; color:${channelMeta.cor}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${channelMeta.texto}</span>
        ${nosDois.has(t.key) ? '<div style="font-size:11px; color:#6B7280; margin-top:4px;">também no outro canal</div>' : ''}
      </td>
      <td style="padding:13px 12px;">
        <span title="${catEscape(kindMeta.ajuda)}" style="background:${kindMeta.bg}; color:${kindMeta.cor}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${kindMeta.texto}</span>
        <div style="font-size:11px; color:#6B7280; margin-top:4px; text-transform:capitalize;">${catEscape(t.audience)}</div>
      </td>
      <td style="padding:13px 12px; font-size:12px; color:#6B7280;" title="${catEscape(senderMeta.endereco)}">${catEscape(senderMeta.texto)}</td>
      <td style="padding:13px 12px; font-size:12px; color:#6B7280; max-width:260px;">${catEscape(t.trigger)}</td>
      <td style="padding:13px 12px; text-align:center;">${catOriginBadge(t)}${metaNaConta}</td>
      <td style="padding:13px 20px; text-align:right;">
        <span style="background:${statusMeta.bg}; color:${statusMeta.cor}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${statusMeta.texto}</span>
        <div style="font-size:11px; color:#9CA3AF; margin-top:4px;">${ultima}</div>
      </td>
    </tr>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

function catClearFilters() {
  Object.assign(catF(), { tipo: 'todos', canal: 'todos', categoria: 'todas', origem: 'todas', busca: '' });
  catRenderFilters(); catRenderTable();
}

/* ------------------------------------------------- criar um texto novo

   O CANAL e' a decisao desta tela, e so' dela: depois de criado, o texto
   pertence ao canal dele -- nao existe virar um e-mail em WhatsApp, porque o
   corpo de um nao serve ao outro. Para ter a mesma comunicacao nos dois
   canais, cria-se o par, e a lista mostra "tambem no outro canal".

   O que se escolhe aqui e' o que o backend precisa saber antes do texto
   existir: canal, nome, categoria e quando dispara. */

let catNovo = { channel: 'email', name: '', category: '', trigger: '' };

function catNovoAbrir() {
  catNovo = { channel: 'email', name: '', category: '', trigger: '' };
  document.getElementById('cat-novo').style.display = 'flex';
  document.getElementById('cat-novo-backdrop').style.display = 'block';
  catNovoRender();
}

function catNovoFechar() {
  document.getElementById('cat-novo').style.display = 'none';
  document.getElementById('cat-novo-backdrop').style.display = 'none';
}

function catNovoSet(campo, valor) {
  catNovo[campo] = valor;
  catNovoRender();
}

function catNovoCanalCard(canal, titulo, descricao, icone) {
  const ativo = catNovo.channel === canal;
  return `<button onclick="catNovoSet('channel','${canal}')" style="flex:1; min-width:210px; text-align:left; padding:13px 15px; border:1.5px solid ${ativo ? '#C74446' : '#D1D5DB'}; background:${ativo ? '#FEF2F2' : 'white'}; border-radius:10px; cursor:pointer; font-family:inherit;">
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">
      <i data-lucide="${icone}" style="width:16px;height:16px;color:${ativo ? '#C74446' : '#6B7280'};"></i>
      <span style="font-size:13px; font-weight:600; color:#111827;">${titulo}</span>
      ${ativo ? '<i data-lucide="check" style="width:14px;height:14px;color:#C74446;margin-left:auto;"></i>' : ''}
    </div>
    <div style="font-size:11.5px; color:#6B7280; line-height:1.45;">${descricao}</div>
  </button>`;
}

function catNovoRender() {
  const categorias = [...new Set(CATALOGO.map(t => t.category).filter(Boolean))].sort();
  const gatilhos = [...new Set(CATALOGO.map(t => t.trigger).filter(Boolean))].sort().slice(0, 12);
  const whats = catNovo.channel === 'whatsapp';

  document.getElementById('cat-novo-sub').textContent = catScope === 'global'
    ? 'Nasce como padrão da WeDO e todo cliente que herdar passa a recebê-lo.'
    : 'Nasce só para este cliente, fora do catálogo da WeDO.';

  document.getElementById('cat-novo-corpo').innerHTML = `
    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:8px;">Canal</label>
    <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:6px;">
      ${catNovoCanalCard('email', 'E-mail', 'Sai no layout da plataforma, com cabeçalho, assinatura e os blocos de privacidade.', 'mail')}
      ${catNovoCanalCard('whatsapp', 'WhatsApp', 'Texto puro numa conversa. Sai livremente enquanto o candidato estiver respondendo. Para ABRIR conversa, só com modelo aprovado pela Meta.', 'message-circle')}
    </div>
    <p style="font-size:11px; color:#9CA3AF; margin:0 0 18px;">O canal se decide agora e não muda depois. Para ter a mesma comunicação nos dois, crie o par.</p>

    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Nome da comunicação</label>
    <input value="${catEscape(catNovo.name)}" oninput="catNovo.name = this.value; catNovoValidar();"
           placeholder="${whats ? 'Ex.: Convite de triagem (WhatsApp)' : 'Ex.: Teste financeiro'}"
           style="width:100%; padding:9px 11px; border:1px solid #D1D5DB; border-radius:8px; font-size:13px; color:#111827; font-family:inherit; margin-bottom:16px;">

    <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px;">
      <div style="flex:1; min-width:200px;">
        <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Categoria</label>
        <select onchange="catNovo.category = this.value; catNovoValidar();" style="width:100%; padding:9px 11px; border:1px solid #D1D5DB; border-radius:8px; font-size:13px; color:#374151; background:white; font-family:inherit;">
          <option value="">Escolha uma categoria</option>
          ${categorias.map(c => `<option value="${catEscape(c)}"${catNovo.category === c ? ' selected' : ''}>${catEscape(c[0].toUpperCase() + c.slice(1))}</option>`).join('')}
        </select>
      </div>
      <div style="flex:1; min-width:200px;">
        <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Quando dispara</label>
        <select onchange="catNovo.trigger = this.value; catNovoValidar();" style="width:100%; padding:9px 11px; border:1px solid #D1D5DB; border-radius:8px; font-size:13px; color:#374151; background:white; font-family:inherit;">
          <option value="">Só quando alguém enviar (manual)</option>
          ${gatilhos.map(g => `<option value="${catEscape(g)}"${catNovo.trigger === g ? ' selected' : ''}>${catEscape(g.length > 60 ? g.slice(0, 60) + '…' : g)}</option>`).join('')}
        </select>
      </div>
    </div>

    ${whats ? `<div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:8px; padding:11px 13px; font-size:12px; color:#065F46;">
      <strong>WhatsApp não tem assunto.</strong> Este texto sai como mensagem da conversa: vale enquanto o candidato tiver respondido nas últimas 24 horas. Texto que precisa <strong>abrir</strong> conversa é outra coisa: a Meta exige modelo aprovado, e isso só existe para os fluxos que a plataforma conhece (triagem, convite e confirmação de entrevista, cadência). Um texto criado aqui não vira modelo na Meta, então fora da janela ele não sai.
    </div>` : `<div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px; padding:11px 13px; font-size:12px; color:#6B7280;">
      O assunto e o corpo você escreve no próximo passo, com a pré-visualização do e-mail montado do jeito que o candidato recebe.
    </div>`}
  `;
  catNovoValidar();
  if (window.lucide) lucide.createIcons();
}

function catNovoValidar() {
  const btn = document.getElementById('cat-novo-criar');
  const ok = catNovo.name.trim().length > 2 && catNovo.category;
  btn.disabled = !ok;
  btn.style.opacity = ok ? '1' : '.45';
  btn.style.cursor = ok ? 'pointer' : 'not-allowed';
}

function catNovoCriar() {
  if (!catNovo.name.trim() || !catNovo.category) return;
  const chave = 'avulso_' + catNovo.name.trim().toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  const novo = {
    key: chave,
    name: catNovo.name.trim(),
    channel: catNovo.channel,
    category: catNovo.category,
    audience: 'candidato',
    status: 'active',
    source: 'criado no painel',
    subject: catNovo.channel === 'email' ? '' : '',
    trigger: catNovo.trigger || 'Só quando alguém enviar, pelos modais da plataforma.',
    variables: ['candidate_name', 'job_title', 'company_name'],
    body: '',
    note: '',
    hasText: false,
    type: catNovo.trigger ? 'automatica' : 'modal',
    sender: 'processo',
    clientEditable: true,
    configToday: 'proprio',
    defaultSubject: '',
    defaultBody: '',
    customized: catScope === 'cliente',
    customizedBy: catScope === 'cliente' ? 'Você' : null,
    customizedAt: catScope === 'cliente' ? 'agora' : null,
    otherClients: []
  };
  CATALOGO.unshift(novo);
  catNovoFechar();
  catRenderFilters();
  catRenderTable();
  catOpen(novo.key, novo.channel);
}

/* --------------------------------------------------------- painel lateral */

function catOpen(chave, canal) {
  catSelected = CATALOGO.find(t => t.key === chave && t.channel === canal);
  if (!catSelected) return;
  catDraft = Object.assign({}, catCurrentText(catSelected));
  catSourceView = false;
  catVarAberto = null;
  document.getElementById('cat-drawer').style.display = 'flex';
  document.getElementById('cat-drawer-backdrop').style.display = 'block';
  catRenderDrawer();
  catTab('conteudo');
}

function catClose() {
  const d = document.getElementById('cat-drawer');
  if (!d) return;
  d.style.display = 'none';
  document.getElementById('cat-drawer-backdrop').style.display = 'none';
  catSelected = null;
}

function catRenderDrawer() {
  const t = catSelected;
  const abaPadrao = document.getElementById('cat-aba-padrao');
  if (abaPadrao) abaPadrao.style.display = catCriadoNoPainel(t) ? 'none' : '';
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
  if (catCriadoNoPainel(t)) {
    return `<div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#065F46;">
      <strong>Texto próprio${catScope === 'cliente' ? ' deste cliente' : ' da WeDO'}.</strong>
      Não existe no catálogo${catScope === 'cliente' ? ' da WeDO' : ''}, então não há padrão para acompanhar nem para voltar.
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

/* Texto nascido aqui nao tem view de e-mail atras, nem padrao da WeDO para
   comparar: os avisos que falam de codigo e de heranca nao se aplicam a ele. */
function catCriadoNoPainel(t) {
  return t.source === 'criado no painel';
}

function catReadOnly() {
  return catScope === 'cliente' && !catSelected.clientEditable;
}

function catRenderContent() {
  const t = catSelected;
  const readOnly = catReadOnly();
  document.getElementById('cat-painel-conteudo').innerHTML = `
    ${catScopeBanner(t)}
    ${t.note ? `<div style="background:#FFF7ED; border:1px solid #FED7AA; border-radius:8px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:#9A3412;">${catEscape(t.note)}</div>` : ''}
    ${!t.defaultBody && !catCriadoNoPainel(t) ? `<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:#B91C1C;">O texto desta comunicação não está numa view de e-mail: ele é montado em <code style="background:none;">${catEscape(t.source)}</code>. Precisa ser extraído de lá na migração.</div>` : ''}

    ${t.channel === 'whatsapp' ? `
    <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:8px; padding:11px 13px; margin-bottom:16px; font-size:12px; color:#065F46;">
      <strong>WhatsApp não tem assunto.</strong> Dentro da janela de 24 horas, contada a partir da última resposta do candidato, este texto sai como mensagem livre da conversa. Fora dela a Meta só entrega modelo que ela aprovou, e só os fluxos que abrem conversa têm um.
    </div>` : `
    <div style="position:relative; display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:6px;">
      <label style="font-size:12px; font-weight:600; color:#374151;">Assunto</label>
      ${catVarBotao('assunto', 'Assunto', readOnly)}
      ${catVarAberto && catVarAberto.campo === 'assunto' ? catVarPopover('assunto', 'Assunto') : ''}
    </div>
    <input id="cat-in-subject" value="${catEscape(catDraft.subject)}" oninput="catEdit('subject', this.value)"
           ${readOnly ? 'disabled' : ''}
           style="width:100%; padding:9px 11px; border:1px solid #D1D5DB; border-radius:8px; font-size:13px; color:#111827; font-family:inherit; margin-bottom:18px; ${readOnly ? 'background:#F3F4F6; color:#9CA3AF;' : ''}">`}

    <div style="position:relative; display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:6px;">
      <label style="font-size:12px; font-weight:600; color:#374151;">Corpo da mensagem</label>
      ${catVarBotao('corpo', 'Corpo da mensagem', readOnly)}
      ${catVarAberto && catVarAberto.campo === 'corpo' ? catVarPopover('corpo', 'Corpo da mensagem') : ''}
    </div>
    ${catBodyEditor(t, readOnly)}

    <div style="margin-top:14px; padding-top:12px; border-top:1px solid #F3F4F6; display:grid; grid-template-columns:110px 1fr; gap:6px 10px; font-size:11px; color:#6B7280;">
      <span style="color:#9CA3AF;">Remetente</span><span>${catEscape((CAT_SENDER[t.sender] || { texto: t.sender }).texto)} <code style="background:#F3F4F6; padding:1px 5px; border-radius:4px;">${catEscape((CAT_SENDER[t.sender] || { endereco: '' }).endereco)}</code></span>
      <span style="color:#9CA3AF;">Hoje o config</span><span>${CAT_CONFIG_REACH[t.configToday]}</span>
      ${catCriadoNoPainel(t) ? '' : `<span style="color:#9CA3AF;">No código</span><span><code style="background:#F3F4F6; padding:1px 5px; border-radius:4px;">${catEscape(t.source)}</code></span>`}
    </div>
    ${catScope === 'cliente' && t.channel === 'whatsapp' && typeof mcMetaAccountsLine === 'function' ? `
      <div style="margin-top:16px; border:1px solid #E5E7EB; border-radius:8px; padding:10px 12px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <span style="font-size:12px; font-weight:600; color:#374151;">Modelo na Meta, por conta</span>
          <a href="#" onclick="catClose(); commTab('modelos'); return false;" style="font-size:11px; color:#C74446; font-weight:500;">ver em Modelos na Meta</a>
        </div>
        ${mcMetaAccountsLine(t.key)}
        <p style="font-size:11px; color:#6B7280; margin:8px 0 0;">Esta comunicação abre conversa, então tem modelo na Meta: salvar o texto gera uma revisão, e o aprovado continua servindo até a nova passar.</p>
      </div>` : ''}
    ${t.hasText ? `<p style="font-size:11px; color:#9A3412; margin-top:8px;">Esta comunicação também tem versão em texto puro, que precisa acompanhar a edição.</p>` : ''}
  `;
  if (window.lucide) lucide.createIcons();
}

/* ------------------------------------------------ seletor de variaveis

   O painel nao lista as variaveis como fileira de etiquetas: elas ficam atras
   de um botao "Inserir variavel", num popover com busca e separadas em duas
   FAMILIAS. A separacao nao e' enfeite -- misturar as duas fazia o operador
   tratar a variavel de conteudo do envio como campo que ele deveria preencher
   aqui, quando ela e' o texto que o recrutador digita na hora de enviar.

   Cada linha mostra rotulo, a marcacao que entra no texto e o que ela traz: o
   nome cru sozinho nao dizia nem uma coisa nem outra. */

const CAT_VAR_FAMILIAS = [
  {
    id: 'dado',
    titulo: 'Dados que a plataforma preenche',
    dica: 'A plataforma resolve sozinha no envio, com o que já está no cadastro do candidato e da vaga.',
    descricaoPadrao: 'A plataforma preenche no envio.'
  },
  {
    id: 'conteudo_do_envio',
    titulo: 'Conteúdo escrito na hora do envio',
    dica: 'Só tem valor quando alguém digita o texto no momento do envio. Aqui no template ela fica como espaço reservado.',
    descricaoPadrao: 'Texto digitado no momento do envio.'
  }
];

const CAT_VAR_CONTEUDO_DO_ENVIO = new Set([
  'custom_message_html', 'mensagem_personalizada', 'assunto_da_mensagem', 'corpo_da_mensagem'
]);

const CAT_VAR_DESCRICAO = {
  company_name:   ['Nome da empresa', 'A marca que o candidato vê, já resolvida pela vaga.'],
  trade_name:     ['Nome fantasia', 'O nome comercial da empresa, quando ela tem um.'],
  job_title:      ['Título da vaga', 'O cargo como está publicado.'],
  job_url:        ['Link da vaga', 'Endereço público da vaga.'],
  candidate_name: ['Nome do candidato', 'Como o candidato se cadastrou.'],
  candidate_email:['E-mail do candidato', 'Para onde a mensagem vai.'],
  recruiter_name: ['Nome do recrutador', 'Quem está conduzindo o processo.'],
  recruiter_email:['E-mail do recrutador', 'Contato de resposta do processo.'],
  user_name:      ['Nome de quem envia', 'O usuário logado no momento do disparo.'],
  stage_name:     ['Etapa do processo', 'A etapa em que o candidato está.'],
  evaluation_url: ['Link da triagem', 'Endereço da conversa com a LIA.'],
  interview_date: ['Data da entrevista', 'Quando a entrevista foi marcada.'],
  date_br_today:  ['Data de hoje', 'No formato brasileiro.']
};

let catVarAberto = null;

function catVarFamilia(nome) {
  return CAT_VAR_CONTEUDO_DO_ENVIO.has(nome) ? 'conteudo_do_envio' : 'dado';
}

function catVarRotulo(nome) {
  const conhecida = CAT_VAR_DESCRICAO[nome];
  if (conhecida) return conhecida[0];
  return (nome.charAt(0).toUpperCase() + nome.slice(1)).replace(/_/g, ' ');
}

function catVarDescricao(nome, familia) {
  const conhecida = CAT_VAR_DESCRICAO[nome];
  if (conhecida) return conhecida[1];
  return CAT_VAR_FAMILIAS.find(f => f.id === familia).descricaoPadrao;
}

function catVarLista() {
  const t = catSelected;
  const nomes = (t && t.variables.length) ? t.variables : ['candidate_name', 'job_title', 'company_name'];
  return nomes;
}

/* O botao vive ao lado do rotulo do campo, e diz quantas variaveis aquela
   comunicacao tem -- como no painel. */
function catVarBotao(campo, rotuloDoCampo, readOnly) {
  const n = catVarLista().length;
  if (!n) return '';
  return `<button ${readOnly ? 'disabled' : ''} onclick="catVarToggle('${campo}')"
    data-testid="template-variaveis-do-${campo}"
    style="display:inline-flex; align-items:center; gap:6px; padding:4px 9px; border:1px solid #D1D5DB; background:white; border-radius:8px; font-size:11px; font-weight:600; color:#6B7280; cursor:${readOnly ? 'not-allowed' : 'pointer'}; opacity:${readOnly ? '.5' : '1'}; font-family:inherit;">
    <i data-lucide="variable" style="width:12px;height:12px;"></i> Inserir variável
    <span style="background:#F3F4F6; color:#9CA3AF; font-weight:400; font-size:10px; padding:0 5px; border-radius:6px;">${n}</span>
  </button>`;
}

function catVarPopover(campo, rotuloDoCampo) {
  const busca = (catVarAberto && catVarAberto.busca || '').trim().toLowerCase();
  const grupos = CAT_VAR_FAMILIAS.map(familia => ({
    familia,
    nomes: catVarLista().filter(nome => {
      if (catVarFamilia(nome) !== familia.id) return false;
      if (!busca) return true;
      return (nome + ' ' + catVarRotulo(nome) + ' ' + catVarDescricao(nome, familia.id)).toLowerCase().includes(busca);
    })
  })).filter(g => g.nomes.length);

  return `<div data-testid="template-variaveis" style="position:absolute; right:0; top:calc(100% + 6px); z-index:50; width:22rem; max-width:92vw; background:white; border:1px solid #E5E7EB; border-radius:12px; box-shadow:0 12px 32px rgba(0,0,0,.14); overflow:hidden;">
    <div style="border-bottom:1px solid #E5E7EB; padding:10px;">
      <div style="position:relative;">
        <i data-lucide="search" style="width:13px;height:13px;position:absolute;left:8px;top:50%;transform:translateY(-50%);color:#9CA3AF;"></i>
        <input id="cat-var-busca" value="${catEscape(catVarAberto.busca || '')}" oninput="catVarBuscar(this.value)" placeholder="Buscar variável"
               style="width:100%; padding:6px 8px 6px 27px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#111827; font-family:inherit;">
      </div>
      <p style="font-size:11px; color:#9CA3AF; margin:6px 0 0;">Entra no cursor do campo ${catEscape(rotuloDoCampo)}.</p>
    </div>
    <div style="max-height:13rem; overflow-y:auto; padding:8px;">
      ${grupos.length === 0
        ? '<p data-testid="template-variaveis-sem-resultado" style="padding:16px 4px; text-align:center; font-size:11px; color:#9CA3AF;">Nenhuma variável com esse nome.</p>'
        : grupos.map(g => `
        <section data-testid="template-familia" data-familia="${g.familia.id}" style="margin-bottom:8px;">
          <h3 style="margin:0 0 2px; padding:0 4px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:#6B7280;">${g.familia.titulo}</h3>
          <p style="margin:0 0 4px; padding:0 4px; font-size:11px; line-height:1.45; color:#9CA3AF;">${g.familia.dica}</p>
          ${g.nomes.map(nome => `
            <button data-testid="template-variavel" data-familia="${g.familia.id}" onclick="catVarInserir('${campo}','${nome}')"
              style="display:block; width:100%; text-align:left; padding:7px 8px; border:1px solid transparent; background:transparent; border-radius:8px; cursor:pointer; font-family:inherit;"
              onmouseover="this.style.background='#F3F4F6'; this.style.borderColor='#D1D5DB';"
              onmouseout="this.style.background='transparent'; this.style.borderColor='transparent';">
              <span style="display:flex; align-items:baseline; gap:6px;">
                <span style="font-size:12px; font-weight:600; color:#111827;">${catEscape(catVarRotulo(nome))}</span>
                <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11px; color:#2B7A8C;">{{${catEscape(nome)}}}</span>
              </span>
              <span style="display:block; margin-top:2px; font-size:11px; line-height:1.45; color:#9CA3AF;">${catEscape(catVarDescricao(nome, g.familia.id))}</span>
            </button>`).join('')}
        </section>`).join('')}
    </div>
  </div>`;
}

function catVarToggle(campo) {
  catVarAberto = (catVarAberto && catVarAberto.campo === campo) ? null : { campo: campo, busca: '' };
  catRenderContent();
}

function catVarBuscar(valor) {
  if (!catVarAberto) return;
  catVarAberto.busca = valor;
  const campo = catVarAberto.campo;
  catRenderContent();
  const input = document.getElementById('cat-var-busca');
  if (input) { input.focus(); input.selectionStart = input.selectionEnd = input.value.length; }
}

function catVarInserir(campo, nome) {
  catVarAberto = null;
  if (campo === 'assunto') {
    const el = document.getElementById('cat-in-subject');
    if (el) {
      const start = el.selectionStart, end = el.selectionEnd;
      el.value = el.value.slice(0, start) + '{{' + nome + '}}' + el.value.slice(end);
      catDraft.subject = el.value;
      catRefreshDirty();
      catRenderContent();
      return;
    }
  }
  catInsertVariable(nome);
  catRenderContent();
}

/* ----------------------------------------------------- editor do corpo

   Um campo so', com barra de formatacao, e o HTML atras de um botao para quem
   sabe o que esta fazendo -- o mesmo desenho do painel. A caixa de texto crua
   nao volta: quem escreve a comunicacao le o texto formatado, nao marcacao.

   WhatsApp fica de fora da formatacao de proposito: o canal entrega texto puro,
   sem negrito nem lista nem link. */

let catSourceView = false;

const CAT_TOOLBAR = [
  { cmd: 'bold',              icone: 'bold',         rotulo: 'Negrito' },
  { cmd: 'italic',            icone: 'italic',       rotulo: 'Itálico' },
  { divisor: true },
  { cmd: 'formatBlock:h2',    icone: 'type',         rotulo: 'Título de seção' },
  { cmd: 'insertUnorderedList', icone: 'table-2',    rotulo: 'Ficha de rótulo e valor' },
  { cmd: 'insertOrderedList', icone: 'list-ordered', rotulo: 'Passos numerados' },
  { cmd: 'createLink',        icone: 'link',         rotulo: 'Link' },
  { divisor: true },
  { cmd: 'undo',              icone: 'undo-2',       rotulo: 'Desfazer' },
  { cmd: 'redo',              icone: 'redo-2',       rotulo: 'Refazer' }
];

function catToHtmlBlocks(texto) {
  return String(texto || '')
    .split(/\n{2,}/)
    .map(bloco => `<p>${catEscape(bloco).replace(/\n/g, '<br>')}</p>`)
    .join('');
}

function catFromHtmlBlocks(el) {
  return Array.from(el.childNodes).map(no => {
    if (no.nodeType === Node.TEXT_NODE) return no.textContent;
    return no.innerText !== undefined ? no.innerText : no.textContent;
  }).join('\n\n').replace(/\n{3,}/g, '\n\n').trim();
}

function catToolbarBotao(item, readOnly) {
  if (item.divisor) return '<span style="width:1px; height:16px; background:#D1D5DB; margin:0 3px;"></span>';
  return `<button title="${item.rotulo}" aria-label="${item.rotulo}" ${readOnly ? 'disabled' : ''}
    onclick="catFormat('${item.cmd}')"
    style="display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border:none; background:transparent; border-radius:6px; color:#374151; cursor:${readOnly ? 'not-allowed' : 'pointer'}; opacity:${readOnly ? '.5' : '1'};"
    onmouseover="if(!this.disabled)this.style.background='#E5E7EB'" onmouseout="this.style.background='transparent'">
    <i data-lucide="${item.icone}" style="width:14px;height:14px;"></i></button>`;
}

function catBodyEditor(t, readOnly) {
  if (t.channel === 'whatsapp') {
    return `<textarea id="cat-in-body" oninput="catEdit('body', this.value)" rows="12" ${readOnly ? 'disabled' : ''}
      style="width:100%; ${readOnly ? 'background:#F3F4F6; color:#6B7280;' : ''} padding:11px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#111827; font-family:inherit; line-height:1.6; resize:vertical;">${catEscape(catDraft.body)}</textarea>
      <p style="font-size:11px; color:#6B7280; margin:6px 0 0;">WhatsApp entrega texto puro: sem negrito, lista ou link.</p>`;
  }
  return `
    <div data-testid="template-formatacao" style="display:flex; flex-wrap:wrap; align-items:center; gap:2px; border:1px solid #D1D5DB; background:#F9FAFB; border-radius:8px; padding:4px 6px; margin-bottom:6px;">
      ${CAT_TOOLBAR.map(i => catToolbarBotao(i, readOnly)).join('')}
      <span style="margin-left:auto; display:flex; align-items:center; gap:6px;">
        <span style="font-size:11px; color:#9CA3AF;">parágrafo = linha em branco</span>
        <button title="${catSourceView ? 'Voltar ao texto formatado' : 'Ver o HTML'}" aria-label="${catSourceView ? 'Voltar ao texto formatado' : 'Ver o HTML'}"
          onclick="catToggleSource()"
          style="display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border:none; border-radius:6px; cursor:pointer; background:${catSourceView ? '#E5E7EB' : 'transparent'}; color:#374151;">
          <i data-lucide="code-2" style="width:14px;height:14px;"></i></button>
      </span>
    </div>
    ${catSourceView
      ? `<textarea data-testid="template-corpo-html" readonly rows="12"
           style="width:100%; padding:11px; border:1px solid #D1D5DB; border-radius:8px; background:#F3F4F6; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11px; line-height:1.6; color:#111827; resize:vertical;">${catEscape(catToHtmlBlocks(catDraft.body))}</textarea>`
      : `<div id="cat-in-body" contenteditable="${readOnly ? 'false' : 'true'}" oninput="catEdit('body', catFromHtmlBlocks(this))"
           style="width:100%; min-height:220px; padding:11px; border:1px solid #D1D5DB; border-radius:8px; background:${readOnly ? '#F3F4F6' : 'white'}; font-size:12.5px; color:${readOnly ? '#6B7280' : '#111827'}; font-family:inherit; line-height:1.65; outline:none;">${catToHtmlBlocks(catDraft.body)}</div>`}
  `;
}

function catFormat(cmd) {
  const alvo = document.getElementById('cat-in-body');
  if (!alvo || alvo.getAttribute('contenteditable') !== 'true') return;
  alvo.focus();
  if (cmd === 'createLink') {
    const url = prompt('Endereço do link');
    if (url) document.execCommand('createLink', false, url);
  } else if (cmd.startsWith('formatBlock:')) {
    document.execCommand('formatBlock', false, cmd.split(':')[1]);
  } else {
    document.execCommand(cmd);
  }
  catEdit('body', catFromHtmlBlocks(alvo));
}

function catToggleSource() {
  catSourceView = !catSourceView;
  catRenderContent();
  if (window.lucide) lucide.createIcons();
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
  const alvo = document.getElementById('cat-in-body');
  if (!alvo) return;
  if (alvo.getAttribute('contenteditable') === 'true') {
    alvo.focus();
    document.execCommand('insertText', false, '{{' + v + '}}');
    catEdit('body', catFromHtmlBlocks(alvo));
    return;
  }
  const start = alvo.selectionStart, end = alvo.selectionEnd;
  alvo.value = alvo.value.slice(0, start) + '{{' + v + '}}' + alvo.value.slice(end);
  alvo.focus();
  alvo.selectionStart = alvo.selectionEnd = start + v.length + 4;
  catEdit('body', alvo.value);
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
  catAdjustModalWidth(aba);
  if (aba === 'preview') catRenderPreview();
}

/* A previa e' para ler a mensagem inteira, nao para rolar: nela o modal ocupa a
   largura util da tela e volta ao tamanho de leitura nas demais abas. */
function catAdjustModalWidth(aba) {
  const modal = document.getElementById('cat-modal');
  if (!modal) return;
  modal.style.width = aba === 'preview' ? '1180px' : '960px';
}

function catEmailCard(assunto, corpo) {
  const remetente = catScope === 'global' ? 'Empresa do cliente' : CURRENT_CLIENT;
  return `
    <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:20px;">
      <div style="max-width:760px; margin:0 auto; background:#fff; border:1px solid #E5E7EB; border-radius:12px; overflow:hidden;">
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

function catWhatsappConversation(corpo) {
  const remetente = catScope === 'global' ? 'Empresa do cliente' : CURRENT_CLIENT;
  const inicial = remetente.trim().charAt(0).toUpperCase() || '?';
  const agora = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  const corpoRenderizado = catHighlightVariables(corpo).replace(/\n/g, '<br>')
    || '<span style="color:#9CA3AF;">Sem corpo definido.</span>';
  return `
    <div style="max-width:520px; margin:0 auto; border:1px solid #E5E7EB; border-radius:14px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.06); display:flex; flex-direction:column; height:100%;">
      <div style="background:#075E54; padding:12px 14px; display:flex; align-items:center; gap:10px;">
        <span style="width:34px; height:34px; border-radius:50%; background:#128C7E; color:#fff; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:600;">${catEscape(inicial)}</span>
        <div style="min-width:0;">
          <div style="font-size:13px; font-weight:600; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${catEscape(remetente)}</div>
          <div style="font-size:11px; color:rgba(255,255,255,.72);">conta comercial</div>
        </div>
      </div>
      <div style="background:#ECE5DD; padding:16px 14px; flex:1; min-height:260px;">
        <div style="text-align:center; margin-bottom:14px;">
          <span style="background:#FDF4C6; color:#7A6A2F; font-size:10px; padding:4px 10px; border-radius:6px;">As mensagens são protegidas com criptografia de ponta a ponta.</span>
        </div>
        <div style="position:relative; background:#fff; border-radius:8px 8px 8px 2px; padding:9px 11px 6px 11px; max-width:86%; box-shadow:0 1px 1px rgba(0,0,0,.10); font-size:13.5px; color:#111827; line-height:1.55;">
          ${corpoRenderizado}
          <div style="text-align:right; font-size:10px; color:#9CA3AF; margin-top:4px;">${agora}</div>
        </div>
      </div>
    </div>`;
}

function catRenderPreview() {
  const t = catSelected;
  const painel = document.getElementById('cat-painel-preview');
  painel.style.height = '100%';
  painel.innerHTML = t.channel === 'whatsapp'
    ? `<p style="font-size:11px; color:#9CA3AF; margin:0 0 10px 0;">como chega no WhatsApp do candidato</p><div style="height:calc(100% - 26px);">${catWhatsappConversation(catDraft.body)}</div>`
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
    ${t.channel === 'whatsapp' ? '' : `
    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Assunto padrão</label>
    <div style="padding:9px 11px; border:1px solid #E5E7EB; background:#F9FAFB; border-radius:8px; font-size:13px; color:#374151; margin-bottom:16px;">${catHighlightVariables(t.defaultSubject) || '<span style="color:#9CA3AF;">sem assunto</span>'}</div>`}
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
    const meta = t.channel === 'whatsapp' && typeof mcMetaAccountCount === 'function'
      ? ` Submetido de novo à Meta nas ${mcMetaAccountCount()} contas de WhatsApp do cliente.` : '';
    catToast((wasDefault
      ? 'Salvo. Este cliente passa a ter a versão dele e não acompanha mais o padrão desta comunicação.'
      : 'Salvo para este cliente.') + meta);
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
  if (escopo === 'cliente' && typeof commGoTo === 'function') { commGoTo('textos'); return; }
  catScope = escopo;
  catClose();
  showScreen('screen-templates-globais');
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
