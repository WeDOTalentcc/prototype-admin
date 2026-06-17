"""Shared manager briefing HTML builder — single source of truth.

Moved here from wizard_service_tools.py (v2) to avoid circular imports
between wizard_service_tools.py and publish.py.
Both files import from here.
"""

import logging

logger = logging.getLogger(__name__)


def build_manager_briefing_html(state: dict) -> str:
    """Monta HTML do briefing executivo para o gestor — v2.

    Secoes: cabecalho estruturado, JD, matriz de competencias (tecnicas x
    comportamentais), BigFive, cronograma com datas absolutas, remuneracao
    (salario + variavel + beneficios), triagem configurada.
    Sem referencia a nome de produto IA — neutro "IA WeDOTalent".
    """
    from datetime import date, timedelta

    # ---- dados basicos -------------------------------------------------
    title      = state.get("parsed_title") or "Vaga"
    seniority  = state.get("parsed_seniority") or ""
    department = state.get("parsed_department") or ""
    work_model = state.get("work_model") or ""
    emp_type   = state.get("employment_type") or ""
    job_id     = state.get("job_id") or ""
    today      = date.today()
    today_str  = today.strftime("%d/%m/%Y")

    mgr_name   = state.get("parsed_manager_name") or "Gestor"
    mgr_email  = state.get("parsed_manager_email") or ""
    rec_name   = state.get("parsed_recruiter_name") or state.get("recruiter_name") or "Recrutador"

    jd_full    = state.get("jd_enriched") or ""
    jd_excerpt = jd_full[:700] + ("…" if len(jd_full) > 700 else "")

    # ---- salario -------------------------------------------------------
    salary_min = state.get("salary_min")
    salary_max = state.get("salary_max")
    if salary_min and salary_max:
        salary_str = "R$ {:,.0f} – R$ {:,.0f}".format(salary_min, salary_max).replace(",", ".")
    elif salary_min:
        salary_str = "A partir de R$ {:,.0f}".format(salary_min).replace(",", ".")
    else:
        salary_str = ""
    salary_source = state.get("salary_source") or ""

    # ---- competencias --------------------------------------------------
    raw_comps = state.get("competencies") or []
    tech_comps, soft_comps = [], []
    for c in raw_comps[:16]:
        name  = (c.get("name") if isinstance(c, dict) else str(c))
        level = (c.get("level") or c.get("proficiency") or "") if isinstance(c, dict) else ""
        kind  = (c.get("type") or c.get("category") or "technical") if isinstance(c, dict) else "technical"
        entry = (name, level)
        if str(kind).lower() in {"behavioral", "comportamental", "soft", "behavior"}:
            soft_comps.append(entry)
        else:
            tech_comps.append(entry)
    if not soft_comps and tech_comps:
        mid = max(1, len(tech_comps) // 2)
        soft_comps = tech_comps[mid:]
        tech_comps = tech_comps[:mid]

    LEVEL_LABEL = {
        "expert": "Especialista", "especialista": "Especialista",
        "advanced": "Avancado", "avancado": "Avancado",
        "essential": "Essencial", "essencial": "Essencial",
        "required": "Requerido", "requerido": "Requerido",
        "desirable": "Desejavel", "desejavel": "Desejavel",
        "intermediate": "Intermediario",
    }
    LEVEL_COLOR = {
        "Especialista": "#085041", "Essencial": "#085041",
        "Avancado": "#3C3489", "Intermediario": "#3C3489",
        "Desejavel": "#5F5E5A", "Requerido": "#5F5E5A",
    }
    LEVEL_BG = {
        "Especialista": "#E1F5EE", "Essencial": "#E1F5EE",
        "Avancado": "#EEEDFE", "Intermediario": "#EEEDFE",
        "Desejavel": "#F1EFE8", "Requerido": "#F1EFE8",
    }

    def _comp_rows(comps):
        rows = []
        for name, level in comps[:7]:
            label = LEVEL_LABEL.get((level or "").lower().strip(), level or "Requerido")
            fg    = LEVEL_COLOR.get(label, "#5F5E5A")
            bg    = LEVEL_BG.get(label, "#F1EFE8")
            rows.append(
                "<tr>"
                "<td style=\"padding:6px 10px;font-size:12px;color:#333;border-bottom:1px solid #eee\">" + name + "</td>"
                "<td style=\"padding:6px 10px;text-align:right;border-bottom:1px solid #eee\">"
                "<span style=\"font-size:10px;padding:2px 7px;border-radius:20px;"
                "background:" + bg + ";color:" + fg + ";font-weight:500\">" + label + "</span>"
                "</td></tr>"
            )
        return "".join(rows)

    comp_block = ""
    if tech_comps or soft_comps:
        comp_block = (
            "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
            "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
            "padding-bottom:6px;margin-bottom:10px\">Competências requeridas</div>"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"margin-bottom:20px\"><tr>"
            "<td width=\"50%\" style=\"vertical-align:top;padding-right:8px\">"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"border:1px solid #eee;border-radius:6px;overflow:hidden\">"
            "<tr style=\"background:#E1F5EE\"><th style=\"padding:7px 10px;font-size:11px;font-weight:500;color:#085041;text-align:left\">Técnicas</th></tr>"
            + _comp_rows(tech_comps) +
            "</table></td>"
            "<td width=\"50%\" style=\"vertical-align:top;padding-left:8px\">"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"border:1px solid #eee;border-radius:6px;overflow:hidden\">"
            "<tr style=\"background:#EEEDFE\"><th style=\"padding:7px 10px;font-size:11px;font-weight:500;color:#3C3489;text-align:left\">Comportamentais</th></tr>"
            + _comp_rows(soft_comps) +
            "</table></td>"
            "</tr></table>"
        )

    # ---- BigFive -------------------------------------------------------
    BF_LABELS = {
        "openness": "Abertura", "conscientiousness": "Conscienciosidade",
        "extraversion": "Extroversão", "agreeableness": "Amabilidade",
        "neuroticism": "Neuroticismo", "estabilidade": "Estabilidade",
        "abertura": "Abertura", "conscienciosidade": "Conscienciosidade",
    }
    BF_COLORS = ["#7F77DD", "#1D9E75", "#378ADD", "#D85A30", "#888780"]
    bigfive = state.get("bigfive_profile") or {}
    bf_cells = ""
    for i, (k, v) in enumerate(bigfive.items()):
        if not isinstance(v, (int, float)):
            continue
        pct = int(round(float(v) * 100 if float(v) <= 1 else float(v)))
        lbl = BF_LABELS.get(k.lower(), k.capitalize())
        col = BF_COLORS[i % len(BF_COLORS)]
        bf_cells += (
            "<td style=\"padding:6px 8px;vertical-align:top;width:20%\">"
            "<div style=\"font-size:10px;color:#888;margin-bottom:2px\">" + lbl + "</div>"
            "<div style=\"font-size:15px;font-weight:500;color:#222\">" + str(pct) + "%</div>"
            "<div style=\"height:4px;background:#eee;border-radius:2px;margin-top:3px;overflow:hidden\">"
            "<div style=\"height:100%;width:" + str(pct) + "%;background:" + col + ";border-radius:2px\"></div>"
            "</div></td>"
        )
    bf_block = ""
    if bf_cells:
        bf_block = (
            "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
            "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
            "padding-bottom:6px;margin-bottom:10px\">Perfil comportamental ideal</div>"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\"><tr>" + bf_cells + "</tr></table>"
            "<div style=\"font-size:10px;color:#aaa;margin-bottom:20px\">"
            "Extraído da descrição da vaga pela inteligência artificial da WeDOTalent"
            "</div>"
        )

    # ---- cronograma ----------------------------------------------------
    chronogram = state.get("derived_chronogram") or []
    DOT_COLORS = ["#1D9E75", "#7F77DD", "#378ADD", "#D85A30", "#888780",
                  "#EF9F27", "#9FE1CB", "#AFA9EC"]
    chron_block = ""
    if chronogram:
        TYPE_LABEL = {"automatic": "Automática", "manual": "Manual", "hybrid": "Híbrida"}
        rows = ""
        for i, stage in enumerate(chronogram):
            start_d = today + timedelta(days=int(stage.get("offset_start", 0)))
            end_d   = today + timedelta(days=int(stage.get("offset_end", stage.get("sla_days", 0))))
            dot     = DOT_COLORS[i % len(DOT_COLORS)]
            s_type  = TYPE_LABEL.get(str(stage.get("type", "")).lower(), "")
            type_td = ("<div style=\"font-size:10px;color:#888\">" + s_type + "</div>") if s_type else ""
            rows += (
                "<tr>"
                "<td style=\"padding:7px 0;border-bottom:1px solid #eee;vertical-align:middle;width:14px\">"
                "<div style=\"width:10px;height:10px;border-radius:50%;background:" + dot + "\"></div></td>"
                "<td style=\"padding:7px 8px;border-bottom:1px solid #eee\">"
                "<div style=\"font-size:12px;color:#222\">" + stage["name"] + "</div>" + type_td + "</td>"
                "<td style=\"padding:7px 8px;border-bottom:1px solid #eee;text-align:center;"
                "font-size:12px;color:#888\">" + str(stage["sla_days"]) + " dias</td>"
                "<td style=\"padding:7px 0;border-bottom:1px solid #eee;text-align:right\">"
                "<span style=\"font-size:11px;color:#888\">" + start_d.strftime("%d/%m") + " → </span>"
                "<span style=\"font-size:11px;font-weight:500;color:#222\">" + end_d.strftime("%d/%m") + "</span>"
                "</td></tr>"
            )
        last_end = today + timedelta(days=int(chronogram[-1].get("offset_end", 0)))
        rows += (
            "<tr><td colspan=\"4\" style=\"padding-top:8px\">"
            "<div style=\"background:#E1F5EE;padding:6px 10px;border-radius:6px;"
            "display:flex;justify-content:space-between\">"
            "<span style=\"font-size:12px;color:#5F5E5A\">Previsão de contratação</span>"
            "<span style=\"font-size:12px;font-weight:500;color:#0F6E56\">até " +
            last_end.strftime("%d/%m/%Y") + "</span></div></td></tr>"
        )
        chron_block = (
            "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
            "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
            "padding-bottom:6px;margin-bottom:10px\">Cronograma do processo seletivo</div>"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"margin-bottom:20px\">"
            + rows + "</table>"
        )

    # ---- remuneracao variavel ------------------------------------------
    var_comps = state.get("variable_compensation") or []
    var_rows = ""
    for vc in var_comps[:6]:
        if isinstance(vc, dict):
            name = vc.get("name") or vc.get("kind") or "Componente"
            pct  = vc.get("target_pct") or vc.get("max_pct")
            amt  = vc.get("max_amount")
            val_str = ("até " + str(pct) + "%") if pct else (
                "até R$ {:,.0f}".format(amt).replace(",", ".") if amt else "—"
            )
            var_rows += (
                "<tr>"
                "<td style=\"padding:5px 0;border-bottom:1px solid #eee;font-size:12px;color:#333\">" + name + "</td>"
                "<td style=\"padding:5px 0;border-bottom:1px solid #eee;text-align:right;"
                "font-size:12px;font-weight:500;color:#0F6E56\">" + val_str + "</td>"
                "</tr>"
            )

    # ---- beneficios ----------------------------------------------------
    benefits = state.get("benefits") or []
    ben_tags = ""
    for b in benefits[:12]:
        label = (b.get("name") or b.get("label") or str(b)) if isinstance(b, dict) else str(b)
        ben_tags += (
            "<span style=\"display:inline-block;font-size:11px;padding:3px 9px;"
            "border-radius:20px;background:#F1EFE8;color:#5F5E5A;margin:3px 4px 0 0;"
            "border:0.5px solid #D3D1C7\">" + label + "</span>"
        )

    # ---- bloco remuneracao completo ------------------------------------
    salary_td = ""
    if salary_str:
        source_div = ("<div style=\"font-size:11px;color:#888;margin-top:2px\">" + salary_source + "</div>") if salary_source else ""
        salary_td = (
            "<td width=\"50%\" style=\"vertical-align:top;padding-right:8px\">"
            "<div style=\"border:1px solid #eee;border-radius:6px;padding:10px 12px\">"
            "<div style=\"font-size:10px;color:#888;margin-bottom:2px\">Salário base</div>"
            "<div style=\"font-size:16px;font-weight:600;color:#222\">" + salary_str + "</div>"
            + source_div + "</div></td>"
        )
    var_td = ""
    if var_rows:
        var_td = (
            "<td width=\"50%\" style=\"vertical-align:top;padding-left:8px\">"
            "<div style=\"border:1px solid #eee;border-radius:6px;padding:10px 12px\">"
            "<div style=\"font-size:10px;color:#888;margin-bottom:6px\">Remuneração variável</div>"
            "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\">" + var_rows + "</table>"
            "</div></td>"
        )
    rem_block = ""
    if salary_td or var_td or ben_tags:
        rem_block = (
            "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
            "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
            "padding-bottom:6px;margin-bottom:10px\">Remuneração &amp; benefícios</div>"
        )
        if salary_td or var_td:
            rem_block += (
                "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"margin-bottom:12px\">"
                "<tr>" + (salary_td or "<td></td>") + (var_td or "<td></td>") + "</tr></table>"
            )
        if ben_tags:
            rem_block += (
                "<div style=\"font-size:11px;color:#888;margin-bottom:4px\">Benefícios incluísos</div>"
                "<div style=\"margin-bottom:20px\">" + ben_tags + "</div>"
            )

    # ---- triagem -------------------------------------------------------
    screening_mode = (state.get("screening_mode") or "wsi").upper()
    n_q       = len(state.get("wsi_questions") or [])
    dist      = state.get("expected_distribution") or {}
    threshold = dist.get("threshold") if isinstance(dist, dict) else 3.75
    threshold = threshold or 3.75

    # ---- cabecalho -----------------------------------------------------
    subtitle_parts = [p for p in [seniority, emp_type, work_model] if p]
    subtitle = " · ".join(subtitle_parts)
    mgr_to   = mgr_name + (" &lt;" + mgr_email + "&gt;" if mgr_email else "")
    job_badge = ""
    if job_id:
        job_badge = (
            "<div style=\"font-size:10px;color:#fff;background:rgba(255,255,255,.15);"
            "display:inline-block;padding:2px 9px;border-radius:20px;margin-top:6px\">"
            "Job ID " + str(job_id) + " · Publicada em " + today_str + "</div>"
        )
    total_days_td = ""
    if chronogram:
        total_d = str(chronogram[-1].get("offset_end", ""))
        total_days_td = (
            "<td align=\"right\" style=\"vertical-align:top\">"
            "<div style=\"font-size:10px;color:#5DCAA5\">Processo estimado</div>"
            "<div style=\"font-size:22px;font-weight:600;color:#fff\">" + total_d + " dias</div>"
            "</td>"
        )
    subtitle_div = ""
    if subtitle:
        subtitle_div = "<div style=\"font-size:12px;color:#5DCAA5;margin-top:3px\">" + subtitle + "</div>"

    html = (
        "<!DOCTYPE html>"
        "<html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width\"></head>"
        "<body style=\"margin:0;padding:0;font-family:Arial,sans-serif;background:#f5f5f5\">"
        "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" "
        "style=\"background:#f5f5f5;padding:24px 0\"><tr><td align=\"center\">"
        "<table width=\"640\" cellspacing=\"0\" cellpadding=\"0\" "
        "style=\"background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e0e0e0\">"

        # cabecalho verde
        "<tr><td style=\"background:#0F6E56;padding:20px 28px\">"
        "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\"><tr>"
        "<td>"
        "<div style=\"font-size:10px;font-weight:500;color:#9FE1CB;"
        "letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px\">"
        "WeDOTalent · Briefing de Contratação</div>"
        "<div style=\"font-size:18px;font-weight:600;color:#fff;line-height:1.3\">" + title + "</div>"
        + subtitle_div + job_badge +
        "</td>" + total_days_td + "</tr></table></td></tr>"

        # barra destinatario
        "<tr><td style=\"background:#085041;padding:10px 28px\">"
        "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" "
        "style=\"font-size:12px\"><tr>"
        "<td style=\"color:#5DCAA5;width:60px\">Para</td>"
        "<td style=\"color:#E1F5EE\">" + mgr_to + "</td>"
        "<td style=\"color:#5DCAA5;width:80px\">Recrutador</td>"
        "<td style=\"color:#E1F5EE\">" + rec_name + "</td>"
        "<td style=\"color:#5DCAA5;width:60px;padding-left:12px\">Enviado</td>"
        "<td style=\"color:#E1F5EE\">" + today_str + "</td>"
        "</tr></table></td></tr>"

        # corpo
        "<tr><td style=\"padding:22px 28px\">"

        # JD
        "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
        "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
        "padding-bottom:6px;margin-bottom:10px\">Descrição da vaga</div>"
        "<div style=\"font-size:13px;line-height:1.7;color:#555;border-left:3px solid #1D9E75;"
        "padding:8px 14px;background:#f9f9f9;border-radius:0 6px 6px 0;margin-bottom:20px\">"
        + jd_excerpt + "</div>"

        + comp_block + bf_block + chron_block + rem_block +

        # triagem
        "<div style=\"font-size:10px;font-weight:500;text-transform:uppercase;"
        "letter-spacing:.07em;color:#888;border-bottom:1px solid #eee;"
        "padding-bottom:6px;margin-bottom:10px\">Triagem automática configurada</div>"
        "<div>"
        "<span style=\"font-size:11px;padding:3px 9px;border-radius:20px;"
        "background:#EEEDFE;color:#534AB7;font-weight:500;margin-right:6px\">"
        + screening_mode + " · " + str(n_q) + " perguntas</span>"
        "<span style=\"font-size:11px;padding:3px 9px;border-radius:20px;"
        "background:#EAF3DE;color:#3B6D11;font-weight:500\">"
        "Aprovação automática ≥ " + str(threshold) + "</span>"
        "</div>"

        "</td></tr>"

        # rodape
        "<tr><td style=\"padding:12px 28px;border-top:1px solid #eee;"
        "font-size:11px;color:#aaa\">"
        "Gerado automaticamente pela inteligência artificial da WeDOTalent · " + today_str +
        "</td></tr>"

        "</table></td></tr></table></body></html>"
    )
    return html
