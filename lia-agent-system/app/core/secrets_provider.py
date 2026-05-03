"""
Secrets Provider — abstração para leitura de secrets.

Suporta dois modos:
- "env": lê diretamente das variáveis de ambiente (padrão dev)
- "doppler": lê via Doppler CLI (produção)

Selecionado por SECRETS_PROVIDER no config.

Uso:
    provider = get_secrets_provider()
    api_key = provider.get("ANTHROPIC_API_KEY")
"""
import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SecretsProvider(ABC):
    """Interface abstrata para provedores de secrets."""

    @abstractmethod
    def get(self, key: str, default: str | None = None) -> str | None:
        """Retorna o valor do secret ou default se não encontrado."""

    def get_required(self, key: str) -> str:
        """Retorna o valor ou lança ValueError se ausente."""
        value = self.get(key)
        if value is None:
            logger.debug("[secrets] Required secret not configured: %s", key)
            raise ValueError(
                "Required secret not configured. Contact the deployment team to verify environment variables."
            )
        return value


class EnvProvider(SecretsProvider):
    """Lê secrets das variáveis de ambiente (desenvolvimento)."""

    def get(self, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)


class DopplerProvider(SecretsProvider):
    """
    Lê secrets via Doppler SDK.

    Requer DOPPLER_TOKEN no ambiente e pacote `doppler-env` instalado.
    Fallback para env vars se Doppler indisponível.
    """

    def __init__(self, token: str | None = None):
        self._token = token or os.environ.get("DOPPLER_TOKEN")
        self._cache: dict = {}
        self._loaded = False
        self._load_secrets()

    def _load_secrets(self) -> None:
        """Carrega todos os secrets do Doppler para cache local."""
        if not self._token:
            logger.warning("[DopplerProvider] DOPPLER_TOKEN não configurado, fallback para env")
            return

        try:
            import subprocess
            result = subprocess.run(
                ["doppler", "secrets", "download", "--no-file", "--format=env"],
                capture_output=True,
                text=True,
                env={**os.environ, "DOPPLER_TOKEN": self._token},
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "=" in line and not line.startswith("#"):
                        k, _, v = line.partition("=")
                        self._cache[k.strip()] = v.strip().strip('"').strip("'")
                self._loaded = True
                logger.info("[DopplerProvider] %d secrets carregados", len(self._cache))
            else:
                logger.warning("[DopplerProvider] Doppler CLI falhou: %s", result.stderr[:200])
        except FileNotFoundError:
            logger.warning("[DopplerProvider] Doppler CLI não instalado, fallback para env")
        except Exception as exc:
            logger.warning("[DopplerProvider] Falha ao carregar secrets: %s", exc)

    def get(self, key: str, default: str | None = None) -> str | None:
        if self._loaded and key in self._cache:
            return self._cache[key]
        return os.environ.get(key, default)


def get_secrets_provider() -> SecretsProvider:
    """Retorna o provider configurado via SECRETS_PROVIDER."""
    from app.core.config import settings
    provider_type = settings.SECRETS_PROVIDER.lower()

    if provider_type == "doppler":
        return DopplerProvider(token=settings.DOPPLER_TOKEN)

    return EnvProvider()


# Singleton — inicializado lazily na primeira chamada
_provider: SecretsProvider | None = None


def secrets() -> SecretsProvider:
    """Retorna singleton do provider de secrets."""
    global _provider
    if _provider is None:
        _provider = get_secrets_provider()
    return _provider
