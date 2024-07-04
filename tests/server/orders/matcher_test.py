from src.server.orders.matcher import Matcher

def test_matcher():
    matcher = Matcher()
    print(matcher)
    assert matcher is not None
