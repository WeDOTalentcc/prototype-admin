/* ==========================================================
   Catálogo de Templates de Comunicação — WEDO-3931
   Tela do painel interno onde a WeDO edita o texto de toda
   comunicação da plataforma. O cliente herda e personaliza.
   ========================================================== */

const catFiltro = { canal: 'todos', categoria: 'todas', publico: 'todos', busca: '' };
let catSelecionado = null;
let catRascunho = null;

const CAT_ROTULO_STATUS = {
  active:  { texto: 'Publicado', bg: '#DCFCE7', cor: '#166534' },
  dynamic: { texto: 'Texto de reserva', bg: '#FEF9C3', cor: '#854D0E' },
};

const CAT_ROTULO_CANAL = {
  email:    { texto: 'E-mail',   bg: 'rgba(96,190,209,.14)', cor: '#2B7A8C', icone: 'mail' },
  whatsapp: { texto: 'WhatsApp', bg: 'rgba(93,164,122,.14)', cor: '#3D7A56', icone: 'message-circle' },
};

function catEscapar(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* Destaca as variáveis {{x}} no meio do texto. */
function catRealcarVars(s) {
  return catEscapar(s).replace(/\{\{(\w+)\}\}/g,
    '<span style="background:rgba(96,190,209,.18); color:#1F6B7D; border-radius:4px; padding:1px 4px; font-weight:600;">{{$1}}</span>');
}

function catListaFiltrada() {
  const b = catFiltro.busca.trim().toLowerCase();
  return CATALOGO.filter(t => {
    if (catFiltro.canal !== 'todos' && t.channel !== catFiltro.canal) return false;
    if (catFiltro.categoria !== 'todas' && t.category !== catFiltro.categoria) return false;
    if (catFiltro.publico !== 'todos' && t.audience !== catFiltro.publico) return false;
    if (!b) return true;
    return (t.name + ' ' + t.key + ' ' + t.subject + ' ' + t.trigger + ' ' + t.source).toLowerCase().includes(b);
  });
}

function catRenderFiltros() {
  const categorias = [...new Set(CATALOGO.map(t => t.category))].sort();
  const publicos = [...new Set(CATALOGO.map(t => t.audience))].sort();
  const sel = (id, valor, opcoes, rotulo) =>
    `<select id="${id}" onchange="catSetFiltro('${valor}', this.value)" style="padding:7px 10px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#374151; background:white; font-family:inherit; cursor:pointer;">
       ${opcoes.map(o => `<option value="${o[0]}"${catFiltro[valor] === o[0] ? ' selected' : ''}>${o[1]}</option>`).join('')}
     </select>`;

  document.getElementById('cat-filtros').innerHTML = `
    <div style="position:relative; flex:1; min-width:200px;">
      <i data-lucide="search" style="width:14px;height:14px;position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#9CA3AF;"></i>
      <input id="cat-busca" value="${catEscapar(catFiltro.busca)}" oninput="catSetFiltro('busca', this.value)"
             placeholder="Buscar por chave, assunto ou gatilho"
             style="width:100%; padding:7px 10px 7px 30px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#374151; font-family:inherit;">
    </div>
    ${sel('cat-f-canal', 'canal', [['todos','Todos os canais'],['email','E-mail'],['whatsapp','WhatsApp']])}
    ${sel('cat-f-cat', 'categoria', [['todas','Todas as categorias']].concat(categorias.map(c => [c, c[0].toUpperCase()+c.slice(1)])))}
    ${sel('cat-f-pub', 'publico', [['todos','Todos os públicos']].concat(publicos.map(p => [p, p[0].toUpperCase()+p.slice(1)])))}
  `;
  if (window.lucide) lucide.createIcons();
}

function catSetFiltro(campo, valor) {
  catFiltro[campo] = valor;
  catRenderTabela();
  if (campo !== 'busca') catRenderFiltros();
}

function catRenderTabela() {
  const lista = catListaFiltrada();
  const corpo = document.getElementById('cat-tbody');
  document.getElementById('cat-contagem').textContent =
    lista.length + (lista.length === 1 ? ' comunicação' : ' comunicações');

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
    const st = CAT_ROTULO_STATUS[t.status] || CAT_ROTULO_STATUS.active;
    const ca = CAT_ROTULO_CANAL[t.channel];
    const heranca = t.custom.length
      ? `<span title="${catEscapar(t.custom.join(', '))}" style="background:#FEF3C7; color:#92400E; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">${t.custom.length} personalizou</span>`
      : `<span style="background:#F3F4F6; color:#6B7280; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px;">Todos herdam</span>`;
    return `
    <tr onclick="catAbrir('${t.key}','${t.channel}')" style="border-top:1px solid #F3F4F6; cursor:pointer; ${i % 2 ? 'background:#F9FAFB;' : ''}"
        onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='${i % 2 ? '#F9FAFB' : 'white'}'">
      <td style="padding:13px 20px;">
        <div style="font-size:13px; font-weight:600; color:#111827;">${catEscapar(t.name)}</div>
        <div style="font-size:12px; color:#6B7280; margin-top:2px;">${t.subject ? catEscapar(t.subject) : '<span style="color:#9CA3AF;">mensagem direta, sem assunto</span>'}</div>
        <div style="font-size:11px; color:#9CA3AF; margin-top:3px; font-family:monospace;">${catEscapar(t.key)}</div>
      </td>
      <td style="padding:13px 12px;">
        <span style="background:${ca.bg}; color:${ca.cor}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${ca.texto}</span>
        <div style="font-size:11px; color:#6B7280; margin-top:4px; text-transform:capitalize;">${catEscapar(t.audience)}</div>
      </td>
      <td style="padding:13px 12px; font-size:12px; color:#6B7280; max-width:300px;">${catEscapar(t.trigger)}</td>
      <td style="padding:13px 12px; text-align:center; white-space:nowrap;">${heranca}</td>
      <td style="padding:13px 20px; text-align:center;">
        <span style="background:${st.bg}; color:${st.cor}; font-size:11px; font-weight:600; padding:2px 8px; border-radius:99px; white-space:nowrap;">${st.texto}</span>
      </td>
    </tr>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

function catLimparFiltros() {
  catFiltro.canal = 'todos'; catFiltro.categoria = 'todas';
  catFiltro.publico = 'todos'; catFiltro.busca = '';
  catRenderFiltros(); catRenderTabela();
}

/* ---------------------------------------------------------- painel lateral */

function catAbrir(chave, canal) {
  catSelecionado = CATALOGO.find(t => t.key === chave && t.channel === canal);
  if (!catSelecionado) return;
  catRascunho = { subject: catSelecionado.subject, body: catSelecionado.body };
  document.getElementById('cat-drawer').style.transform = 'translateX(0)';
  document.getElementById('cat-drawer-backdrop').style.display = 'block';
  catRenderDrawer();
  catAba('conteudo');
}

function catFechar() {
  document.getElementById('cat-drawer').style.transform = 'translateX(100%)';
  document.getElementById('cat-drawer-backdrop').style.display = 'none';
  catSelecionado = null;
}

function catRenderDrawer() {
  const t = catSelecionado;
  const ca = CAT_ROTULO_CANAL[t.channel];
  document.getElementById('cat-drawer-titulo').textContent = t.name;
  document.getElementById('cat-drawer-sub').innerHTML =
    `<span style="font-family:monospace;">${catEscapar(t.key)}</span> ·
     <span style="color:${ca.cor}; font-weight:600;">${ca.texto}</span> ·
     <span style="text-transform:capitalize;">${catEscapar(t.audience)}</span>`;
  catRenderConteudo();
  catRenderClientes();
  catRenderHistorico();
}

function catRenderConteudo() {
  const t = catSelecionado;
  const vars = t.variables.length ? t.variables : ['candidate_name', 'job_title'];
  document.getElementById('cat-painel-conteudo').innerHTML = `
    ${t.note ? `<div style="background:#FFF7ED; border:1px solid #FED7AA; border-radius:8px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:#9A3412;">${catEscapar(t.note)}</div>` : ''}
    ${!t.body ? `<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:10px 12px; margin-bottom:16px; font-size:12px; color:#B91C1C;">O texto desta comunicação não está numa view de e-mail: ele é montado em <code style="background:none;">${catEscapar(t.source)}</code>. Precisa ser extraído de lá na migração para o catálogo.</div>` : ''}

    <label style="display:block; font-size:12px; font-weight:600; color:#374151; margin-bottom:6px;">Assunto</label>
    <input id="cat-in-subject" value="${catEscapar(catRascunho.subject)}" oninput="catEditar('subject', this.value)"
           ${t.channel === 'whatsapp' ? 'disabled placeholder="WhatsApp não tem assunto"' : ''}
           style="width:100%; padding:9px 11px; border:1px solid #D1D5DB; border-radius:8px; font-size:13px; color:#111827; font-family:inherit; margin-bottom:18px; ${t.channel === 'whatsapp' ? 'background:#F3F4F6; color:#9CA3AF;' : ''}">

    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
      <label style="font-size:12px; font-weight:600; color:#374151;">Corpo da mensagem</label>
      <span style="font-size:11px; color:#9CA3AF;">clique numa variável para inserir no cursor</span>
    </div>
    <div style="display:flex; flex-wrap:wrap; gap:5px; margin-bottom:8px;">
      ${vars.map(v => `<button onclick="catInserirVar('${v}')" style="padding:3px 8px; border:1px solid #D1D5DB; background:white; border-radius:6px; font-size:11px; color:#1F6B7D; font-family:monospace; cursor:pointer;" onmouseover="this.style.background='#F3F4F6'" onmouseout="this.style.background='white'">{{${v}}}</button>`).join('')}
    </div>
    <textarea id="cat-in-body" oninput="catEditar('body', this.value)" rows="12"
      style="width:100%; padding:11px; border:1px solid #D1D5DB; border-radius:8px; font-size:12px; color:#111827; font-family:inherit; line-height:1.6; resize:vertical;">${catEscapar(catRascunho.body)}</textarea>

    <div style="display:flex; gap:8px; margin-top:8px; align-items:center;">
      <span style="font-size:11px; color:#9CA3AF;">Origem no código:</span>
      <code style="font-size:11px; color:#6B7280; background:#F3F4F6; padding:2px 6px; border-radius:4px;">${catEscapar(t.source)}</code>
    </div>
    ${t.hasText ? `<p style="font-size:11px; color:#9A3412; margin-top:8px;">Esta comunicação também tem versão em texto puro, que precisa acompanhar a edição.</p>` : ''}
  `;
}

function catEditar(campo, valor) {
  catRascunho[campo] = valor;
  catMarcarSujo();
  if (document.getElementById('cat-painel-preview').style.display !== 'none') catRenderPreview();
}

function catMarcarSujo() {
  const sujo = catRascunho.subject !== catSelecionado.subject || catRascunho.body !== catSelecionado.body;
  document.getElementById('cat-btn-publicar').disabled = !sujo;
  document.getElementById('cat-btn-publicar').style.opacity = sujo ? '1' : '0.45';
  document.getElementById('cat-btn-publicar').style.cursor = sujo ? 'pointer' : 'not-allowed';
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
  ['conteudo', 'preview', 'clientes', 'historico'].forEach(a => {
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

function catRenderPreview() {
  const t = catSelecionado;
  const corpoHtml = catRealcarVars(catRascunho.body).replace(/\n/g, '<br>');

  if (t.channel === 'whatsapp') {
    document.getElementById('cat-painel-preview').innerHTML = `
      <p style="font-size:11px; color:#9CA3AF; margin:0 0 10px 0;">como chega no WhatsApp do candidato</p>
      <div style="background:#ECE5DD; border-radius:12px; padding:18px;">
        <div style="background:#fff; border-radius:8px 8px 8px 2px; padding:10px 12px; max-width:85%; box-shadow:0 1px 1px rgba(0,0,0,.08); font-size:13px; color:#111827; line-height:1.5;">
          ${corpoHtml || '<span style="color:#9CA3AF;">Sem corpo definido.</span>'}
          <div style="text-align:right; font-size:10px; color:#9CA3AF; margin-top:4px;">agora</div>
        </div>
      </div>`;
    return;
  }

  document.getElementById('cat-painel-preview').innerHTML = `
    <p style="font-size:11px; color:#9CA3AF; margin:0 0 10px 0;">como chega na caixa de entrada, dentro do layout do produto</p>
    <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:20px;">
      <div style="max-width:560px; margin:0 auto; background:#fff; border:1px solid #E5E7EB; border-radius:12px; overflow:hidden;">
        <div style="padding:18px 24px; border-bottom:1px solid #F3F4F6; display:flex; align-items:center; justify-content:space-between;">
          <span style="font-size:13px; font-weight:600; color:#6B7280;">WeDO Talent</span>
          <span style="width:8px;height:8px;border-radius:50%;background:#60BED1;display:inline-block;"></span>
        </div>
        <div style="padding:22px 24px;">
          <p style="margin:0 0 14px 0; font-size:11px; color:#9CA3AF; text-transform:uppercase; letter-spacing:.05em;">Assunto</p>
          <p style="margin:0 0 18px 0; font-size:15px; font-weight:600; color:#111827;">${catRealcarVars(catRascunho.subject) || '<span style="color:#9CA3AF;">sem assunto</span>'}</p>
          <div style="font-size:13px; color:#374151; line-height:1.65;">${corpoHtml || '<span style="color:#9CA3AF;">Sem corpo definido no catálogo.</span>'}</div>
        </div>
        <div style="background:#0d0d0d; padding:20px 24px;">
          <span style="display:inline-block; background:#1f1f1f; border-radius:4px; padding:6px 10px; font-size:12px; font-weight:700; color:#e5e7eb;">WeDO Talent</span>
          <p style="margin:10px 0 0 0; font-size:11px; color:#9ca3af;">Tecnologia avançada para o RH do futuro.</p>
        </div>
      </div>
    </div>`;
}

function catRenderClientes() {
  const t = catSelecionado;
  const todos = ['Sodexo', 'Talenses', 'Mappit', 'Grupo Boticário', 'Localiza'];
  document.getElementById('cat-painel-clientes').innerHTML = `
    <p style="font-size:12px; color:#6B7280; margin:0 0 14px 0;">
      Quem não personalizou acompanha o catálogo: publicar aqui muda o texto para esses clientes na hora.
    </p>
    <div style="border:1px solid #E5E7EB; border-radius:10px; overflow:hidden;">
      ${todos.map((c, i) => {
        const personalizou = t.custom.includes(c);
        return `<div style="display:flex; align-items:center; justify-content:space-between; padding:11px 14px; ${i ? 'border-top:1px solid #F3F4F6;' : ''} ${i % 2 ? 'background:#F9FAFB;' : ''}">
          <div>
            <div style="font-size:13px; font-weight:600; color:#111827;">${c}</div>
            <div style="font-size:11px; color:#6B7280; margin-top:2px;">${personalizou ? 'Escreveu o texto próprio, não recebe a atualização' : 'Herda o texto do catálogo'}</div>
          </div>
          ${personalizou
            ? `<button onclick="catVoltarPadrao('${c}')" style="padding:5px 10px; border:1px solid #FECACA; background:#FEF2F2; color:#B91C1C; border-radius:6px; font-size:12px; cursor:pointer; font-family:inherit;">Voltar ao padrão</button>`
            : `<span style="background:#F3F4F6; color:#6B7280; font-size:11px; font-weight:600; padding:3px 9px; border-radius:99px;">Herdado</span>`}
        </div>`;
      }).join('')}
    </div>`;
}

function catVoltarPadrao(cliente) {
  if (!confirm('Voltar ao padrão descarta o texto que ' + cliente + ' escreveu. Confirmar?')) return;
  catSelecionado.custom = catSelecionado.custom.filter(c => c !== cliente);
  catRenderClientes();
  catRenderTabela();
  catAviso(cliente + ' voltou a herdar o texto do catálogo.');
}

function catRenderHistorico() {
  const linhas = [
    ['Hoje, 14:02', 'Rodrigo Alfieri', 'Abriu o template para revisão de copy'],
    ['12/09/2026', 'Paulo Moraes', 'Ajustou o assunto'],
    ['16/06/2026', 'Sistema', 'Importado do código na criação do catálogo'],
  ];
  document.getElementById('cat-painel-historico').innerHTML = `
    <p style="font-size:12px; color:#6B7280; margin:0 0 14px 0;">Toda alteração fica registrada na trilha de auditoria, com autor e texto anterior.</p>
    ${linhas.map(([q, quem, oque]) => `
      <div style="display:flex; gap:12px; padding:11px 0; border-bottom:1px solid #F3F4F6;">
        <div style="width:110px; flex-shrink:0; font-size:11px; color:#9CA3AF;">${q}</div>
        <div>
          <div style="font-size:12px; font-weight:600; color:#111827;">${quem}</div>
          <div style="font-size:12px; color:#6B7280; margin-top:2px;">${oque}</div>
        </div>
      </div>`).join('')}`;
}

function catPublicar() {
  if (catRascunho.subject === catSelecionado.subject && catRascunho.body === catSelecionado.body) return;
  catSelecionado.subject = catRascunho.subject;
  catSelecionado.body = catRascunho.body;
  catMarcarSujo();
  catRenderDrawer();
  catRenderTabela();
  const herdam = 5 - catSelecionado.custom.length;
  catAviso('Publicado. ' + herdam + ' cliente(s) passam a usar este texto agora.');
}

function catDescartar() {
  catRascunho = { subject: catSelecionado.subject, body: catSelecionado.body };
  catRenderConteudo();
  catMarcarSujo();
}

function catAviso(msg) {
  const el = document.getElementById('cat-toast');
  el.textContent = msg;
  el.style.display = 'block';
  el.style.opacity = '1';
  clearTimeout(window._catToast);
  window._catToast = setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.style.display = 'none', 250); }, 3200);
}

function catRenderMortos() {
  document.getElementById('cat-mortos').innerHTML = CATALOGO_MORTOS.map(d => `
    <div style="display:flex; gap:10px; padding:9px 0; border-bottom:1px solid #F3F4F6;">
      <code style="font-size:11px; color:#6B7280; background:#F3F4F6; padding:2px 6px; border-radius:4px; height:fit-content; white-space:nowrap;">${catEscapar(d.source)}</code>
      <span style="font-size:12px; color:#6B7280;">${catEscapar(d.reason)}</span>
    </div>`).join('');
}

function catIniciar() {
  if (!document.getElementById('cat-tbody')) return;
  catRenderFiltros();
  catRenderTabela();
  catRenderMortos();
}

document.addEventListener('DOMContentLoaded', catIniciar);
document.addEventListener('keydown', e => { if (e.key === 'Escape' && catSelecionado) catFechar(); });
