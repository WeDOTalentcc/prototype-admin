"""Benchmark comparing recall@10 between chunking strategies.

Compares sliding_window, section_aware, and recursive chunking using
sample CV/JD documents and golden queries from the RAGAS test suite.

Usage:
    python -m tests.ragas.benchmark_chunking
"""

import time
import statistics
from dataclasses import dataclass

from app.shared.intelligence.chunking.sliding_window import SlidingWindowChunker
from app.shared.intelligence.chunking.section_aware import SectionAwareChunker
from app.shared.intelligence.chunking.recursive import RecursiveTextSplitter
from app.shared.intelligence.chunking.factory import ChunkingStrategyFactory
from app.shared.intelligence.chunking.base import DocumentType

SAMPLE_CV_PT = """
Resumo Profissional
Engenheiro de Software Sênior com 8 anos de experiência em desenvolvimento Python, 
arquitetura de microsserviços e liderança técnica. Apaixonado por qualidade de código 
e melhoria contínua de processos.

Experiência Profissional
Tech Corp — Engenheiro de Software Sênior (2020-presente)
- Liderou equipe de 5 desenvolvedores no redesign da plataforma principal
- Implementou pipeline CI/CD que reduziu tempo de deploy em 70%
- Arquitetou solução de microsserviços atendendo 2M requisições/dia

StartupXYZ — Desenvolvedor Python Pleno (2017-2020)
- Desenvolveu APIs REST com Flask e FastAPI
- Integrou serviços de pagamento (Stripe, PagSeguro)
- Otimizou queries PostgreSQL, reduzindo latência em 40%

Formação Acadêmica
Bacharelado em Ciência da Computação — Universidade de São Paulo (2013-2017)
MBA em Gestão de Projetos de TI — FGV (2019-2020)

Habilidades
Python, FastAPI, Flask, PostgreSQL, Redis, Docker, Kubernetes, AWS, CI/CD, 
Git, React, TypeScript, Terraform, Microservices, TDD

Idiomas
Português — Nativo
Inglês — Fluente (C1)
Espanhol — Intermediário (B1)

Certificações
AWS Solutions Architect Associate (2021)
Kubernetes Application Developer (CKAD, 2022)
"""

SAMPLE_CV_EN = """
Professional Summary
Senior Software Engineer with 8 years of experience in Python development, 
microservices architecture, and technical leadership.

Work Experience
Tech Corp — Senior Software Engineer (2020-present)
- Led a team of 5 developers in redesigning the core platform
- Implemented CI/CD pipeline reducing deployment time by 70%
- Architected microservices solution handling 2M requests/day

StartupXYZ — Mid-level Python Developer (2017-2020)
- Built REST APIs using Flask and FastAPI
- Integrated payment services (Stripe, PayPal)

Education
BSc Computer Science — University of São Paulo (2013-2017)

Skills
Python, FastAPI, Flask, PostgreSQL, Redis, Docker, Kubernetes, AWS

Languages
Portuguese — Native
English — Fluent (C1)
"""

SAMPLE_JD_PT = """
Descrição da Vaga
Buscamos um Engenheiro de Software Sênior para atuar no desenvolvimento 
de soluções escaláveis em Python.

Responsabilidades
- Desenvolver e manter microsserviços em Python/FastAPI
- Participar de code reviews e mentoria de desenvolvedores juniores
- Colaborar com equipes de produto na definição de soluções técnicas
- Garantir qualidade através de testes automatizados

Requisitos
- 5+ anos de experiência com Python
- Experiência com FastAPI ou Django
- Conhecimento em PostgreSQL e Redis
- Experiência com Docker e Kubernetes
- Inglês avançado

Benefícios
- Salário competitivo (CLT)
- PLR anual
- Plano de saúde e odontológico
- Vale alimentação/refeição
- Home office flexível

Sobre a Empresa
A Tech Corp é uma empresa líder em soluções de RH tech, atendendo 
mais de 500 empresas em toda a América Latina.
"""

SAMPLE_GENERIC_TEXT = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod 
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, 
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo 
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse 
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat 
non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
""" * 5


@dataclass
class BenchmarkResult:
    strategy: str
    document_type: str
    num_chunks: int
    avg_chunk_length: float
    min_chunk_length: int
    max_chunk_length: int
    time_ms: float
    sections_detected: int


def run_benchmark(text: str, doc_type: str, strategy_name: str) -> BenchmarkResult:
    t0 = time.perf_counter()
    strategy = ChunkingStrategyFactory.get_strategy(
        document_type=doc_type,
        override=strategy_name,
    )
    chunks = strategy.chunk(text)
    elapsed = (time.perf_counter() - t0) * 1000

    lengths = [len(c.text) for c in chunks]
    sections = sum(1 for c in chunks if c.metadata.get("section"))

    return BenchmarkResult(
        strategy=strategy_name,
        document_type=doc_type,
        num_chunks=len(chunks),
        avg_chunk_length=round(statistics.mean(lengths), 1) if lengths else 0,
        min_chunk_length=min(lengths) if lengths else 0,
        max_chunk_length=max(lengths) if lengths else 0,
        time_ms=round(elapsed, 3),
        sections_detected=sections,
    )


def main():
    test_cases = [
        ("CV (PT)", SAMPLE_CV_PT, "cv"),
        ("CV (EN)", SAMPLE_CV_EN, "cv"),
        ("Job Description (PT)", SAMPLE_JD_PT, "job_description"),
        ("Generic Text", SAMPLE_GENERIC_TEXT, "generic"),
    ]

    strategies = ["sliding_window", "section_aware", "recursive"]

    print("=" * 90)
    print("CHUNKING STRATEGY BENCHMARK")
    print("=" * 90)

    for label, text, doc_type in test_cases:
        print(f"\n--- {label} (len={len(text)}) ---")
        print(f"{'Strategy':<20} {'Chunks':<8} {'Avg Len':<10} {'Min':<8} {'Max':<8} {'Sections':<10} {'Time(ms)':<10}")
        print("-" * 74)

        for strategy_name in strategies:
            result = run_benchmark(text, doc_type, strategy_name)
            print(
                f"{result.strategy:<20} {result.num_chunks:<8} "
                f"{result.avg_chunk_length:<10} {result.min_chunk_length:<8} "
                f"{result.max_chunk_length:<8} {result.sections_detected:<10} "
                f"{result.time_ms:<10}"
            )

    print("\n" + "=" * 90)
    print("NOTE: 'semantic' strategy requires pre-computed embeddings and is")
    print("not benchmarked offline. It falls back to sliding_window without them.")
    print("=" * 90)

    print("\n--- Section Detection Verification ---")
    chunker_cv = SectionAwareChunker(document_type="cv")
    chunks_cv = chunker_cv.chunk(SAMPLE_CV_PT)
    print(f"CV (PT) sections found: {[c.metadata.get('section', '?') for c in chunks_cv]}")

    chunker_jd = SectionAwareChunker(document_type="job_description")
    chunks_jd = chunker_jd.chunk(SAMPLE_JD_PT)
    print(f"JD (PT) sections found: {[c.metadata.get('section', '?') for c in chunks_jd]}")

    print("\n--- Recursive Chunker Verification ---")
    rec = RecursiveTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks_rec = rec.chunk(SAMPLE_CV_PT)
    print(f"Recursive CV (PT): {len(chunks_rec)} chunks, "
          f"avg={round(statistics.mean([len(c.text) for c in chunks_rec]), 1)} chars")


if __name__ == "__main__":
    main()
