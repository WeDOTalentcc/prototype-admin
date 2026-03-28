"""
DateTime utility functions for Microsoft Graph API responses.
"""
import re
import logging
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


# Comprehensive mapping of Microsoft/Windows timezone names to IANA timezone names
# Based on Microsoft's official Windows Time Zone to IANA mapping
# Covers ~95% of common use cases
WINDOWS_TO_IANA_TIMEZONES = {
    # UTC/GMT
    "UTC": "UTC",
    "GMT Standard Time": "Europe/London",
    "Greenwich Standard Time": "Atlantic/Reykjavik",

    # Americas - North
    "Eastern Standard Time": "America/New_York",
    "Central Standard Time": "America/Chicago",
    "Mountain Standard Time": "America/Denver",
    "Pacific Standard Time": "America/Los_Angeles",
    "Alaskan Standard Time": "America/Anchorage",
    "Hawaiian Standard Time": "Pacific/Honolulu",
    "Canada Central Standard Time": "America/Regina",
    "Atlantic Standard Time": "America/Halifax",
    "Newfoundland Standard Time": "America/St_Johns",

    # Americas - South
    "SA Pacific Standard Time": "America/Bogota",
    "SA Western Standard Time": "America/La_Paz",
    "SA Eastern Standard Time": "America/Cayenne",
    "Argentina Standard Time": "America/Buenos_Aires",
    "E. South America Standard Time": "America/Sao_Paulo",
    "Pacific SA Standard Time": "America/Santiago",

    # Europe - West
    "W. Europe Standard Time": "Europe/Berlin",
    "Romance Standard Time": "Europe/Paris",
    "Central Europe Standard Time": "Europe/Budapest",
    "Central European Standard Time": "Europe/Warsaw",

    # Europe - East
    "FLE Standard Time": "Europe/Kiev",
    "GTB Standard Time": "Europe/Bucharest",
    "E. Europe Standard Time": "Europe/Chisinau",
    "Russian Standard Time": "Europe/Moscow",

    # Middle East
    "Egypt Standard Time": "Africa/Cairo",
    "Israel Standard Time": "Asia/Jerusalem",
    "Jordan Standard Time": "Asia/Amman",
    "Arabic Standard Time": "Asia/Baghdad",
    "Arab Standard Time": "Asia/Riyadh",
    "Iran Standard Time": "Asia/Tehran",

    # Asia - South & Southeast
    "India Standard Time": "Asia/Kolkata",
    "Sri Lanka Standard Time": "Asia/Colombo",
    "Myanmar Standard Time": "Asia/Rangoon",
    "SE Asia Standard Time": "Asia/Bangkok",
    "Singapore Standard Time": "Asia/Singapore",
    "China Standard Time": "Asia/Shanghai",

    # Asia - East
    "Tokyo Standard Time": "Asia/Tokyo",
    "Korea Standard Time": "Asia/Seoul",
    "Taipei Standard Time": "Asia/Taipei",

    # Pacific
    "AUS Eastern Standard Time": "Australia/Sydney",
    "AUS Central Standard Time": "Australia/Darwin",
    "Cen. Australia Standard Time": "Australia/Adelaide",
    "W. Australia Standard Time": "Australia/Perth",
    "Tasmania Standard Time": "Australia/Hobart",
    "New Zealand Standard Time": "Pacific/Auckland",
    "Fiji Standard Time": "Pacific/Fiji",

    # Africa
    "South Africa Standard Time": "Africa/Johannesburg",
    "W. Central Africa Standard Time": "Africa/Lagos",
    "E. Africa Standard Time": "Africa/Nairobi",
}


def parse_graph_datetime(graph_datetime_str: str, timezone_hint: Optional[str] = None) -> datetime:
    """
    Parse datetime string from Microsoft Graph API and return timezone-aware UTC datetime.

    Graph returns timestamps with 7 fractional digits (e.g., "2025-11-23T10:00:00.0000000Z")
    but Python's datetime.fromisoformat() only accepts up to 6 digits.

    Additionally, Graph sometimes returns datetime without 'Z' suffix but with a separate
    timeZone field (e.g., "Pacific Standard Time"). This function converts local times
    to UTC.

    Args:
        graph_datetime_str: DateTime string from Graph API
        timezone_hint: Optional timezone from Graph response (Windows timezone name)

    Returns:
        Timezone-aware datetime object in UTC
    """
    has_z_suffix = graph_datetime_str.endswith("Z")
    if has_z_suffix:
        datetime_part = graph_datetime_str[:-1]
    else:
        datetime_part = graph_datetime_str

    # Truncate fractional seconds to 6 digits (Python max)
    pattern = r"\.(\d{7,})"
    match = re.search(pattern, datetime_part)
    if match:
        fractional_part = match.group(1)[:6]
        datetime_part = re.sub(pattern, f".{fractional_part}", datetime_part)

    naive_dt = datetime.fromisoformat(datetime_part)

    if has_z_suffix:
        aware_dt = naive_dt.replace(tzinfo=timezone.utc)
    elif timezone_hint:
        iana_tz_name = WINDOWS_TO_IANA_TIMEZONES.get(timezone_hint)
        if not iana_tz_name:
            logger.warning(
                f"Unknown Windows timezone '{timezone_hint}' - falling back to UTC. "
                f"Please add mapping to WINDOWS_TO_IANA_TIMEZONES."
            )
            aware_dt = naive_dt.replace(tzinfo=timezone.utc)
        else:
            try:
                local_tz = ZoneInfo(iana_tz_name)
                localized_dt = naive_dt.replace(tzinfo=local_tz)
                aware_dt = localized_dt.astimezone(timezone.utc)
            except Exception as e:
                logger.error(f"Timezone conversion failed for {iana_tz_name}: {e}")
                aware_dt = naive_dt.replace(tzinfo=timezone.utc)
    else:
        aware_dt = naive_dt.replace(tzinfo=timezone.utc)

    return aware_dt
