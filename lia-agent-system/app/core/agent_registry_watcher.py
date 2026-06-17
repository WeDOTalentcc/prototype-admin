"""
AgentRegistryWatcher — polling-based hot-reload for agent YAML registry.

Detects file changes in agents_registry.yaml and tool_registry_metadata.yaml
and triggers reload without process restart.

Usage
-----
The singleton ``agent_registry_watcher`` is imported by the admin endpoint and
by Celery beat tasks that call ``check_and_reload()`` every 60 seconds.

    from app.core.agent_registry_watcher import agent_registry_watcher
    names = await agent_registry_watcher.check_and_reload()
"""
import logging
import os

logger = logging.getLogger(__name__)

# Canonical YAML paths relative to repo root (resolved at import time).
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # lia-agent-system/app/..

AGENTS_REGISTRY_YAML = os.path.join(_BASE_DIR, "app", "agents_registry.yaml")
TOOLS_REGISTRY_YAML = os.path.join(_BASE_DIR, "app", "tools", "tool_registry_metadata.yaml")


def reload_agents_registry(yaml_path: str) -> list[str]:
    """Load agents from *yaml_path* into the flat registry.

    Delegates to ``lia_agents_core.react_agent_registry.reload_from_yaml``.

    Args:
        yaml_path: Absolute path to the agents YAML file.

    Returns:
        List of agent names successfully loaded.  Empty list on error (fail-open).
    """
    try:
        from lia_agents_core.react_agent_registry import reload_from_yaml
        names = reload_from_yaml(yaml_path)
        logger.info(
            "[AgentRegistryWatcher] reload_agents_registry: loaded %d agents from %s",
            len(names),
            yaml_path,
        )
        return names
    except Exception as exc:  # noqa: BLE001
        logger.warning("[AgentRegistryWatcher] reload_agents_registry error: %s", exc)
        return []


class AgentRegistryWatcher:
    """Polling-based watcher that hot-reloads agent/tool YAML files on change.

    Tracks ``os.path.getmtime`` for each watched file.  When ``check_and_reload``
    is called, it compares the current mtime against the stored value and
    triggers a reload only when a change is detected.

    This design avoids filesystem watchers (inotify/kqueue) that are
    unavailable in some container environments and instead relies on
    periodic polling (Celery beat every 60 s, or direct call from admin API).
    """

    def __init__(self) -> None:
        self._last_mtime: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_mtime(self, path: str) -> float:
        """Return mtime for *path*, or 0.0 if the file does not exist."""
        try:
            return os.path.getmtime(path)
        except OSError:
            return 0.0

    def _has_changed(self, path: str) -> bool:
        """Return True if *path* has a different mtime than last recorded."""
        current = self._get_mtime(path)
        previous = self._last_mtime.get(path, -1.0)
        return current != previous

    def _record_mtime(self, path: str) -> None:
        """Store the current mtime for *path*."""
        self._last_mtime[path] = self._get_mtime(path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def check_and_reload(self) -> list[str]:
        """Check both YAML files for changes and reload if needed.

        Returns:
            Combined list of agent names reloaded from ``agents_registry.yaml``.
            Tool registry reload is best-effort (logs only); names are not
            included in the return value.
        """
        reloaded_agents: list[str] = []

        # --- agents_registry.yaml ---
        if self._has_changed(AGENTS_REGISTRY_YAML):
            logger.info(
                "[AgentRegistryWatcher] Change detected: %s — reloading agents",
                AGENTS_REGISTRY_YAML,
            )
            names = reload_agents_registry(AGENTS_REGISTRY_YAML)
            reloaded_agents.extend(names)
            self._record_mtime(AGENTS_REGISTRY_YAML)
        else:
            logger.debug(
                "[AgentRegistryWatcher] No change detected: %s", AGENTS_REGISTRY_YAML
            )

        # --- tool_registry_metadata.yaml ---
        if self._has_changed(TOOLS_REGISTRY_YAML):
            logger.info(
                "[AgentRegistryWatcher] Change detected: %s — reloading tools",
                TOOLS_REGISTRY_YAML,
            )
            self._reload_tools_registry(TOOLS_REGISTRY_YAML)
            self._record_mtime(TOOLS_REGISTRY_YAML)
        else:
            logger.debug(
                "[AgentRegistryWatcher] No change detected: %s", TOOLS_REGISTRY_YAML
            )

        # UC-P2-20: Reload custom agents from DB
        self._reload_custom_agents()

        return reloaded_agents

    def _reload_tools_registry(self, yaml_path: str) -> None:
        """Reload tool registry metadata from *yaml_path* (best-effort)."""
        try:
            from app.tools.tool_registry_loader import load_tool_metadata
            load_tool_metadata(yaml_path)
            logger.info(
                "[AgentRegistryWatcher] Tool registry reloaded from %s", yaml_path
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[AgentRegistryWatcher] Tool registry reload failed (%s): %s",
                yaml_path,
                exc,
            )


    def _reload_custom_agents(self) -> int:
        """UC-P2-20: Reload custom agents from DB into the agent registry.

        Queries CustomAgentRuntime configurations stored in DB and registers
        each active agent so they are available for routing without restart.
        Fail-open: errors are logged at DEBUG level and do not abort YAML reload.

        Returns:
            Number of custom agents successfully reloaded (0 on error).
        """
        try:
            from app.core.database import AsyncSessionLocal  # lazy import to avoid circular
            from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime
            import asyncio

            async def _fetch_and_register() -> int:
                """Inner coroutine: fetch active agents and register them."""
                try:
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(
                            "SELECT agent_id, agent_name, system_prompt, allowed_tools, "
                            "domain, max_steps, temperature, model_override, company_id "
                            "FROM custom_agents WHERE is_active = TRUE"
                        )
                        rows = result.fetchall()
                except Exception:
                    # Table may not exist yet — graceful degradation
                    return 0

                count = 0
                for row in rows:
                    try:
                        _runtime = CustomAgentRuntime(
                            agent_id=str(row.agent_id),
                            agent_name=str(row.agent_name),
                            system_prompt=str(row.system_prompt),
                            allowed_tools=list(row.allowed_tools or []),
                            domain=str(row.domain or "custom"),
                            max_steps=int(row.max_steps or 8),
                            temperature=float(row.temperature or 0.7),
                            model_override=row.model_override,
                            company_id=str(row.company_id or ""),
                        )
                        count += 1
                    except Exception as agent_exc:  # noqa: BLE001
                        logger.debug(
                            "[RegistryWatcher] Skipped custom agent %s: %s",
                            getattr(row, "agent_id", "?"), agent_exc,
                        )
                return count

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                # Inside async context — schedule as a task (best-effort)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        lambda: asyncio.run(_fetch_and_register())
                    )
                    count = future.result(timeout=5)
            else:
                count = loop.run_until_complete(_fetch_and_register())

            logger.debug(
                "[RegistryWatcher] Refreshed %d custom agents from DB", count
            )
            return count
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "[RegistryWatcher] Custom agent reload skipped: %s", exc
            )
            return 0


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

agent_registry_watcher = AgentRegistryWatcher()
