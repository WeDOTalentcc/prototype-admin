# Quando NÃO Pular Dimensões

> Parte da skill `feature-audit`. Carregue quando precisar deste topico especifico.

### Para Features de Frontend/Produto:
- Features pequenas (1 arquivo): Dimensão 1 (wiring) + Dimensão 3 (UI/DS) + Dimensão 6 (fluxo)
- Ajustes de estilo: Dimensão 3 (UI/DS v4.2.1) + Dimensão 7 (consistência)
- Novas telas/páginas: Dimensões 1-8 obrigatórias + D13 (segurança) + D14 (performance)

### Para Features de IA/Backend:
- Novo domínio/agente: Dimensões 9, 10, 11, 12 obrigatórias + D4 (backend) + D13 (segurança)
- Novo prompt/intent: Dimensão 10 (qualidade LLM) + D12 (governança)
- Nova integração externa: Dimensão 11 (serviços) + D13 (segurança) + D14 (performance)
- Feature flag IA: Dimensão 12 (governança)

### Para Features Full-Stack:
- Pipeline/transição: TODAS as 14 dimensões obrigatórias
- Correções de bug: Dimensão 2 (dados) + Dimensão 6 (fluxo) + dimensão do layer afetado
