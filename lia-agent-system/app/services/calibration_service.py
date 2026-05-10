"""Shim: calibration_service — re-exports CalibrationService from canonical location."""
from app.domains.analytics.services.calibration_service import CalibrationService  # noqa: F401

__all__ = ["CalibrationService"]
