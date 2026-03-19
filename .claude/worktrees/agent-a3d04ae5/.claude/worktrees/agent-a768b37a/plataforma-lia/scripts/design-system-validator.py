#!/usr/bin/env python3
"""
Design System LIA v4.1 - Validator & Auto-Fixer
================================================

Script completo e robusto para validar e corrigir automaticamente componentes 
React/Tailwind seguindo o Design System LIA v4.1.

Baseado em:
- docs/design-system/00-design-system-v4.md
- docs/PROMPTS-DESIGN-PADRONIZACAO.md
- src/lib/design-tokens.ts

ESPECIFICAÇÕES IMPLEMENTADAS:
- Tipografia: Open Sans 85%, Inter 10%, Source Serif 4 5% (apenas sidebar)
- Cores: 90% grayscale + 10% accent (cyan #60BED1 apenas para LIA)
- Espaçamento: base 4px
- Cards: rounded-xl obrigatório
- Botões primários: bg-gray-900 (preto)
- Dark mode: obrigatório em todos componentes
- Focus ring: ring-gray-900/20 (grayscale)

FASES DE VALIDAÇÃO:
- Fase 0: Inventário (informativo)
- Fase 1: Setup Base (fontes, tailwind config)
- Fase 2: Botões
- Fase 3: Inputs e Forms
- Fase 4: Cards e Containers
- Fase 5: Navegação e Sidebar (tipografia)
- Fase 6: Modais e Componentes Avançados
- Fase 7: Badges e Utilities
- Fase 8: Validação Final (tokens, imports)

Uso:
  python scripts/design-system-validator.py [opções] [arquivos]

Exemplos:
  python scripts/design-system-validator.py --validate src/components/
  python scripts/design-system-validator.py --fix src/components/settings/
  python scripts/design-system-validator.py -v --report --output report.json src/
  python scripts/design-system-validator.py --phase 2 src/components/ui/Button.tsx

@version 4.1
@updated 2026-02
"""

import re
import os
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import json
from datetime import datetime

# ============================================================
# DESIGN SYSTEM v4.1 - ESPECIFICAÇÕES COMPLETAS
# ============================================================

DESIGN_SYSTEM = {
    "version": "4.1",
    "updated": "Fevereiro 2026",
    
    # TIPOGRAFIA
    "typography": {
        "open_sans": {
            "usage": "85%",
            "scope": "UI geral - headers, labels, botões, body text, títulos de cards",
            "tailwind": "font-['Open_Sans',sans-serif]",
            "token": "textStyles.body, textStyles.title, textStyles.h1-h4"
        },
        "inter": {
            "usage": "10%",
            "scope": "APENAS métricas numéricas, KPIs, números em tabelas, dashboards",
            "tailwind": "font-['Inter',sans-serif]",
            "token": "textStyles.metric, textStyles.metricLarge"
        },
        "source_serif_4": {
            "usage": "5%",
            "scope": "APENAS sidebar/navigation",
            "tailwind": "font-['Source_Serif_4',serif]",
            "token": "textStyles.sidebarItem, textStyles.sidebarTitle"
        }
    },
    
    # CORES
    "colors": {
        "philosophy": "90% grayscale + 10% accent",
        "primary_button": "bg-gray-900",
        "primary_button_hover": "bg-gray-800",
        "primary_button_dark": "dark:bg-gray-50 dark:text-gray-900",
        "secondary_button": "border border-gray-300 bg-white",
        "focus_ring": "ring-2 ring-gray-900/20",
        "wedo_cyan": "#60BED1",
        "wedo_cyan_usage": "APENAS para LIA/IA (brain icon, Sparkles, Bot icons, badges LIA)",
        "text_primary": "text-gray-900 dark:text-gray-50",
        "text_body": "text-gray-800 dark:text-gray-200",
        "text_secondary": "text-gray-600 dark:text-gray-400",
        "text_muted": "text-gray-500",
        "border_subtle": "border-gray-200 dark:border-gray-700",
        "border_default": "border-gray-300 dark:border-gray-600",
        "bg_primary": "bg-white dark:bg-gray-900",
        "bg_secondary": "bg-gray-50 dark:bg-gray-800",
    },
    
    # ESPAÇAMENTO
    "spacing": {
        "base": "4px",
        "scale": {
            "0.5": "2px",
            "1": "4px",
            "2": "8px",
            "3": "12px",
            "4": "16px",
            "5": "20px",
            "6": "24px",
            "8": "32px",
            "10": "40px",
            "12": "48px",
            "16": "64px"
        }
    },
    
    # COMPONENTES
    "components": {
        "cards": {
            "border_radius": "rounded-xl",
            "border": "border border-gray-200 dark:border-gray-700",
            "shadow": "shadow-sm",
            "token": "cardStyles.default"
        },
        "buttons": {
            "primary": "bg-gray-900 text-white hover:bg-gray-800",
            "primary_dark": "dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200",
            "secondary": "bg-white border border-gray-300 hover:bg-gray-50",
            "token": "buttonStyles.primary, buttonStyles.secondary"
        },
        "inputs": {
            "focus_ring": "focus:ring-2 focus:ring-gray-900/20 focus:border-gray-900",
            "token": "inputStyles.default"
        },
        "badges": {
            "lia_only_cyan": True,
            "token": "badgeStyles.*"
        },
        "modals": {
            "border_radius": "rounded-xl",
            "token": "modalStyles.*"
        }
    },
    
    # ÍCONES LIA (cyan permitido)
    "lia_icons": ["Sparkles", "Brain", "Bot", "Wand2", "Cpu", "Zap", "Lightbulb"],
    
    # CORES PROIBIDAS EM BOTÕES
    "prohibited_button_colors": [
        "bg-cyan", "bg-blue-500", "bg-blue-600", "bg-blue-700",
        "bg-[#60BED1]", "bg-teal", "bg-sky"
    ],
    
    # DESIGN TOKENS
    "design_tokens_path": "src/lib/design-tokens.ts",
    "design_tokens_import": "from '@/lib/design-tokens'",
}

# ============================================================
# MAPEAMENTO DE CLASSES INLINE → TOKENS
# ============================================================

INLINE_TO_TOKEN_MAPPING = {
    # Text Styles
    "font-['Open_Sans',sans-serif] text-[24px] font-semibold text-gray-900": "textStyles.h1",
    "font-['Open_Sans',sans-serif] text-[18px] font-semibold text-gray-900": "textStyles.h2",
    "font-['Open_Sans',sans-serif] text-[14px] font-semibold text-gray-900": "textStyles.h3",
    "font-['Open_Sans',sans-serif] text-[13px] font-semibold text-gray-900": "textStyles.h4",
    "font-['Open_Sans',sans-serif] text-[12px] font-normal text-gray-800": "textStyles.body",
    "font-['Open_Sans',sans-serif] text-[11px] font-normal text-gray-800": "textStyles.bodySmall",
    "font-['Open_Sans',sans-serif] text-[11px] font-medium text-gray-800": "textStyles.label",
    "font-['Inter',sans-serif] text-[14px] font-semibold text-gray-900": "textStyles.metric",
    "font-['Inter',sans-serif] text-[24px] font-semibold text-gray-900": "textStyles.metricLarge",
    "font-['Source_Serif_4',serif] text-[12px] font-medium text-gray-700": "textStyles.sidebarItem",
    
    # Button Styles
    "bg-gray-900 text-white hover:bg-gray-800": "buttonStyles.primary",
    "bg-gray-900 hover:bg-gray-800 text-white": "buttonStyles.primary",
    "bg-white border border-gray-300 hover:bg-gray-50": "buttonStyles.outline",
    "bg-gray-100 hover:bg-gray-200 text-gray-700": "buttonStyles.secondary",
    "bg-red-600 hover:bg-red-700 text-white": "buttonStyles.destructive",
    
    # Card Styles
    "bg-white border border-gray-200 rounded-xl shadow-sm": "cardStyles.default",
    "bg-white border border-gray-200 rounded-xl shadow-md": "cardStyles.elevated",
    
    # Badge Styles
    "bg-green-50 text-green-700": "badgeStyles.success",
    "bg-amber-50 text-amber-700": "badgeStyles.warning",
    "bg-red-50 text-red-700": "badgeStyles.error",
    "bg-blue-50 text-blue-700": "badgeStyles.info",
    "bg-gray-100 text-gray-700": "badgeStyles.default",
}

# ============================================================
# REGRAS DE VALIDAÇÃO POR FASE
# ============================================================

@dataclass
class Rule:
    """Representa uma regra do Design System"""
    id: str
    phase: int
    severity: str  # error, warning, info
    description: str
    pattern: str
    fix_pattern: Optional[str] = None
    fix_replacement: Optional[str] = None
    context_check: Optional[str] = None
    token_suggestion: Optional[str] = None


VALIDATION_RULES: List[Rule] = [
    # FASE 1: Setup Base
    Rule(
        id="FONT_IMPORT_MISSING",
        phase=1,
        severity="info",
        description="Verificar se design-tokens.ts está importado",
        pattern=r"^(?!.*design-tokens).*$",
        context_check="check_imports",
        token_suggestion="import { textStyles, buttonStyles, cardStyles } from '@/lib/design-tokens'"
    ),
    
    # FASE 2: Botões
    Rule(
        id="BUTTON_CYAN_PRIMARY",
        phase=2,
        severity="error",
        description="Botão primário não deve usar cyan/blue - usar bg-gray-900",
        pattern=r"(?:<button|<Button)[^>]*className=[\"'][^\"']*(?:bg-cyan-\d+|bg-blue-500|bg-blue-600|bg-blue-700|bg-\[#60BED1\])",
        fix_pattern=r"(bg-cyan-\d+|bg-blue-500|bg-blue-600|bg-blue-700|bg-\[#60BED1\])",
        fix_replacement="bg-gray-900",
        token_suggestion="buttonStyles.primary"
    ),
    Rule(
        id="BUTTON_FOCUS_RING_CYAN",
        phase=2,
        severity="warning",
        description="Focus ring deve ser grayscale (ring-gray-900/20), não cyan",
        pattern=r"(?:<button|<Button)[^>]*className=[\"'][^\"']*(?:ring-cyan|ring-blue|ring-\[#60BED1\]|focus:ring-cyan)",
        fix_pattern=r"(ring-cyan-\d+|ring-blue-\d+|ring-\[#60BED1\]|focus:ring-cyan-\d+)",
        fix_replacement="ring-gray-900/20",
        token_suggestion="buttonStyles.primary inclui focus ring correto"
    ),
    Rule(
        id="BUTTON_MISSING_DARK_MODE",
        phase=2,
        severity="warning",
        description="Botão primário deve ter variante dark mode",
        pattern=r"(?:<button|<Button)[^>]*className=[\"'][^\"']*bg-gray-900(?![^\"']*dark:)",
        token_suggestion="buttonStyles.primary inclui dark mode"
    ),
    Rule(
        id="BUTTON_PRIMARY_CORRECT",
        phase=2,
        severity="info",
        description="Botão com classes inline que podem usar token",
        pattern=r"bg-gray-900\s+text-white\s+hover:bg-gray-800",
        token_suggestion="buttonStyles.primary"
    ),
    
    # FASE 3: Inputs e Forms
    Rule(
        id="INPUT_FOCUS_RING_CYAN",
        phase=3,
        severity="warning",
        description="Input focus ring deve ser grayscale, não cyan",
        pattern=r"<input[^>]*className=[\"'][^\"']*(?:focus:ring-cyan|focus:border-cyan|focus:ring-\[#60BED1\])",
        fix_pattern=r"(focus:ring-cyan-\d+|focus:border-cyan-\d+|focus:ring-\[#60BED1\])",
        fix_replacement="focus:ring-gray-900/20",
        token_suggestion="inputStyles.default"
    ),
    Rule(
        id="INPUT_MISSING_FOCUS_STYLES",
        phase=3,
        severity="info",
        description="Input pode estar sem estilos de focus adequados",
        pattern=r"<input[^>]*className=[\"'][^\"']*border[^\"']*(?!focus:)",
        token_suggestion="inputStyles.default"
    ),
    Rule(
        id="LABEL_TYPOGRAPHY",
        phase=3,
        severity="info",
        description="Label pode usar token de tipografia",
        pattern=r"<label[^>]*className=[\"'][^\"']*text-\[\d+px\][^\"']*font-medium",
        token_suggestion="textStyles.label"
    ),
    
    # FASE 4: Cards e Containers
    Rule(
        id="CARD_ROUNDED_MD",
        phase=4,
        severity="warning",
        description="Cards devem usar rounded-xl, não rounded-md",
        pattern=r"(?:bg-white|border)[^\"']*rounded-md(?![^\"']*(?:w-[4-9]|h-[4-9]|icon|Icon))",
        fix_pattern=r"rounded-md",
        fix_replacement="rounded-xl",
        token_suggestion="cardStyles.default"
    ),
    Rule(
        id="CARD_MISSING_DARK_MODE",
        phase=4,
        severity="warning",
        description="Card deve ter variante dark mode",
        pattern=r"bg-white\s+border\s+border-gray-200(?![^\"']*dark:)",
        token_suggestion="cardStyles.default inclui dark mode"
    ),
    Rule(
        id="CARD_INLINE_CLASSES",
        phase=4,
        severity="info",
        description="Card com classes inline pode usar token",
        pattern=r"bg-white\s+border\s+border-gray-200\s+rounded-xl\s+shadow-sm",
        token_suggestion="cardStyles.default"
    ),
    
    # FASE 5: Navegação e Sidebar (Tipografia)
    Rule(
        id="TYPOGRAPHY_SOURCE_SERIF_WRONG_CONTEXT",
        phase=5,
        severity="error",
        description="Source Serif 4 usado fora de sidebar (apenas permitido em navigation)",
        pattern=r"font-\['Source_Serif_4'[^\]]*\][^\"']*(?!sidebar|Sidebar|nav|Nav)",
        context_check="check_not_sidebar",
        fix_pattern=r"font-\['Source_Serif_4'[^\]]*\]",
        fix_replacement="font-['Open_Sans',sans-serif]",
        token_suggestion="textStyles.body ou textStyles.title"
    ),
    Rule(
        id="TYPOGRAPHY_CARD_TITLE_WRONG_FONT",
        phase=5,
        severity="error",
        description="Título de card/dialog não deve usar Source Serif 4",
        pattern=r"(?:<h[1-6]|<DialogTitle|<CardTitle|CardHeader)[^>]*className=[\"'][^\"']*font-\['Source_Serif_4",
        fix_pattern=r"font-\['Source_Serif_4'[^\]]*\]",
        fix_replacement="font-['Open_Sans',sans-serif]",
        token_suggestion="textStyles.h3 ou textStyles.title"
    ),
    Rule(
        id="TYPOGRAPHY_INTER_WRONG_CONTEXT",
        phase=5,
        severity="warning",
        description="Inter deve ser usado apenas para números/métricas",
        pattern=r"font-\['Inter'[^\"']*(?!.*(?:metric|kpi|number|data|percent|score|\d))",
        context_check="check_not_numeric",
        token_suggestion="textStyles.metric apenas para dados numéricos"
    ),
    
    # FASE 6: Modais e Componentes Avançados
    Rule(
        id="MODAL_ROUNDED_MD",
        phase=6,
        severity="warning",
        description="Modal deve usar rounded-xl",
        pattern=r"(?:Dialog|Modal|Sheet)[^>]*className=[\"'][^\"']*rounded-md",
        fix_pattern=r"rounded-md",
        fix_replacement="rounded-xl",
        token_suggestion="modalStyles.container"
    ),
    Rule(
        id="MODAL_MISSING_DARK_MODE",
        phase=6,
        severity="warning",
        description="Modal deve ter suporte a dark mode",
        pattern=r"(?:DialogContent|ModalContent)[^>]*className=[\"'][^\"']*bg-white(?![^\"']*dark:)",
        token_suggestion="modalStyles.container"
    ),
    Rule(
        id="DIALOG_OVERLAY_CORRECT",
        phase=6,
        severity="info",
        description="Dialog overlay pode usar token",
        pattern=r"bg-black/50\s+backdrop-blur",
        token_suggestion="modalStyles.overlay"
    ),
    
    # FASE 7: Badges e Utilities
    Rule(
        id="BADGE_CYAN_NON_LIA",
        phase=7,
        severity="warning",
        description="Cyan (#60BED1) usado sem contexto LIA/IA",
        pattern=r"className=[\"'][^\"']*(?:text-\[#60BED1\]|bg-\[#60BED1\]|border-\[#60BED1\])",
        context_check="check_lia_context",
        token_suggestion="badgeStyles.cyan (apenas com ícones LIA)"
    ),
    Rule(
        id="BADGE_STATUS_INLINE",
        phase=7,
        severity="info",
        description="Badge de status com classes inline pode usar token",
        pattern=r"bg-(?:green|amber|red|blue)-50\s+text-(?:green|amber|red|blue)-700",
        token_suggestion="badgeStyles.success/warning/error/info"
    ),
    Rule(
        id="SWITCH_CYAN_NON_LIA",
        phase=7,
        severity="warning",
        description="Switch/Toggle com cyan deve ser apenas para LIA",
        pattern=r"(?:Switch|Toggle)[^>]*className=[\"'][^\"']*(?:bg-\[#60BED1\]|bg-cyan)",
        context_check="check_lia_context",
        token_suggestion="Switch padrão: bg-gray-900, cyan apenas em LiaFieldToggle"
    ),
    
    # FASE 8: Validação Final
    Rule(
        id="DARK_MODE_MISSING_BG",
        phase=8,
        severity="warning",
        description="Componente principal sem dark mode",
        pattern=r"<(?:div|section|article|main|aside)[^>]*className=[\"'][^\"']*bg-(?:white|gray-50|gray-100)(?![^\"']*dark:)",
        token_suggestion="Adicionar dark:bg-gray-800 ou dark:bg-gray-900"
    ),
    Rule(
        id="DARK_MODE_MISSING_TEXT",
        phase=8,
        severity="info",
        description="Texto sem variante dark mode",
        pattern=r"text-gray-(?:900|800|700)(?![^\"']*dark:text)",
        token_suggestion="Adicionar dark:text-gray-50/100/200"
    ),
    Rule(
        id="DARK_MODE_MISSING_BORDER",
        phase=8,
        severity="info",
        description="Borda sem variante dark mode",
        pattern=r"border-gray-(?:200|300)(?![^\"']*dark:border)",
        token_suggestion="Adicionar dark:border-gray-600/700"
    ),
    Rule(
        id="TOKENS_IMPORT_MISSING",
        phase=8,
        severity="info",
        description="Arquivo não importa design-tokens.ts",
        pattern=r"^(?!.*(?:design-tokens|from\s+['\"]@/lib/design-tokens))",
        context_check="check_no_token_import",
        token_suggestion="import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'"
    ),
    Rule(
        id="INLINE_CLASSES_TOKENIZABLE",
        phase=8,
        severity="info",
        description="Classes inline podem ser substituídas por tokens",
        pattern=r"className=[\"'][^\"']{100,}",
        token_suggestion="Considere usar tokens do design-tokens.ts"
    ),
]

# ============================================================
# CLASSES DE DADOS
# ============================================================

@dataclass
class Violation:
    """Representa uma violação do Design System"""
    file: str
    line: int
    column: int
    rule_id: str
    phase: int
    severity: str
    message: str
    suggestion: str
    original_code: str
    fixed_code: Optional[str] = None
    token_suggestion: Optional[str] = None
    auto_fixable: bool = False

    def to_dict(self) -> Dict:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "rule_id": self.rule_id,
            "phase": self.phase,
            "severity": self.severity,
            "message": self.message,
            "suggestion": self.suggestion,
            "token_suggestion": self.token_suggestion,
            "original_code": self.original_code[:100] + "..." if len(self.original_code) > 100 else self.original_code,
            "auto_fixable": self.auto_fixable
        }


@dataclass
class FileResult:
    """Resultado da validação de um arquivo"""
    file: str
    violations: List[Violation] = field(default_factory=list)
    imports_design_tokens: bool = False
    component_count: int = 0
    
    @property
    def passed(self) -> bool:
        return not any(v.severity == "error" for v in self.violations)
    
    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")
    
    @property
    def info_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "info")


@dataclass
class ValidationReport:
    """Relatório completo de validação"""
    version: str = "4.1"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    files_analyzed: int = 0
    files_passed: int = 0
    files_with_errors: int = 0
    files_with_warnings: int = 0
    total_violations: int = 0
    violations_by_phase: Dict[str, int] = field(default_factory=dict)
    violations_by_severity: Dict[str, int] = field(default_factory=dict)
    violations_by_rule: Dict[str, int] = field(default_factory=dict)
    files_without_tokens: List[str] = field(default_factory=list)
    details: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "design_system_version": self.version,
            "timestamp": self.timestamp,
            "summary": {
                "files_analyzed": self.files_analyzed,
                "files_passed": self.files_passed,
                "files_with_errors": self.files_with_errors,
                "files_with_warnings": self.files_with_warnings,
                "total_violations": self.total_violations,
            },
            "violations_by_phase": self.violations_by_phase,
            "violations_by_severity": self.violations_by_severity,
            "violations_by_rule": self.violations_by_rule,
            "files_without_tokens": self.files_without_tokens,
            "details": self.details
        }


# ============================================================
# VALIDADOR PRINCIPAL
# ============================================================

class DesignSystemValidator:
    """Validador completo do Design System LIA v4.1"""
    
    def __init__(
        self,
        verbose: bool = False,
        phase_filter: Optional[int] = None,
        check_tokens: bool = True
    ):
        self.verbose = verbose
        self.phase_filter = phase_filter
        self.check_tokens = check_tokens
        self.results: Dict[str, FileResult] = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compila todos os padrões regex para performance"""
        self.compiled_rules: Dict[str, Tuple[Rule, re.Pattern]] = {}
        
        for rule in VALIDATION_RULES:
            if self.phase_filter and rule.phase != self.phase_filter:
                continue
            try:
                pattern = re.compile(rule.pattern, re.IGNORECASE | re.MULTILINE)
                self.compiled_rules[rule.id] = (rule, pattern)
            except re.error as e:
                if self.verbose:
                    print(f"⚠️ Erro ao compilar regex para {rule.id}: {e}")
        
        # Padrões adicionais para contexto
        self.pattern_lia_icons = re.compile(
            r'<(?:' + '|'.join(DESIGN_SYSTEM['lia_icons']) + r')[^>]*',
            re.IGNORECASE
        )
        self.pattern_sidebar_context = re.compile(
            r'(?:sidebar|Sidebar|nav-sidebar|navigation|Navigation)',
            re.IGNORECASE
        )
        self.pattern_import_tokens = re.compile(
            r"(?:import\s+.*from\s+['\"].*design-tokens|from\s+['\"]@/lib/design-tokens)",
            re.IGNORECASE
        )
        self.pattern_numeric_context = re.compile(
            r'(?:metric|kpi|percent|score|count|total|number|data-|tabular|\d+%|\d+\.\d)',
            re.IGNORECASE
        )
    
    def validate_file(self, filepath: str) -> FileResult:
        """Valida um arquivo contra o Design System"""
        result = FileResult(file=filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            result.violations.append(Violation(
                file=filepath,
                line=0,
                column=0,
                rule_id="FILE_READ_ERROR",
                phase=0,
                severity="error",
                message=f"Não foi possível ler o arquivo: {e}",
                suggestion="Verifique permissões do arquivo",
                original_code=""
            ))
            self.results[filepath] = result
            return result
        
        # Verificar import de design-tokens
        result.imports_design_tokens = bool(self.pattern_import_tokens.search(content))
        
        # Contar componentes
        result.component_count = len(re.findall(r'(?:function|const)\s+\w+\s*(?:=|)\s*(?:\([^)]*\)|)\s*(?:=>|{)', content))
        
        # Executar todas as regras
        for rule_id, (rule, pattern) in self.compiled_rules.items():
            self._check_rule(filepath, lines, content, rule, pattern, result)
        
        # Verificações especiais
        self._check_inline_to_token(filepath, lines, content, result)
        
        self.results[filepath] = result
        return result
    
    def _check_rule(
        self,
        filepath: str,
        lines: List[str],
        content: str,
        rule: Rule,
        pattern: re.Pattern,
        result: FileResult
    ):
        """Verifica uma regra específica"""
        
        # Pular arquivos de configuração para certas regras
        if self._should_skip_file(filepath, rule):
            return
        
        for i, line in enumerate(lines, 1):
            for match in pattern.finditer(line):
                # Verificar contexto se necessário
                if rule.context_check and not self._check_context(
                    rule.context_check, lines, i, content
                ):
                    continue
                
                # Determinar se é auto-corrigível
                auto_fixable = rule.fix_pattern is not None and rule.fix_replacement is not None
                
                # Gerar código corrigido se possível
                fixed_code = None
                if auto_fixable and rule.fix_pattern and rule.fix_replacement:
                    fixed_code = re.sub(rule.fix_pattern, rule.fix_replacement, line)
                
                violation = Violation(
                    file=filepath,
                    line=i,
                    column=match.start(),
                    rule_id=rule.id,
                    phase=rule.phase,
                    severity=rule.severity,
                    message=rule.description,
                    suggestion=self._generate_suggestion(rule, match.group()),
                    original_code=line.strip(),
                    fixed_code=fixed_code.strip() if fixed_code else None,
                    token_suggestion=rule.token_suggestion,
                    auto_fixable=auto_fixable
                )
                result.violations.append(violation)
    
    def _check_context(
        self,
        check_type: str,
        lines: List[str],
        line_num: int,
        content: str
    ) -> bool:
        """Verifica contexto para regras condicionais"""
        
        # Pegar contexto (5 linhas antes e depois)
        start = max(0, line_num - 6)
        end = min(len(lines), line_num + 5)
        context = '\n'.join(lines[start:end])
        
        if check_type == "check_lia_context":
            # Verificar se há ícone LIA próximo
            return not bool(self.pattern_lia_icons.search(context))
        
        elif check_type == "check_not_sidebar":
            # Verificar se NÃO está em contexto de sidebar
            return not bool(self.pattern_sidebar_context.search(context))
        
        elif check_type == "check_not_numeric":
            # Verificar se NÃO está em contexto numérico
            return not bool(self.pattern_numeric_context.search(context))
        
        elif check_type == "check_no_token_import":
            # Verificar se NÃO tem import de tokens
            return not bool(self.pattern_import_tokens.search(content))
        
        elif check_type == "check_imports":
            return not bool(self.pattern_import_tokens.search(content))
        
        return True
    
    def _should_skip_file(self, filepath: str, rule: Rule) -> bool:
        """Determina se um arquivo deve ser pulado para uma regra"""
        skip_patterns = [
            'tailwind.config',
            'design-tokens',
            '.test.',
            '.spec.',
            '.stories.',
            'node_modules',
            '.d.ts'
        ]
        return any(pattern in filepath for pattern in skip_patterns)
    
    def _generate_suggestion(self, rule: Rule, matched_text: str) -> str:
        """Gera sugestão de correção"""
        if rule.fix_replacement:
            return f"Substituir '{matched_text[:50]}...' por '{rule.fix_replacement}'"
        return rule.description
    
    def _check_inline_to_token(
        self,
        filepath: str,
        lines: List[str],
        content: str,
        result: FileResult
    ):
        """Verifica se classes inline podem ser substituídas por tokens"""
        if not self.check_tokens:
            return
        
        for token_pattern, token_name in INLINE_TO_TOKEN_MAPPING.items():
            if token_pattern in content:
                for i, line in enumerate(lines, 1):
                    if token_pattern in line:
                        result.violations.append(Violation(
                            file=filepath,
                            line=i,
                            column=0,
                            rule_id="TOKEN_SUGGESTION",
                            phase=8,
                            severity="info",
                            message=f"Classes inline podem ser substituídas por token",
                            suggestion=f"Considere usar: {token_name}",
                            original_code=line.strip()[:80],
                            token_suggestion=token_name
                        ))
                        break  # Uma sugestão por padrão
    
    def fix_file(self, filepath: str) -> Tuple[bool, int]:
        """Aplica correções automáticas em um arquivo"""
        result = self.results.get(filepath)
        if not result:
            result = self.validate_file(filepath)
        
        fixable_violations = [v for v in result.violations if v.auto_fixable and v.fixed_code]
        
        if not fixable_violations:
            return True, 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return False, 0
        
        original_content = content
        fixes_applied = 0
        
        # Ordenar por linha (reverso) para não afetar posições
        fixable_violations.sort(key=lambda v: v.line, reverse=True)
        
        lines = content.split('\n')
        
        for violation in fixable_violations:
            if violation.line <= len(lines):
                line_idx = violation.line - 1
                original_line = lines[line_idx]
                
                # Aplicar fix específico da regra
                rule = next((r for r in VALIDATION_RULES if r.id == violation.rule_id), None)
                if rule and rule.fix_pattern and rule.fix_replacement:
                    new_line = re.sub(rule.fix_pattern, rule.fix_replacement, original_line)
                    if new_line != original_line:
                        lines[line_idx] = new_line
                        fixes_applied += 1
        
        new_content = '\n'.join(lines)
        
        if new_content != original_content:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True, fixes_applied
            except Exception:
                return False, 0
        
        return True, fixes_applied
    
    def generate_report(self) -> ValidationReport:
        """Gera relatório completo de validação"""
        report = ValidationReport()
        report.files_analyzed = len(self.results)
        
        for filepath, result in self.results.items():
            # Contadores
            if result.passed:
                report.files_passed += 1
            if result.error_count > 0:
                report.files_with_errors += 1
            if result.warning_count > 0:
                report.files_with_warnings += 1
            
            report.total_violations += len(result.violations)
            
            # Arquivos sem tokens
            if not result.imports_design_tokens and result.component_count > 0:
                report.files_without_tokens.append(filepath)
            
            # Agregações
            for v in result.violations:
                phase_key = f"Fase {v.phase}"
                report.violations_by_phase[phase_key] = report.violations_by_phase.get(phase_key, 0) + 1
                report.violations_by_severity[v.severity] = report.violations_by_severity.get(v.severity, 0) + 1
                report.violations_by_rule[v.rule_id] = report.violations_by_rule.get(v.rule_id, 0) + 1
            
            # Detalhes
            if result.violations:
                report.details.append({
                    "file": filepath,
                    "passed": result.passed,
                    "imports_design_tokens": result.imports_design_tokens,
                    "error_count": result.error_count,
                    "warning_count": result.warning_count,
                    "info_count": result.info_count,
                    "violations": [v.to_dict() for v in result.violations]
                })
        
        return report
    
    def generate_inventory(self, files: List[str]) -> Dict:
        """Gera inventário do projeto (Fase 0)"""
        inventory = {
            "total_files": len(files),
            "by_directory": defaultdict(int),
            "components_count": 0,
            "files_with_tokens": 0,
            "potential_issues": defaultdict(int)
        }
        
        for filepath in files:
            # Por diretório
            dir_path = os.path.dirname(filepath)
            inventory["by_directory"][dir_path] += 1
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Contar componentes
                components = len(re.findall(r'(?:export\s+)?(?:function|const)\s+[A-Z]\w+', content))
                inventory["components_count"] += components
                
                # Verificar tokens
                if self.pattern_import_tokens.search(content):
                    inventory["files_with_tokens"] += 1
                
                # Problemas potenciais
                if 'bg-cyan' in content or 'bg-blue-500' in content:
                    inventory["potential_issues"]["buttons_with_cyan"] += 1
                if 'rounded-md' in content and 'bg-white' in content:
                    inventory["potential_issues"]["cards_rounded_md"] += 1
                if "Source_Serif_4" in content:
                    inventory["potential_issues"]["source_serif_usage"] += 1
                if 'bg-white' in content and 'dark:' not in content:
                    inventory["potential_issues"]["missing_dark_mode"] += 1
            
            except Exception:
                pass
        
        inventory["by_directory"] = dict(inventory["by_directory"])
        inventory["potential_issues"] = dict(inventory["potential_issues"])
        
        return inventory


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def find_tsx_files(paths: List[str], recursive: bool = True) -> List[str]:
    """Encontra todos os arquivos .tsx/.jsx"""
    files = []
    extensions = {'.tsx', '.jsx'}
    
    for path in paths:
        path_obj = Path(path)
        
        if path_obj.is_file():
            if path_obj.suffix in extensions:
                files.append(str(path_obj))
        elif path_obj.is_dir():
            if recursive:
                for ext in extensions:
                    files.extend([str(f) for f in path_obj.rglob(f'*{ext}')])
            else:
                for ext in extensions:
                    files.extend([str(f) for f in path_obj.glob(f'*{ext}')])
    
    # Filtrar arquivos de teste, stories, etc.
    exclude_patterns = ['.test.', '.spec.', '.stories.', 'node_modules', '__tests__']
    files = [f for f in files if not any(p in f for p in exclude_patterns)]
    
    return sorted(set(files))


def print_violation(v: Violation, verbose: bool = False):
    """Imprime uma violação formatada"""
    icons = {"error": "🔴", "warning": "🟡", "info": "🔵"}
    icon = icons.get(v.severity, "⚪")
    
    print(f"      {icon} L{v.line}:{v.column} [{v.rule_id}]")
    print(f"         {v.message}")
    
    if verbose:
        print(f"         📝 {v.original_code[:80]}...")
        if v.fixed_code:
            print(f"         ✅ {v.fixed_code[:80]}...")
        if v.token_suggestion:
            print(f"         💡 Token: {v.token_suggestion}")
    else:
        if v.token_suggestion:
            print(f"         💡 {v.token_suggestion}")


def print_file_result(result: FileResult, verbose: bool = False):
    """Imprime resultado de um arquivo"""
    if not result.violations:
        print(f"  ✅ {result.file}")
        return
    
    status = "❌" if not result.passed else "⚠️"
    counts = f"({result.error_count}E/{result.warning_count}W/{result.info_count}I)"
    tokens = "📦" if result.imports_design_tokens else "📭"
    
    print(f"  {status} {result.file} {counts} {tokens}")
    
    if verbose:
        for v in result.violations:
            print_violation(v, verbose)
        print()


def print_summary(report: ValidationReport):
    """Imprime resumo do relatório"""
    print(f"\n{'='*70}")
    print(f"📊 RESUMO - Design System LIA v{report.version}")
    print(f"{'='*70}")
    print(f"   Arquivos analisados:    {report.files_analyzed}")
    print(f"   ✅ Aprovados:           {report.files_passed}")
    print(f"   ❌ Com erros:           {report.files_with_errors}")
    print(f"   ⚠️  Com warnings:        {report.files_with_warnings}")
    print(f"   Total violações:        {report.total_violations}")
    
    if report.files_without_tokens:
        print(f"\n   📭 Arquivos sem design-tokens: {len(report.files_without_tokens)}")
    
    if report.violations_by_phase:
        print(f"\n   Por fase:")
        for phase in sorted(report.violations_by_phase.keys()):
            count = report.violations_by_phase[phase]
            print(f"      {phase}: {count}")
    
    if report.violations_by_severity:
        print(f"\n   Por severidade:")
        icons = {"error": "🔴", "warning": "🟡", "info": "🔵"}
        for sev in ["error", "warning", "info"]:
            if sev in report.violations_by_severity:
                print(f"      {icons[sev]} {sev}: {report.violations_by_severity[sev]}")
    
    if report.violations_by_rule:
        print(f"\n   Top regras violadas:")
        sorted_rules = sorted(report.violations_by_rule.items(), key=lambda x: x[1], reverse=True)[:10]
        for rule, count in sorted_rules:
            print(f"      {rule}: {count}")
    
    print(f"{'='*70}\n")


def print_phase_help():
    """Imprime ajuda sobre as fases"""
    print("""
🎨 FASES DO DESIGN SYSTEM LIA v4.1
==================================

Fase 0: Inventário
   - Mapear arquivos e componentes
   - Identificar problemas potenciais

Fase 1: Setup Base
   - Fontes (Open Sans 85%, Inter 10%, Source Serif 4 5%)
   - Importação de design-tokens.ts

Fase 2: Botões
   - Primary: bg-gray-900 (PRETO, não cyan)
   - Focus ring: ring-gray-900/20 (grayscale)
   - Dark mode obrigatório

Fase 3: Inputs e Forms
   - Focus: ring-gray-900/20
   - Labels com tipografia correta

Fase 4: Cards e Containers
   - Border radius: rounded-xl (não rounded-md)
   - Dark mode obrigatório

Fase 5: Navegação e Sidebar
   - Source Serif 4 APENAS em sidebar
   - Open Sans para todos os outros títulos

Fase 6: Modais e Componentes Avançados
   - rounded-xl para modais
   - Dark mode obrigatório

Fase 7: Badges e Utilities
   - Cyan apenas para LIA/IA
   - Tokens para badges de status

Fase 8: Validação Final
   - Dark mode completo
   - Importação de tokens
   - Classes inline → tokens
""")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Design System LIA v4.1 - Validator & Auto-Fixer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s --validate src/components/
  %(prog)s --fix src/components/settings/
  %(prog)s -v --report -o report.json src/
  %(prog)s --phase 2 src/components/ui/Button.tsx
  %(prog)s --inventory src/components/

Design System Specs:
  - Tipografia: Open Sans 85%%, Inter 10%%, Source Serif 4 5%% (sidebar)
  - Cores: 90%% grayscale + 10%% accent (cyan apenas LIA)
  - Cards: rounded-xl, botões: bg-gray-900
  - Dark mode obrigatório
        """
    )
    
    parser.add_argument(
        "paths",
        nargs="*",
        default=["src/components"],
        help="Arquivos ou diretórios para validar (padrão: src/components)"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Modo validação (apenas reportar, sem correções)"
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Aplicar correções automáticas"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Gerar relatório JSON detalhado"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Arquivo de saída para o relatório"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar detalhes de cada violação"
    )
    
    parser.add_argument(
        "--phase",
        type=int,
        choices=[0, 1, 2, 3, 4, 5, 6, 7, 8],
        help="Validar apenas uma fase específica"
    )
    
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="Gerar inventário do projeto (Fase 0)"
    )
    
    parser.add_argument(
        "--no-tokens",
        action="store_true",
        help="Não verificar uso de design-tokens"
    )
    
    parser.add_argument(
        "--phases-help",
        action="store_true",
        help="Mostrar descrição das fases"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output em formato JSON"
    )
    
    args = parser.parse_args()
    
    if args.phases_help:
        print_phase_help()
        sys.exit(0)
    
    # Coletar arquivos
    all_files = find_tsx_files(args.paths)
    
    if not all_files:
        print("❌ Nenhum arquivo .tsx/.jsx encontrado")
        print(f"   Caminhos verificados: {args.paths}")
        sys.exit(1)
    
    # Criar validador
    validator = DesignSystemValidator(
        verbose=args.verbose,
        phase_filter=args.phase,
        check_tokens=not args.no_tokens
    )
    
    # Modo inventário
    if args.inventory:
        print(f"\n📋 INVENTÁRIO - Design System LIA v4.1")
        print(f"{'='*60}\n")
        
        inventory = validator.generate_inventory(all_files)
        
        print(f"   Total arquivos: {inventory['total_files']}")
        print(f"   Componentes: {inventory['components_count']}")
        print(f"   Com design-tokens: {inventory['files_with_tokens']}")
        
        if inventory['by_directory']:
            print(f"\n   Por diretório:")
            for dir_path, count in sorted(inventory['by_directory'].items())[:15]:
                print(f"      {dir_path}: {count}")
        
        if inventory['potential_issues']:
            print(f"\n   ⚠️ Problemas potenciais:")
            for issue, count in inventory['potential_issues'].items():
                print(f"      {issue}: {count} arquivo(s)")
        
        print(f"\n{'='*60}\n")
        
        if args.json or args.output:
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(inventory, f, indent=2, ensure_ascii=False)
                print(f"📊 Inventário salvo em: {args.output}")
            else:
                print(json.dumps(inventory, indent=2, ensure_ascii=False))
        
        sys.exit(0)
    
    # Modo validação/correção
    phase_str = f" (Fase {args.phase})" if args.phase else ""
    print(f"\n🎨 Design System LIA v4.1 - Validator{phase_str}")
    print(f"   Analisando {len(all_files)} arquivo(s)...\n")
    
    # Validar todos os arquivos
    for filepath in all_files:
        result = validator.validate_file(filepath)
        if not args.json:
            print_file_result(result, args.verbose)
    
    # Aplicar correções se solicitado
    if args.fix:
        print("\n🔧 Aplicando correções automáticas...")
        total_fixes = 0
        files_fixed = 0
        
        for filepath in all_files:
            success, fixes = validator.fix_file(filepath)
            if fixes > 0:
                print(f"   ✅ {filepath}: {fixes} correção(ões)")
                total_fixes += fixes
                files_fixed += 1
        
        if total_fixes > 0:
            print(f"\n   Total: {total_fixes} correção(ões) em {files_fixed} arquivo(s)")
        else:
            print("   Nenhuma correção automática aplicável")
    
    # Gerar relatório
    report = validator.generate_report()
    
    if args.report or args.output:
        report_dict = report.to_dict()
        report_json = json.dumps(report_dict, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report_json)
            print(f"\n📊 Relatório salvo em: {args.output}")
        elif args.json:
            print(report_json)
    
    # Resumo
    if not args.json:
        print_summary(report)
    
    # Exit code
    sys.exit(0 if report.files_with_errors == 0 else 1)


if __name__ == "__main__":
    main()
