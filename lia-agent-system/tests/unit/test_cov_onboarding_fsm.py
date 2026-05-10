"""Coverage tests for app/services/onboarding_orchestrator.py — FSM and pure logic."""
import pytest
from datetime import datetime
from app.services.onboarding_orchestrator import (
    OnboardingPhase,
    TRANSITIONS,
    OnboardingSession,
)


class TestOnboardingPhase:
    def test_all_phases_exist(self):
        phases = [
            OnboardingPhase.PENDING,
            OnboardingPhase.WELCOME,
            OnboardingPhase.WHATSAPP_INTRO,
            OnboardingPhase.WHATSAPP_LEARN,
            OnboardingPhase.AWAITING_LOGIN,
            OnboardingPhase.FIRST_LOGIN,
            OnboardingPhase.PLATFORM_TOUR,
            OnboardingPhase.ACTION_CHOICE,
            OnboardingPhase.JOB_CREATION,
            OnboardingPhase.COMPLETE,
        ]
        assert len(phases) == 10

    def test_phase_values(self):
        assert OnboardingPhase.PENDING.value == "pending"
        assert OnboardingPhase.COMPLETE.value == "complete"
        assert OnboardingPhase.WELCOME.value == "welcome"
        assert OnboardingPhase.FIRST_LOGIN.value == "first_login"
        assert OnboardingPhase.PLATFORM_TOUR.value == "platform_tour"

    def test_is_enum(self):
        from enum import Enum
        assert isinstance(OnboardingPhase.PENDING, Enum)


class TestTransitions:
    def test_all_phases_in_transitions(self):
        for phase in OnboardingPhase:
            assert phase in TRANSITIONS, f"Phase {phase} not in TRANSITIONS"

    def test_pending_can_go_to_welcome(self):
        assert OnboardingPhase.WELCOME in TRANSITIONS[OnboardingPhase.PENDING]

    def test_welcome_can_skip_whatsapp(self):
        assert OnboardingPhase.AWAITING_LOGIN in TRANSITIONS[OnboardingPhase.WELCOME]

    def test_complete_has_no_transitions(self):
        assert TRANSITIONS[OnboardingPhase.COMPLETE] == []

    def test_action_choice_branches(self):
        targets = TRANSITIONS[OnboardingPhase.ACTION_CHOICE]
        assert OnboardingPhase.JOB_CREATION in targets
        assert OnboardingPhase.COMPLETE in targets

    def test_linear_path(self):
        """Verify the main happy path exists."""
        assert OnboardingPhase.FIRST_LOGIN in TRANSITIONS[OnboardingPhase.AWAITING_LOGIN]
        assert OnboardingPhase.PLATFORM_TOUR in TRANSITIONS[OnboardingPhase.FIRST_LOGIN]
        assert OnboardingPhase.ACTION_CHOICE in TRANSITIONS[OnboardingPhase.PLATFORM_TOUR]
        assert OnboardingPhase.COMPLETE in TRANSITIONS[OnboardingPhase.JOB_CREATION]


class TestOnboardingSession:
    def _make_session(self, phase=OnboardingPhase.PENDING, **kwargs):
        defaults = dict(
            session_id="sess-001",
            user_id=1,
            account_id=100,
            user_name="Ana Silva",
            user_email="ana@example.com",
        )
        defaults.update(kwargs)
        return OnboardingSession(phase=phase, **defaults)

    def test_basic_creation(self):
        s = self._make_session()
        assert s.session_id == "sess-001"
        assert s.user_id == 1
        assert s.account_id == 100
        assert s.user_name == "Ana Silva"
        assert s.user_email == "ana@example.com"
        assert s.phase == OnboardingPhase.PENDING

    def test_default_channel(self):
        s = self._make_session()
        assert s.channel == "web"

    def test_default_flags(self):
        s = self._make_session()
        assert s.onboarding_lia_enabled is True
        assert s.is_complete is False
        assert s.whatsapp_messages == []
        assert s.tour_steps_completed == []

    def test_is_complete_false(self):
        for phase in OnboardingPhase:
            if phase != OnboardingPhase.COMPLETE:
                s = self._make_session(phase=phase)
                assert s.is_complete is False, f"Phase {phase} should not be complete"

    def test_is_complete_true(self):
        s = self._make_session(phase=OnboardingPhase.COMPLETE)
        assert s.is_complete is True

    def test_progress_pending(self):
        s = self._make_session(phase=OnboardingPhase.PENDING)
        assert s.progress == pytest.approx(0.0)

    def test_progress_complete(self):
        s = self._make_session(phase=OnboardingPhase.COMPLETE)
        assert s.progress == pytest.approx(1.0)

    def test_progress_welcome(self):
        s = self._make_session(phase=OnboardingPhase.WELCOME)
        assert s.progress == pytest.approx(0.05)

    def test_progress_platform_tour(self):
        s = self._make_session(phase=OnboardingPhase.PLATFORM_TOUR)
        assert s.progress == pytest.approx(0.60)

    def test_progress_job_creation(self):
        s = self._make_session(phase=OnboardingPhase.JOB_CREATION)
        assert s.progress == pytest.approx(0.90)

    def test_progress_action_choice(self):
        s = self._make_session(phase=OnboardingPhase.ACTION_CHOICE)
        assert s.progress == pytest.approx(0.80)

    def test_progress_increases_monotonically(self):
        order = [
            OnboardingPhase.PENDING,
            OnboardingPhase.WELCOME,
            OnboardingPhase.WHATSAPP_INTRO,
            OnboardingPhase.WHATSAPP_LEARN,
            OnboardingPhase.AWAITING_LOGIN,
            OnboardingPhase.FIRST_LOGIN,
            OnboardingPhase.PLATFORM_TOUR,
            OnboardingPhase.ACTION_CHOICE,
            OnboardingPhase.JOB_CREATION,
            OnboardingPhase.COMPLETE,
        ]
        progresses = [self._make_session(phase=p).progress for p in order]
        for i in range(len(progresses) - 1):
            assert progresses[i] <= progresses[i + 1]

    def test_to_dict(self):
        s = self._make_session(phase=OnboardingPhase.FIRST_LOGIN)
        d = s.to_dict()
        assert d["session_id"] == "sess-001"
        assert d["user_id"] == 1
        assert d["account_id"] == 100
        assert d["user_name"] == "Ana Silva"
        assert d["phase"] == "first_login"
        assert d["channel"] == "web"
        assert d["is_complete"] is False
        assert d["progress"] == pytest.approx(0.35)
        assert d["onboarding_data"] == {}
        assert d["tour_steps_completed"] == []

    def test_to_dict_complete(self):
        s = self._make_session(phase=OnboardingPhase.COMPLETE)
        d = s.to_dict()
        assert d["phase"] == "complete"
        assert d["is_complete"] is True
        assert d["progress"] == pytest.approx(1.0)

    def test_from_invite_event(self):
        event = {
            "payload": {
                "user_id": 42,
                "account_id": 200,
                "name": "Carlos Santos",
                "email": "carlos@company.com",
                "phone": "+5511999999999",
                "magic_link_url": "https://app.example.com/onboard?token=abc",
                "onboarding_lia_enabled": True,
                "invited_by": "admin@company.com",
            }
        }
        s = OnboardingSession.from_invite_event(event)
        assert s.user_id == 42
        assert s.account_id == 200
        assert s.user_name == "Carlos Santos"
        assert s.user_email == "carlos@company.com"
        assert s.user_phone == "+5511999999999"
        assert s.magic_link_url == "https://app.example.com/onboard?token=abc"
        assert s.onboarding_lia_enabled is True
        assert s.invited_by == "admin@company.com"
        assert s.phase == OnboardingPhase.PENDING
        assert s.session_id  # auto-generated UUID

    def test_from_invite_event_flat_payload(self):
        """Also supports flat event (payload at top level)."""
        event = {
            "user_id": 10,
            "account_id": 50,
            "name": "Maria",
            "email": "maria@test.com",
        }
        s = OnboardingSession.from_invite_event(event)
        assert s.user_id == 10
        assert s.user_name == "Maria"

    def test_from_invite_event_optional_fields_missing(self):
        event = {
            "payload": {
                "user_id": 1,
                "account_id": 1,
            }
        }
        s = OnboardingSession.from_invite_event(event)
        assert s.user_name == ""
        assert s.user_email == ""
        assert s.user_phone is None
        assert s.magic_link_url is None
        assert s.onboarding_lia_enabled is True

    def test_onboarding_data_mutable(self):
        s = self._make_session()
        s.onboarding_data["company_size"] = "50-200"
        assert s.onboarding_data["company_size"] == "50-200"

    def test_tour_steps_mutable(self):
        s = self._make_session()
        s.tour_steps_completed.append("step_1")
        s.tour_steps_completed.append("step_2")
        assert len(s.tour_steps_completed) == 2

    def test_whatsapp_messages_mutable(self):
        s = self._make_session()
        s.whatsapp_messages.append({"role": "user", "content": "Hello"})
        assert len(s.whatsapp_messages) == 1

    def test_session_id_uniqueness(self):
        """from_invite_event should generate unique session IDs."""
        event = {"payload": {"user_id": 1, "account_id": 1}}
        s1 = OnboardingSession.from_invite_event(event)
        s2 = OnboardingSession.from_invite_event(event)
        assert s1.session_id != s2.session_id
