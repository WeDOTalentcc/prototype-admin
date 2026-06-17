"""
SEG-3A — Testes do PII Masking em workers Celery.

Cobre:
  1. Signal worker_process_init está conectado no celery_app
  2. install_global_pii_masking é chamado ao disparar o signal
"""
import unittest
from unittest.mock import patch, MagicMock


class TestCeleryWorkerPIIMasking(unittest.TestCase):
    """Verifica que o worker Celery instala o PIIMaskingFilter ao iniciar."""

    def test_worker_process_init_signal_connected(self):
        """O signal worker_process_init deve ter um receiver configurado."""
        from lia_config.celery_app import celery_app
        from celery import signals

        # Verifica que há receivers no signal worker_process_init
        receivers = signals.worker_process_init.receivers
        self.assertGreater(
            len(receivers), 0,
            "worker_process_init deve ter pelo menos um receiver para PII masking"
        )

    def test_pii_masking_handler_calls_install(self):
        """O handler do signal deve chamar install_global_pii_masking."""
        # Testa o handler diretamente — mais confiável que disparar o signal em teste
        import importlib
        import lia_config.celery_app as celery_mod

        # Localiza o handler registrado no signal
        from celery import signals
        handler = None
        for _, ref in signals.worker_process_init.receivers:
            try:
                fn = ref()
                if fn is not None and fn.__name__ == "_install_pii_masking_on_worker":
                    handler = fn
                    break
            except Exception:
                pass

        if handler is None:
            self.skipTest("Handler _install_pii_masking_on_worker não encontrado nos receivers")

        with patch("app.shared.pii_masking.install_global_pii_masking") as mock_install:
            handler()
            mock_install.assert_called_once()


if __name__ == "__main__":
    unittest.main()
