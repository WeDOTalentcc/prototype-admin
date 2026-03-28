export function EstadoDesejado() {
  const domains = [
    { name: "evaluation", label: "Evaluation", color: "#6366f1" },
    { name: "autonomous", label: "Autonomous", color: "#8b5cf6" },
    { name: "applies", label: "Applies", color: "#ec4899" },
    { name: "screening", label: "Screening", color: "#f59e0b" },
    { name: "interview", label: "Interview", color: "#10b981" },
    { name: "learning", label: "Learning", color: "#3b82f6" },
    { name: "profile", label: "Profile", color: "#ef4444" },
    { name: "matching", label: "Matching", color: "#14b8a6" },
    { name: "future_A", label: "Futuro A", color: "#a78bfa" },
  ];

  const concerns = [
    { id: "C01", label: "Fairness Guard" },
    { id: "C02", label: "Bias Audit" },
    { id: "C03", label: "PII Pré-LLM" },
    { id: "C04", label: "Audit opt-in" },
    { id: "C05", label: "Audit imutável" },
    { id: "C06", label: "Retenção SOX" },
    { id: "C07", label: "Guardrails" },
    { id: "C08", label: "Prompt Inject." },
    { id: "C09", label: "Confidence" },
    { id: "C10", label: "Hiring Policy" },
    { id: "C11", label: "Fact Check" },
    { id: "C12", label: "Learning Gate" },
  ];

  const layers = [
    {
      id: "kernel",
      name: "ComplianceDomainPrompt (Kernel)",
      subtitle: "Herança automática — 1 arquivo governa todos os domínios",
      color: "#4f46e5",
      bg: "#1e1b4b",
      border: "#4338ca",
      items: [
        { icon: "⚡", text: "_setup_enhanced()", desc: "chama todos os guards na inicialização" },
        { icon: "🔒", text: "pii_masking_pipeline()", desc: "4 camadas antes de qualquer chamada LLM" },
        { icon: "⚖️", text: "fairness_gate()", desc: "14 categorias discriminatórias bloqueadas" },
        { icon: "📋", text: "bias_audit_decorator()", desc: "log automático em toda execução" },
        { icon: "🛡️", text: "guardrail_repository()", desc: "repositório central de regras" },
        { icon: "🔐", text: "prompt_injection_scanner()", desc: "jailbreak + injection detectados" },
        { icon: "📝", text: "audit_immutable_writer()", desc: "ON CONFLICT DO NOTHING + retenção 7 anos" },
        { icon: "📊", text: "confidence_threshold()", desc: "bloqueia respostas abaixo de 0.7" },
        { icon: "📜", text: "hiring_policy_enforcer()", desc: "diretrizes contratuais aplicadas" },
        { icon: "✅", text: "fact_check_gate()", desc: "hallucination prevention ativo" },
        { icon: "🎓", text: "learning_fairness_gate()", desc: "bias antes de qualquer aprendizado" },
        { icon: "🗃️", text: "sox_retention_manager()", desc: "WORM compliance automático" },
      ],
    },
    {
      id: "domains",
      name: "Domínios de Negócio",
      subtitle: "Implementam apenas a lógica específica — compliance já está garantido",
      color: "#059669",
      bg: "#022c22",
      border: "#065f46",
      items: domains.map(d => ({ icon: "▸", text: `${d.label}Domain`, desc: "extends ComplianceDomainPrompt", color: d.color })),
    },
  ];

  return (
    <div style={{ background: "#030712", minHeight: "100vh", fontFamily: "'Inter', system-ui, sans-serif", color: "#e5e7eb", padding: "32px" }}>
      <div style={{ maxWidth: "1100px", margin: "0 auto" }}>

        <div style={{ marginBottom: "28px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
            <div style={{ background: "#052e16", border: "1px solid #16a34a", borderRadius: "6px", padding: "6px 14px", fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", color: "#4ade80" }}>
              ✓ ESTADO DESEJADO — COMPLIANCE-BY-DESIGN
            </div>
            <div style={{ fontSize: "11px", color: "#6b7280" }}>Caminho 2 · ComplianceDomainPrompt · 3 semanas</div>
          </div>
          <h1 style={{ fontSize: "24px", fontWeight: 700, color: "#f9fafb", margin: "0 0 4px" }}>
            Arquitetura de Herança Automática de Compliance
          </h1>
          <p style={{ fontSize: "13px", color: "#9ca3af", margin: 0 }}>
            Um único kernel governa todos os 23 guards. Todo domínio — presente e futuro — herda compliance automaticamente.
          </p>
        </div>

        <div style={{ background: "#0f172a", border: "2px solid #1e3a5f", borderRadius: "16px", padding: "20px", marginBottom: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
            <span style={{ fontSize: "11px", color: "#93c5fd", fontWeight: 700, letterSpacing: "0.08em" }}>PRINCÍPIO CENTRAL</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px" }}>
            {[
              { label: "v5 (hoje)", code: "class EvaluationDomain:\n  def process_intent(self, req):\n    pii = self._manual_pii(req)  # esquece?\n    fair = self._manual_fair(pii) # esquece?\n    return self._execute(fair)", color: "#7f1d1d", border: "#dc2626", tag: "✗ FRÁGIL" },
              { label: "LIA (referência)", code: "class EvaluationAgent(\n  ComplianceDomainPrompt\n):\n  def _execute_logic(self, req):\n    # compliance já aplicado\n    return self._domain_logic(req)", color: "#052e16", border: "#16a34a", tag: "✓ ROBUSTO" },
              { label: "v5 (desejado)", code: "class EvaluationDomain(\n  ComplianceDomainPrompt\n):\n  def _execute_logic(self, req):\n    # mesma proteção LIA\n    return self._business(req)", color: "#1e3a5f", border: "#3b82f6", tag: "→ ALVO" },
            ].map(item => (
              <div key={item.label} style={{ background: item.color + "55", border: `1px solid ${item.border}`, borderRadius: "8px", padding: "12px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 700, color: "#d1d5db" }}>{item.label}</span>
                  <span style={{ fontSize: "10px", fontWeight: 700, color: item.border }}>{item.tag}</span>
                </div>
                <pre style={{ margin: 0, fontSize: "9.5px", color: "#94a3b8", lineHeight: "1.5", fontFamily: "'JetBrains Mono', 'Courier New', monospace", whiteSpace: "pre-wrap" }}>
                  {item.code}
                </pre>
              </div>
            ))}
          </div>
        </div>

        {layers.map(layer => (
          <div key={layer.id} style={{ background: layer.bg, border: `2px solid ${layer.border}`, borderRadius: "16px", padding: "20px", marginBottom: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <div style={{ background: layer.color + "33", border: `1px solid ${layer.color}`, borderRadius: "8px", padding: "8px 14px" }}>
                <div style={{ fontSize: "13px", fontWeight: 700, color: "#f9fafb" }}>{layer.name}</div>
                <div style={{ fontSize: "11px", color: "#9ca3af" }}>{layer.subtitle}</div>
              </div>
              {layer.id === "kernel" && (
                <div style={{ marginLeft: "auto", background: "#052e16", border: "1px solid #16a34a", borderRadius: "8px", padding: "8px 14px", textAlign: "center" }}>
                  <div style={{ fontSize: "20px", fontWeight: 800, color: "#4ade80" }}>100%</div>
                  <div style={{ fontSize: "10px", color: "#6b7280" }}>cobertura</div>
                </div>
              )}
              {layer.id === "domains" && (
                <div style={{ marginLeft: "auto", background: "#1e3a5f", border: "1px solid #3b82f6", borderRadius: "8px", padding: "8px 14px", textAlign: "center" }}>
                  <div style={{ fontSize: "20px", fontWeight: 800, color: "#93c5fd" }}>∞</div>
                  <div style={{ fontSize: "10px", color: "#6b7280" }}>futuros domínios</div>
                </div>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: layer.id === "kernel" ? "repeat(4, 1fr)" : "repeat(5, 1fr)", gap: "8px" }}>
              {layer.items.map((item, i) => (
                <div key={i} style={{
                  background: "#00000033",
                  border: `1px solid ${(item as any).color ? (item as any).color + "44" : layer.color + "33"}`,
                  borderRadius: "8px",
                  padding: "10px 12px",
                  borderLeft: `3px solid ${(item as any).color || layer.color}`,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "3px" }}>
                    <span style={{ fontSize: "14px" }}>{item.icon}</span>
                    <span style={{ fontSize: "10.5px", fontWeight: 700, color: "#e2e8f0", fontFamily: "'JetBrains Mono', monospace" }}>{item.text}</span>
                  </div>
                  <div style={{ fontSize: "10px", color: "#64748b" }}>{item.desc}</div>
                </div>
              ))}
              {layer.id === "domains" && (
                <div style={{
                  background: "#1e293b55",
                  border: "1px dashed #475569",
                  borderRadius: "8px",
                  padding: "10px 12px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "4px",
                }}>
                  <span style={{ fontSize: "18px" }}>＋</span>
                  <span style={{ fontSize: "10px", color: "#475569", textAlign: "center" }}>Futuro B<br />compliance<br />automático</span>
                </div>
              )}
            </div>
          </div>
        ))}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "16px" }}>
          {[
            { icon: "⏱", value: "3 semanas", label: "para implementação", color: "#4f46e5" },
            { icon: "📉", value: "−87%", label: "de linhas de compliance", color: "#059669" },
            { icon: "🛡️", value: "0 esquecimentos", label: "possíveis no futuro", color: "#0891b2" },
          ].map(item => (
            <div key={item.label} style={{ background: "#111827", border: "1px solid #1f2937", borderRadius: "12px", padding: "16px 20px", textAlign: "center" }}>
              <div style={{ fontSize: "24px", marginBottom: "4px" }}>{item.icon}</div>
              <div style={{ fontSize: "22px", fontWeight: 800, color: item.color }}>{item.value}</div>
              <div style={{ fontSize: "11px", color: "#6b7280" }}>{item.label}</div>
            </div>
          ))}
        </div>

        <div style={{ background: "#111827", border: "1px solid #374151", borderRadius: "12px", padding: "20px" }}>
          <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#f9fafb", marginBottom: "16px" }}>
            Mapa de Cobertura após Migração — todos os domínios
          </h3>
          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "separate", borderSpacing: "2px" }}>
              <thead>
                <tr>
                  <th style={{ width: "100px", fontSize: "10px", color: "#6b7280", textAlign: "left", padding: "4px 8px" }}></th>
                  {domains.map(d => (
                    <th key={d.name} style={{ padding: "2px 4px" }}>
                      <div style={{ background: "#1f2937", borderRadius: "4px", padding: "4px 6px", border: `1px solid ${d.color}44` }}>
                        <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: d.color, margin: "0 auto 2px" }} />
                        <div style={{ fontSize: "9px", color: "#d1d5db", fontWeight: 600, whiteSpace: "nowrap" }}>{d.name === "future_A" ? "Futuro A" : d.label}</div>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {concerns.map(c => (
                  <tr key={c.id}>
                    <td style={{ padding: "2px 8px 2px 0" }}>
                      <span style={{ fontSize: "9px", fontWeight: 700, color: "#6366f1", background: "#1e1b4b", borderRadius: "3px", padding: "1px 5px" }}>{c.id}</span>
                      <span style={{ fontSize: "10px", color: "#6b7280", marginLeft: "4px" }}>{c.label}</span>
                    </td>
                    {domains.map(d => (
                      <td key={d.name} style={{ padding: "2px" }}>
                        <div style={{
                          background: "#052e16",
                          border: "1px solid #16a34a",
                          borderRadius: "4px",
                          textAlign: "center",
                          padding: "5px 4px",
                          fontSize: "11px",
                          color: "#4ade80",
                          fontWeight: 700,
                          minWidth: "32px",
                        }}>
                          ✓
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: "12px", background: "#052e16", border: "1px solid #16a34a", borderRadius: "8px", padding: "10px 16px", display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "16px" }}>✓</span>
            <span style={{ fontSize: "12px", color: "#86efac" }}>
              <strong>100% de cobertura</strong> — incluindo Futuro A e qualquer domínio criado depois. Compliance é garantido pela arquitetura, não pela disciplina individual.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
