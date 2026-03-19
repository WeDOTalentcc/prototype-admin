"""
Script automático para gerar 19.500 exemplos sintéticos WSI.

Distribui em:
- 5.000 perguntas científicas
- 10.000 respostas calibradas
- 1.000 red flags
- 2.000 pareceres estruturados
- 1.500 feedbacks
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os

from langchain_anthropic import ChatAnthropic


class WSIDatasetGenerator:
    """Gerador automático de datasets WSI com rate limiting."""
    
    def __init__(self):
        self.llm = ChatAnthropic(
            model_name="claude-sonnet-4-20250514",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.8
        )
        
        self.output_dir = Path("lia-agent-system/training/datasets/synthetic")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting: max 5 concurrent LLM calls
        self.semaphore = asyncio.Semaphore(5)
        self.call_delay = 0.5  # 0.5s delay between calls = ~120 req/min
    
    async def _call_llm_with_rate_limit(self, prompt: str) -> str:
        """
        Call LLM with rate limiting to avoid 429 errors.
        
        Uses semaphore to limit concurrent calls and adds delay between requests.
        """
        async with self.semaphore:
            try:
                response = await self.llm.ainvoke(prompt)
                await asyncio.sleep(self.call_delay)  # Rate limiting delay
                return response.content if isinstance(response.content, str) else str(response.content)
            except Exception as e:
                print(f"⚠️  LLM call failed: {e}")
                await asyncio.sleep(2.0)  # Backoff on error
                raise
    
    async def generate_all(self):
        """Gera todos os 19.500 exemplos."""
        
        print("🚀 Iniciando geração de 19.500 exemplos sintéticos WSI...")
        print(f"📁 Output: {self.output_dir}")
        print("")
        
        # 1. Perguntas Científicas (5.000)
        print("1️⃣ Gerando 5.000 perguntas científicas...")
        questions = await self.generate_questions(5000)
        self._save_json("questions_5000.json", questions)
        print(f"   ✅ Salvas: {len(questions)} perguntas")
        print("")
        
        # 2. Respostas Calibradas (10.000)
        print("2️⃣ Gerando 10.000 respostas calibradas...")
        responses = await self.generate_calibrated_responses(10000)
        self._save_json("responses_10000.json", responses)
        print(f"   ✅ Salvas: {len(responses)} respostas")
        print("")
        
        # 3. Red Flags (1.000)
        print("3️⃣ Gerando 1.000 exemplos de red flags...")
        red_flags = await self.generate_red_flags(1000)
        self._save_json("red_flags_1000.json", red_flags)
        print(f"   ✅ Salvos: {len(red_flags)} red flags")
        print("")
        
        # 4. Pareceres Estruturados (2.000)
        print("4️⃣ Gerando 2.000 pareceres estruturados...")
        reports = await self.generate_reports(2000)
        self._save_json("reports_2000.json", reports)
        print(f"   ✅ Salvos: {len(reports)} pareceres")
        print("")
        
        # 5. Feedbacks (1.500)
        print("5️⃣ Gerando 1.500 feedbacks para candidatos...")
        feedbacks = await self.generate_feedbacks(1500)
        self._save_json("feedbacks_1500.json", feedbacks)
        print(f"   ✅ Salvos: {len(feedbacks)} feedbacks")
        print("")
        
        # Metadata
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "total_examples": 19500,
            "breakdown": {
                "questions": len(questions),
                "responses": len(responses),
                "red_flags": len(red_flags),
                "reports": len(reports),
                "feedbacks": len(feedbacks)
            },
            "model": "claude-sonnet-4-20250514",
            "methodology": "WSI - WeDoTalent Skill Index"
        }
        self._save_json("metadata.json", metadata)
        
        print("✅ CONCLUÍDO! 19.500 exemplos gerados com sucesso!")
        print(f"💾 Arquivos salvos em: {self.output_dir}")
    
    async def generate_questions(self, count: int) -> List[Dict]:
        """Gera perguntas científicas WSI."""
        
        questions = []
        batch_size = 50
        
        # Distribuição por framework
        frameworks = {
            "CBI": int(count * 0.40),  # 2.000 perguntas CBI
            "Bloom": int(count * 0.30),  # 1.500 Bloom
            "Dreyfus": int(count * 0.20),  # 1.000 Dreyfus
            "BigFive": int(count * 0.10)  # 500 Big Five
        }
        
        for framework, qty in frameworks.items():
            print(f"   - {framework}: {qty} perguntas")
            
            for i in range(0, qty, batch_size):
                batch = min(batch_size, qty - i)
                
                prompt = self._get_question_generation_prompt(framework, batch)
                response = await self.llm.ainvoke(prompt)
                
                content_str = response.content if isinstance(response.content, str) else str(response.content)
                batch_questions = json.loads(content_str)
                questions.extend(batch_questions)
                
                print(f"     Geradas: {len(questions)}/{count}", end="\r")
        
        print("")
        return questions[:count]
    
    async def generate_calibrated_responses(self, count: int) -> List[Dict]:
        """Gera respostas calibradas (scores 1-5)."""
        
        responses = []
        batch_size = 40
        
        # Distribuição por score (baseado em curva normal)
        score_distribution = {
            5: int(count * 0.10),  # 1.000 Expert
            4: int(count * 0.25),  # 2.500 Proficient
            3: int(count * 0.35),  # 3.500 Competent
            2: int(count * 0.20),  # 2.000 Advanced Beginner
            1: int(count * 0.10)   # 1.000 Novice
        }
        
        for score, qty in score_distribution.items():
            print(f"   - Score {score}: {qty} respostas")
            
            for i in range(0, qty, batch_size):
                batch = min(batch_size, qty - i)
                
                prompt = self._get_response_generation_prompt(score, batch)
                response = await self.llm.ainvoke(prompt)
                
                content_str = response.content if isinstance(response.content, str) else str(response.content)
                batch_responses = json.loads(content_str)
                responses.extend(batch_responses)
                
                print(f"     Geradas: {len(responses)}/{count}", end="\r")
        
        print("")
        return responses[:count]
    
    async def generate_red_flags(self, count: int) -> List[Dict]:
        """Gera exemplos de red flags."""
        
        red_flags = []
        batch_size = 30
        
        types = {
            "inflacao_score": int(count * 0.30),  # 300
            "generico": int(count * 0.25),  # 250
            "falta_contexto": int(count * 0.20),  # 200
            "inconsistencia": int(count * 0.15),  # 150
            "copiado": int(count * 0.10)  # 100
        }
        
        for red_flag_type, qty in types.items():
            print(f"   - {red_flag_type}: {qty} exemplos")
            
            for i in range(0, qty, batch_size):
                batch = min(batch_size, qty - i)
                
                prompt = self._get_red_flag_generation_prompt(red_flag_type, batch)
                response = await self.llm.ainvoke(prompt)
                
                content_str = response.content if isinstance(response.content, str) else str(response.content)
                batch_flags = json.loads(content_str)
                red_flags.extend(batch_flags)
                
                print(f"     Gerados: {len(red_flags)}/{count}", end="\r")
        
        print("")
        return red_flags[:count]
    
    async def generate_reports(self, count: int) -> List[Dict]:
        """Gera pareceres estruturados."""
        
        reports = []
        batch_size = 20
        
        categories = {
            "aprovado": int(count * 0.40),  # 800
            "aguardando": int(count * 0.30),  # 600
            "nao_aprovado": int(count * 0.30)  # 600
        }
        
        for category, qty in categories.items():
            print(f"   - {category}: {qty} pareceres")
            
            for i in range(0, qty, batch_size):
                batch = min(batch_size, qty - i)
                
                prompt = self._get_report_generation_prompt(category, batch)
                response = await self.llm.ainvoke(prompt)
                
                content_str = response.content if isinstance(response.content, str) else str(response.content)
                batch_reports = json.loads(content_str)
                reports.extend(batch_reports)
                
                print(f"     Gerados: {len(reports)}/{count}", end="\r")
        
        print("")
        return reports[:count]
    
    async def generate_feedbacks(self, count: int) -> List[Dict]:
        """Gera feedbacks para candidatos."""
        
        feedbacks = []
        batch_size = 20
        
        categories = {
            "aprovado": int(count * 0.40),  # 600
            "construtivo": int(count * 0.40),  # 600
            "desenvolvimento": int(count * 0.20)  # 300
        }
        
        for category, qty in categories.items():
            print(f"   - {category}: {qty} feedbacks")
            
            for i in range(0, qty, batch_size):
                batch = min(batch_size, qty - i)
                
                prompt = self._get_feedback_generation_prompt(category, batch)
                response = await self.llm.ainvoke(prompt)
                
                content_str = response.content if isinstance(response.content, str) else str(response.content)
                batch_feedbacks = json.loads(content_str)
                feedbacks.extend(batch_feedbacks)
                
                print(f"     Gerados: {len(feedbacks)}/{count}", end="\r")
        
        print("")
        return feedbacks[:count]
    
    def _get_question_generation_prompt(self, framework: str, count: int) -> str:
        """Gera prompt para perguntas."""
        
        if framework == "CBI":
            return f"""Gere {count} perguntas de triagem técnica baseadas em CBI (Competency-Based Interviewing).

Princípio: "Comportamentos passados são os melhores preditores de performance futura."

Estrutura da pergunta:
- Sempre começar com "Conte sobre uma situação em que..."
- Focar em experiências reais e concretas
- Avaliar: contexto (quando/onde), ação (o que fez), resultado (impacto)

Áreas técnicas (variar):
- Desenvolvimento (Python, JavaScript, React, etc.)
- DevOps (Docker, Kubernetes, CI/CD)
- Dados (SQL, Analytics, ML)
- Design (Figma, UX Research)
- Produto (Roadmap, Priorização)

Responda em JSON array:
[
  {{
    "framework": "CBI",
    "competency": "Python",
    "question_type": "contextual",
    "question_text": "Conte sobre uma situação em que você precisou otimizar código Python para melhorar performance. O que você fez e qual foi o resultado?",
    "weight": 0.20,
    "expected_signals": ["Contexto claro", "Ação técnica específica", "Resultado mensurável"],
    "scoring_criteria": {{
      "score_5": "Contexto complexo + decisões técnicas avançadas + impacto quantificado",
      "score_3": "Contexto claro + ação técnica + resultado",
      "score_1": "Contexto vago + ação genérica + sem resultado"
    }}
  }},
  ...
]

Gere {count} perguntas CBI variadas."""

        elif framework == "Bloom":
            return f"""Gere {count} microcases técnicos baseados na Taxonomia de Bloom.

Níveis cognitivos:
1. Lembrar - Recordar fatos
2. Compreender - Explicar ideias
3. Aplicar - Usar conhecimento
4. Analisar - Diferenciar conceitos
5. Criar - Gerar soluções

Foco em níveis 3-5 (Aplicar, Analisar, Criar).

Responda em JSON array similar ao exemplo CBI, mas com:
- question_type: "microcase"
- Perguntas técnicas práticas (SQL, código, arquitetura)

Gere {count} microcases."""

        elif framework == "Dreyfus":
            return f"""Gere {count} perguntas de autodeclaração baseadas no Modelo Dreyfus.

Estrutura:
"De 1 a 5, quanto você domina [tecnologia]? Pode citar um projeto recente onde aplicou?"

Combina:
- Autodeclaração (score 1-5)
- Validação contextual (projeto real)

Áreas: Python, JavaScript, React, SQL, AWS, Docker, Figma, etc.

Responda em JSON array similar aos anteriores.

Gere {count} perguntas."""

        else:  # BigFive
            return f"""Gere {count} perguntas situacionais baseadas no Big Five (OCEAN).

Traços:
- Openness: Inovação, aprendizado
- Conscientiousness: Organização, entrega
- Extraversion: Comunicação, liderança
- Agreeableness: Colaboração, empatia
- Emotional Stability: Controle sob pressão

Estrutura: "Como você reage quando...", "Descreva uma situação em que..."

Responda em JSON array similar.

Gere {count} perguntas."""
    
    def _get_response_generation_prompt(self, score: int, count: int) -> str:
        """Gera prompt para respostas calibradas."""
        
        score_descriptions = {
            5: "Expert - Domínio intuitivo, liderança técnica, contribuições significativas",
            4: "Proficient - Autonomia completa, mentoria, otimizações",
            3: "Competent - Execução consistente, boas práticas, entrega",
            2: "Advanced Beginner - Conhece ferramentas, precisa supervisão",
            1: "Novice - Apenas teórico, sem experiência prática"
        }
        
        return f"""Gere {count} respostas de candidatos para perguntas técnicas, calibradas para Score {score}.

Descrição do nível {score}: {score_descriptions[score]}

Perguntas base (variar):
- "De 1 a 5, quanto domina Python? Cite projeto recente."
- "Conte sobre otimização de performance que fez."
- "Descreva experiência com arquitetura de microsserviços."

Responda em JSON array:
[
  {{
    "question": "De 1 a 5, quanto domina Python? Cite projeto.",
    "competency": "Python",
    "response_text": "[Resposta do candidato aqui]",
    "annotation": {{
      "autodeclaration_score": {score},
      "context_score": {score},
      "bloom_level": {min(score, 5)},
      "dreyfus_level": {score},
      "evidences": ["Lista de evidências concretas"],
      "final_score": {score},
      "classification": "{score_descriptions[score].split(' - ')[0]}"
    }}
  }},
  ...
]

IMPORTANTE: Respostas devem REALMENTE refletir o nível {score}.
- Score 5: Mencione contribuições open source, mentoria, decisões arquiteturais complexas, métricas
- Score 3: Projeto real, tecnologias específicas, boas práticas
- Score 1: "Fiz curso", "estudando", sem projeto concreto

Gere {count} respostas calibradas para Score {score}."""
    
    def _get_red_flag_generation_prompt(self, red_flag_type: str, count: int) -> str:
        """Gera prompt para red flags."""
        
        return f"""Gere {count} exemplos de respostas problemáticas tipo: {red_flag_type}

Tipos:
- inflacao_score: Autodeclara 5, mas contexto mostra 2-3
- generico: "Trabalhei com isso", "fiz alguns projetos" (vago)
- falta_contexto: Autodeclara alto, mas não cita exemplos
- inconsistencia: Contradições na resposta
- copiado: Resposta que parece copiada de tutorial/doc

Responda em JSON array:
[
  {{
    "tipo_red_flag": "{red_flag_type}",
    "question": "De 1 a 5, quanto domina React?",
    "response": "[Resposta problemática]",
    "analysis": {{
      "autodeclaration": 5,
      "context_score": 2.0,
      "inconsistency": true,
      "penalty": -1.5,
      "final_score": 2.5,
      "alert": "Descrição do problema"
    }}
  }},
  ...
]

Gere {count} exemplos de {red_flag_type}."""
    
    def _get_report_generation_prompt(self, category: str, count: int) -> str:
        """Gera prompt para pareceres."""
        
        wsi_ranges = {
            "aprovado": "4.0-5.0",
            "aguardando": "3.5-3.9",
            "nao_aprovado": "< 3.5"
        }
        
        return f"""Gere {count} pareceres estruturados para candidatos categoria: {category} (WSI {wsi_ranges[category]})

Estrutura do parecer:
- Sumário executivo (2-3 frases)
- Análise técnica (pontos fortes, gaps, evidências)
- Análise comportamental (colaboração, inovação, comunicação)
- Fit cultural (valores alinhados)
- Recomendação (APROVADO/AGUARDANDO/NÃO APROVADO + justificativa)

Responda em JSON array com pareceres completos.

Gere {count} pareceres."""
    
    def _get_feedback_generation_prompt(self, category: str, count: int) -> str:
        """Gera prompt para feedbacks."""
        
        return f"""Gere {count} feedbacks estruturados para candidatos tipo: {category}

Estrutura:
- Mensagem principal (encorajadora)
- Pontos fortes técnicos (3-5)
- Oportunidades de desenvolvimento (2-3)
- Pontos fortes comportamentais (2-3)
- Próximos passos OU plano de desenvolvimento
- Recursos recomendados (se não aprovado)

Tom: Construtivo, empático, profissional

Responda em JSON array com feedbacks completos.

Gere {count} feedbacks tipo {category}."""
    
    def _save_json(self, filename: str, data: Any):
        """Salva dados em JSON."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


async def main():
    """Executa geração de todos os datasets."""
    generator = WSIDatasetGenerator()
    await generator.generate_all()


if __name__ == "__main__":
    asyncio.run(main())
