"""Contract: can_load_more deve ser False quando search_pearch=False."""
import pytest


class FakeSearchResult:
    def __init__(self, pearch_count=0):
        self.pearch_count = pearch_count


class FakeRequest:
    def __init__(self, search_pearch=False, pearch_limit=15):
        self.search_pearch = search_pearch
        self.pearch_limit = pearch_limit


def compute_can_load_more(result, request, fb_can_load_more=False):
    _pearch_was_requested = request.search_pearch and (request.pearch_limit > 0)
    return _pearch_was_requested and (
        (result.pearch_count >= request.pearch_limit) or fb_can_load_more
    )


class TestCanLoadMoreContract:
    def test_false_when_search_pearch_is_false(self):
        result = FakeSearchResult(pearch_count=0)
        request = FakeRequest(search_pearch=False, pearch_limit=0)
        assert compute_can_load_more(result, request) is False

    def test_true_when_pearch_returned_full_page(self):
        result = FakeSearchResult(pearch_count=15)
        request = FakeRequest(search_pearch=True, pearch_limit=15)
        assert compute_can_load_more(result, request) is True

    def test_false_when_pearch_returned_partial_page(self):
        result = FakeSearchResult(pearch_count=7)
        request = FakeRequest(search_pearch=True, pearch_limit=15)
        assert compute_can_load_more(result, request) is False

    def test_true_via_apify_fallback(self):
        result = FakeSearchResult(pearch_count=0)
        request = FakeRequest(search_pearch=True, pearch_limit=15)
        assert compute_can_load_more(result, request, fb_can_load_more=True) is True

    def test_false_when_pearch_limit_zero(self):
        result = FakeSearchResult(pearch_count=0)
        request = FakeRequest(search_pearch=True, pearch_limit=0)
        assert compute_can_load_more(result, request) is False
