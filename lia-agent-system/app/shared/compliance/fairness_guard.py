"""
FairnessGuard - Middleware that blocks discriminatory filters.

Intercepts queries before domain processing and checks for bias indicators.
When a discriminatory pattern is detected, returns an educational message
instead of proceeding with the query.

Part of the 3-pillar compliance architecture (LGPD, SOX, EU AI Act).
"""
import hashlib
import re
import logging
import unicodedata
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_METRICS_AVAILABLE = False


def _normalize_text(text: str) -> str:
    return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')


IMPLICIT_BIAS_TERMS: Dict[str, str] = {
    # Chaves sem acentuação — _normalize_text() normaliza antes da busca
    "boa aparencia": "O termo 'boa aparência' pode configurar discriminação estética (Lei 12.984/14). Use critérios objetivos de apresentação profissional.",
    "bairros nobres": "Filtrar por 'bairros nobres' pode configurar discriminação socioeconômica. Considere critérios de disponibilidade ou mobilidade.",
    "regiao nobre": "Filtrar por 'região nobre' pode configurar discriminação socioeconômica. Considere critérios de disponibilidade ou mobilidade.",
    "universidades de primeira linha": "Filtrar por 'universidades de primeira linha' pode configurar elitismo acadêmico. Avalie competências e resultados.",
    "faculdade de ponta": "Filtrar por 'faculdade de ponta' pode configurar elitismo acadêmico. Avalie competências e resultados.",
    "escola particular": "Filtrar por 'escola particular' pode configurar discriminação socioeconômica. Avalie formação e competências.",
    "clube social": "Referência a 'clube social' pode configurar discriminação socioeconômica ou de classe.",
    "perfil adequado": "O termo 'perfil adequado' é vago e pode mascarar vieses inconscientes. Especifique competências objetivas.",
    "apresentacao pessoal": "O termo 'apresentação pessoal' pode configurar discriminação estética. Use critérios objetivos.",
    "morar proximo": "Filtrar por 'morar próximo' pode configurar discriminação socioeconômica. Considere disponibilidade ou trabalho remoto.",
    "boa familia": "O termo 'boa família' pode configurar discriminação socioeconômica ou de origem. Use critérios profissionais.",
    # Proxy socioeconômico por localização
    "zona rural": "Filtrar por 'zona rural' pode configurar discriminação socioeconômica ou geográfica indireta. Considere critérios de mobilidade ou trabalho remoto.",
    "periferia": "Filtrar por 'periferia' pode configurar discriminação socioeconômica. Considere critérios de disponibilidade, transporte ou trabalho remoto.",
    "interior do estado": "Filtrar por 'interior do estado' como critério eliminatório pode configurar discriminação geográfica indireta.",
    "suburbio": "Filtrar por 'subúrbio' pode configurar discriminação socioeconômica indireta.",
    # Proxy PCD / acessibilidade
    "sem adaptacoes": "O termo 'sem adaptações' pode configurar discriminação indireta contra PCDs (Lei 13.146/15). Especifique os requisitos funcionais objetivos.",
    "sem necessidade de acessibilidade": "Este critério pode configurar discriminação indireta contra PCDs. Descreva os requisitos funcionais objetivos da vaga.",
    "sem restricoes fisicas": "O termo 'sem restrições físicas' pode configurar discriminação contra PCDs. Use requisitos funcionais objetivos.",
    # Religiões afro-brasileiras e outras (diversidade religiosa)
    "espirita": "Referência a 'espírita' pode configurar discriminação religiosa (CF Art. 5º, VI). Avalie candidatos por competências.",
    "candomble": "Referência a 'candomblé' pode configurar discriminação religiosa. Avalie candidatos por competências.",
    "umbanda": "Referência a 'umbanda' pode configurar discriminação religiosa. Avalie candidatos por competências.",
    "valores cristaos": "Exigir 'valores cristãos' pode configurar discriminação religiosa (CF Art. 5º, VI). Use critérios comportamentais objetivos.",
    "principios religiosos": "Exigir 'princípios religiosos' pode configurar discriminação religiosa. Especifique valores comportamentais objetivos.",
    # Proxy estado civil / maternidade
    "sem obrigacoes": "O termo 'sem obrigações' pode ser proxy para discriminação por estado civil ou responsabilidades familiares (Lei 9.029/95).",
    "disponibilidade total": "Exigir 'disponibilidade total' sem especificação pode mascarar discriminação por estado civil ou responsabilidades familiares.",
    "sem compromissos pessoais": "Este critério pode ser proxy para discriminação por estado civil ou maternidade/paternidade (CLT Art. 373-A).",
    "mae solo": "Referência a 'mãe solo' como critério pode configurar discriminação por maternidade (Lei 9.029/95).",
    # Proxy etário
    "alto potencial de crescimento rapido": "Este critério pode ser proxy para discriminação etária. Especifique competências e resultados esperados.",
    "energia jovem": "O critério 'energia jovem' pode configurar discriminação etária (Lei 10.741/03). Use competências objetivas.",
}


IMPLICIT_BIAS_TERMS_EN: dict = {
    # Age proxies
    "young and dynamic":        "May indicate age bias. Use objective competency criteria.",
    "young blood":              "Age proxy. Specify behavioral competencies.",
    "energetic":                "Can be age proxy. Define expected outcomes instead.",
    "digital native":           "Age proxy. Evaluate specific technical skills instead.",
    "recent graduate":          "May exclude experienced older candidates. Define skill requirements.",
    # Class / academic elitism
    "culture fit":              "Vague — can mask racial or class bias. Define specific values.",
    "prestigious university":   "Academic elitism proxy. Evaluate competencies and results.",
    "ivy league":               "Academic elitism. Focus on demonstrated skills.",
    "top school":               "Academic elitism. Specify required skills, not institution.",
    "right neighborhood":       "Socioeconomic discrimination proxy.",
    "proper background":        "Vague — can mask socioeconomic or racial bias.",
    # Appearance
    "clean-cut":                "Appearance criterion. Use objective professional conduct standards.",
    "good looking":             "Appearance discrimination.",
    "presentable":              "Vague appearance standard. Specify professional conduct.",
    # Origin / culture
    "native speaker":           "May be national origin proxy. Only require if operationally justified.",
    "traditional values":       "May indicate religious or cultural discrimination.",
    # Disability
    "without restrictions":     "May discriminate against candidates with disabilities (ADA/CRPD).",
    "fully able":               "Potential disability discrimination. Specify functional requirements.",
    # Family status
    "no family obligations":    "May discriminate by marital or parental status.",
    "available at all times":   "May discriminate against candidates with caregiving responsibilities.",
}



@dataclass
class FairnessCheckResult:
    is_blocked: bool
    blocked_terms: List[str] = field(default_factory=list)
    category: Optional[str] = None
    educational_message: Optional[str] = None
    original_query: str = ""
    confidence: float = 0.0
    soft_warnings: List[str] = field(default_factory=list)

    @property
    def is_biased(self) -> bool:
        """Alias semântico para is_blocked (Layer 1 = viés explícito)."""
        return self.is_blocked


DISCRIMINATORY_CATEGORIES = {
    "genero": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(homens?|mulheres?|masculino|feminino)\b",
            r"\b(sexo|gênero|genero)\s*(\w+\s+)*(masculino|feminino|macho|fêmea|femea)\b",
            r"\bexcluir?\s+(\w+\s+)*(homens?|mulheres?)\b",
            r"\bpreferência\s+por\s+(\w+\s+)*(homens?|mulheres?)\b",
            r"\bpreferencia\s+por\s+(\w+\s+)*(homens?|mulheres?)\b",
            r"\b(gender|male|female)\s+only\b",
            # Formas implícitas: "prefiro homens/mulheres"
            r"\bprefiro\s+(\w+\s+)*(homens?|mulheres?)\b",
            r"\bprefere?mos?\s+(\w+\s+)*(homens?|mulheres?)\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por gênero. "
            "A legislação trabalhista brasileira (Art. 5º, CLT) e a LGPD proíbem "
            "discriminação por gênero em processos seletivos. "
            "Posso ajudar você a definir critérios baseados em competências e experiência?"
        ),
    },
    "raca_etnia": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(brancos?|negros?|pardos?|indígenas?|indigenas?|amarelos?)\b",
            r"\b(raça|raca|cor|etnia)\s*(\w+\s+)*(branca|negra|parda)\b",
            r"\bexcluir?\s+(\w+\s+)*(brancos?|negros?|pardos?)\b",
            r"\b(race|ethnicity|white|black)\s+only\b",
            # Formas implícitas: "negros não se encaixam", "origem europeia"
            r"\b(negros?|pardos?|brancos?|indígenas?|indigenas?)\s+n[ãa]o\s+(se\s+)?(encaixam?|adequam?|servem?|funcionam?|combina[m]?)\b",
            r"\borigem\s+(europeia|africana|asi[aá]tica|latina|nordestina|nordestino)\b",
            r"\bprefiro\s+.*\b(europeus?|brancos?)\b",
            r"\bperfil\s+(europeu|branco|ocidental)\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por raça ou etnia. "
            "A Constituição Federal (Art. 5º) e a Lei 7.716/89 proíbem "
            "discriminação racial em qualquer contexto, incluindo processos seletivos. "
            "Posso ajudar você a buscar candidatos por habilidades e experiência?"
        ),
    },
    "idade": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(jovens?|velhos?|idosos?)\b",
            r"\b(muito|demais|bastante|bem)?\s*(velh[oa]s?|idosos?|jovens?)\s*(demais|para)?\b",
            r"\b(idade|anos?)\s*(máxim[oa]|mínim[oa]|maxim[oa]|minim[oa])\s*[:\s]*\d+\b",
            r"\bexcluir?\s+maiores?\s+de\s+\d+\b",
            r"\bexcluir?\s+menores?\s+de\s+\d+\b",
            r"\b(máximo|mínimo|maximo|minimo)\s+\d+\s+anos\b(?!\s+(?:de|no|na|em)\s+(experiên|experienc|atua|mercado|setor|ramo|empresa|cargo|fun[çc]|pr[aá]tica|trabalho|carreira|vivên|vivenc|profissional|experi))",
            r"\bidade\s+entre\s+\d+\s+e\s+\d+\b",
            r"\bde\s+\d+\s+(a|até|ate)\s+\d+\s+anos\b(?!\s+(?:de|no|na|em)\s+(experiên|experienc|atua|mercado|setor|ramo|empresa|cargo|fun[çc]|pr[aá]tica|trabalho|carreira|vivên|vivenc|profissional|experi|atuac))",
            r"\b(age|old|young)\s+only\b",
            r"\b(velho|velha|idoso|idosa)\s+(para|pra|demais)\b",
            # Formas implícitas: "até 30 anos", "mais de 50 anos" (sem range explícito)
            r"\baté\s+\d+\s+anos\b(?!\s+(?:de|no|na|em)\s+(experiên|experienc|atua|mercado|setor|ramo|empresa|cargo|fun[çc]|pr[aá]tica|trabalho|carreira|vivên|vivenc|profissional|experi))",
            r"\bmais\s+de\s+\d+\s+anos\b(?!\s+(?:de|no|na|em)\s+(experiên|experienc|atua|mercado|setor|ramo|empresa|cargo|fun[çc]|pr[aá]tica|trabalho|carreira|vivên|vivenc|profissional|experi))",
            r"\bn[ãa]o\s+(quero|queremos)\s+.*\b(mais\s+de|acima\s+de)\s+\d+\b",
            # FIX bug: "maiores de X anos" e variações não eram capturadas
            r"\b(maiores?\s+de|acima\s+de)\s+\d+\s+anos?\b",
            r"\b(menores?\s+de|abaixo\s+de)\s+\d+\s+anos?\b",
            r"\bidade\s*(máxima|mínima|maxima|minima|limite)\s*[:\s]*\d+\b",
            r"\b(limite|faixa)\s+etári[ao]\b",
            r"\bfaixa\s+etária\s*(de|entre|até)?\s*\d*",
            r"\b(etário|etária)\b",
            r"\bidade\s+(superior|inferior)\s+a\s+\d+\b",
            # EN age patterns
            r"\bunder\s+\d+\s+(years?|y\.?o\.?)\b",
            r"\bover\s+\d+\s+(years?|y\.?o\.?)\b",
            r"\bage\s*[:<]\s*\d+\b",
            r"\bno\s+older\s+than\s+\d+\b",
            r"\bage\s+limit\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por idade. "
            "O Estatuto do Idoso (Lei 10.741/03) e a CLT proíbem discriminação etária "
            "em processos seletivos. Posso ajudar a definir requisitos de senioridade "
            "baseados em experiência profissional?"
        ),
    },
    "religiao": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(cristãos?|cristaos?|muçulmanos?|muculmanos?|judeus?|budistas?|ateus?)\b",
            r"\b(religião|religiao)\s*(\w+\s+)*(cristã|crista|católica|catolica|evangélica|evangelica|muçulmana|muculmana|judaica)\b",
            r"\bexcluir?\s+(\w+\s+)*(cristãos?|cristaos?|muçulmanos?|muculmanos?|judeus?|ateus?)\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por religião. "
            "A Constituição Federal garante liberdade religiosa (Art. 5º, VI) "
            "e proíbe discriminação por credo. "
            "Posso ajudar a definir critérios baseados em disponibilidade e competências?"
        ),
    },
    "orientacao_sexual": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(heterossexuais?|homossexuais?|gays?|lésbicas?|lesbicas?|bi)\b",
            r"\b(orientação|orientacao)\s+sexual\b",
            r"\bexcluir?\s+(\w+\s+)*(gays?|lésbicas?|lesbicas?|heterossexuais?)\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por orientação sexual. "
            "O STF reconhece a criminalização da homofobia (ADO 26) e qualquer "
            "discriminação por orientação sexual é vedada. "
            "Posso ajudar a buscar candidatos com base em qualificações profissionais?"
        ),
    },
    "estado_civil": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(solteiros?|casados?|divorciados?|viúvos?|viuvos?)\b",
            r"\bestado\s+civil\b",
            r"\bexcluir?\s+(\w+\s+)*(solteiros?|casados?|divorciados?)\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por estado civil. "
            "A CLT proíbe discriminação por estado civil em processos seletivos. "
            "Posso ajudar a definir critérios baseados em experiência e competências?"
        ),
    },
    "deficiencia": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(deficientes?|pcd|pne)\b",
            r"\bexcluir?\s+(\w+\s+)*(deficientes?|pcd|cadeirantes?)\b",
            r"\bsem\s+defici[eê]ncia\b",
            r"\bsem\s+deficiencia\b",
            # Formas implícitas: "não quero candidatos com deficiência", "sem limitações físicas"
            r"\bn[ãa]o\s+(quero|queremos|aceito|aceitar)\s+.*\bdefici[eê]ncia\b",
            r"\bcandidatos?\s+com\s+defici[eê]ncia\s+n[ãa]o\b",
            r"\bsem\s+limita[çc][õo]es?\s+(f[íi]sicas?|mentais?|cognitivas?)",
            r"\bsem\s+(limita[çc][õo]es?\s+)?(f[íi]sicas?\s+(ou|e)\s+mentais?)\b",
        ],
        "message": (
            "A LIA não pode excluir candidatos com deficiência. "
            "A Lei 8.213/91 (Lei de Cotas) e o Estatuto da Pessoa com Deficiência "
            "(Lei 13.146/15) protegem os direitos de PCDs. "
            "Posso ajudar a buscar candidatos com as competências necessárias?"
        ),
    },
    "maternidade_paternidade": {
        "terms": [
            r"\bengravidar\b",
            r"\bgravidez\b",
            r"\bgrávid[ao]s?\b",
            r"\b(tem|ter|possui|possuir|ter)\s+filhos?\b",
            r"\bsem\s+filhos?\b",
            r"\bplano\s+(de\s+)?ter\s+filhos?\b",
            r"\bplanej(a|and[oa])\s+(ter|engravidar)\b",
            r"\bfilhos?\s+(previsto|planejado|futuro)\b",
            # Formas implícitas: "filhos pequenos", "sem obrigações familiares"
            r"\bfilhos?\s+pequenos?\b",
            r"\bfilhos?\s+(menores?|bebês?|bebes?)\b",
            r"\bsem\s+(obriga[çc][õo]es?\s+)?(familiares?)\b",
            r"\bsem\s+compromisso\s+familiar\b",
            r"\bdedica[çc][ãa]o\s+(total|integral|exclusiva)\s*[—\-]?\s*(sem|nenhum[ao]?)\s+(obriga|familiar|filho|família|familia)\b",
        ],
        "message": (
            "A LIA não pode questionar candidatos sobre planos de maternidade/paternidade "
            "ou existência de filhos. A CLT (Art. 373-A) e a Lei 9.029/95 proíbem "
            "discriminação por gestação ou maternidade em processos seletivos. "
            "Posso ajudar a definir critérios baseados em disponibilidade e competências?"
        ),
    },
    "nacionalidade": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(brasileiros?|estrangeiros?)\b",
            r"\bexcluir?\s+(\w+\s+)*(estrangeiros?|imigrantes?)\b",
            r"\bnacionalidade\s*(brasileira|estrangeira)\b",
        ],
        "message": (
            "A LIA não pode discriminar por nacionalidade em processos seletivos. "
            "A Constituição Federal garante igualdade entre brasileiros e estrangeiros "
            "residentes (Art. 5º). Posso ajudar com critérios de proficiência linguística "
            "ou experiência regional?"
        ),
    },
    # FAR-1: novas categorias adicionadas em Sprint FAR (20/03/2026)
    "antecedentes_criminais": {
        "terms": [
            r"\bsem\s+(antecedentes?\s+criminais?|antecedentes?\s+policiais?|passagem\s+policial|ocorrências?\s+policiais?|ocorrencias?\s+policiais?)\b",
            r"\bficha\s+limpa\s+(obrigatória|obrigatorio|exigida|exigido|requerida|requerido|comprovada|comprovado)\b",
            r"\bexcluir?\s+(\w+\s+)*(com\s+)?(ficha\s+suja|antecedentes?\s+criminais?|passagem\s+policial)\b",
            r"\bn[ãa]o\s+(aceitar?|queremos?|aceitamos?)\s+(\w+\s+)*(com\s+)?(ficha\s+suja|antecedentes?|passagem\s+policial)\b",
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(candidatos?\s+)?(com\s+)?ficha\s+limpa\b",
            r"\bcertidão\s+de\s+(nada\s+consta|antecedentes?)\s+(obrigatória|obrigatorio|exigida|exigido|requerida|requerido)\b",
            r"\bcertidao\s+de\s+(nada\s+consta|antecedentes?)\s+(obrigatoria|exigida|exigido|requerida|requerido)\b",
        ],
        "message": (
            "A LIA não pode discriminar candidatos por antecedentes criminais de forma genérica. "
            "A CNJ Resolução 65/08 e a Lei 7.210/84 proíbem o uso de certidões criminais como "
            "critério eliminatório generalizado. Apenas funções específicas regulamentadas "
            "(ex: segurança armada, instituições financeiras) podem exigir esse requisito. "
            "Consulte o setor jurídico antes de incluir esse critério."
        ),
    },
    "saude_doenca": {
        "terms": [
            r"\bsem\s+(HIV|AIDS|hepatite\s+[ABC]|doenças?\s+cr[oô]nicas?|enfermidades?\s+cr[oô]nicas?)\b",
            r"\bsem\s+(hiv|aids|hepatite)\b",
            r"\bn[ãa]o\s+(aceitar?|queremos?|aceitamos?)\s+(\w+\s+)*(com\s+)?(HIV|AIDS|doenças?\s+cr[oô]nicas?|hiv|aids)\b",
            r"\bexcluir?\s+(\w+\s+)*(portadores?\s+de\s+)?(HIV|AIDS|doenças?\s+cr[oô]nicas?|hiv|aids)\b",
            r"\bteste\s+(HIV|de\s+HIV|de\s+AIDS|hiv|aids)\s+(obrigatório|obrigatorio|exigido|requerido)\b",
            r"\bportadores?\s+de\s+(HIV|AIDS|doenças?\s+cr[oô]nicas?|hiv|aids)\s+n[ãa]o\b",
            r"\bsaúde\s+perfeita\s+(obrigatória|obrigatorio|exigida|exigido|comprovada|comprovado)\b",
            r"\bsaude\s+perfeita\s+(obrigatoria|exigida|exigido|comprovada|comprovado)\b",
        ],
        "message": (
            "A LIA não pode discriminar candidatos por condições de saúde. "
            "A Lei 9.029/95 (Art. 1º) e a Lei 9.313/96 proíbem discriminação "
            "por doenças crônicas, incluindo HIV/AIDS, em processos seletivos. "
            "Posso ajudar a definir requisitos funcionais objetivos para a vaga?"
        ),
    },
    "filiacao_sindical": {
        "terms": [
            r"\bn[ãa]o\s+(sindicalizado|filiado\s+a\s+sindicato|filiado\s+ao\s+sindicato)\b",
            r"\bsem\s+filia[çc][ãa]o\s+sindical\b",
            r"\bsem\s+filiacao\s+sindical\b",
            r"\bexcluir?\s+(\w+\s+)*(sindicalistas?|filiados?\s+(ao?\s+)sindicato)\b",
            r"\bn[ãa]o\s+(aceitar?|queremos?|aceitamos?)\s+(\w+\s+)*(sindicalistas?|filiados?\s+(ao?\s+)sindicato)\b",
            r"\bfilia[çc][ãa]o\s+sindical\s+(proibida|n[ãa]o\s+permitida|n[ãa]o\s+aceita)\b",
        ],
        "message": (
            "A LIA não pode discriminar candidatos por filiação sindical. "
            "A CLT (Art. 543) e a Constituição Federal (Art. 8º) garantem "
            "liberdade de associação sindical e proíbem discriminação por esse motivo. "
            "Posso ajudar a definir critérios baseados em competências profissionais?"
        ),
    },
    "aparencia_fisica": {
        "terms": [
            r"\baltura\s+(m[íi]nima|m[áa]xima|minima|maxima|m[íi]n\.?|m[áa]x\.?)\s*[:\s]*\d+",
            r"\bestatura\s+(m[íi]nima|m[áa]xima|minima|maxima)\b",
            r"\bpeso\s+(m[áa]ximo|m[íi]nimo|maximo|minimo|ideal)\s*[:\s]*\d*",
            r"\bsem\s+(sobrepeso|obesidade|excesso\s+de\s+peso)\b",
            r"\b(boa\s+forma|em\s+boa\s+forma)\s*(f[íi]sica)?\s*(obrigatória|obrigatorio|exigida|exigido|requerida|requerido)\b",
            r"\bboa\s+forma\s+f[íi]sica\b",
            r"\b(corpo|f[íi]sico|fisico)\s+(atl[eé]tico|atletico|definido|escultural)\b",
            r"\bperfil\s+atl[eé]tico\b",
            r"\b(ótima|excelente)\s+aparência\s+(f[íi]sica|pessoal)?\b",
            r"\b(otima|excelente)\s+aparencia\b",
        ],
        "message": (
            "A LIA não pode filtrar candidatos por características físicas como altura, "
            "peso, forma física ou aparência. A Lei 9.029/95 e a jurisprudência trabalhista "
            "proíbem discriminação estética em processos seletivos, salvo funções com "
            "requisito funcional objetivo comprovado (ex: atleta profissional). "
            "Posso ajudar a definir critérios baseados em capacidade técnica e experiência?"
        ),
    },
    "gender_en": {
        "terms": [
            r"\b(only|just)\s+(men|women|male|female|males|females)\b",
            r"\b(prefer|preference\s+for)\s+(men|women|male|female)\b",
            r"\b(male|female)\s+only\b",
            r"\b(men|women)\s+preferred\b",
            r"\bgender\s*:\s*(male|female|man|woman)\b",
        ],
        "message": (
            "LIA cannot filter candidates by gender. "
            "This violates anti-discrimination law (Lei 9.029/95, Title VII, EU Directive 2006/54)."
        ),
    },
    "race_en": {
        "terms": [
            r"\b(only|just)\s+(white|black|asian|hispanic|latino|latina)\b",
            r"\b(race|ethnicity|color)\s*[:\-]\s*(white|black|asian|hispanic)\b",
            r"\b(white|black|asian)\s+only\b",
            r"\bprefer\s+(white|black|asian|hispanic)\b",
        ],
        "message": (
            "LIA cannot filter candidates by race or ethnicity. "
            "This violates Lei 7.716/89, CRFB/88 Art. 5 and international anti-discrimination law."
        ),
    },
    "age_en": {
        "terms": [
            r"\bunder\s+\d+\s+(years?|y\.?o\.?)\b",
            r"\bover\s+\d+\s+(years?|y\.?o\.?)\b",
            r"\bage\s*[:<]\s*\d+\b",
            r"\b(young|youthful)\s+(candidate|professional|team\s+member)\b",
            r"\bno\s+older\s+than\s+\d+\b",
            r"\bage\s+limit\b",
        ],
        "message": (
            "Age-based filtering may violate age discrimination laws "
            "(ADEA in the US, EU Directive 2000/78, and Lei 9.029/95 in Brazil)."
        ),
    },
}

_COMPILED_PATTERNS: Dict[str, List[re.Pattern]] = {}
# Versão dos patterns — incrementar quando patterns forem adicionados para forçar recompilação
# v3: FAR-1 — 5 novas categorias (antecedentes_criminais, saude_doenca, filiacao_sindical,
#              aparencia_fisica), expansão IMPLICIT_BIAS_TERMS, fix regex idade
_PATTERNS_VERSION = 4

HIGH_IMPACT_ACTIONS = {
    "rejection", "shortlist", "wsi_score", "policy_save", "bulk_rejection",
    # FAR-4: sourcing search e import de JD são ações de alto impacto para Layer 3
    "sourcing_search", "jd_import",
    # FAR-2/A: transição de pipeline também é ação de alto impacto
    "pipeline_move",
    # LIA-R05: domínios adicionais com ações de alto impacto
    "analytics_query",           # analytics domain
    "job_create", "job_edit",    # job_management domain
    "bulk_automation",           # automation domain
    "policy_check", "diversity_check",  # hiring_policy domain
}


def _ensure_compiled() -> None:
    global _COMPILED_PATTERNS
    if not _COMPILED_PATTERNS:
        for category, config in DISCRIMINATORY_CATEGORIES.items():
            _COMPILED_PATTERNS[category] = [
                re.compile(p, re.IGNORECASE | re.UNICODE) for p in config["terms"]
            ]
        logger.info(
            "FairnessGuard compiled patterns v%d for %d categories (%d total patterns)",
            _PATTERNS_VERSION,
            len(_COMPILED_PATTERNS),
            sum(len(v) for v in _COMPILED_PATTERNS.values()),
        )


# F1-02: campos que NUNCA devem gerar padrões de aprendizado (atributos protegidos)
_LEARNING_PROTECTED_FIELDS: frozenset = frozenset({
    "gender", "genero", "gênero", "sex", "sexo",
    "race", "raca", "raça", "ethnicity", "etnia",
    "age", "idade", "birth_date", "data_nascimento",
    "religion", "religiao", "religião",
    "disability", "deficiencia", "deficiência", "pcd",
    "nationality", "nacionalidade",
    "marital_status", "estado_civil",
    "skin_color", "cor_pele",
})


@dataclass
class LearningBatchValidationResult:
    """Resultado da validação de fairness de um batch de padrões aprendidos (F1-02)."""
    is_clean: bool
    blocked_patterns: List[str]
    warnings: List[str] = field(default_factory=list)


class FairnessGuard:
    def __init__(self):
        _ensure_compiled()

    def check(self, query: str) -> FairnessCheckResult:
        if not query or not query.strip():
            return FairnessCheckResult(is_blocked=False, original_query=query)

        query_lower = query.lower().strip()
        query_normalized = _normalize_text(query_lower)
        blocked_terms = []
        detected_category = None
        max_confidence = 0.0

        for category, patterns in _COMPILED_PATTERNS.items():
            for pattern in patterns:
                match = pattern.search(query_lower)
                if not match:
                    match = pattern.search(query_normalized)
                if match:
                    blocked_terms.append(match.group())
                    if not detected_category:
                        detected_category = category
                    confidence = min(0.95, 0.7 + len(match.group()) * 0.02)
                    max_confidence = max(max_confidence, confidence)

        soft_warnings = self.check_implicit_bias(query)

        if blocked_terms and detected_category:
            educational_message = DISCRIMINATORY_CATEGORIES[detected_category]["message"]
            logger.warning(
                "FairnessGuard BLOCKED query: category=%s, terms=%s, query_len=%d",
                detected_category, blocked_terms, len(query),
            )
            if _METRICS_AVAILABLE:
                fairness_blocks_total.labels(category=detected_category).inc()
            return FairnessCheckResult(
                is_blocked=True,
                blocked_terms=blocked_terms,
                category=detected_category,
                educational_message=educational_message,
                original_query=query,
                confidence=max_confidence,
                soft_warnings=soft_warnings,
            )

        return FairnessCheckResult(
            is_blocked=False,
            original_query=query,
            soft_warnings=soft_warnings,
        )

    def check_explicit_bias(self, text: str) -> "FairnessCheckResult":
        """Alias semântico para check() — verifica Camada 1 (padrões explícitos de viés)."""
        return self.check(text)

    def check_implicit_bias(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        text_lower = text.lower().strip()
        text_normalized = _normalize_text(text_lower)
        warnings = []

        for term, warning_message in {**IMPLICIT_BIAS_TERMS, **IMPLICIT_BIAS_TERMS_EN}.items():
            term_lower = term.lower()
            term_normalized = _normalize_text(term_lower)
            if term_lower in text_lower or term_normalized in text_normalized:
                if warning_message not in warnings:
                    warnings.append(warning_message)

        if warnings:
            # LGPD: logar apenas contagem e tamanho — nunca fragmentos do texto
            # (pode conter dados do candidato gerados pelo LLM)
            logger.info(
                "FairnessGuard implicit bias detected: %d warnings for text_len=%d",
                len(warnings), len(text),
            )

        return warnings

    async def check_semantic(self, text: str, context: str = "", model: Optional[str] = None) -> FairnessCheckResult:
        result = self.check(text)

        try:
            from app.services.llm_service import LLMService
            llm_service = LLMService()

            semantic_prompt = (
                "Analise o seguinte texto de política de contratação e identifique "
                "possíveis vieses discriminatórios implícitos ou explícitos. "
                "Responda APENAS com uma lista de alertas, um por linha. "
                "Se não houver vieses, responda 'NENHUM_VIES_DETECTADO'.\n\n"
                f"Texto: {text}\n"
            )
            if context:
                semantic_prompt += f"Contexto: {context}\n"

            generate_kwargs: Dict[str, Any] = {}
            if model:
                generate_kwargs["model"] = model

            response = await llm_service.generate(semantic_prompt, **generate_kwargs)

            if response and "NENHUM_VIES_DETECTADO" not in response:
                semantic_warnings = [
                    line.strip() for line in response.strip().split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
                result.soft_warnings.extend(semantic_warnings)

        except (ImportError, Exception) as e:
            logger.debug(f"Semantic analysis unavailable: {e}")

        return result

    async def check_with_layer3(
        self,
        text: str,
        action_type: str = "general",
        context: Optional[str] = None,
    ) -> FairnessCheckResult:
        """
        Verificação com Layer 3 (LLM semântico) ativada seletivamente.
        Layer 3 só é executada para ações de alto impacto (controle de custo).
        Usa Haiku em vez de Sonnet para reduzir custo em ~75%.
        """
        # Layers 1 e 2 sempre executadas
        base_result = self.check(text)
        if base_result.is_blocked:
            return base_result

        implicit_warnings = self.check_implicit_bias(text)

        # Layer 3 apenas para ações de alto impacto
        if action_type not in HIGH_IMPACT_ACTIONS:
            return FairnessCheckResult(
                is_blocked=base_result.is_blocked,
                blocked_terms=base_result.blocked_terms,
                category=base_result.category,
                educational_message=base_result.educational_message,
                original_query=text,
                confidence=base_result.confidence,
                soft_warnings=implicit_warnings,
            )

        # Cache check para evitar chamadas LLM repetidas
        cache_key = f"fairness_l3:{hash(text[:200])}"
        _redis = None
        try:
            import json
            import redis.asyncio as _aioredis
            from lia_config.config import settings
            _redis = _aioredis.from_url(settings.REDIS_URL)
            cached = await _redis.get(cache_key)
            if cached:
                cached_data = json.loads(cached)
                # Close client before returning cached result
                try:
                    await _redis.aclose()
                except Exception:
                    pass
                return FairnessCheckResult(**cached_data)
        except Exception:
            pass

        # Layer 3 — LLM semântico com Haiku — respeitando feature flag FAIRNESS_LAYER3_ENABLED
        _layer3_enabled = False
        try:
            from lia_config.config import settings as _settings
            _layer3_enabled = getattr(_settings, "FAIRNESS_LAYER3_ENABLED", False)
        except Exception:
            pass

        if not _layer3_enabled:
            return FairnessCheckResult(
                is_blocked=base_result.is_blocked,
                blocked_terms=base_result.blocked_terms,
                category=base_result.category,
                educational_message=base_result.educational_message,
                original_query=text,
                confidence=base_result.confidence,
                soft_warnings=implicit_warnings,
            )

        try:
            semantic_result = await self.check_semantic(
                text,
                context=context or "",
                model="claude-haiku-4-5-20251001",
            )
            # Cache resultado por 1h
            try:
                import json
                if _redis is not None:
                    await _redis.setex(cache_key, 3600, json.dumps({
                        "is_blocked": semantic_result.is_blocked,
                        "blocked_terms": semantic_result.blocked_terms,
                        "category": semantic_result.category,
                        "educational_message": semantic_result.educational_message,
                        "original_query": text,
                        "confidence": semantic_result.confidence,
                        "soft_warnings": implicit_warnings,
                    }))
            except Exception:
                pass
            return FairnessCheckResult(
                is_blocked=semantic_result.is_blocked,
                blocked_terms=semantic_result.blocked_terms,
                category=semantic_result.category,
                educational_message=semantic_result.educational_message,
                original_query=text,
                confidence=semantic_result.confidence,
                soft_warnings=implicit_warnings,
            )
        except Exception as exc:
            logger.debug("[FairnessGuard] Layer 3 skipped: %s", exc)
            return FairnessCheckResult(
                is_blocked=False,
                blocked_terms=[],
                category=None,
                educational_message=None,
                original_query=text,
                confidence=0.5,
                soft_warnings=implicit_warnings,
            )

    async def check_with_sector(
        self,
        text: str,
        sector: str,
        action_type: str = "general",
        context: Optional[str] = None,
    ) -> FairnessCheckResult:
        """
        Sector-dependent FairnessGuard check (Fase 5 / G4).

        Uses ALPHA1_SECTOR_RULES to determine whether Layer 3 (LLM semantic)
        analysis is enabled for a given sector. Sectors like tech, financeiro,
        saude, and rpo have L3 enabled; varejo and logistica do not.

        When L3 is enabled for the sector, uses sector-specific prompt context
        to improve bias detection accuracy for that industry.
        """
        try:
            from app.services.policy_engine_service import ALPHA1_SECTOR_RULES
        except ImportError:
            ALPHA1_SECTOR_RULES = {}

        sector_key = (sector or "").lower().strip()
        sector_config = ALPHA1_SECTOR_RULES.get(sector_key, {})
        sector_l3_enabled = sector_config.get("fairness_layer3_enabled", False)

        base_result = self.check(text)
        if base_result.is_blocked:
            base_result.soft_warnings.insert(
                0, f"[Setor: {sector_key}] Viés explícito detectado"
            )
            return base_result

        implicit_warnings = self.check_implicit_bias(text)

        sector_context_map = {
            "tech": "Setor de tecnologia: atenção a vieses de gênero em cargos técnicos, etarismo (age bias) e elitismo acadêmico.",
            "financeiro": "Setor financeiro: atenção a vieses socioeconômicos, elitismo institucional e discriminação indireta por origem.",
            "saude": "Setor de saúde: atenção a vieses de gênero em especialidades, discriminação por PCD e exigências físicas não-funcionais.",
            "rpo": "RPO (terceirização de recrutamento): atenção a vieses transferidos do cliente, discriminação indireta em requisitos vagos.",
            "varejo": "Setor de varejo: atenção a vieses de aparência e discriminação geográfica/socioeconômica.",
            "logistica": "Setor de logística: atenção a vieses de gênero em cargos operacionais e discriminação por PCD.",
        }

        if not sector_l3_enabled:
            return FairnessCheckResult(
                is_blocked=False,
                blocked_terms=base_result.blocked_terms,
                category=base_result.category,
                educational_message=base_result.educational_message,
                original_query=text,
                confidence=base_result.confidence,
                soft_warnings=implicit_warnings,
            )

        sector_context = sector_context_map.get(sector_key, f"Setor: {sector_key}")
        full_context = f"{sector_context}\n{context or ''}"

        return await self.check_with_layer3(
            text=text,
            action_type=action_type,
            context=full_context,
        )

    def validate_learning_batch(
        self,
        patterns_to_update: Dict[str, Any],
    ) -> "LearningBatchValidationResult":
        """
        Valida um batch de padrões aprendidos antes de persistir no DB (F1-02).

        Verifica duas camadas:
          - Layer 1: field_name do padrão é atributo protegido (LGPD/EU AI Act)
          - Layer 2: valores aceitos contêm termos discriminatórios (FairnessGuard L1)

        Args:
            patterns_to_update: Dict[pattern_key, {values, pattern_type, ...}]
                                 construído por process_unprocessed_feedback().

        Returns:
            LearningBatchValidationResult. is_clean=True quando nenhum padrão bloqueado.
        """
        blocked: List[str] = []
        warnings: List[str] = []

        for pattern_key, data in patterns_to_update.items():
            # pattern_key format: "field_name:role:seniority"
            field_name = (
                pattern_key.split(":")[0].lower()
                if ":" in pattern_key
                else pattern_key.lower()
            )

            # Layer 1: campo é atributo protegido
            if field_name in _LEARNING_PROTECTED_FIELDS:
                blocked.append(pattern_key)
                warnings.append(
                    f"Campo protegido '{field_name}' não pode gerar padrão de aprendizado "
                    f"(LGPD Art. 11 / EU AI Act Art. 10)"
                )
                logger.warning(
                    "[FairnessGuard] Learning blocked — campo protegido: key=%s field=%s",
                    pattern_key, field_name,
                )
                continue

            # Layer 2: valores aceitos contêm termos discriminatórios
            for value in data.get("values", []):
                if not isinstance(value, str) or not value.strip():
                    continue
                result = self.check_explicit_bias(value)
                if result.is_blocked:
                    blocked.append(pattern_key)
                    warnings.append(
                        f"Valor discriminatório em '{field_name}': "
                        f"categoria={result.category}, termo={result.blocked_terms[:1]}"
                    )
                    logger.warning(
                        "[FairnessGuard] Learning blocked — valor discriminatório: "
                        "key=%s categoria=%s",
                        pattern_key, result.category,
                    )
                    break

        if blocked and _METRICS_AVAILABLE:
            try:
                for _ in blocked:
                    fairness_blocks_total.labels(category="learning_batch").inc()
            except Exception:
                pass

        return LearningBatchValidationResult(
            is_clean=len(blocked) == 0,
            blocked_patterns=blocked,
            warnings=warnings,
        )

    def get_categories(self) -> List[str]:
        return list(DISCRIMINATORY_CATEGORIES.keys())

    async def log_check(
        self,
        result: "FairnessCheckResult",
        db: Optional["AsyncSession"] = None,
        context: Any = "unknown",
        company_id: Optional[str] = None,
        recruiter_id: Optional[str] = None,
        job_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        # Parâmetro ignorado (compatibilidade com chamadas antigas que passavam input_text)
        input_text: Optional[str] = None,
    ) -> None:
        """
        Persist a FairnessGuard check result to the audit log (EU AI Act compliance).

        Only logs checks that blocked the query OR generated soft warnings.
        Clean checks are not persisted to avoid flooding the table.

        Args:
            result: The FairnessCheckResult from check().
            db: Async SQLAlchemy session. Se None, usa AsyncSessionLocal() internamente.
            context: Where the check occurred (pipeline | wizard | sourcing | search).
                     Aceita str ou dict; dict é convertido para str.
            company_id: Company that made the request.
            recruiter_id: Recruiter user ID.
            job_id: Related job vacancy ID.
            candidate_id: Related candidate ID.
            input_text: Ignorado (retrocompatibilidade).
        """
        if not result.is_blocked and not result.soft_warnings:
            return

        # Normalizar context para str
        if isinstance(context, dict):
            context_str = context.get("domain", context.get("context", "unknown"))
        else:
            context_str = str(context) if context else "unknown"

        async def _persist(session: "AsyncSession") -> None:
            from app.models.fairness_audit import FairnessAuditLog
            import uuid as _uuid
            query_hash = hashlib.sha256(result.original_query.encode("utf-8")).hexdigest()
            record = FairnessAuditLog(
                company_id=_uuid.UUID(company_id) if company_id else None,
                recruiter_id=_uuid.UUID(recruiter_id) if recruiter_id else None,
                job_id=_uuid.UUID(job_id) if job_id else None,
                candidate_id=_uuid.UUID(candidate_id) if candidate_id else None,
                query_hash=query_hash,
                category=result.category,
                blocked_terms=result.blocked_terms or [],
                confidence=result.confidence,
                is_blocked=result.is_blocked,
                context=context_str,
                soft_warnings=result.soft_warnings or [],
            )
            session.add(record)
            await session.flush()
            logger.debug(
                "FairnessGuard audit logged: is_blocked=%s category=%s context=%s warnings=%d",
                result.is_blocked, result.category, context_str, len(result.soft_warnings or []),
            )

        try:
            if db is not None:
                await _persist(db)
            else:
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as _db:
                    await _persist(_db)
                    await _db.commit()
        except Exception as e:
            logger.error("FairnessGuard audit log failed (non-blocking): %s", e)
