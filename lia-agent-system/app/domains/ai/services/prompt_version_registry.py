"""
PromptVersionRegistry — Registro de versões de system prompts para rastreabilidade.

Cada prompt registrado tem:
- name: identificador (ex: "talent_react_v2")
- version: string semver-like (ex: "2.1.0")
- template: texto do prompt
- hash_sha256: calculado automaticamente no registro (12 chars prefix)
- created_at: datetime UTC

Armazenamento: dict em memória (singleton).
Persiste hash no ConversationLog.prompt_version para auditoria.

Uso:
    from app.shared.services.prompt_version_registry import prompt_version_registry

    hash_prefix = prompt_version_registry.register(
        name="talent_react_v2",
        version="2.1.0",
        template=MY_SYSTEM_PROMPT,
    )
    # Guarda hash_prefix no ConversationLog.prompt_version
"""
import hashlib
import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class PromptVersionRegistry:
    """
    Registro singleton de versões de system prompts.

    Thread-safety: leituras e escritas são operações atômicas em CPython
    (GIL protege dict). Para uso em workers multi-processo, cada processo
    terá seu próprio singleton — comportamento aceitável pois o registry
    é reconstituído no startup por register() calls.
    """

    def __init__(self) -> None:
        # { name -> { version -> dict } }
        self._store: dict[str, dict[str, dict]] = {}
        # { hash_prefix -> dict } — índice reverso para lookup rápido
        self._hash_index: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------

    def register(self, name: str, version: str, template: str) -> str:
        """
        Registra (ou atualiza) um prompt.

        Retorna o hash SHA-256 truncado nos primeiros 12 caracteres.
        Se o mesmo (name, version) já existir, atualiza o template e
        recalcula o hash (útil durante desenvolvimento).
        """
        full_hash = hashlib.sha256(template.encode("utf-8")).hexdigest()
        hash_prefix = full_hash[:12]

        entry = {
            "name": name,
            "version": version,
            "template": template,
            "hash_sha256": full_hash,
            "hash_prefix": hash_prefix,
            "created_at": datetime.now(UTC).isoformat(),
        }

        if name not in self._store:
            self._store[name] = {}

        # Remove índice antigo se a versão já existia
        old_entry = self._store[name].get(version)
        if old_entry:
            old_prefix = old_entry.get("hash_prefix")
            if old_prefix and old_prefix in self._hash_index:
                del self._hash_index[old_prefix]

        self._store[name][version] = entry
        self._hash_index[hash_prefix] = entry

        logger.debug(
            "[PromptVersionRegistry] Registrado: name=%s version=%s hash=%s",
            name,
            version,
            hash_prefix,
        )
        return hash_prefix

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def get(self, name: str, version: str = "latest") -> dict | None:
        """
        Retorna o dict de um prompt específico ou None se não encontrado.

        version="latest" retorna a versão mais recentemente registrada
        (por ordem de inserção no dict, Python 3.7+).
        """
        versions = self._store.get(name)
        if not versions:
            return None

        if version == "latest":
            # Última chave inserida
            last_key = list(versions.keys())[-1]
            return versions[last_key]

        return versions.get(version)

    def get_by_hash(self, hash_prefix: str) -> dict | None:
        """
        Lookup por prefixo SHA-256 (12 chars).
        Retorna None se não encontrado.
        """
        return self._hash_index.get(hash_prefix)

    def list_versions(self, name: str) -> list[dict]:
        """
        Lista todas as versões registradas para um nome, ordenadas
        por created_at ascendente.
        """
        versions = self._store.get(name, {})
        entries = list(versions.values())
        entries.sort(key=lambda e: e.get("created_at", ""))
        return entries

    def get_current_hash(self, name: str) -> str | None:
        """
        Retorna o hash_prefix da versão mais recente de um nome.
        Retorna None se o nome não existir.
        """
        entry = self.get(name, version="latest")
        if entry is None:
            return None
        return entry.get("hash_prefix")

    def list_all(self) -> list[dict]:
        """
        Lista todos os prompts registrados (todas versões de todos os nomes).
        Ordenado por (name, created_at).
        """
        result: list[dict] = []
        for versions in self._store.values():
            result.extend(versions.values())
        result.sort(key=lambda e: (e.get("name", ""), e.get("created_at", "")))
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        """Número total de entradas (todas versões de todos os nomes)."""
        return sum(len(v) for v in self._store.values())

    def __contains__(self, name: str) -> bool:
        return name in self._store


# Singleton global — importar e usar diretamente
prompt_version_registry = PromptVersionRegistry()
