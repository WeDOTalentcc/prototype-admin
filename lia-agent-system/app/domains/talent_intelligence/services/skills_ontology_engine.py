"""
Skills Ontology Engine — Graph-based skill taxonomy with adjacencies,
hierarchy (skill -> specialization -> domain), and hybrid proximity scoring.

Core of the Talent Intelligence capability. Replaces treating skills as flat
strings with a structured graph that enables:
- Related skill inference via graph traversal
- Adjacency discovery with weighted edges
- Gap analysis between candidate and job requirements
- Hybrid proximity scoring: graph propagation + embedding cosine similarity
  (embeddings loaded lazily via Gemini; falls back to graph-only if unavailable)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class SkillNode:
    id: str
    name: str
    domain: str
    specialization: str
    aliases: list[str] = field(default_factory=list)
    level_weight: float = 1.0

    @property
    def canonical(self) -> str:
        return self.name.lower().strip()


@dataclass
class SkillEdge:
    source: str
    target: str
    weight: float
    relation: str


class SkillsOntologyEngine:
    """
    In-memory graph of skills with adjacencies, hierarchy, and proximity scoring.

    The graph is pre-populated with a curated taxonomy covering the most common
    tech and business skills. It can be extended at runtime via ``add_skill``
    and ``add_adjacency``.

    Hierarchy: skill -> specialization -> domain
    Example: "FastAPI" -> "Python Web Frameworks" -> "Backend Development"
    """

    def __init__(self) -> None:
        self._nodes: dict[str, SkillNode] = {}
        self._edges: list[SkillEdge] = []
        self._adjacency: dict[str, list[tuple[str, float, str]]] = {}
        self._alias_map: dict[str, str] = {}
        self._embeddings: dict[str, list[float]] = {}
        self._embeddings_loaded: bool = False
        self._build_default_ontology()

    def _build_default_ontology(self) -> None:
        domains = self._get_seed_data()
        for domain_name, specializations in domains.items():
            for spec_name, skills in specializations.items():
                for skill_name, aliases in skills.items():
                    self.add_skill(
                        skill_name,
                        domain=domain_name,
                        specialization=spec_name,
                        aliases=aliases,
                    )

        self._build_implicit_edges()

    @staticmethod
    def _get_seed_data() -> dict[str, dict[str, dict[str, list[str]]]]:
        return {
            "Backend Development": {
                "Python Ecosystem": {
                    "Python": ["python3", "py"],
                    "Django": ["django-rest-framework", "drf"],
                    "FastAPI": ["fastapi"],
                    "Flask": ["flask"],
                    "SQLAlchemy": ["sqlalchemy", "sqla"],
                    "Celery": ["celery"],
                    "asyncio": ["async python"],
                },
                "Java Ecosystem": {
                    "Java": ["java8", "java11", "java17", "java21"],
                    "Spring Boot": ["spring", "spring-framework"],
                    "Hibernate": ["jpa", "hibernate-orm"],
                    "Maven": ["maven"],
                    "Gradle": ["gradle"],
                },
                "Node.js Ecosystem": {
                    "Node.js": ["nodejs", "node"],
                    "Express.js": ["express", "expressjs"],
                    "NestJS": ["nestjs"],
                    "TypeScript": ["ts", "typescript"],
                },
                "Go Ecosystem": {
                    "Go": ["golang"],
                    "Gin": ["gin-gonic"],
                },
                "API Design": {
                    "REST": ["restful", "rest-api"],
                    "GraphQL": ["graphql"],
                    "gRPC": ["grpc", "protobuf"],
                },
            },
            "Frontend Development": {
                "React Ecosystem": {
                    "React": ["reactjs", "react.js"],
                    "Next.js": ["nextjs"],
                    "Redux": ["redux-toolkit", "rtk"],
                },
                "Vue Ecosystem": {
                    "Vue.js": ["vue", "vuejs"],
                    "Nuxt.js": ["nuxt", "nuxtjs"],
                    "Vuetify": ["vuetify"],
                },
                "Angular Ecosystem": {
                    "Angular": ["angular2+", "angularjs"],
                    "RxJS": ["rxjs"],
                },
                "Web Fundamentals": {
                    "HTML": ["html5"],
                    "CSS": ["css3", "scss", "sass", "less"],
                    "JavaScript": ["js", "es6", "ecmascript"],
                    "Tailwind CSS": ["tailwind", "tailwindcss"],
                },
            },
            "Data & AI": {
                "Data Engineering": {
                    "SQL": ["sql", "postgres", "mysql", "postgresql"],
                    "Apache Spark": ["spark", "pyspark"],
                    "Apache Kafka": ["kafka"],
                    "Airflow": ["apache-airflow"],
                    "dbt": ["dbt-core"],
                    "ETL": ["etl-pipelines"],
                },
                "Machine Learning": {
                    "Machine Learning": ["ml"],
                    "Deep Learning": ["dl", "neural-networks"],
                    "NLP": ["nlp", "natural-language-processing"],
                    "Computer Vision": ["cv", "image-recognition"],
                    "TensorFlow": ["tf", "tensorflow"],
                    "PyTorch": ["pytorch"],
                    "scikit-learn": ["sklearn"],
                    "LLM": ["large-language-models", "genai", "generative-ai"],
                    "RAG": ["retrieval-augmented-generation"],
                    "LangChain": ["langchain"],
                },
                "Data Analysis": {
                    "Pandas": ["pandas"],
                    "NumPy": ["numpy"],
                    "Data Visualization": ["dataviz"],
                    "Tableau": ["tableau"],
                    "Power BI": ["powerbi", "power-bi"],
                    "Statistics": ["estatística"],
                },
            },
            "DevOps & Cloud": {
                "Cloud Platforms": {
                    "AWS": ["amazon-web-services"],
                    "Azure": ["microsoft-azure"],
                    "GCP": ["google-cloud", "google-cloud-platform"],
                },
                "Containers & Orchestration": {
                    "Docker": ["docker", "containerization"],
                    "Kubernetes": ["k8s"],
                    "Helm": ["helm-charts"],
                },
                "CI/CD": {
                    "GitHub Actions": ["gh-actions"],
                    "Jenkins": ["jenkins"],
                    "GitLab CI": ["gitlab-ci"],
                    "ArgoCD": ["argocd"],
                },
                "Infrastructure as Code": {
                    "Terraform": ["tf-iac", "terraform"],
                    "Ansible": ["ansible"],
                    "Pulumi": ["pulumi"],
                },
                "Monitoring": {
                    "Prometheus": ["prometheus"],
                    "Grafana": ["grafana"],
                    "Datadog": ["datadog"],
                    "ELK Stack": ["elasticsearch", "logstash", "kibana"],
                },
            },
            "Management & Soft Skills": {
                "Leadership": {
                    "Liderança": ["leadership"],
                    "Gestão de Pessoas": ["people-management"],
                    "Mentoria": ["mentoring", "coaching"],
                    "Gestão de Projetos": ["project-management", "pm"],
                },
                "Methodologies": {
                    "Agile": ["agile", "ágil"],
                    "Scrum": ["scrum"],
                    "Kanban": ["kanban"],
                    "SAFe": ["safe", "scaled-agile"],
                },
                "Communication": {
                    "Comunicação": ["communication"],
                    "Apresentação": ["presentation"],
                    "Negociação": ["negotiation"],
                    "Trabalho em Equipe": ["teamwork"],
                },
                "Product": {
                    "Product Management": ["product-manager", "pm"],
                    "Product Discovery": ["discovery"],
                    "OKR": ["okr", "objectives-key-results"],
                    "Design Thinking": ["design-thinking"],
                },
            },
            "Security": {
                "Application Security": {
                    "OWASP": ["owasp-top-10"],
                    "Penetration Testing": ["pentest"],
                    "SAST": ["static-analysis"],
                    "DAST": ["dynamic-analysis"],
                },
                "Infrastructure Security": {
                    "IAM": ["identity-access-management"],
                    "Zero Trust": ["zero-trust-architecture"],
                    "LGPD": ["lgpd", "gdpr"],
                    "SOC 2": ["soc2"],
                },
            },
            "Mobile Development": {
                "Cross-Platform": {
                    "React Native": ["react-native", "rn"],
                    "Flutter": ["flutter", "dart"],
                },
                "Native iOS": {
                    "Swift": ["swift"],
                    "SwiftUI": ["swiftui"],
                    "Objective-C": ["objc"],
                },
                "Native Android": {
                    "Kotlin": ["kotlin"],
                    "Jetpack Compose": ["compose"],
                },
            },
            "Design": {
                "UX/UI": {
                    "Figma": ["figma"],
                    "UX Design": ["ux", "user-experience"],
                    "UI Design": ["ui", "user-interface"],
                    "Design System": ["design-system", "ds"],
                    "Usability Testing": ["usability"],
                },
                "Visual Design": {
                    "Adobe Photoshop": ["photoshop"],
                    "Adobe Illustrator": ["illustrator"],
                    "Typography": ["tipografia"],
                },
            },
        }

    def add_skill(
        self,
        name: str,
        domain: str,
        specialization: str,
        aliases: list[str] | None = None,
    ) -> SkillNode:
        canonical = name.lower().strip()
        node = SkillNode(
            id=canonical,
            name=name,
            domain=domain,
            specialization=specialization,
            aliases=aliases or [],
        )
        self._nodes[canonical] = node
        for alias in node.aliases:
            self._alias_map[alias.lower().strip()] = canonical
        self._alias_map[canonical] = canonical
        return node

    def add_adjacency(self, skill_a: str, skill_b: str, weight: float = 0.5, relation: str = "related") -> None:
        a = self._resolve(skill_a)
        b = self._resolve(skill_b)
        if a and b and a != b:
            edge = SkillEdge(source=a, target=b, weight=weight, relation=relation)
            self._edges.append(edge)
            self._adjacency.setdefault(a, []).append((b, weight, relation))
            self._adjacency.setdefault(b, []).append((a, weight, relation))

    def _build_implicit_edges(self) -> None:
        by_spec: dict[str, list[str]] = {}
        by_domain: dict[str, list[str]] = {}
        for node in self._nodes.values():
            by_spec.setdefault(node.specialization, []).append(node.id)
            by_domain.setdefault(node.domain, []).append(node.id)

        for spec_skills in by_spec.values():
            for i, a in enumerate(spec_skills):
                for b in spec_skills[i + 1 :]:
                    self.add_adjacency(a, b, weight=0.8, relation="same_specialization")

        for domain_skills in by_domain.values():
            for i, a in enumerate(domain_skills):
                for b in domain_skills[i + 1 :]:
                    if not self._has_edge(a, b):
                        self.add_adjacency(a, b, weight=0.4, relation="same_domain")

    def _has_edge(self, a: str, b: str) -> bool:
        for target, _, _ in self._adjacency.get(a, []):
            if target == b:
                return True
        return False

    def _resolve(self, skill: str) -> str | None:
        key = skill.lower().strip()
        resolved = self._alias_map.get(key)
        if resolved:
            return resolved
        for node_id, node in self._nodes.items():
            if key in node_id or node_id in key:
                return node_id
        return None

    def get_skill_info(self, skill: str) -> dict[str, Any] | None:
        resolved = self._resolve(skill)
        if not resolved or resolved not in self._nodes:
            return None
        node = self._nodes[resolved]
        return {
            "id": node.id,
            "name": node.name,
            "domain": node.domain,
            "specialization": node.specialization,
            "aliases": node.aliases,
        }

    def get_adjacencies(self, skill: str, min_weight: float = 0.0) -> list[dict[str, Any]]:
        resolved = self._resolve(skill)
        if not resolved:
            return []
        adjacencies = []
        seen = set()
        for target, weight, relation in self._adjacency.get(resolved, []):
            if weight >= min_weight and target not in seen:
                seen.add(target)
                node = self._nodes.get(target)
                adjacencies.append(
                    {
                        "skill": node.name if node else target,
                        "weight": round(weight, 3),
                        "relation": relation,
                        "domain": node.domain if node else "",
                        "specialization": node.specialization if node else "",
                    }
                )
        adjacencies.sort(key=lambda x: x["weight"], reverse=True)
        return adjacencies

    def infer_related_skills(self, skills: list[str], depth: int = 2, limit: int = 15) -> list[dict[str, Any]]:
        resolved = [self._resolve(s) for s in skills]
        resolved = [r for r in resolved if r]
        if not resolved:
            return []

        visited: set[str] = set(resolved)
        scored: dict[str, float] = {}

        frontier = [(s, 1.0) for s in resolved]
        for _d in range(depth):
            next_frontier = []
            for node_id, incoming_score in frontier:
                for target, weight, _rel in self._adjacency.get(node_id, []):
                    if target in visited:
                        continue
                    propagated = incoming_score * weight
                    if target in scored:
                        scored[target] = max(scored[target], propagated)
                    else:
                        scored[target] = propagated
                    next_frontier.append((target, propagated))
            for node_id, _ in next_frontier:
                visited.add(node_id)
            frontier = next_frontier

        result = []
        for skill_id, score in sorted(scored.items(), key=lambda x: x[1], reverse=True)[:limit]:
            node = self._nodes.get(skill_id)
            if node:
                result.append(
                    {
                        "skill": node.name,
                        "relevance_score": round(score, 3),
                        "domain": node.domain,
                        "specialization": node.specialization,
                    }
                )
        return result

    def analyze_skill_gaps(
        self,
        candidate_skills: list[str],
        required_skills: list[str],
    ) -> dict[str, Any]:
        c_resolved = {self._resolve(s) for s in candidate_skills}
        c_resolved.discard(None)
        r_resolved = {self._resolve(s) for s in required_skills}
        r_resolved.discard(None)

        matched = c_resolved & r_resolved
        missing = r_resolved - c_resolved
        extra = c_resolved - r_resolved

        adjacency_matches: list[dict[str, Any]] = []
        for m in missing:
            for c in c_resolved:
                for target, weight, rel in self._adjacency.get(c, []):
                    if target == m and weight >= 0.5:
                        c_node = self._nodes.get(c)
                        m_node = self._nodes.get(m)
                        adjacency_matches.append(
                            {
                                "missing_skill": m_node.name if m_node else m,
                                "related_candidate_skill": c_node.name if c_node else c,
                                "proximity": round(weight, 3),
                                "relation": rel,
                            }
                        )

        match_pct = round(len(matched) / len(r_resolved) * 100, 1) if r_resolved else 0.0

        adj_coverage = set()
        for am in adjacency_matches:
            adj_coverage.add(self._resolve(am["missing_skill"]))
        effective_pct = (
            round((len(matched) + len(adj_coverage) * 0.7) / len(r_resolved) * 100, 1) if r_resolved else 0.0
        )

        def _name(sid: str | None) -> str:
            if sid and sid in self._nodes:
                return self._nodes[sid].name
            return sid or ""

        return {
            "match_percentage": match_pct,
            "effective_match_percentage": min(effective_pct, 100.0),
            "matched_skills": sorted([_name(s) for s in matched]),
            "missing_skills": sorted([_name(s) for s in missing]),
            "extra_skills": sorted([_name(s) for s in extra]),
            "adjacency_matches": adjacency_matches,
            "development_suggestions": self._suggest_development(missing),
            "gap_severity": ("low" if match_pct >= 80 else "medium" if match_pct >= 50 else "high"),
        }

    def _suggest_development(self, missing_skills: set[str | None]) -> list[dict[str, Any]]:
        suggestions = []
        for skill_id in missing_skills:
            if skill_id is None:
                continue
            node = self._nodes.get(skill_id)
            if node:
                related = self.get_adjacencies(skill_id, min_weight=0.6)[:3]
                suggestions.append(
                    {
                        "skill": node.name,
                        "domain": node.domain,
                        "specialization": node.specialization,
                        "learning_path": [r["skill"] for r in related],
                    }
                )
        return suggestions[:10]

    def map_skills_to_ontology(self, raw_skills: list[str]) -> dict[str, Any]:
        mapped = []
        unmapped = []
        for raw in raw_skills:
            resolved = self._resolve(raw)
            if resolved and resolved in self._nodes:
                node = self._nodes[resolved]
                mapped.append(
                    {
                        "original": raw,
                        "canonical": node.name,
                        "domain": node.domain,
                        "specialization": node.specialization,
                    }
                )
            else:
                unmapped.append(raw)

        domains: dict[str, int] = {}
        specializations: dict[str, int] = {}
        for m in mapped:
            domains[m["domain"]] = domains.get(m["domain"], 0) + 1
            specializations[m["specialization"]] = specializations.get(m["specialization"], 0) + 1

        return {
            "total_skills": len(raw_skills),
            "mapped_count": len(mapped),
            "unmapped_count": len(unmapped),
            "coverage_percentage": round(len(mapped) / len(raw_skills) * 100, 1) if raw_skills else 0,
            "mapped_skills": mapped,
            "unmapped_skills": unmapped,
            "domain_distribution": dict(sorted(domains.items(), key=lambda x: x[1], reverse=True)),
            "specialization_distribution": dict(sorted(specializations.items(), key=lambda x: x[1], reverse=True)),
        }

    async def _load_embeddings(self) -> None:
        """
        Lazily generate embeddings for all skills via the canonical embedding
        provider (Choose Your AI / BYOK). Falls back gracefully if the provider
        is unavailable — graph-only scoring continues to work.

        R-001: NAO instanciar SDK do Gemini diretamente; consumir
        EmbeddingProviderFactory (allowlisted) que respeita config do tenant.
        """
        if self._embeddings_loaded:
            return
        self._embeddings_loaded = True
        try:
            from app.shared.providers.embedding_factory import EmbeddingProviderFactory

            try:
                provider = EmbeddingProviderFactory.get_default()
            except Exception as exc:
                logger.info(
                    "Embedding provider unavailable (%s); embedding proximity disabled (graph-only mode)",
                    exc,
                )
                return

            skill_names = [n.name for n in self._nodes.values()]
            if not skill_names:
                return

            batch_size = 100
            for i in range(0, len(skill_names), batch_size):
                batch = skill_names[i : i + batch_size]
                try:
                    results = await provider.embed_batch(batch)
                except Exception as exc:
                    logger.warning(
                        "Could not load skill embeddings batch %d (graph-only mode): %s",
                        i // batch_size,
                        exc,
                    )
                    return
                for name, result in zip(batch, results):
                    self._embeddings[name.lower().strip()] = result.vector
            logger.info(f"Loaded embeddings for {len(self._embeddings)} skills")
        except Exception as e:
            logger.warning(f"Could not load skill embeddings (graph-only mode): {e}")

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def get_embedding_similarity(self, skill_a: str, skill_b: str) -> float | None:
        """
        Get cosine similarity between two skills using their embeddings.
        Returns None if embeddings are not available.
        """
        a_key = (self._resolve(skill_a) or skill_a).lower().strip()
        b_key = (self._resolve(skill_b) or skill_b).lower().strip()
        emb_a = self._embeddings.get(a_key)
        emb_b = self._embeddings.get(b_key)
        if emb_a and emb_b:
            return self._cosine_similarity(emb_a, emb_b)
        return None

    def get_hybrid_proximity(self, skill_a: str, skill_b: str) -> dict[str, Any]:
        """
        Hybrid proximity combining graph adjacency weight and embedding cosine
        similarity.  Weight blend: 0.6 * graph + 0.4 * embedding (when available).
        """
        graph_weight = 0.0
        a_resolved = self._resolve(skill_a)
        b_resolved = self._resolve(skill_b)
        if a_resolved and b_resolved:
            for target, weight, _ in self._adjacency.get(a_resolved, []):
                if target == b_resolved:
                    graph_weight = weight
                    break

        embedding_sim = self.get_embedding_similarity(skill_a, skill_b)

        if embedding_sim is not None:
            hybrid = 0.6 * graph_weight + 0.4 * embedding_sim
        else:
            hybrid = graph_weight

        return {
            "graph_weight": round(graph_weight, 3),
            "embedding_similarity": round(embedding_sim, 3) if embedding_sim is not None else None,
            "hybrid_proximity": round(hybrid, 3),
            "scoring_mode": "hybrid" if embedding_sim is not None else "graph_only",
        }

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_skills": len(self._nodes),
            "total_edges": len(self._edges),
            "domains": list(set(n.domain for n in self._nodes.values())),
            "specializations": list(set(n.specialization for n in self._nodes.values())),
            "embeddings_loaded": len(self._embeddings) > 0,
            "embeddings_count": len(self._embeddings),
        }


skills_ontology = SkillsOntologyEngine()
