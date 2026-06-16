"""
Response Filter - Tone consistency filter for LIA responses.

This module provides:
- Informal language detection and replacement
- Formal greeting enforcement
- Professional tone validation
- Emoji normalization
"""
import logging
import re
from re import Pattern

logger = logging.getLogger(__name__)

INFORMAL_TERMS: dict[str, str] = {
    r'\bvc\b': 'você',
    r'\bpra\b': 'para',
    r'\btá\b': 'está',
    r'\bta\b': 'está',
    r'\btô\b': 'estou',
    r'\bto\b': 'estou',
    r'\bblz\b': 'ok',
    r'\btmj\b': '',
    r'\bflw\b': '',
    r'\bvlw\b': 'obrigado',
    r'\bqd\b': 'quando',
    r'\bqdo\b': 'quando',
    r'\btb\b': 'também',
    r'\btbm\b': 'também',
    r'\bpq\b': 'porque',
    r'\bq\b': 'que',
    r'\bcmg\b': 'comigo',
    r'\bctg\b': 'contigo',
    r'\bvdd\b': 'verdade',
    r'\bmsm\b': 'mesmo',
    r'\bnd\b': 'nada',
    r'\bngm\b': 'ninguém',
    r'\bdps\b': 'depois',
    r'\bhj\b': 'hoje',
    r'\bagr\b': 'agora',
    r'\bobs\b': 'observação',
    r'\bmt\b': 'muito',
    r'\bmto\b': 'muito',
    r'\bbjs\b': '',
    r'\babs\b': '',
}

LAUGHTER_PATTERNS: list[str] = [
    r'\brs+\b',
    r'\brsrs+\b',
    r'\bkk+\b',
    r'\bhaha+\b',
    r'\bhehe+\b',
    r'\bhihi+\b',
    r'\blol\b',
]

INFORMAL_GREETINGS: dict[str, str] = {
    r'^oi\b': 'Olá',
    r'^e aí\b': 'Olá',
    r'^eai\b': 'Olá',
    r'^fala\b': 'Olá',
    r'^salve\b': 'Olá',
    r'^opa\b': 'Olá',
    r'^eae\b': 'Olá',
    r'^iae\b': 'Olá',
}

FORBIDDEN_PATTERNS: list[str] = [
    r'\bvc\b',
    r'\bpra\b',
    r'\btá\b',
    r'\bblz\b',
    r'\btmj\b',
    r'\bflw\b',
    r'\bvlw\b',
    r'\brs+\b',
    r'\bkk+\b',
    r'\bhaha+\b',
    r'\bcara\b',
    r'\bmano\b',
    r'\bvei\b',
    r'\bbro\b',
    r'\bshow\b',
    r'\btop\b',
    r'\bfirmeza\b',
    r'\bbeleza\b',
    r'\bsuave\b',
    r'\btranquilo\b',
    r'\btranqui\b',
]

PROFESSIONAL_INDICATORS: list[str] = [
    'olá',
    'prezado',
    'prezada',
    'senhor',
    'senhora',
    'obrigado',
    'obrigada',
    'agradeço',
    'atenciosamente',
    'cordialmente',
    'por favor',
    'gentileza',
    'disponibilidade',
    'fico à disposição',
    'estou à disposição',
]

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "]+",
    flags=re.UNICODE
)


class ToneFilter:
    """Filter for ensuring consistent professional tone in LIA responses."""
    
    def __init__(self, max_emojis: int = 1):
        """
        Initialize the ToneFilter.
        
        Args:
            max_emojis: Maximum number of emojis allowed (default: 1)
        """
        self.max_emojis = max_emojis
        self._compiled_informal: list[tuple[Pattern, str]] = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in INFORMAL_TERMS.items()
        ]
        self._compiled_laughter: list[Pattern] = [
            re.compile(pattern, re.IGNORECASE) for pattern in LAUGHTER_PATTERNS
        ]
        self._compiled_greetings: list[tuple[Pattern, str]] = [
            (re.compile(pattern, re.IGNORECASE | re.MULTILINE), replacement)
            for pattern, replacement in INFORMAL_GREETINGS.items()
        ]
        self._compiled_forbidden: list[Pattern] = [
            re.compile(pattern, re.IGNORECASE) for pattern in FORBIDDEN_PATTERNS
        ]
    
    def filter_informal_language(self, text: str) -> str:
        """
        Remove or replace informal language with formal equivalents.
        
        Args:
            text: Input text that may contain informal language
            
        Returns:
            Text with informal language replaced
        """
        if not text:
            return text
        
        result = text
        
        for pattern, replacement in self._compiled_informal:
            result = pattern.sub(replacement, result)
        
        for pattern in self._compiled_laughter:
            result = pattern.sub('', result)
        
        result = self._normalize_emojis(result)
        result = re.sub(r'[^\S\n]+', ' ', result)
        result = re.sub(r' +([.,!?;:])', r'\1', result)
        
        return result.strip()
    
    def _normalize_emojis(self, text: str) -> str:
        """
        Normalize emojis to keep only the maximum allowed.
        
        Args:
            text: Input text that may contain emojis
            
        Returns:
            Text with excess emojis removed
        """
        if not text:
            return text
        
        emoji_positions = []
        for match in EMOJI_PATTERN.finditer(text):
            for char in match.group(0):
                emoji_positions.append((match.start(), char))
        
        if len(emoji_positions) <= self.max_emojis:
            return text
        
        chars_to_remove = set()
        for i, (pos, char) in enumerate(emoji_positions):
            if i >= self.max_emojis:
                chars_to_remove.add(i)
        
        result = []
        for match in EMOJI_PATTERN.finditer(text):
            pass
        
        kept_count = 0
        result = []
        i = 0
        while i < len(text):
            match = EMOJI_PATTERN.match(text, i)
            if match:
                emoji_chars = match.group(0)
                for char in emoji_chars:
                    if kept_count < self.max_emojis:
                        result.append(char)
                        kept_count += 1
                i = match.end()
            else:
                result.append(text[i])
                i += 1
        
        return ''.join(result)
    
    def ensure_formal_greeting(self, text: str) -> str:
        """
        Ensure the text starts with a formal greeting.
        
        Args:
            text: Input text that may start with informal greeting
            
        Returns:
            Text with formal greeting
        """
        if not text:
            return text
        
        result = text.strip()
        
        for pattern, replacement in self._compiled_greetings:
            result = pattern.sub(replacement, result, count=1)
        
        return result
    
    def validate_professional_tone(self, text: str) -> tuple[bool, list[str]]:
        """
        Validate if the text maintains a professional tone.
        
        Args:
            text: Input text to validate
            
        Returns:
            Tuple of (is_professional, list_of_issues)
        """
        if not text:
            return True, []
        
        issues: list[str] = []
        text_lower = text.lower()
        
        for pattern in self._compiled_forbidden:
            matches = pattern.findall(text)
            if matches:
                for match in matches:
                    issues.append(f"Termo informal encontrado: '{match}'")
        
        emojis_found = EMOJI_PATTERN.findall(text)
        total_emoji_count = sum(len(e) for e in emojis_found)
        if total_emoji_count > self.max_emojis:
            issues.append(
                f"Excesso de emojis: {total_emoji_count} encontrados, "
                f"máximo permitido: {self.max_emojis}"
            )
        
        has_professional_indicator = any(
            indicator in text_lower for indicator in PROFESSIONAL_INDICATORS
        )
        
        if not has_professional_indicator and len(text) > 100:
            issues.append(
                "Considere adicionar indicadores de tom profissional "
                "(ex: 'Olá', 'Por favor', 'Atenciosamente')"
            )
        
        is_professional = len(issues) == 0
        return is_professional, issues
    
    def apply_all_filters(self, text: str) -> str:
        """
        Apply all tone filters in sequence.
        
        Args:
            text: Input text to filter
            
        Returns:
            Filtered text with consistent professional tone
        """
        if not text:
            return text
        
        result = self.ensure_formal_greeting(text)
        result = self.filter_informal_language(result)
        
        return result
    
    def get_filter_stats(self, original: str, filtered: str) -> dict[str, any]:
        """
        Get statistics about the filtering applied.
        
        Args:
            original: Original text
            filtered: Filtered text
            
        Returns:
            Dictionary with filtering statistics
        """
        original_issues = self.validate_professional_tone(original)
        filtered_issues = self.validate_professional_tone(filtered)
        
        return {
            "original_length": len(original),
            "filtered_length": len(filtered),
            "characters_changed": abs(len(original) - len(filtered)),
            "original_issues_count": len(original_issues[1]),
            "filtered_issues_count": len(filtered_issues[1]),
            "issues_fixed": len(original_issues[1]) - len(filtered_issues[1]),
            "is_now_professional": filtered_issues[0],
        }


tone_filter = ToneFilter()


def filter_response(text: str) -> str:
    """
    Convenience function to filter a response using the default ToneFilter.
    
    Args:
        text: Input text to filter
        
    Returns:
        Filtered text
    """
    return tone_filter.apply_all_filters(text)


def validate_response(text: str) -> tuple[bool, list[str]]:
    """
    Convenience function to validate a response using the default ToneFilter.
    
    Args:
        text: Input text to validate
        
    Returns:
        Tuple of (is_professional, list_of_issues)
    """
    return tone_filter.validate_professional_tone(text)
