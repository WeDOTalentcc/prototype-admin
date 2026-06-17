# Skills Adjacency & Inference — Arquitetura Técnica para LIA

## Índice

1. [Modelo Conceitual](#1-modelo-conceitual)
2. [Taxonomia Base (ESCO)](#2-taxonomia-base-esco)
3. [Schema do Banco de Dados](#3-schema-do-banco-de-dados)
4. [Motor de Inferência de Skills](#4-motor-de-inferência-de-skills)
5. [Motor de Adjacência](#5-motor-de-adjacência)
6. [Learnability Score](#6-learnability-score)
7. [Pipeline Completo](#7-pipeline-completo)
8. [Integração com a Plataforma LIA](#8-integração-com-a-plataforma-lia)

---

## 1. Modelo Conceitual

O sistema opera em três camadas interdependentes:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   CAMADA 1: INFERÊNCIA                                         │
│   "Que skills essa pessoa TEM mas não DECLAROU?"               │
│                                                                 │
│   Input: currículo, histórico, projetos, feedbacks             │
│   Output: lista de skills com confidence score (0.0 – 1.0)    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CAMADA 2: ADJACÊNCIA                                         │
│   "Quais skills estão PRÓXIMAS das que essa pessoa já tem?"    │
│                                                                 │
│   Input: skills confirmadas + inferidas do candidato           │
│   Output: grafo de skills adjacentes com peso de relação       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CAMADA 3: LEARNABILITY                                       │
│   "Qual a PROBABILIDADE de aprender essa skill nova?"          │
│                                                                 │
│   Input: skills atuais + skill alvo + trajetória de carreira   │
│   Output: score de 0.0 a 1.0 (potencial de aprendizado)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Conceitos-chave

| Conceito | Definição | Exemplo |
|----------|-----------|---------|
| **Skill Explícita** | Declarada diretamente no currículo ou perfil | "Python" listado em "Habilidades Técnicas" |
| **Skill Inferida** | Detectada por NLP a partir de contexto (projetos, descrições de cargo) | Pessoa que "liderou equipe de 12 pessoas" → inferir "gestão de pessoas" |
| **Skill Adjacente** | Habilidade próxima no grafo de skills que a pessoa provavelmente tem ou pode aprender rápido | Python → Pandas (adjacência forte, peso 0.85) |
| **Learnability** | Probabilidade de adquirir uma skill nova baseada nas skills atuais | Dev Python com NumPy → learnability para "Machine Learning" = 0.72 |
| **Hidden Gem** | Candidato cujo potencial (skills inferidas + adjacentes) excede suas credenciais visíveis | Gerente de restaurante → tem skills de orçamento, equipe, inventário, atendimento |

---

## 2. Taxonomia Base (ESCO)

### Por que ESCO?

ESCO (European Skills, Competences, Qualifications and Occupations) é a taxonomia da Comissão Europeia com:
- **13.485 skills/competências** categorizadas
- **2.942 ocupações** mapeadas
- Relações hierárquicas (broader/narrower) entre todas
- API pública e download gratuito (CC BY 4.0)
- Crosswalk oficial com O*NET (taxonomia americana)

### Estrutura Hierárquica

```
ESCO Skills Pillar
├── Knowledge (K)
│   ├── Business and administration
│   │   ├── ICT project management methodologies
│   │   │   └── Agile project management        ← skill individual (nível 4)
│   │   └── ...
│   ├── Engineering and technology
│   └── ...
├── Skills (S)
│   ├── Communication, collaboration, creativity
│   ├── Information skills
│   └── ...
├── Language skills (L)
└── Transversal skills (T)
    ├── Thinking
    ├── Self-management
    └── ...
```

### Arquivos de Dados (Download)

URL: `https://esco.ec.europa.eu/en/use-esco/download`

| Arquivo | Conteúdo |
|---------|----------|
| `skills_en.csv` | 13.485 skills (label, descrição, URI, tipo) |
| `skillsHierarchy_en.csv` | Hierarquia de grupos (3 níveis superiores) |
| `broaderRelationsSkillPillar_en.csv` | Relações pai→filho entre grupos e skills |
| `skillSkillRelations.csv` | Relações skill↔skill (essencial/opcional) |
| `occupationSkillRelations.csv` | Mapeamento ocupação↔skill |

### API REST

```
Base URL: https://ec.europa.eu/esco/api

GET /resource/skill?uri={esco_uri}           → detalhes de uma skill
GET /search?text=python&type=skill&language=en → busca textual
GET /resource/taxonomy?uri=...               → navegar hierarquia
```

### Crosswalk ESCO ↔ O*NET

A Comissão Europeia treinou modelos BERT fine-tuned para mapear ocupações ESCO → O*NET usando similaridade semântica. O crosswalk publicado tem matches exatos, narrow, broad e close.

---

## 3. Schema do Banco de Dados

### 3.1 Catálogo de Skills

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE skill_catalog (
    id              BIGSERIAL PRIMARY KEY,
    esco_uri        TEXT UNIQUE,
    name            TEXT NOT NULL,
    name_pt         TEXT,
    description     TEXT,
    description_pt  TEXT,
    skill_type      TEXT NOT NULL CHECK (skill_type IN ('knowledge', 'skill', 'language', 'transversal')),
    reusability     TEXT CHECK (reusability IN ('cross-sector', 'sector-specific', 'occupation-specific', 'transversal')),
    aliases         TEXT[],
    parent_id       BIGINT REFERENCES skill_catalog(id),
    hierarchy_level INT DEFAULT 4,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_skill_catalog_name ON skill_catalog USING gin(to_tsvector('english', name));
CREATE INDEX idx_skill_catalog_name_pt ON skill_catalog USING gin(to_tsvector('portuguese', coalesce(name_pt, '')));
CREATE INDEX idx_skill_catalog_type ON skill_catalog(skill_type);
CREATE INDEX idx_skill_catalog_parent ON skill_catalog(parent_id);
```

### 3.2 Embeddings de Skills

```sql
CREATE TABLE skill_embeddings (
    skill_id        BIGINT PRIMARY KEY REFERENCES skill_catalog(id) ON DELETE CASCADE,
    model_id        TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    embedding       VECTOR(1536),
    embedded_text   TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_skill_embeddings_hnsw ON skill_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

### 3.3 Grafo de Adjacência (Edges)

```sql
CREATE TABLE skill_adjacency (
    skill_a_id      BIGINT NOT NULL REFERENCES skill_catalog(id),
    skill_b_id      BIGINT NOT NULL REFERENCES skill_catalog(id),
    edge_type       TEXT NOT NULL CHECK (edge_type IN (
        'prerequisite',
        'co_occurrence',
        'semantic_similarity',
        'career_path',
        'taxonomy_sibling'
    )),
    weight          FLOAT NOT NULL CHECK (weight >= 0.0 AND weight <= 1.0),
    evidence_count  INT DEFAULT 0,
    source          TEXT,
    computed_at     TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (skill_a_id, skill_b_id, edge_type)
);

CREATE INDEX idx_adjacency_a ON skill_adjacency(skill_a_id);
CREATE INDEX idx_adjacency_b ON skill_adjacency(skill_b_id);
CREATE INDEX idx_adjacency_weight ON skill_adjacency(weight DESC);
```

### 3.4 Skills do Candidato

```sql
CREATE TABLE candidate_skills (
    id              BIGSERIAL PRIMARY KEY,
    candidate_id    TEXT NOT NULL,
    company_id      TEXT NOT NULL,
    skill_id        BIGINT REFERENCES skill_catalog(id),
    skill_name_raw  TEXT NOT NULL,
    source          TEXT NOT NULL CHECK (source IN (
        'resume_explicit',
        'resume_inferred',
        'assessment',
        'project_history',
        'feedback',
        'self_declared',
        'llm_inferred'
    )),
    confidence      FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    proficiency     TEXT CHECK (proficiency IN ('beginner', 'intermediate', 'advanced', 'expert')),
    years_experience FLOAT,
    last_used_at    DATE,
    evidence_text   TEXT,
    inferred_by     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cand_skills_candidate ON candidate_skills(candidate_id, company_id);
CREATE INDEX idx_cand_skills_skill ON candidate_skills(skill_id);
CREATE INDEX idx_cand_skills_source ON candidate_skills(source);
```

### 3.5 Learnability Scores

```sql
CREATE TABLE candidate_learnability (
    id              BIGSERIAL PRIMARY KEY,
    candidate_id    TEXT NOT NULL,
    company_id      TEXT NOT NULL,
    target_skill_id BIGINT REFERENCES skill_catalog(id),
    learnability    FLOAT NOT NULL CHECK (learnability >= 0.0 AND learnability <= 1.0),
    adjacency_score FLOAT,
    career_path_score FLOAT,
    semantic_score  FLOAT,
    computed_at     TIMESTAMPTZ DEFAULT NOW(),
    model_version   TEXT DEFAULT 'v1'
);

CREATE INDEX idx_learnability_candidate ON candidate_learnability(candidate_id, company_id);
CREATE INDEX idx_learnability_score ON candidate_learnability(learnability DESC);
```

---

## 4. Motor de Inferência de Skills

### 4.1 Pipeline de Extração

```
Documento (PDF/DOCX/texto)
    │
    ▼
┌──────────────────┐
│ 1. Parse/OCR     │  pdfplumber + pytesseract
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 2. Segmentação   │  Identificar seções: Skills, Experience, Education, Projects
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 3. Extração      │  Duas abordagens em paralelo:
│    Explícita     │  a) NER fine-tuned para skills
│                  │  b) LLM structured extraction
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 4. Normalização  │  Mapear para skill_catalog (fuzzy match + embedding similarity)
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 5. Inferência    │  Detectar skills NÃO declaradas a partir do contexto
│    Contextual    │  "liderou equipe" → inferir "gestão de pessoas"
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 6. Scoring       │  Atribuir confidence a cada skill (explícita=0.95, inferida=0.3-0.8)
└──────────────────┘
```

### 4.2 Extração Explícita (NER + LLM)

```python
from dataclasses import dataclass

@dataclass
class ExtractedSkill:
    name_raw: str
    source: str          # 'resume_explicit' | 'resume_inferred'
    confidence: float    # 0.0 - 1.0
    evidence_text: str   # trecho do documento que originou a extração
    section: str         # 'skills' | 'experience' | 'education' | 'projects'

class SkillExtractor:
    """Extrai skills de texto usando LLM com structured output."""

    EXTRACTION_PROMPT = """
    Analise o seguinte texto de currículo e extraia TODAS as skills mencionadas.

    Para cada skill, retorne:
    - name: nome da skill normalizado
    - source: "explicit" se mencionada diretamente, "inferred" se deduzida do contexto
    - confidence: 0.0-1.0 (quão certo você está)
    - evidence: trecho exato do texto que suporta a extração
    - section: em qual seção do currículo foi encontrada

    Regras de inferência:
    - "Liderou equipe de X pessoas" → inferir "people management" (confidence 0.7-0.9)
    - "Apresentou resultados para diretoria" → inferir "executive communication" (confidence 0.6)
    - "Implementou pipeline de dados" → inferir "ETL", "data engineering" (confidence 0.7)
    - Experiência em empresa de consultoria → inferir "client management" (confidence 0.5)
    - MBA ou pós-graduação em área X → inferir skills da área (confidence 0.6)

    Texto do currículo:
    ---
    {resume_text}
    ---

    Retorne APENAS um JSON array de skills extraídas.
    """

    async def extract(self, resume_text: str, sections: dict) -> list[ExtractedSkill]:
        weighted_text = self._weight_sections(resume_text, sections)

        response = await self.llm.structured_output(
            prompt=self.EXTRACTION_PROMPT.format(resume_text=weighted_text),
            response_schema=list[ExtractedSkill]
        )

        return self._deduplicate(response)

    def _weight_sections(self, text: str, sections: dict) -> str:
        """Seção 'Skills' tem peso maior que menção em 'Experience'."""
        priority = {'skills': 1.0, 'summary': 0.9, 'experience': 0.8,
                    'projects': 0.7, 'education': 0.6, 'certifications': 0.8}
        return text  # O peso é aplicado no confidence score, não no texto
```

### 4.3 Normalização contra o Catálogo

```python
class SkillNormalizer:
    """Mapeia skills brutas para o catálogo ESCO usando embedding similarity."""

    SIMILARITY_THRESHOLD = 0.78

    async def normalize(self, raw_skill: str) -> tuple[int | None, float]:
        """
        Retorna (skill_catalog_id, similarity_score) ou (None, 0.0) se não encontrou match.
        """
        embedding = await self.embed(raw_skill)

        results = await self.db.execute("""
            SELECT sc.id, sc.name, 1 - (se.embedding <=> $1::vector) AS similarity
            FROM skill_embeddings se
            JOIN skill_catalog sc ON sc.id = se.skill_id
            WHERE 1 - (se.embedding <=> $1::vector) > $2
            ORDER BY se.embedding <=> $1::vector
            LIMIT 5
        """, embedding, self.SIMILARITY_THRESHOLD)

        if not results:
            return None, 0.0

        best = results[0]
        return best['id'], best['similarity']
```

### 4.4 Inferência Contextual

```python
class ContextualInference:
    """Infere skills não declaradas a partir de padrões no texto."""

    INFERENCE_RULES = [
        {
            "pattern": r"(?:lider|gerenci|coorden|supervis)\w+\s+(?:equipe|time|grupo)\s+(?:de\s+)?(\d+)",
            "inferred_skills": ["people management", "leadership"],
            "base_confidence": 0.75,
            "confidence_boost_per_person": 0.02,  # +0.02 por pessoa na equipe
        },
        {
            "pattern": r"(?:apresent|report)\w+\s+(?:para|ao|à)\s+(?:diretor|c-level|board|diretoria)",
            "inferred_skills": ["executive communication", "stakeholder management"],
            "base_confidence": 0.65,
        },
        {
            "pattern": r"(?:implement|desenvolv|constru)\w+\s+(?:pipeline|etl|fluxo de dados)",
            "inferred_skills": ["data engineering", "ETL"],
            "base_confidence": 0.70,
        },
        {
            "pattern": r"(?:orçamento|budget)\s+(?:de\s+)?R?\$?\s*[\d.,]+\s*(?:mil|mi|MM|M)",
            "inferred_skills": ["budget management", "financial planning"],
            "base_confidence": 0.70,
        },
    ]

    CAREER_CONTEXT_RULES = [
        {
            "job_title_pattern": r"gerente\s+de\s+restaurante",
            "inferred_skills": [
                ("payroll management", 0.70),
                ("inventory management", 0.75),
                ("team building", 0.80),
                ("customer service", 0.85),
                ("budget management", 0.65),
                ("food safety compliance", 0.70),
            ],
        },
        {
            "job_title_pattern": r"(?:dev|desenvolved|engineer|engenheiro)\w*\s+(?:senior|sênior|sr\.?|pleno)",
            "inferred_skills": [
                ("code review", 0.80),
                ("mentoring", 0.65),
                ("technical documentation", 0.60),
                ("architecture decisions", 0.55),
            ],
        },
    ]
```

---

## 5. Motor de Adjacência

### 5.1 Fontes de Adjacência

O peso final de uma aresta no grafo vem de múltiplas fontes combinadas:

| Fonte | Peso na Fórmula | Como Calcular |
|-------|-----------------|---------------|
| **Similaridade Semântica** | 25% | Cosine similarity entre embeddings das descrições ESCO |
| **Co-ocorrência em Vagas** | 30% | Quantas vezes Skill A e B aparecem juntas em job postings / total de postings |
| **Trajetória de Carreira** | 20% | Frequência com que profissionais passam de Skill A → B ao longo da carreira |
| **Hierarquia Taxonômica** | 15% | Distância na árvore ESCO (irmãos=0.8, primos=0.5, distantes=0.2) |
| **Transferabilidade** | 10% | Skills com reusability "cross-sector" têm boost de adjacência |

### 5.2 Cálculo de Co-ocorrência

```python
import math

class CoOccurrenceCalculator:
    """Calcula score de co-ocorrência entre pares de skills em job postings."""

    async def compute_pair(self, skill_a_id: int, skill_b_id: int) -> float:
        """
        Chi-squared inspired relatedness:
        score = P(A∩B) / sqrt(P(A) * P(B))

        Normalizado para 0.0-1.0.
        Quanto mais frequentemente A e B aparecem JUNTAS vs. sozinhas,
        maior o score.
        """
        stats = await self.db.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE has_a AND has_b) AS both,
                COUNT(*) FILTER (WHERE has_a) AS only_a,
                COUNT(*) FILTER (WHERE has_b) AS only_b,
                COUNT(*) AS total
            FROM (
                SELECT
                    jp.id,
                    EXISTS(SELECT 1 FROM job_posting_skills WHERE job_posting_id = jp.id AND skill_id = $1) AS has_a,
                    EXISTS(SELECT 1 FROM job_posting_skills WHERE job_posting_id = jp.id AND skill_id = $2) AS has_b
                FROM job_postings jp
                WHERE jp.created_at > NOW() - INTERVAL '2 years'
            ) sub
        """, skill_a_id, skill_b_id)

        if stats['only_a'] == 0 or stats['only_b'] == 0:
            return 0.0

        p_both = stats['both'] / stats['total']
        p_a = stats['only_a'] / stats['total']
        p_b = stats['only_b'] / stats['total']

        raw = p_both / math.sqrt(p_a * p_b)
        return min(raw, 1.0)
```

### 5.3 Similaridade Semântica via pgvector

```python
class SemanticAdjacency:
    """Calcula adjacência semântica entre skills usando embeddings."""

    async def compute_top_adjacent(self, skill_id: int, top_k: int = 20) -> list[dict]:
        """Retorna as top_k skills mais semanticamente próximas."""
        return await self.db.fetch("""
            SELECT
                sc.id,
                sc.name,
                sc.skill_type,
                1 - (se1.embedding <=> se2.embedding) AS cosine_similarity
            FROM skill_embeddings se1
            CROSS JOIN LATERAL (
                SELECT se.skill_id, se.embedding
                FROM skill_embeddings se
                WHERE se.skill_id != se1.skill_id
                ORDER BY se.embedding <=> se1.embedding
                LIMIT $2
            ) se2
            JOIN skill_catalog sc ON sc.id = se2.skill_id
            WHERE se1.skill_id = $1
            ORDER BY cosine_similarity DESC
        """, skill_id, top_k)
```

### 5.4 Cálculo do Peso Combinado

```python
class AdjacencyEngine:
    """Calcula o peso final de adjacência combinando múltiplas fontes."""

    WEIGHTS = {
        'semantic':     0.25,
        'cooccurrence': 0.30,
        'career_path':  0.20,
        'taxonomy':     0.15,
        'reusability':  0.10,
    }

    async def compute_adjacency(self, skill_a_id: int, skill_b_id: int) -> float:
        scores = {}

        scores['semantic'] = await self.semantic.compute_pair(skill_a_id, skill_b_id)

        scores['cooccurrence'] = await self.cooccurrence.compute_pair(skill_a_id, skill_b_id)

        scores['career_path'] = await self.career.compute_pair(skill_a_id, skill_b_id)

        scores['taxonomy'] = await self.taxonomy.compute_pair(skill_a_id, skill_b_id)

        scores['reusability'] = await self.reusability.compute_pair(skill_a_id, skill_b_id)

        final = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS)

        return round(final, 4)
```

### 5.5 node2vec para Embeddings Estruturais (Opcional, enriquecimento)

```python
import networkx as nx
from node2vec import Node2Vec

class SkillGraphEmbeddings:
    """Gera embeddings baseados na estrutura do grafo (não apenas semântica)."""

    async def generate(self) -> dict[int, list[float]]:
        G = nx.Graph()

        edges = await self.db.fetch("""
            SELECT skill_a_id, skill_b_id, weight
            FROM skill_adjacency
            WHERE weight > 0.3
        """)

        for e in edges:
            G.add_edge(e['skill_a_id'], e['skill_b_id'], weight=e['weight'])

        node2vec = Node2Vec(
            G,
            dimensions=64,
            walk_length=30,
            num_walks=200,
            p=1.0,     # return parameter (BFS-like)
            q=0.5,     # in-out parameter (DFS-like, explora mais longe)
            workers=4,
            weight_key='weight',
        )

        model = node2vec.fit(window=10, min_count=1, batch_words=4)

        return {
            int(node): model.wv[str(node)].tolist()
            for node in G.nodes()
        }
```

---

## 6. Learnability Score

### 6.1 Fórmula

```
learnability(candidato, skill_alvo) =
    w1 * adjacency_max                    (maior adjacência entre skills atuais e alvo)
  + w2 * adjacency_avg                    (média de adjacência de TODAS as skills atuais)
  + w3 * career_trajectory_alignment      (alinhamento da trajetória de carreira)
  + w4 * learning_velocity                (velocidade histórica de aquisição de skills)
  + w5 * proficiency_depth                (profundidade nas skills adjacentes)

Pesos padrão: w1=0.35, w2=0.15, w3=0.20, w4=0.15, w5=0.15
```

### 6.2 Implementação

```python
from dataclasses import dataclass

@dataclass
class LearnabilityResult:
    target_skill_id: int
    target_skill_name: str
    learnability: float
    adjacency_max: float
    adjacency_avg: float
    career_alignment: float
    learning_velocity: float
    proficiency_depth: float
    bridge_skills: list[str]   # skills que conectam o candidato ao alvo
    estimated_time_months: int  # estimativa de tempo para aquisição

class LearnabilityCalculator:

    WEIGHTS = {
        'adjacency_max': 0.35,
        'adjacency_avg': 0.15,
        'career_alignment': 0.20,
        'learning_velocity': 0.15,
        'proficiency_depth': 0.15,
    }

    TIME_ESTIMATES = {
        # learnability_range: meses estimados
        (0.8, 1.0): 1,
        (0.6, 0.8): 3,
        (0.4, 0.6): 6,
        (0.2, 0.4): 12,
        (0.0, 0.2): 18,
    }

    async def compute(
        self,
        candidate_id: str,
        company_id: str,
        target_skill_id: int
    ) -> LearnabilityResult:

        candidate_skills = await self.db.fetch("""
            SELECT cs.skill_id, cs.confidence, cs.proficiency, cs.years_experience, sc.name
            FROM candidate_skills cs
            JOIN skill_catalog sc ON sc.id = cs.skill_id
            WHERE cs.candidate_id = $1 AND cs.company_id = $2
            AND cs.confidence > 0.5
            ORDER BY cs.confidence DESC
        """, candidate_id, company_id)

        if not candidate_skills:
            return LearnabilityResult(
                target_skill_id=target_skill_id,
                target_skill_name="",
                learnability=0.0,
                adjacency_max=0.0, adjacency_avg=0.0,
                career_alignment=0.0, learning_velocity=0.0,
                proficiency_depth=0.0, bridge_skills=[], estimated_time_months=18
            )

        adjacencies = []
        for cs in candidate_skills:
            adj = await self.adjacency_engine.get_weight(cs['skill_id'], target_skill_id)
            adjacencies.append({
                'skill_name': cs['name'],
                'adjacency': adj,
                'proficiency': cs['proficiency'],
                'confidence': cs['confidence'],
            })

        adjacency_max = max(a['adjacency'] for a in adjacencies)
        adjacency_avg = sum(a['adjacency'] for a in adjacencies) / len(adjacencies)

        career_alignment = await self._career_trajectory_score(candidate_id, target_skill_id)

        learning_velocity = await self._learning_velocity(candidate_id, company_id)

        proficiency_depth = self._proficiency_depth_score(adjacencies)

        learnability = sum([
            self.WEIGHTS['adjacency_max'] * adjacency_max,
            self.WEIGHTS['adjacency_avg'] * adjacency_avg,
            self.WEIGHTS['career_alignment'] * career_alignment,
            self.WEIGHTS['learning_velocity'] * learning_velocity,
            self.WEIGHTS['proficiency_depth'] * proficiency_depth,
        ])

        bridge = sorted(adjacencies, key=lambda a: a['adjacency'], reverse=True)[:3]
        bridge_skills = [b['skill_name'] for b in bridge if b['adjacency'] > 0.3]

        estimated_months = 18
        for (lo, hi), months in self.TIME_ESTIMATES.items():
            if lo <= learnability < hi:
                estimated_months = months
                break

        target_name = await self.db.fetchval(
            "SELECT name FROM skill_catalog WHERE id = $1", target_skill_id
        )

        return LearnabilityResult(
            target_skill_id=target_skill_id,
            target_skill_name=target_name,
            learnability=round(learnability, 3),
            adjacency_max=round(adjacency_max, 3),
            adjacency_avg=round(adjacency_avg, 3),
            career_alignment=round(career_alignment, 3),
            learning_velocity=round(learning_velocity, 3),
            proficiency_depth=round(proficiency_depth, 3),
            bridge_skills=bridge_skills,
            estimated_time_months=estimated_months,
        )

    def _proficiency_depth_score(self, adjacencies: list[dict]) -> float:
        """
        Candidato expert nas skills adjacentes tem learnability maior
        que alguém com skills adjacentes mas nível beginner.
        """
        PROF_WEIGHTS = {'expert': 1.0, 'advanced': 0.75, 'intermediate': 0.5, 'beginner': 0.25}
        relevant = [a for a in adjacencies if a['adjacency'] > 0.3]
        if not relevant:
            return 0.0
        weighted = sum(
            a['adjacency'] * PROF_WEIGHTS.get(a['proficiency'], 0.5)
            for a in relevant
        )
        return min(weighted / len(relevant), 1.0)

    async def _learning_velocity(self, candidate_id: str, company_id: str) -> float:
        """
        Mede a velocidade com que o candidato adquire skills novas.
        Baseado no histórico: quantas skills adquiridas por ano de carreira.
        """
        stats = await self.db.fetchrow("""
            SELECT
                COUNT(DISTINCT skill_id) AS total_skills,
                EXTRACT(YEAR FROM AGE(MAX(created_at), MIN(created_at))) AS career_span_years
            FROM candidate_skills
            WHERE candidate_id = $1 AND company_id = $2
        """, candidate_id, company_id)

        if not stats or stats['career_span_years'] in (None, 0):
            return 0.5  # default

        rate = stats['total_skills'] / max(stats['career_span_years'], 1)
        return min(rate / 10.0, 1.0)  # normalizar: 10 skills/ano = score 1.0
```

---

## 7. Pipeline Completo

### 7.1 Fluxo End-to-End

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PIPELINE: Candidato → Skills Profile → Hidden Gems                    │
│                                                                         │
│  1. INGESTÃO                                                           │
│     Currículo (PDF) ──► parse ──► texto segmentado por seções          │
│                                                                         │
│  2. EXTRAÇÃO                                                            │
│     Texto ──► LLM + NER ──► skills explícitas + inferidas              │
│                                                                         │
│  3. NORMALIZAÇÃO                                                        │
│     Skills brutas ──► embedding similarity ──► skill_catalog IDs        │
│     Skills não encontradas ──► fila para curadoria humana              │
│                                                                         │
│  4. ENRIQUECIMENTO                                                      │
│     Para cada skill do candidato:                                       │
│       ──► buscar top-20 skills adjacentes no grafo                     │
│       ──► calcular learnability para cada adjacente                    │
│                                                                         │
│  5. HIDDEN GEMS                                                         │
│     Comparar skills (explícitas + inferidas + adjacentes)              │
│     contra os requisitos da vaga:                                       │
│       ──► Se match de adjacência > 0.6 para skills que o candidato     │
│           NÃO tem explicitamente mas TEM adjacência forte              │
│       ──► Marcar como "Hidden Gem"                                     │
│                                                                         │
│  6. SCORING FINAL                                                       │
│     match_score = Σ(weight_i * score_i)                                │
│       onde score_i considera:                                           │
│         - explicit match (peso 1.0)                                    │
│         - inferred match (peso 0.7)                                    │
│         - adjacent match (peso 0.4 * adjacency_weight)                 │
│         - learnable match (peso 0.2 * learnability_score)              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Classe Orquestradora

```python
@dataclass
class CandidateSkillProfile:
    candidate_id: str
    explicit_skills: list[ExtractedSkill]
    inferred_skills: list[ExtractedSkill]
    adjacent_skills: list[dict]       # {skill, adjacency_score, source_skill}
    learnability_map: list[LearnabilityResult]
    hidden_gem_indicators: list[dict] # {skill, reason, learnability}

class SkillAdjacencyPipeline:
    """Orquestra o pipeline completo de inferência + adjacência."""

    def __init__(
        self,
        extractor: SkillExtractor,
        normalizer: SkillNormalizer,
        inference: ContextualInference,
        adjacency: AdjacencyEngine,
        learnability: LearnabilityCalculator,
    ):
        self.extractor = extractor
        self.normalizer = normalizer
        self.inference = inference
        self.adjacency = adjacency
        self.learnability = learnability

    async def process_candidate(
        self,
        candidate_id: str,
        company_id: str,
        resume_text: str,
        target_job_skills: list[int] | None = None,
    ) -> CandidateSkillProfile:

        # 1. Extrair skills explícitas e inferidas
        all_skills = await self.extractor.extract(resume_text, {})

        explicit = [s for s in all_skills if s.source == 'resume_explicit']
        inferred = [s for s in all_skills if s.source == 'resume_inferred']

        # 2. Normalizar contra catálogo
        for skill in all_skills:
            catalog_id, similarity = await self.normalizer.normalize(skill.name_raw)
            if catalog_id:
                skill.catalog_id = catalog_id
                skill.catalog_similarity = similarity

        # 3. Persistir
        await self._persist_skills(candidate_id, company_id, all_skills)

        # 4. Buscar adjacências
        confirmed_ids = [s.catalog_id for s in all_skills if hasattr(s, 'catalog_id')]
        adjacent_skills = []
        for sid in confirmed_ids:
            neighbors = await self.adjacency.get_top_adjacent(sid, top_k=10)
            for n in neighbors:
                if n['skill_id'] not in confirmed_ids:
                    adjacent_skills.append(n)

        # 5. Calcular learnability para skills da vaga (se fornecidas)
        learnability_map = []
        if target_job_skills:
            for target_id in target_job_skills:
                if target_id not in confirmed_ids:
                    result = await self.learnability.compute(
                        candidate_id, company_id, target_id
                    )
                    learnability_map.append(result)

        # 6. Identificar Hidden Gems
        hidden_gems = self._identify_hidden_gems(
            confirmed_ids, adjacent_skills, learnability_map, target_job_skills or []
        )

        return CandidateSkillProfile(
            candidate_id=candidate_id,
            explicit_skills=explicit,
            inferred_skills=inferred,
            adjacent_skills=adjacent_skills,
            learnability_map=learnability_map,
            hidden_gem_indicators=hidden_gems,
        )

    def _identify_hidden_gems(
        self,
        confirmed_ids: list[int],
        adjacent_skills: list[dict],
        learnability_map: list[LearnabilityResult],
        target_skills: list[int],
    ) -> list[dict]:
        """
        Hidden Gem = candidato que NÃO tem a skill explicitamente
        mas TEM adjacência forte (>0.6) ou learnability alta (>0.7).
        """
        gems = []
        for lr in learnability_map:
            if lr.target_skill_id not in confirmed_ids:
                if lr.learnability > 0.7 or lr.adjacency_max > 0.6:
                    gems.append({
                        'skill': lr.target_skill_name,
                        'learnability': lr.learnability,
                        'adjacency_max': lr.adjacency_max,
                        'bridge_skills': lr.bridge_skills,
                        'estimated_months': lr.estimated_time_months,
                        'reason': self._gem_reason(lr),
                    })
        return gems

    def _gem_reason(self, lr: LearnabilityResult) -> str:
        if lr.adjacency_max > 0.8:
            return f"Skills altamente adjacentes: {', '.join(lr.bridge_skills)}"
        elif lr.learnability > 0.7:
            return f"Alto potencial de aprendizado ({lr.learnability:.0%})"
        else:
            return f"Combinação de adjacência ({lr.adjacency_max:.0%}) e potencial ({lr.learnability:.0%})"
```

---

## 8. Integração com a Plataforma LIA

### 8.1 Onde Encaixa na Arquitetura Atual

```
Domínios atuais da LIA:
  app/domains/
    ├── sourcing/          ← Usar adjacência para EXPANDIR o pool de candidatos
    ├── screening/         ← Usar inferência para ENRIQUECER o perfil antes da triagem
    ├── job_wizard/        ← Sugerir skills adjacentes ao criar vaga
    ├── candidate_profile/ ← Mostrar skills inferidas + adjacentes no perfil
    └── evaluation/        ← Considerar potencial (learnability) na avaliação

Novos domínios necessários:
  app/domains/
    ├── skill_catalog/     ← CRUD do catálogo ESCO + custom skills
    ├── skill_inference/   ← Motor de extração + inferência
    ├── skill_adjacency/   ← Motor de adjacência + grafo
    └── skill_learnability/ ← Cálculo de potencial de aprendizado
```

### 8.2 Endpoints REST

```
POST   /api/v1/skills/extract          ← Extrair skills de texto/arquivo
POST   /api/v1/skills/normalize        ← Mapear skill bruta para catálogo
GET    /api/v1/skills/{id}/adjacent     ← Top-N skills adjacentes
GET    /api/v1/skills/search            ← Busca textual + semântica no catálogo

POST   /api/v1/candidates/{id}/skills/infer     ← Rodar inferência completa
GET    /api/v1/candidates/{id}/skills/profile    ← Perfil completo (explícitas + inferidas + adjacentes)
GET    /api/v1/candidates/{id}/learnability/{skill_id}  ← Learnability para skill específica

POST   /api/v1/jobs/{id}/hidden-gems    ← Encontrar hidden gems para uma vaga
GET    /api/v1/jobs/{id}/skill-gaps      ← Gap analysis: skills requeridas vs. pool de candidatos
```

### 8.3 Dependências de Infraestrutura

| Componente | Já Existe na LIA? | Ação |
|-----------|-------------------|------|
| PostgreSQL + pgvector | Sim (pgvector já referenciado em `app/main.py`) | Criar tabelas do schema acima |
| LLM para extração | Sim (LLM Factory com Claude/Gemini/OpenAI) | Usar factory existente |
| Embeddings | Sim (já usado para RAG search) | Reusar provider de embeddings |
| Redis (cache) | Sim | Cachear adjacências computadas |
| ESCO dataset | Não | Download + ingestão única (~13K skills) |
| Job postings para co-ocorrência | Parcial (via data_collector) | Precisa pipeline de ingestão |

### 8.4 Faseamento Sugerido

| Fase | Escopo | Esforço |
|------|--------|---------|
| **F1** | Catálogo ESCO + schema + embeddings + busca semântica | 2 sprints |
| **F2** | Motor de inferência (LLM extraction + normalização) | 2 sprints |
| **F3** | Grafo de adjacência (semântica + taxonomia) | 2 sprints |
| **F4** | Co-ocorrência (precisa de dados de vagas) + Learnability | 3 sprints |
| **F5** | Hidden Gems + integração com sourcing/screening | 2 sprints |
| **F6** | UI no frontend (perfil enriquecido, hidden gems na busca) | 2 sprints |

---

## Referências

- **Josh Bersin** — "Enterprise Talent Intelligence: Applying Skills Technology and AI at Work" (Eightfold AI whitepaper)
  - PDF: https://eightfold.ai/wp-content/uploads/Enterprise-Talent-Intelligence-Applying-Skills-Technology-and-AI-at-Work-Josh-Bersin.pdf
- **ESCO** — European Skills, Competences, Qualifications and Occupations
  - Download: https://esco.ec.europa.eu/en/use-esco/download
  - API: https://ec.europa.eu/esco/api
- **O*NET** — Occupational Information Network
  - API: https://services.onetcenter.org/ws/
- **node2vec** — Grover & Leskovec, 2016 — "Scalable Feature Learning for Networks"
- **pgvector** — https://github.com/pgvector/pgvector
