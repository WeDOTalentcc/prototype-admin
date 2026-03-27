export function EstadoAtual() {
  const domains = [
    { name: "evaluation", label: "Evaluation", color: "#6366f1" },
    { name: "autonomous", label: "Autonomous", color: "#8b5cf6" },
    { name: "applies", label: "Applies", color: "#ec4899" },
    { name: "screening", label: "Screening", color: "#f59e0b" },
    { name: "interview", label: "Interview", color: "#10b981" },
    { name: "learning", label: "Learning", color: "#3b82f6" },
    { name: "profile", label: "Profile", color: "#ef4444" },
    { name: "matching", label: "Matching", color: "#14b8a6" },
  ];

  const concerns = [
    { id: "C01", label: "Fairness Guard", severity: "CRÍTICO" },
    { id: "C02", label: "Bias Audit", severity: "CRÍTICO" },
    { id: "C03", label: "PII Pré-LLM", severity: "CRÍTICO" },
    { id: "C04", label: "Audit opt-in", severity: "CRÍTICO" },
    { id: "C05", label: "Audit imutável", severity: "CRÍTICO" },
    { id: "C06", label: "Retenção SOX", severity: "CRÍTICO" },
    { id: "C07", label: "Guardrails", severity: "CRÍTICO" },
    { id: "C08", label: "Prompt Inject.", severity: "CRÍTICO" },
    { id: "C09", label: "Confidence", severity: "ALTO" },
    { id: "C10", label: "Hiring Policy", severity: "ALTO" },
    { id: "C11", label: "Fact Check", severity: "ALTO" },
    { id: "C12", label: "Learning Gate", severity: "ALTO" },
  ];

  const coverage: Record<string, Record<string, "ok" | "partial" | "missing">> = {
    evaluation: {
      C01: "partial", C02: "partial", C03: "missing", C04: "ok", C05: "ok",
      C06: "missing", C07: "missing", C08: "missing", C09: "ok", C10: "ok", C11: "missing", C12: "missing",
    },
    autonomous: {
      C01: "missing", C02: "missing", C03: "missing", C04: "missing", C05: "missing",
      C06: "missing", C07: "partial", C08: "missing", C09: "missing", C10: "missing", C11: "missing", C12: "missing",
    },
    applies: {
      C01: "missing", C02: "missing", C03: "partial", C04: "missing", C05: "missing",
      C06: "missing", C07: "missing", C08: "missing", C09: "missing", C10: "partial", C11: "missing", C12: "missing",
    },
    screening: {
      C01: "ok", C02: "partial", C03: "missing", C04: "ok", C05: "ok",
      C06: "missing", C07: "missing", C08: "missing", C09: "partial", C10: "ok", C11: "missing", C12: "missing",
    },
    interview: {
      C01: "missing", C02: "missing", C03: "missing", C04: "missing", C05: "missing",
      C06: "missing", C07: "missing", C08: "missing", C09: "missing", C10: "missing", C11: "missing", C12: "missing",
    },
    learning: {
      C01: "missing", C02: "missing", C03: "missing", C04: "missing", C05: "missing",
      C06: "missing", C07: "missing", C08: "missing", C09: "missing", C10: "missing", C11: "missing", C12: "missing",
    },
    profile: {
      C01: "missing", C02: "missing", C03: "partial", C04: "missing", C05: "missing",
      C06: "missing", C07: "missing", C08: "missing", C09: "missing", C10: "missing", C11: "missing", C12: "missing",
    },
    matching: {
      C01: "partial", C02: "missing", C03: "missing", C04: "missing", C05: "missing",
      C06: "missing", C07: "missing", C08: "missing", C09: "partial", C10: "missing", C11: "missing", C12: "missing",
    },
  };

  const getCellStyle = (status: "ok" | "partial" | "missing") => {
    if (status === "ok") return { bg: "#052e16", border: "#16a34a", text: "#4ade80", icon: "✓" };
    if (status === "partial") return { bg: "#422006", border: "#d97706", text: "#fbbf24", icon: "~" };
    return { bg: "#1c0909", border: "#7f1d1d", text: "#f87171", icon: "✗" };
  };

  const getSeverityColor = (sev: string) => {
    if (sev === "CRÍTICO") return "#ef4444";
    if (sev === "ALTO") return "#f59e0b";
    return "#3b82f6";
  };

  const totalCells = domains.length * concerns.length;
  const okCount = Object.values(coverage).reduce((acc, domain) =>
    acc + Object.values(domain).filter(v => v === "ok").length, 0);
  const partialCount = Object.values(coverage).reduce((acc, domain) =>
    acc + Object.values(domain).filter(v => v === "partial").length, 0);
  const missingCount = totalCells - okCount - partialCount;

  return (
    <div style={{ background: "#0a0a0a", minHeight: "100vh", fontFamily: "'Inter', system-ui, sans-serif", color: "#e5e7eb", padding: "32px" }}>
      <div style={{ maxWidth: "1100px", margin: "0 auto" }}>

        <div style={{ marginBottom: "32px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
            <div style={{ background: "#7f1d1d", border: "1px solid #dc2626", borderRadius: "6px", padding: "6px 14px", fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", color: "#fca5a5" }}>
              ⚠ ESTADO ATUAL — v5 AUTOCONTIDO
            </div>
            <div style={{ fontSize: "11px", color: "#6b7280" }}>compliance-by-discipline · não escala com rotatividade de time</div>
          </div>
          <h1 style={{ fontSize: "24px", fontWeight: 700, color: "#f9fafb", margin: "0 0 4px" }}>
            Mapa de Cobertura de Compliance por Domínio
          </h1>
          <p style={{ fontSize: "13px", color: "#9ca3af", margin: 0 }}>
            Cada domínio implementa (ou não) seus próprios guards de forma independente e manual. Lacunas invisíveis em code reviews.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", marginBottom: "24px" }}>
          {[
            { color: "#4ade80", bg: "#052e16", border: "#16a34a", label: "Implementado", count: okCount },
            { color: "#fbbf24", bg: "#422006", border: "#d97706", label: "Parcial", count: partialCount },
            { color: "#f87171", bg: "#1c0909", border: "#7f1d1d", label: "Ausente", count: missingCount },
          ].map(item => (
            <div key={item.label} style={{ background: item.bg, border: `1px solid ${item.border}`, borderRadius: "8px", padding: "10px 16px", display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: item.color }} />
              <span style={{ fontSize: "12px", color: "#d1d5db" }}>{item.label}</span>
              <span style={{ fontSize: "16px", fontWeight: 700, color: item.color }}>{item.count}</span>
              <span style={{ fontSize: "11px", color: "#6b7280" }}>/ {totalCells}</span>
            </div>
          ))}
          <div style={{ flex: 1, background: "#111827", border: "1px solid #374151", borderRadius: "8px", padding: "10px 16px", display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "12px", color: "#9ca3af" }}>Cobertura real:</span>
            <span style={{ fontSize: "18px", fontWeight: 700, color: "#f87171" }}>
              {Math.round((okCount / totalCells) * 100)}%
            </span>
            <div style={{ flex: 1, height: "6px", background: "#1f2937", borderRadius: "3px", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${Math.round((okCount / totalCells) * 100)}%`, background: "linear-gradient(90deg, #dc2626, #ef4444)" }} />
            </div>
          </div>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: "2px" }}>
            <thead>
              <tr>
                <th style={{ width: "120px", textAlign: "left", padding: "6px 8px", fontSize: "11px", color: "#6b7280", fontWeight: 600 }}>
                  Concern ↓  /  Domínio →
                </th>
                {domains.map(d => (
                  <th key={d.name} style={{ padding: "6px 4px", textAlign: "center" }}>
                    <div style={{ background: "#1f2937", borderRadius: "6px", padding: "6px 8px", border: `1px solid ${d.color}44` }}>
                      <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: d.color, margin: "0 auto 3px" }} />
                      <div style={{ fontSize: "10px", color: "#d1d5db", fontWeight: 600, whiteSpace: "nowrap" }}>{d.label}</div>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {concerns.map(c => (
                <tr key={c.id}>
                  <td style={{ padding: "2px 8px 2px 0" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span style={{ fontSize: "9px", fontWeight: 700, color: getSeverityColor(c.severity), background: `${getSeverityColor(c.severity)}22`, borderRadius: "3px", padding: "1px 5px", letterSpacing: "0.05em" }}>
                        {c.id}
                      </span>
                      <span style={{ fontSize: "11px", color: "#9ca3af" }}>{c.label}</span>
                    </div>
                  </td>
                  {domains.map(d => {
                    const status = coverage[d.name]?.[c.id] || "missing";
                    const style = getCellStyle(status);
                    return (
                      <td key={d.name} style={{ padding: "2px" }}>
                        <div style={{
                          background: style.bg,
                          border: `1px solid ${style.border}`,
                          borderRadius: "4px",
                          textAlign: "center",
                          padding: "8px 4px",
                          fontSize: "14px",
                          color: style.text,
                          fontWeight: 700,
                        }}>
                          {style.icon}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: "28px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <div style={{ background: "#111827", border: "1px solid #374151", borderRadius: "12px", padding: "20px" }}>
            <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#f9fafb", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "#ef4444" }}>✗</span> Por que isso falha em produção
            </h3>
            {[
              { text: "Novo domínio nasce sem nenhum guard de compliance", highlight: "interview · learning" },
              { text: "Code review não detecta ausência — só detecta presença incorreta", highlight: "invisível" },
              { text: "Rotatividade de time = compliance regride sem aviso", highlight: "não escala" },
              { text: "Mesmo critério: bloqueia em 1 domínio, passa em outros 7", highlight: "inconsistência" },
            ].map((item, i) => (
              <div key={i} style={{ display: "flex", gap: "10px", marginBottom: "8px" }}>
                <div style={{ width: "4px", background: "#dc2626", borderRadius: "2px", flexShrink: 0 }} />
                <div>
                  <span style={{ fontSize: "12px", color: "#9ca3af" }}>{item.text} </span>
                  <span style={{ fontSize: "11px", color: "#f87171", fontWeight: 600 }}>[{item.highlight}]</span>
                </div>
              </div>
            ))}
          </div>

          <div style={{ background: "#111827", border: "1px solid #374151", borderRadius: "12px", padding: "20px" }}>
            <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#f9fafb", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "#f59e0b" }}>⚡</span> Custos ocultos do modelo autocontido
            </h3>
            {[
              { label: "Duplicação", desc: "cada memory.py reinventa pii_masking" },
              { label: "Divergência", desc: "3 implementações distintas de 'anonimizar'" },
              { label: "8× revisão", desc: "qualquer mudança de policy = 8 PRs" },
              { label: "Auditoria", desc: "SOX/LGPD exige 7 anos de imutabilidade" },
            ].map((item, i) => (
              <div key={i} style={{ display: "flex", gap: "10px", marginBottom: "8px", alignItems: "flex-start" }}>
                <div style={{ background: "#422006", border: "1px solid #d97706", borderRadius: "4px", padding: "2px 8px", fontSize: "10px", fontWeight: 700, color: "#fbbf24", flexShrink: 0, whiteSpace: "nowrap" }}>
                  {item.label}
                </div>
                <span style={{ fontSize: "12px", color: "#9ca3af" }}>{item.desc}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: "16px", background: "#0f172a", border: "1px solid #1e3a5f", borderRadius: "8px", padding: "14px 18px", display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ fontSize: "20px" }}>🔍</span>
          <div>
            <div style={{ fontSize: "12px", fontWeight: 700, color: "#93c5fd" }}>Problema raiz identificado</div>
            <div style={{ fontSize: "12px", color: "#64748b" }}>
              <strong style={{ color: "#e2e8f0" }}>compliance-by-discipline</strong> — o sistema depende de que cada desenvolvedor, em cada PR, lembre de implementar todos os 23 guards. Com rotatividade, isso regride inevitavelmente.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
