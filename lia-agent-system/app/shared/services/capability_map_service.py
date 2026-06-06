"""
CapabilityMapService — loads and queries capability_map.yaml.

Guide computacional: declarative config eliminates P(LIA attempting chat
when capability is not available or entity context is missing).

PR-J harness-engineering. Consumed by main_orchestrator and entity_resolver.
"""
from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "capability_map.yaml"


@dataclass
class EntityRequirement:
    type: str   # "candidate" | "job" | "interview" | "stage"
    param: str  # key used in ui_action_params


@dataclass
class Capability:
    intent: str
    chat_executable: bool
    entity_required: list[EntityRequirement] = field(default_factory=list)
    modal_id: str | None = None
    navigate_fallback: str | None = None
    requires_confirmation: bool = False   # HITL: ação destrutiva/mutante
    navigate_page: str | None = None   # canonical page p/ navegar (sem modal)
    required_role: str | None = None   # role-gate: papel exigido (None=todos)


class CapabilityMapService:
    """Static service — loads capability_map.yaml once, cached."""

    @classmethod
    @lru_cache(maxsize=1)
    def load(cls) -> dict[str, Capability]:
        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        result: dict[str, Capability] = {}
        for intent, cfg in data.get("capabilities", {}).items():
            entity_required = [
                EntityRequirement(type=e["type"], param=e["param"])
                for e in cfg.get("entity_required", [])
            ]
            result[intent] = Capability(
                intent=intent,
                chat_executable=cfg.get("chat_executable", True),
                entity_required=entity_required,
                modal_id=cfg.get("modal_id"),
                navigate_fallback=cfg.get("navigate_fallback"),
                requires_confirmation=cfg.get("requires_confirmation", False),
                navigate_page=cfg.get("navigate_page"),
                required_role=cfg.get("required_role"),
            )
        return result

    @classmethod
    def get(cls, intent: str) -> Capability | None:
        return cls.load().get(intent)

    @classmethod
    def needs_entity(cls, intent: str) -> list[EntityRequirement]:
        cap = cls.get(intent)
        return cap.entity_required if cap else []

    @classmethod
    def is_chat_executable(cls, intent: str) -> bool:
        cap = cls.get(intent)
        return cap.chat_executable if cap is not None else True

    @classmethod
    def get_modal_id(cls, intent: str) -> str | None:
        cap = cls.get(intent)
        return cap.modal_id if cap else None

    @classmethod
    def get_navigate_fallback(cls, intent: str) -> str | None:
        cap = cls.get(intent)
        return cap.navigate_fallback if cap else None

    @classmethod
    def requires_confirmation(cls, intent: str) -> bool:
        """HITL: True se a capability é destrutiva/mutante e o modal deve
        confirmar a ação antes de efetivá-la (decisão Paulo 2026-06-06)."""
        cap = cls.get(intent)
        return cap.requires_confirmation if cap else False
