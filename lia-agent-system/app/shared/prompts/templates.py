"""
Prompt Template System for LIA Agent.

Provides a structured way to manage, compose, and render prompts
with support for few-shot examples and Chain-of-Thought reasoning.

Moved from app/prompts/templates.py (I3b cleanup).
"""
import logging
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PromptTemplate(BaseModel):
    """
    A structured prompt template with support for few-shot examples and CoT.

    Attributes:
        name: Unique identifier for the template
        system_prompt: The system-level instruction for the LLM
        few_shot_examples: List of input/output example pairs
        cot_enabled: Whether to include Chain-of-Thought instructions
        cot_steps: Custom CoT reasoning steps (uses defaults if None)
        output_format: Expected output format description
        variables: List of variable names that can be interpolated
    """
    name: str
    system_prompt: str
    few_shot_examples: list[dict[str, Any]] = Field(default_factory=list)
    cot_enabled: bool = False
    cot_steps: list[str] | None = None
    output_format: str | None = None
    variables: list[str] = Field(default_factory=list)

    def render(self, context: dict[str, Any]) -> str:
        """
        Render the full prompt with context variables, examples, and CoT.

        Args:
            context: Dictionary of variable values to interpolate

        Returns:
            Fully rendered prompt string
        """
        prompt_parts = []

        rendered_system = self._interpolate(self.system_prompt, context)
        prompt_parts.append(rendered_system)

        if self.few_shot_examples:
            examples_section = self._render_examples(context)
            if examples_section:
                prompt_parts.append("\n\n## Exemplos:\n" + examples_section)

        if self.cot_enabled:
            cot_section = self._render_cot()
            prompt_parts.append("\n\n" + cot_section)

        if self.output_format:
            rendered_format = self._interpolate(self.output_format, context)
            prompt_parts.append("\n\n## Formato de Saída:\n" + rendered_format)

        return "".join(prompt_parts)

    def render_system_prompt(self, context: dict[str, Any]) -> str:
        """Render only the system prompt with context."""
        return self._interpolate(self.system_prompt, context)

    def render_user_message(self, user_input: str, context: dict[str, Any]) -> str:
        """
        Render a user message with examples and context.

        Args:
            user_input: The actual user message
            context: Additional context variables

        Returns:
            Formatted user message
        """
        parts = []

        if context:
            context_str = "\n".join(f"- {k}: {v}" for k, v in context.items() if v is not None)
            if context_str:
                parts.append(f"Contexto atual:\n{context_str}")

        if self.few_shot_examples:
            examples_section = self._render_examples(context)
            if examples_section:
                parts.append(f"Exemplos de referência:\n{examples_section}")

        parts.append(f"Mensagem do usuário: {user_input}")

        if self.cot_enabled:
            parts.append(self._render_cot())

        return "\n\n".join(parts)

    def _interpolate(self, text: str, context: dict[str, Any]) -> str:
        """Replace {variable} placeholders with context values."""
        result = text
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value) if value is not None else "")

        remaining = re.findall(r'\{(\w+)\}', result)
        for var in remaining:
            if var not in context:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Unresolved variable in template '{self.name}': {var}")

        return result

    def _render_examples(self, context: dict[str, Any]) -> str:
        """Render few-shot examples section."""
        if not self.few_shot_examples:
            return ""

        example_parts = []
        for i, example in enumerate(self.few_shot_examples, 1):
            ex_str = f"### Exemplo {i}:\n"

            if "input" in example:
                ex_str += f"**Entrada:** {example['input']}\n"

            if "reasoning" in example:
                ex_str += f"**Raciocínio:** {example['reasoning']}\n"

            if "output" in example:
                output = example['output']
                if isinstance(output, dict):
                    output_str = "\n".join(f"  - {k}: {v}" for k, v in output.items())
                    ex_str += f"**Saída:**\n{output_str}\n"
                else:
                    ex_str += f"**Saída:** {output}\n"

            example_parts.append(ex_str)

        return "\n".join(example_parts)

    def _render_cot(self) -> str:
        """Render Chain-of-Thought instructions."""
        if self.cot_steps:
            steps = self.cot_steps
        else:
            steps = [
                "Analise a entrada do usuário cuidadosamente",
                "Identifique as informações relevantes e entidades",
                "Considere o contexto atual da conversa",
                "Formule sua resposta baseada na análise"
            ]

        cot_text = "## Processo de Raciocínio:\nAntes de responder, pense passo a passo:\n"
        for i, step in enumerate(steps, 1):
            cot_text += f"{i}. {step}\n"

        cot_text += "\nMostre seu raciocínio brevemente, depois forneça a resposta estruturada."

        return cot_text


class PromptLibrary:
    """
    Central registry for all prompt templates.

    Provides a singleton pattern for managing templates across the application.
    """
    _templates: dict[str, PromptTemplate] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, template: PromptTemplate) -> None:
        """
        Register a new template in the library.

        Args:
            template: The PromptTemplate to register
        """
        if template.name in cls._templates:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.warning(f"Overwriting existing template: {template.name}")

        cls._templates[template.name] = template
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.debug(f"Registered prompt template: {template.name}")

    @classmethod
    def get(cls, name: str) -> PromptTemplate:
        """
        Get a template by name.

        Args:
            name: Template identifier

        Returns:
            The requested PromptTemplate

        Raises:
            KeyError: If template not found
        """
        if not cls._initialized:
            cls._initialize_defaults()

        if name not in cls._templates:
            available = list(cls._templates.keys())
            raise KeyError(f"Template '{name}' not found. Available: {available}")

        return cls._templates[name]

    @classmethod
    def list_templates(cls) -> list[str]:
        """Get list of all registered template names."""
        if not cls._initialized:
            cls._initialize_defaults()
        return list(cls._templates.keys())

    @classmethod
    def has_template(cls, name: str) -> bool:
        """Check if a template exists."""
        if not cls._initialized:
            cls._initialize_defaults()
        return name in cls._templates

    @classmethod
    def _initialize_defaults(cls) -> None:
        """Initialize default templates from job_wizard module."""
        if cls._initialized:
            return

        try:
            from app.shared.prompts.job_wizard import register_job_wizard_templates
            register_job_wizard_templates()
            cls._initialized = True
            logger.info(f"Initialized {len(cls._templates)} prompt templates")
        except ImportError as e:
            logger.warning(f"Could not load job_wizard templates: {e}")
            cls._initialized = True

    @classmethod
    def clear(cls) -> None:
        """Clear all templates (mainly for testing)."""
        cls._templates.clear()
        cls._initialized = False


prompt_library = PromptLibrary
