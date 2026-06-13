"""Policy domain — PolicyEngineService, PolicySetupAgent, FairnessGuard.

Motor canônico de políticas de contratação. Consumido por hiring_policy/,
job_creation/, orchestrator/, fairness_guard e outros.

Este diretório NÃO é um domain registrado no DomainRegistry (sem domain.py).
O domain registrado é hiring_policy/ (domain_id="hiring_policy").
"""
