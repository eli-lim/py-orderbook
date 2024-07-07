import re

from sortedcontainers import SortedDict

from src.server.orders.matcher import Matcher, OrderBookOrder, OrderBook, Execution
from src.server.orders.model import Order, Side, OrderType


def test_matcher_bids():
    matcher = Matcher(
        orderbook("""
          ASK 11.5 : 1[200]
          ASK 11.0 : 2[100]
          ASK 10.5 : 3[50]
          BID 10.0 : 3[50] 
          BID 9.80 : 2[100]
          BID 9.70 : 1[200]
        """)
    )

    result = matcher.add(
        Order(
            id="1",
            client_id=4,
            security_id=1,
            type=OrderType.limit,
            side=Side.BUY,
            quantity=120,
            price=11.0,
        )
    )

    assert result.executions == [
        Execution(maker_id=3, taker_id=4, price=11.0, quantity=50),
        Execution(maker_id=2, taker_id=4, price=11.0, quantity=70),
    ]
    assert result.order_book == orderbook("""
        ASK 11.5 : 1[200]
        ASK 11.0 :  2[30]
        BID 10.0 :  3[50] 
        BID 9.80 : 2[100]
        BID 9.70 : 1[200]
    """)

    result = matcher.add(
        Order(
            id="2",
            client_id=5,
            security_id=1,
            type=OrderType.limit,
            side=Side.BUY,
            quantity=120,
            price=11.0,
        )
    )

    assert result.executions == [
        Execution(maker_id=2, taker_id=5, price=11.0, quantity=30),
    ]
    assert result.order_book == orderbook("""
        ASK 11.5 : 1[200]
        BID 11.0 :  5[90]
        BID 10.0 :  3[50] 
        BID 9.80 : 2[100]
        BID 9.70 : 1[200]
    """)


def test_matcher_asks():
    matcher = Matcher(
        orderbook("""
            ASK 11.5 : 1[200]
            BID 11.0 :  5[90] 
            BID 10.0 :  3[50] 
            BID 9.80 : 2[100]
            BID 9.70 : 1[200]
        """)
    )

    result = matcher.add(
        Order(
            id="1",
            client_id=4,
            security_id=1,
            type=OrderType.limit,
            side=Side.SELL,
            quantity=120,
            price=10.5,  # better than the top of the book
        )
    )

    assert result.executions == [
        Execution(maker_id=5, taker_id=4, price=10.5, quantity=90),
    ]
    assert result.order_book == orderbook("""
        ASK 11.5 : 1[200]
        ASK 10.5 :  4[30]
        BID 10.0 :  3[50] 
        BID 9.80 : 2[100]
        BID 9.70 : 1[200]
    """)


def test_large_orders():
    matcher = Matcher(
        orderbook("""
            ASK 11.5 : 1[200]
            ASK 11.0 : 2[100]
            ASK 10.5 : 3[50]
            BID 10.0 : 3[50] 
            BID 9.80 : 2[100]
            BID 9.70 : 1[200]
        """)
    )

    result = matcher.add(
        Order(
            id="1",
            client_id=1337,
            security_id=1,
            type=OrderType.limit,
            side=Side.BUY,
            # a ridiculous buy that exhausts the book
            quantity=1000,
            price=100,
        )
    )

    assert result.executions == [
        Execution(maker_id=3, taker_id=1337, price=100, quantity=50),
        Execution(maker_id=2, taker_id=1337, price=100, quantity=100),
        Execution(maker_id=1, taker_id=1337, price=100, quantity=200),
    ]
    assert result.order_book == orderbook("""
        BID 100  : 1337[650]
        BID 10.0 : 3[50]  
        BID 9.80 : 2[100]
        BID 9.70 : 1[200]
    """)


def test_price_time_priority():
    """
    Test that price-time priority is respected.
    """

    matcher = Matcher(
        orderbook("""
            ASK 10.5 : 3[50] 2[100] 3[20]
        """)
    )

    result = matcher.add(
        Order(
            id="1",
            client_id=4,
            security_id=1,
            type=OrderType.limit,
            side=Side.BUY,
            quantity=70,
            price=10.6,
        )
    )

    assert result.executions == [
        Execution(maker_id=3, taker_id=4, price=10.6, quantity=50),
        Execution(maker_id=2, taker_id=4, price=10.6, quantity=20),
    ]
    assert result.order_book == orderbook("""
       ASK 10.5 : 2[80] 3[20]
    """)

    result = matcher.add(
        Order(
            id="2",
            client_id=5,
            security_id=1,
            type=OrderType.limit,
            side=Side.SELL,
            quantity=50,
            price=10.5,
        )
    )
    assert result.executions == []
    assert result.order_book == orderbook("""
       ASK 10.5 : 2[80] 3[20] 5[50]
    """)

    result = matcher.add(
        Order(
            id="3",
            client_id=6,
            security_id=1,
            type=OrderType.limit,
            side=Side.BUY,
            quantity=250,
            price=10.5,
        )
    )
    assert result.executions == [
        Execution(maker_id=2, taker_id=6, price=10.5, quantity=80),
        Execution(maker_id=3, taker_id=6, price=10.5, quantity=20),
        Execution(maker_id=5, taker_id=6, price=10.5, quantity=50),
    ]
    assert result.order_book == orderbook("""
        BID 10.5 : 6[100]
    """)


def orderbook(book: str) -> OrderBook:
    """
    This is a helper function to enhance test readability.
    Parses a string representation of an order book into an OrderBook object.
    """

    order_book = OrderBook(security_id=1, asks=SortedDict(), bids=SortedDict())

    for line in book.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Example: `ASK 10.5 : 3[50] 2[100] 3[20]  -- executions must respect this order`
        pattern = r"^(ASK|BID)\s+(\d+\.?\d*)\s+:\s+(.*)"

        side, price, makers = re.match(pattern, line).groups()
        price = float(price)

        for maker in makers.split():
            pattern = r"(\d+)\[(\d+)\]"
            match = re.match(pattern, maker)
            if not match:
                continue

            maker, quantity = match.groups()
            maker = int(maker)
            quantity = int(quantity)

            if side == "ASK":
                if price not in order_book.asks:
                    order_book.asks[price] = []

                order_book.asks[price].append(
                    OrderBookOrder(maker_id=maker, quantity=quantity, price=price)
                )

            elif side == "BID":
                if price not in order_book.bids:
                    order_book.bids[price] = []

                order_book.bids[price].append(
                    OrderBookOrder(maker_id=maker, quantity=quantity, price=price)
                )

    return order_book
