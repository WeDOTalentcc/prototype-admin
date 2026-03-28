"""
Template channel constants for multi-channel communication system.
Defines all supported channels for templates across the LIA platform.
"""

CHANNEL_EMAIL = "email"
CHANNEL_WHATSAPP = "whatsapp"
CHANNEL_BELL = "bell"
CHANNEL_TEAMS = "teams"
CHANNEL_CHAT_LIA = "chat_lia"
CHANNEL_REPORT = "report"
CHANNEL_BRIEFING = "briefing"
CHANNEL_PARECER = "parecer"

ALL_CHANNELS = [
    CHANNEL_EMAIL,
    CHANNEL_WHATSAPP,
    CHANNEL_BELL,
    CHANNEL_TEAMS,
    CHANNEL_CHAT_LIA,
    CHANNEL_REPORT,
    CHANNEL_BRIEFING,
    CHANNEL_PARECER,
]

CHANNEL_LABELS = {
    CHANNEL_EMAIL: "E-mail",
    CHANNEL_WHATSAPP: "WhatsApp",
    CHANNEL_BELL: "Notificação (Sino)",
    CHANNEL_TEAMS: "Microsoft Teams",
    CHANNEL_CHAT_LIA: "Chat LIA",
    CHANNEL_REPORT: "Relatórios",
    CHANNEL_BRIEFING: "Briefings LIA",
    CHANNEL_PARECER: "Pareceres LIA",
}

CHANNEL_DESCRIPTIONS = {
    CHANNEL_EMAIL: "Templates para comunicações por e-mail",
    CHANNEL_WHATSAPP: "Templates para mensagens WhatsApp",
    CHANNEL_BELL: "Templates para notificações no sistema (sino)",
    CHANNEL_TEAMS: "Templates para integração Microsoft Teams",
    CHANNEL_CHAT_LIA: "Templates para chat interno da LIA",
    CHANNEL_REPORT: "Templates para relatórios automatizados",
    CHANNEL_BRIEFING: "Templates para briefings diários da LIA",
    CHANNEL_PARECER: "Templates para pareceres de candidatos",
}
