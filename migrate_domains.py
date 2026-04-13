"""Migrate 7 domains to use KeywordIntentMatcher."""
import os
import sys

BASE = os.path.expanduser("~/workspace/lia-agent-system")

def migrate_pattern1(domain_id, class_name, default_action):
    """Pattern 1: min(0.95, 0.6 + len(keyword) * 0.02) + length tiebreaker"""
    path = f"{BASE}/app/domains/{domain_id}/domain.py"
    with open(path) as f:
        content = f.read()
    
    import_line = "from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher"
    if import_line in content:
        print(f"  {domain_id}: already migrated, skipping")
        return
    
    # Add import
    content = content.replace(
        "logger = logging.getLogger(__name__)",
        f"{import_line}\n\nlogger = logging.getLogger(__name__)",
        1,
    )
    
    # Add matcher singleton before @register_domain
    matcher_line = f'\n# LIA-I03: Shared KeywordIntentMatcher singleton\n_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="{domain_id}")\n'
    content = content.replace(
        f"\n\n@register_domain\nclass {class_name}",
        f"{matcher_line}\n\n@register_domain\nclass {class_name}",
        1,
    )
    
    # Replace process_intent - find it and replace
    old_block = f"""    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower().strip()
        best_action = "{default_action}"
        best_confidence = 0.3
        best_keyword = ""

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                if confidence > best_confidence or (confidence == best_confidence and len(keyword) > len(best_keyword)):
                    best_action = action_id
                    best_confidence = confidence
                    best_keyword = keyword

        return IntentResult(
            intent_id=f"{domain_id}.{{best_action}}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={{"raw_query": query}},
            reasoning=f"Keyword heuristic matched action '{{best_action}}'",
        )"""
    
    new_block = f"""    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="{default_action}")
            return IntentResult(
                intent_id=f"{domain_id}.{{match.action}}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={{"raw_query": query}},
                reasoning=f"KeywordIntentMatcher matched action '{{match.action}}'",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            query_lower = query.lower().strip()
            best_action = "{default_action}"
            best_confidence = 0.3
            best_keyword = ""
            for keyword, action_id in _KEYWORD_ACTION_MAP.items():
                if keyword in query_lower:
                    confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                    if confidence > best_confidence or (confidence == best_confidence and len(keyword) > len(best_keyword)):
                        best_action = action_id
                        best_confidence = confidence
                        best_keyword = keyword
            return IntentResult(
                intent_id=f"{domain_id}.{{best_action}}",
                action_id=best_action,
                confidence=best_confidence,
                extracted_params={{"raw_query": query}},
                reasoning=f"Keyword heuristic matched action '{{best_action}}'",
            )"""
    
    if old_block in content:
        content = content.replace(old_block, new_block)
        with open(path, "w") as f:
            f.write(content)
        print(f"  {domain_id}: UPDATED (pattern1)")
    else:
        print(f"  {domain_id}: WARNING - could not find process_intent block to replace")
        # Try to write anyway with import + matcher
        with open(path, "w") as f:
            f.write(content)
        print(f"  {domain_id}: import + matcher added, process_intent needs manual check")


def migrate_hiring_policy():
    """Pattern 2: 0.85 if len(keyword) > 4 else 0.7"""
    domain_id = "hiring_policy"
    path = f"{BASE}/app/domains/{domain_id}/domain.py"
    with open(path) as f:
        content = f.read()
    
    import_line = "from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher"
    if import_line in content:
        print(f"  {domain_id}: already migrated, skipping")
        return
    
    content = content.replace(
        "logger = logging.getLogger(__name__)",
        f"{import_line}\n\nlogger = logging.getLogger(__name__)",
        1,
    )
    
    matcher_line = f'\n# LIA-I03: Shared KeywordIntentMatcher singleton\n_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="{domain_id}")\n'
    content = content.replace(
        "\nHIRING_POLICY_ACTIONS = [",
        f"{matcher_line}\nHIRING_POLICY_ACTIONS = [",
        1,
    )
    
    old_block = """    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower()
        best_action = "configure_policy"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = 0.85 if len(keyword) > 4 else 0.7
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"hiring_policy.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )"""
    
    new_block = """    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="configure_policy")
            return IntentResult(
                intent_id=f"hiring_policy.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}'",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            query_lower = query.lower()
            best_action = "configure_policy"
            best_confidence = 0.3
            for keyword, action_id in _KEYWORD_ACTION_MAP.items():
                if keyword in query_lower:
                    confidence = 0.85 if len(keyword) > 4 else 0.7
                    if confidence > best_confidence:
                        best_action = action_id
                        best_confidence = confidence
            return IntentResult(
                intent_id=f"hiring_policy.{best_action}",
                action_id=best_action,
                confidence=best_confidence,
                extracted_params={"raw_query": query},
                reasoning=f"Keyword heuristic matched action '{best_action}'",
            )"""
    
    if old_block in content:
        content = content.replace(old_block, new_block)
        with open(path, "w") as f:
            f.write(content)
        print(f"  {domain_id}: UPDATED (pattern2)")
    else:
        with open(path, "w") as f:
            f.write(content)
        print(f"  {domain_id}: import + matcher added, process_intent needs manual check")


def migrate_pattern3(domain_id, class_name, default_action):
    """Pattern 3: 0.9 if len(kw) > 6 else 0.75"""
    path = f"{BASE}/app/domains/{domain_id}/domain.py"
    with open(path) as f:
        content = f.read()
    
    import_line = "from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher"
    if import_line in content:
        print(f"  {domain_id}: already migrated, skipping")
        return
    
    content = content.replace(
        "logger = logging.getLogger(__name__)",
        f"{import_line}\n\nlogger = logging.getLogger(__name__)",
        1,
    )
    
    matcher_line = f'\n# LIA-I03: Shared KeywordIntentMatcher singleton\n_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="{domain_id}")\n'
    content = content.replace(
        f"\n@register_domain\nclass {class_name}",
        f"{matcher_line}\n@register_domain\nclass {class_name}",
        1,
    )
    
    old_block = f"""    async def process_intent(self, query, context):
        q = query.lower()
        best_action, best_conf = "{default_action}", 0.3
        for kw, action in _KEYWORD_ACTION_MAP.items():
            if kw in q:
                conf = 0.9 if len(kw) > 6 else 0.75
                if conf > best_conf:
                    best_action, best_conf = action, conf
        return IntentResult(intent_id=f"{domain_id}.{{best_action}}", action_id=best_action, confidence=best_conf, extracted_params={{"raw_query": query}}, reasoning=f"Keyword matched '{{best_action}}'")"""
    
    new_block = f"""    async def process_intent(self, query, context):
        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="{default_action}")
            return IntentResult(intent_id=f"{domain_id}.{{match.action}}", action_id=match.action, confidence=match.confidence, extracted_params={{"raw_query": query}}, reasoning=f"KeywordIntentMatcher matched '{{match.action}}'")
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            q = query.lower()
            best_action, best_conf = "{default_action}", 0.3
            for kw, action in _KEYWORD_ACTION_MAP.items():
                if kw in q:
                    conf = 0.9 if len(kw) > 6 else 0.75
                    if conf > best_conf:
                        best_action, best_conf = action, conf
            return IntentResult(intent_id=f"{domain_id}.{{best_action}}", action_id=best_action, confidence=best_conf, extracted_params={{"raw_query": query}}, reasoning=f"Keyword matched '{{best_action}}'")"""
    
    if old_block in content:
        content = content.replace(old_block, new_block)
        with open(path, "w") as f:
            f.write(content)
        print(f"  {domain_id}: UPDATED (pattern3)")
    else:
        with open(path, "w") as f:
            f.write(content)
        print(f"  {domain_id}: import + matcher added, process_intent needs manual check")


def migrate_recruiter_assistant():
    """recruiter_assistant has same Pattern 1 but need to read its process_intent carefully"""
    domain_id = "recruiter_assistant"
    path = f"{BASE}/app/domains/{domain_id}/domain.py"
    with open(path) as f:
        content = f.read()
    
    import_line = "from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher"
    if import_line in content:
        print(f"  {domain_id}: already migrated, skipping")
        return
    
    content = content.replace(
        "logger = logging.getLogger(__name__)",
        f"{import_line}\n\nlogger = logging.getLogger(__name__)",
        1,
    )
    
    matcher_line = f'\n# LIA-I03: Shared KeywordIntentMatcher singleton\n_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="{domain_id}")\n'
    content = content.replace(
        "\n\n@register_domain\nclass RecruiterAssistantDomain",
        f"{matcher_line}\n\n@register_domain\nclass RecruiterAssistantDomain",
        1,
    )
    
    # For recruiter_assistant, we need to find process_intent
    # It starts with "    async def process_intent" and we need to find it + replace it
    # The method has same pattern as others but need to check the exact text
    # Let's search for the old block
    import re
    # Find the process_intent method
    pi_match = re.search(
        r'(    async def process_intent\(self, query: str, context: DomainContext\) -> IntentResult:\n'
        r'        query_lower = query\.lower\(\)\.strip\(\)\n'
        r'        best_action = "quick_question"\n'
        r'        best_confidence = 0\.3\n'
        r'        best_keyword = ""\n'
        r'\n'
        r'        for keyword, action_id in _KEYWORD_ACTION_MAP\.items\(\):\n'
        r'            if keyword in query_lower:\n'
        r'                confidence = min\(0\.95, 0\.6 \+ len\(keyword\) \* 0\.02\)\n'
        r'                if confidence > best_confidence or \(confidence == best_confidence and len\(keyword\) > len\(best_keyword\)\):\n'
        r'                    best_action = action_id\n'
        r'                    best_confidence = confidence\n'
        r'                    best_keyword = keyword\n'
        r'\n'
        r'        return IntentResult\(\n'
        r'            intent_id=f"recruiter_assistant\..*?\n'
        r'            action_id=best_action,\n'
        r'            confidence=best_confidence,\n'
        r'            extracted_params=\{"raw_query": query\},\n'
        r'            reasoning=f"Keyword heuristic matched action \'.*?\n'
        r'        \))',
        content,
        re.DOTALL,
    )
    
    if pi_match:
        old_text = pi_match.group(0)
        new_text = """    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="quick_question")
            return IntentResult(
                intent_id=f"recruiter_assistant.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}'",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            query_lower = query.lower().strip()
            best_action = "quick_question"
            best_confidence = 0.3
            best_keyword = ""
            for keyword, action_id in _KEYWORD_ACTION_MAP.items():
                if keyword in query_lower:
                    confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                    if confidence > best_confidence or (confidence == best_confidence and len(keyword) > len(best_keyword)):
                        best_action = action_id
                        best_confidence = confidence
                        best_keyword = keyword
            return IntentResult(
                intent_id=f"recruiter_assistant.{best_action}",
                action_id=best_action,
                confidence=best_confidence,
                extracted_params={"raw_query": query},
                reasoning=f"Keyword heuristic matched action '{best_action}'",
            )"""
        content = content.replace(old_text, new_text)
        with open(path, "w") as f:
            f.write(content)
        print(f"  {domain_id}: UPDATED (pattern1 via regex)")
    else:
        with open(path, "w") as f:
            f.write(content)
        print(f"  {domain_id}: import + matcher added, process_intent needs manual check")


if __name__ == "__main__":
    print("=== Migrating Pattern 1 domains ===")
    migrate_pattern1("interview_scheduling", "InterviewSchedulingDomain", "list_today_interviews")
    migrate_pattern1("ats_integration", "ATSIntegrationDomain", "check_sync_status")
    migrate_pattern1("automation", "AutomationDomain", "list_tasks")
    
    print("\n=== Migrating recruiter_assistant (Pattern 1 special) ===")
    migrate_recruiter_assistant()
    
    print("\n=== Migrating hiring_policy (Pattern 2) ===")
    migrate_hiring_policy()
    
    print("\n=== Migrating Pattern 3 domains ===")
    migrate_pattern3("digital_twin", "DigitalTwinDomain", "list_twins")
    migrate_pattern3("recruitment_campaign", "RecruitmentCampaignDomain", "list_campaigns")
    
    print("\n=== ALL DONE ===")
