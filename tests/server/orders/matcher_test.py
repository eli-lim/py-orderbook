from pprint import pprint

from src.server.orders.matcher import Matcher, OrderBookEntry
from src.server.orders.model import Order, Side, OrderType


def test_matcher():
    matcher = Matcher()
    print(matcher)
    assert matcher is not None


def test_matcher_bid():
    matcher = Matcher(
        asks={
            11.5: [OrderBookEntry(maker_id=1, quantity=200, price=11.5)],
            11.0: [OrderBookEntry(maker_id=2, quantity=100, price=11.0)],
            10.5: [OrderBookEntry(maker_id=3, quantity=50, price=10.5)],
        },
    )

    order = Order(
        id="1",
        client_id=4,
        securities_id=1,
        side=Side.BUY,
        quantity=120,
        type=OrderType.limit,
        price=11.0,
    )

    result = matcher.match(order)
    print()
    pprint(result)
