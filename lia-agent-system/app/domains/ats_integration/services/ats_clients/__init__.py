"""ATS API Client Abstractions — Z6-01: shim para app.services.ats_clients (source of truth).

Fonte canônica: app/services/ats_clients/
Este pacote re-exporta de lá para evitar duplicação de código.
"""
# Z6-01: re-export do path canônico em app.services.ats_clients
from app.services.ats_clients.base import ATSClient, ATSClientConfig, ATSCandidate, ATSJob
from app.services.ats_clients.gupy import GupyClient
from app.services.ats_clients.pandape import PandapeClient
from app.services.ats_clients.stackone import StackOneClient
from app.services.ats_clients.merge import MergeClient

__all__ = [
    "ATSClient",
    "ATSClientConfig",
    "ATSCandidate",
    "ATSJob",
    "GupyClient",
    "PandapeClient",
    "StackOneClient",
    "MergeClient",
]
