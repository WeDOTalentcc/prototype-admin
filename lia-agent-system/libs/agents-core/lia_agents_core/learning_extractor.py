"""
LearningExtractor - Extracts learnings from completed ReAct loop executions.

Analyzes a completed ReActState and extracts patterns, preferences, and outcomes
to save as long-term memories for agent improvement.
"""

import logging
from collections import Counter
from typing import Any, Dict, List

from lia_agents_core.tool_adapter import ReActState

logger = logging.getLogger(__name__)

SCORE_KEYS = {"fit_score", "wsi_score", "match_score", "culture_score", "technical_score", "overall_score"}


class LearningExtractor:
    """Extracts structured learnings from a completed ReAct loop execution.

    Analyzes tool calls, actions, and outcomes to produce learning dicts
    that can be persisted as long-term agent memories.
    """

    def extract(
        self,
        state: ReActState,
        domain: str,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract learnings from a completed ReActState.

        Args:
            state: The completed ReActState after a ReAct loop execution.
            domain: The domain the loop operated in (e.g. 'wizard', 'pipeline').
            context: Domain-specific context that was provided to the loop.

        Returns:
            A deduplicated list of learning dicts, each with keys:
            ``type``, ``key``, ``value``, and ``tags``.
        """
        learnings: List[Dict[str, Any]] = []

        try:
            learnings.extend(self._extract_patterns(state, domain))
        except Exception as exc:
            logger.warning("LearningExtractor: pattern extraction failed: %s", exc, exc_info=True)

        try:
            learnings.extend(self._extract_preferences(state, domain, context))
        except Exception as exc:
            logger.warning("LearningExtractor: preference extraction failed: %s", exc, exc_info=True)

        try:
            learnings.extend(self._extract_outcomes(state, domain))
        except Exception as exc:
            logger.warning("LearningExtractor: outcome extraction failed: %s", exc, exc_info=True)

        return self._deduplicate(learnings)

    def _extract_patterns(self, state: ReActState, domain: str) -> List[Dict[str, Any]]:
        """Extract tool-usage patterns from the state.

        Identifies successfully called tools and tools that were called
        multiple times with different arguments.

        Args:
            state: Completed ReActState.
            domain: Current domain identifier.

        Returns:
            List of pattern learning dicts.
        """
        patterns: List[Dict[str, Any]] = []
        tool_call_groups: Dict[str, List[Dict[str, Any]]] = {}

        for call in state.tool_calls_made:
            try:
                tool_name = call.get("tool_name", "")
                result = call.get("result", {})
                success = result.get("success", False) if isinstance(result, dict) else False
                tool_args = call.get("tool_args", {})

                if not tool_name:
                    continue

                tool_call_groups.setdefault(tool_name, []).append(call)

                if success:
                    args_keys = sorted(tool_args.keys()) if isinstance(tool_args, dict) else []
                    patterns.append({
                        "type": "pattern",
                        "key": f"tool_usage_{tool_name}",
                        "value": {
                            "tool": tool_name,
                            "args_pattern": args_keys,
                            "success": True,
                            "domain": domain,
                        },
                        "tags": [domain, tool_name],
                    })
            except Exception as exc:
                logger.debug("LearningExtractor: skipping tool call pattern: %s", exc)

        for tool_name, calls in tool_call_groups.items():
            try:
                if len(calls) <= 1:
                    continue

                unique_arg_sets = set()
                for c in calls:
                    args = c.get("tool_args", {})
                    key = tuple(sorted(args.items())) if isinstance(args, dict) else ()
                    unique_arg_sets.add(key)

                if len(unique_arg_sets) > 1:
                    patterns.append({
                        "type": "pattern",
                        "key": f"repeated_tool_{tool_name}",
                        "value": {
                            "count": len(calls),
                            "indicates": "complex_query",
                        },
                        "tags": [domain, "repeated_tool"],
                    })
            except Exception as exc:
                logger.debug("LearningExtractor: skipping repeated tool pattern: %s", exc)

        return patterns

    def _extract_preferences(
        self,
        state: ReActState,
        domain: str,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract navigation and preference signals from the state.

        Looks for stage transitions in actions_taken and context to capture
        user navigation preferences.

        Args:
            state: Completed ReActState.
            domain: Current domain identifier.
            context: Domain-specific context dict.

        Returns:
            List of preference learning dicts.
        """
        preferences: List[Dict[str, Any]] = []

        for action in state.actions_taken:
            try:
                action_type = action.get("type", "")
                tool_name = action.get("tool", "")

                is_navigation = (
                    "navigate" in tool_name.lower()
                    or "transition" in tool_name.lower()
                    or "stage" in tool_name.lower()
                    or action_type == "guardrail_blocked"
                )

                if not is_navigation:
                    continue

                args = action.get("args", {})
                from_stage = args.get("from_stage", args.get("current_stage", context.get("current_stage", "unknown")))
                to_stage = args.get("to_stage", args.get("target_stage", args.get("stage", "unknown")))

                confirmation_used = action_type == "guardrail_blocked"

                preferences.append({
                    "type": "preference",
                    "key": f"stage_transition_{from_stage}_{to_stage}",
                    "value": {
                        "from_stage": from_stage,
                        "confirmation_used": confirmation_used,
                    },
                    "tags": [domain, "navigation"],
                })
            except Exception as exc:
                logger.debug("LearningExtractor: skipping preference: %s", exc)

        return preferences

    def _extract_outcomes(self, state: ReActState, domain: str) -> List[Dict[str, Any]]:
        """Extract session outcome metrics and scoring results.

        Produces a session-level summary and, if any tool returned score
        data, a separate scoring outcome.

        Args:
            state: Completed ReActState.
            domain: Current domain identifier.

        Returns:
            List of outcome learning dicts.
        """
        outcomes: List[Dict[str, Any]] = []

        try:
            tools_used = len(state.tool_calls_made)
            had_error = bool(state.error)
            estimated_confidence = self._estimate_confidence(state)

            outcomes.append({
                "type": "outcome",
                "key": "session_outcome",
                "value": {
                    "iterations": state.iteration,
                    "tools_used": tools_used,
                    "had_error": had_error,
                    "confidence": estimated_confidence,
                },
                "tags": [domain, "session_metrics"],
            })
        except Exception as exc:
            logger.debug("LearningExtractor: session outcome failed: %s", exc)

        try:
            scores = self._collect_scores(state)
            if scores:
                outcomes.append({
                    "type": "outcome",
                    "key": "scoring_result",
                    "value": scores,
                    "tags": [domain, "scoring"],
                })
        except Exception as exc:
            logger.debug("LearningExtractor: scoring outcome failed: %s", exc)

        return outcomes

    def _estimate_confidence(self, state: ReActState) -> float:
        """Estimate a confidence score for the session.

        Heuristic based on error presence, iteration count, and tool
        success rate.

        Args:
            state: Completed ReActState.

        Returns:
            A float between 0.0 and 1.0.
        """
        try:
            if state.error:
                return 0.2

            if not state.tool_calls_made:
                return 0.5

            successes = sum(
                1 for c in state.tool_calls_made
                if isinstance(c.get("result"), dict) and c["result"].get("success", False)
            )
            success_rate = successes / len(state.tool_calls_made) if state.tool_calls_made else 0.0

            base = 0.4 + (success_rate * 0.5)

            if state.iteration <= 2:
                base += 0.1

            return min(round(base, 2), 1.0)
        except Exception:
            return 0.5

    def _collect_scores(self, state: ReActState) -> Dict[str, Any]:
        """Collect score values from tool call results.

        Scans all tool results for keys matching known score names
        (``fit_score``, ``wsi_score``, etc.).

        Args:
            state: Completed ReActState.

        Returns:
            A dict of score_name -> value, or empty dict if none found.
        """
        scores: Dict[str, Any] = {}

        for call in state.tool_calls_made:
            try:
                result = call.get("result", {})
                if not isinstance(result, dict):
                    continue
                self._extract_scores_recursive(result, scores)
            except Exception:
                continue

        return scores

    def _extract_scores_recursive(self, data: Any, scores: Dict[str, Any], depth: int = 0) -> None:
        """Recursively search a dict for score keys.

        Args:
            data: Data structure to search.
            scores: Accumulator dict to update in place.
            depth: Current recursion depth (capped at 5).
        """
        if depth > 5 or not isinstance(data, dict):
            return

        for key, value in data.items():
            if key in SCORE_KEYS and isinstance(value, (int, float)):
                scores[key] = value
            elif isinstance(value, dict):
                self._extract_scores_recursive(value, scores, depth + 1)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._extract_scores_recursive(item, scores, depth + 1)

    def _deduplicate(self, learnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate learnings by key, keeping the last occurrence.

        Args:
            learnings: List of learning dicts.

        Returns:
            Deduplicated list preserving insertion order of last occurrence.
        """
        seen: Dict[str, int] = {}
        for idx, learning in enumerate(learnings):
            key = learning.get("key", "")
            seen[key] = idx

        return [learnings[idx] for idx in sorted(seen.values())]
