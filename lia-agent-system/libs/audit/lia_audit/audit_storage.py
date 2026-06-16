"""
Audit Storage — abstração de armazenamento para logs completos de auditoria.

Dev/staging: LocalFileStorage  → salva em ./audit_logs/{company_id}/{date}/{exec_id}.json
Produção:    S3Storage          → s3://{bucket}/{prefix}/{domain}/{date}/{company_id}/{exec_id}.json

Configurado por AUDIT_STORAGE_TYPE ("file" | "s3") nas settings.
"""
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Política de retenção: 90 dias Standard → Glacier Instant Retrieval → Glacier Deep Archive após 365 dias
AUDIT_RETENTION_DAYS_HOT = 90       # S3 Standard → Glacier Instant Retrieval
AUDIT_RETENTION_DAYS_COLD = 365     # Glacier Instant → Deep Archive
AUDIT_RETENTION_DAYS_DELETE = 2555  # 7 anos total (SOX compliance) → Delete


class AuditStorage(ABC):
    """Interface abstrata para storage de logs de auditoria."""

    @abstractmethod
    async def save(self, path: str, data: dict) -> str:
        """
        Persiste o payload de auditoria.

        Args:
            path: Caminho relativo (ex: "vagas/2026/03/07/company-id/exec-id.json")
            data: Payload completo da execução

        Returns:
            Caminho/URI completo onde foi salvo (para referência no PostgreSQL)
        """
        ...

    @abstractmethod
    async def load(self, path: str) -> Optional[dict]:
        """Carrega um payload de auditoria pelo caminho retornado em save()."""
        ...


class LocalFileStorage(AuditStorage):
    """
    Storage local em arquivos JSON — usado em desenvolvimento e testes.
    Estrutura: {base_dir}/{path}
    """

    def __init__(self, base_dir: str = "./audit_logs"):
        self.base_dir = base_dir

    async def save(self, path: str, data: dict) -> str:
        full_path = os.path.join(self.base_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, default=str)
            logger.debug("Audit log salvo em %s", full_path)
            return full_path
        except Exception as exc:
            logger.error("Falha ao salvar audit log em %s: %s", full_path, exc)
            return full_path  # retorna path mesmo em erro — não bloquear execução

    async def load(self, path: str) -> Optional[dict]:
        full_path = path if os.path.isabs(path) else os.path.join(self.base_dir, path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Audit log não encontrado: %s", full_path)
            return None
        except Exception as exc:
            logger.error("Falha ao carregar audit log %s: %s", full_path, exc)
            return None

    async def apply_lifecycle_policy(self) -> bool:
        """
        LocalFileStorage não tem lifecycle policy S3.
        Retorna False com log informativo.
        """
        logger.info(
            "[AuditStorage] LocalFileStorage não suporta lifecycle policy S3. "
            "Configure AUDIT_STORAGE_TYPE=s3 para habilitar retenção automática."
        )
        return False


class S3Storage(AuditStorage):
    """
    Storage em AWS S3 — usado em staging e produção.
    Estrutura: s3://{bucket}/{prefix}/{path}

    Append-only por convenção: nunca sobrescrever execuções existentes.
    Lifecycle policy recomendada: hot 90 dias → Glacier após.
    """

    def __init__(self, bucket: str, prefix: str = "audit", region: str = "us-east-1"):
        self.bucket = bucket
        self.prefix = prefix
        self.region = region
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                from lia_config.config import settings
                self._client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=getattr(settings, "S3_ACCESS_KEY", None),
                    aws_secret_access_key=getattr(settings, "S3_SECRET_KEY", None),
                )
            except ImportError:
                logger.error("boto3 não instalado. Adicionar 'boto3' ao requirements.txt para usar S3Storage.")
                raise
        return self._client

    async def save(self, path: str, data: dict) -> str:
        s3_key = f"{self.prefix}/{path}"
        s3_uri = f"s3://{self.bucket}/{s3_key}"
        try:
            import asyncio
            payload = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
            client = self._get_client()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=payload,
                    ContentType="application/json",
                    ServerSideEncryption="AES256",
                )
            )
            logger.debug("Audit log salvo em %s", s3_uri)
            return s3_uri
        except Exception as exc:
            logger.error("Falha ao salvar audit log no S3 (%s): %s", s3_uri, exc)
            return s3_uri

    async def load(self, path: str) -> Optional[dict]:
        s3_key = path.replace(f"s3://{self.bucket}/", "") if path.startswith("s3://") else f"{self.prefix}/{path}"
        try:
            import asyncio
            client = self._get_client()
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.get_object(Bucket=self.bucket, Key=s3_key)
            )
            body = response["Body"].read().decode("utf-8")
            return json.loads(body)
        except Exception as exc:
            logger.error("Falha ao carregar audit log do S3 (%s): %s", path, exc)
            return None

    def get_lifecycle_config(self) -> dict:
        """
        Retorna configuração de lifecycle policy S3 para o bucket de auditoria.

        Política:
        - 0-90 dias: S3 Standard (hot, acesso rápido)
        - 90-365 dias: Glacier Instant Retrieval (acesso em millisegundos, 68% mais barato)
        - 365-2555 dias: Glacier Deep Archive (acesso 12h, 95% mais barato)
        - Após 2555 dias (7 anos): Deletar

        SOX/ISO 27001: 7 anos de retenção mínima para registros de auditoria.
        """
        return {
            "Rules": [
                {
                    "ID": "audit-log-lifecycle",
                    "Status": "Enabled",
                    "Prefix": self.prefix,
                    "Transitions": [
                        {
                            "Days": AUDIT_RETENTION_DAYS_HOT,
                            "StorageClass": "GLACIER_IR",  # Glacier Instant Retrieval
                        },
                        {
                            "Days": AUDIT_RETENTION_DAYS_COLD,
                            "StorageClass": "DEEP_ARCHIVE",
                        },
                    ],
                    "Expiration": {
                        "Days": AUDIT_RETENTION_DAYS_DELETE,
                    },
                }
            ]
        }

    async def apply_lifecycle_policy(self) -> bool:
        """
        Aplica a política de lifecycle no bucket S3.
        Idempotente — pode ser chamado múltiplas vezes sem problema.
        Returns True se aplicado com sucesso.
        """
        try:
            import asyncio
            from lia_config.config import settings
            client = self._get_client()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: client.put_bucket_lifecycle_configuration(
                    Bucket=self.bucket,
                    LifecycleConfiguration=self.get_lifecycle_config(),
                )
            )
            logger.info(f"[AuditStorage] S3 lifecycle policy applied to bucket={self.bucket}")
            return True
        except Exception as exc:
            logger.warning(f"[AuditStorage] Failed to apply lifecycle policy: {exc}")
            return False


def build_storage_path(domain: str, company_id: str, execution_id: str) -> str:
    """
    Gera o caminho padronizado para armazenar um audit log.
    Exemplo: vagas/2026/03/07/company-abc/exec-uuid.json
    """
    now = datetime.now(timezone.utc)
    date_path = now.strftime("%Y/%m/%d")
    safe_company = company_id.replace("/", "-")[:36]
    return f"{domain}/{date_path}/{safe_company}/{execution_id}.json"


_storage_instance: Optional[AuditStorage] = None


def get_audit_storage() -> AuditStorage:
    """Factory: retorna instância configurada de AuditStorage (singleton)."""
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    from lia_config.config import settings
    storage_type = getattr(settings, "AUDIT_STORAGE_TYPE", "file")

    if storage_type == "s3":
        bucket = getattr(settings, "AUDIT_STORAGE_BUCKET", "")
        prefix = getattr(settings, "AUDIT_STORAGE_PREFIX", "audit")
        region = getattr(settings, "S3_REGION", "us-east-1")
        if not bucket:
            logger.warning("AUDIT_STORAGE_TYPE=s3 mas AUDIT_STORAGE_BUCKET não configurado. Usando LocalFileStorage.")
            _storage_instance = LocalFileStorage()
        else:
            _storage_instance = S3Storage(bucket=bucket, prefix=prefix, region=region)
    else:
        base_dir = getattr(settings, "AUDIT_LOCAL_DIR", "./audit_logs")
        _storage_instance = LocalFileStorage(base_dir=base_dir)

    return _storage_instance
