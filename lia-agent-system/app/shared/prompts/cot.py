"""
Chain-of-Thought (CoT) Prompting Builder for LIA Agent.

Provides utilities to enhance prompts with step-by-step reasoning
instructions that improve LLM output quality and consistency.

Moved from app/prompts/cot.py (I3b cleanup).
"""
from enum import Enum, StrEnum


class CoTStrategy(StrEnum):
    """Different CoT strategies for different use cases."""
    STANDARD = "standard"
    ZERO_SHOT = "zero_shot"
    SELF_CONSISTENCY = "self_consistency"
    TREE_OF_THOUGHT = "tree_of_thought"


DEFAULT_COT_STEPS_PT = [
    "Analise a entrada do usuário cuidadosamente",
    "Identifique as informações e entidades relevantes",
    "Considere o contexto atual da conversa",
    "Avalie possíveis interpretações",
    "Formule sua resposta baseada na análise"
]

DEFAULT_COT_STEPS_EN = [
    "Carefully analyze the user's input",
    "Identify relevant information and entities",
    "Consider the current conversation context",
    "Evaluate possible interpretations",
    "Formulate your response based on the analysis"
]


class ChainOfThoughtBuilder:
    """
    Builder for Chain-of-Thought prompts that encourage step-by-step reasoning.

    CoT prompting has been shown to significantly improve LLM performance
    on complex reasoning tasks by making the model "think out loud".
    """

    @staticmethod
    def wrap_with_cot(
        prompt: str,
        steps: list[str] | None = None,
        language: str = "pt"
    ) -> str:
        """
        Add CoT instruction to an existing prompt.

        Args:
            prompt: The original prompt to enhance
            steps: Custom reasoning steps (uses defaults if None)
            language: Language for default steps ("pt" or "en")

        Returns:
            Enhanced prompt with CoT instructions
        """
        if steps is None:
            steps = DEFAULT_COT_STEPS_PT if language == "pt" else DEFAULT_COT_STEPS_EN

        if language == "pt":
            cot_instruction = "Antes de responder, pense passo a passo:\n"
            footer = "\nMostre seu raciocínio brevemente, depois forneça a resposta estruturada."
        else:
            cot_instruction = "Before responding, think step by step:\n"
            footer = "\nShow your reasoning briefly, then provide the structured response."

        for i, step in enumerate(steps, 1):
            cot_instruction += f"{i}. {step}\n"

        cot_instruction += footer

        return prompt + "\n\n" + cot_instruction

    @staticmethod
    def build_cot_section(
        steps: list[str] | None = None,
        language: str = "pt",
        include_examples: bool = False
    ) -> str:
        """
        Build a standalone CoT section that can be appended to prompts.

        Args:
            steps: Custom reasoning steps
            language: Language for the section
            include_examples: Whether to include example reasoning

        Returns:
            Formatted CoT section
        """
        if steps is None:
            steps = DEFAULT_COT_STEPS_PT if language == "pt" else DEFAULT_COT_STEPS_EN

        if language == "pt":
            section = "## Processo de Raciocínio\n\n"
            section += "Para garantir uma resposta precisa, siga este processo:\n\n"
        else:
            section = "## Reasoning Process\n\n"
            section += "To ensure an accurate response, follow this process:\n\n"

        for i, step in enumerate(steps, 1):
            section += f"**Passo {i}:** {step}\n" if language == "pt" else f"**Step {i}:** {step}\n"

        if include_examples:
            section += ChainOfThoughtBuilder._get_example_reasoning(language)

        return section

    @staticmethod
    def _get_example_reasoning(language: str) -> str:
        """Get example reasoning demonstration."""
        if language == "pt":
            return """
### Exemplo de Raciocínio:
```
Entrada: "Preciso de um dev Python senior para SP, remoto"

Passo 1: O usuário quer criar uma vaga de desenvolvedor
Passo 2: Entidades - cargo: Python, senioridade: senior, local: SP, modelo: remoto
Passo 3: Contexto indica criação de nova vaga
Passo 4: Todas as informações são claras, não há ambiguidade
Passo 5: Extrair campos e confirmar com usuário

Resposta: [campos extraídos estruturados]
```
"""
        else:
            return """
### Reasoning Example:
```
Input: "I need a senior Python dev for SP, remote"

Step 1: The user wants to create a developer position
Step 2: Entities - role: Python, seniority: senior, location: SP, model: remote
Step 3: Context indicates new job creation
Step 4: All information is clear, no ambiguity
Step 5: Extract fields and confirm with user

Response: [structured extracted fields]
```
"""

    @staticmethod
    def create_task_specific_cot(task_type: str, language: str = "pt") -> str:
        """
        Create CoT instructions specific to a task type.

        Args:
            task_type: Type of task (job_extraction, salary_analysis, etc.)
            language: Language for instructions

        Returns:
            Task-specific CoT instructions
        """
        task_steps = {
            "job_extraction": {
                "pt": [
                    "Leia a mensagem e identifique menções a cargos/funções",
                    "Extraia informações de senioridade (junior, pleno, senior, etc.)",
                    "Identifique localização e modelo de trabalho",
                    "Procure por valores salariais ou faixas",
                    "Liste skills e competências mencionadas",
                    "Estruture os dados extraídos no formato esperado"
                ],
                "en": [
                    "Read the message and identify job role mentions",
                    "Extract seniority information (junior, mid, senior, etc.)",
                    "Identify location and work model",
                    "Look for salary values or ranges",
                    "List mentioned skills and competencies",
                    "Structure extracted data in expected format"
                ]
            },
            "salary_analysis": {
                "pt": [
                    "Identifique o cargo e senioridade para análise",
                    "Considere a localização e modelo de trabalho",
                    "Compare com dados de mercado conhecidos",
                    "Avalie se a faixa proposta está acima, abaixo ou no mercado",
                    "Calcule recomendação baseada em percentis de mercado",
                    "Forneça justificativa clara para a recomendação"
                ],
                "en": [
                    "Identify the role and seniority for analysis",
                    "Consider location and work model",
                    "Compare with known market data",
                    "Evaluate if proposed range is above, below or at market",
                    "Calculate recommendation based on market percentiles",
                    "Provide clear justification for the recommendation"
                ]
            },
            "intent_classification": {
                "pt": [
                    "Analise o verbo principal da mensagem",
                    "Identifique o objeto da ação (vaga, candidato, salário, etc.)",
                    "Verifique se há indicadores de ação específica",
                    "Considere o contexto implícito da conversa",
                    "Classifique a intenção com nível de confiança"
                ],
                "en": [
                    "Analyze the main verb in the message",
                    "Identify the action object (job, candidate, salary, etc.)",
                    "Check for specific action indicators",
                    "Consider implicit conversation context",
                    "Classify intent with confidence level"
                ]
            },
            "orchestration": {
                "pt": [
                    "Determine o tipo de solicitação do usuário",
                    "Verifique o estágio atual do wizard",
                    "Avalie se há dados suficientes para a ação",
                    "Identifique se precisa de esclarecimento",
                    "Decida a ação apropriada (atualizar, avançar, responder, esclarecer)"
                ],
                "en": [
                    "Determine the type of user request",
                    "Check the current wizard stage",
                    "Evaluate if there's enough data for the action",
                    "Identify if clarification is needed",
                    "Decide appropriate action (update, advance, respond, clarify)"
                ]
            },
            "competency_extraction": {
                "pt": [
                    "Identifique termos técnicos e tecnologias",
                    "Separe habilidades técnicas de comportamentais",
                    "Reconheça certificações mencionadas",
                    "Classifique como obrigatório ou diferencial",
                    "Normalize nomes de skills para padrão"
                ],
                "en": [
                    "Identify technical terms and technologies",
                    "Separate technical skills from soft skills",
                    "Recognize mentioned certifications",
                    "Classify as required or preferred",
                    "Normalize skill names to standard"
                ]
            }
        }

        if task_type not in task_steps:
            return ChainOfThoughtBuilder.build_cot_section(language=language)

        lang_key = language if language in ["pt", "en"] else "pt"
        steps = task_steps[task_type].get(lang_key, task_steps[task_type]["pt"])

        return ChainOfThoughtBuilder.build_cot_section(steps=steps, language=language)

    @staticmethod
    def create_self_consistency_prompt(
        base_prompt: str,
        num_paths: int = 3,
        language: str = "pt"
    ) -> str:
        """
        Create a self-consistency CoT prompt that generates multiple reasoning paths.

        This is useful for complex decisions where multiple valid interpretations exist.

        Args:
            base_prompt: The original prompt
            num_paths: Number of reasoning paths to generate
            language: Language for instructions

        Returns:
            Prompt with self-consistency instructions
        """
        if language == "pt":
            instruction = f"""
## Análise Multi-Perspectiva

Para garantir consistência, analise este problema de {num_paths} formas diferentes:

"""
            for i in range(1, num_paths + 1):
                instruction += f"**Caminho {i}:** [Raciocine de forma diferente]\n"

            instruction += """
Após os {num_paths} caminhos, compare as conclusões e forneça a resposta mais consistente.
Se houver divergência significativa, explique as diferentes interpretações possíveis.
"""
        else:
            instruction = f"""
## Multi-Perspective Analysis

To ensure consistency, analyze this problem in {num_paths} different ways:

"""
            for i in range(1, num_paths + 1):
                instruction += f"**Path {i}:** [Reason differently]\n"

            instruction += """
After the {num_paths} paths, compare conclusions and provide the most consistent answer.
If there's significant divergence, explain the different possible interpretations.
"""

        return base_prompt + "\n\n" + instruction.format(num_paths=num_paths)


cot_builder = ChainOfThoughtBuilder()
