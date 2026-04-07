from app.domains.automation.services.automation_service import AutomationService, automation_service as _auto_singleton


def get_automation_service() -> AutomationService:
    return _auto_singleton
