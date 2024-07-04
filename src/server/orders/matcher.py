from collections import OrderedDict
from dataclasses import dataclass
from typing import List

from .model import Order, Side


@dataclass
class OrderBookEntry:
    """
    An entry in the order book.
    """

    maker_id: int
    quantity: int
    price: float
    # TODO: timestamp


@dataclass
class OrderBook:
    """
    Order book for a given securities.

    Example of an order book displayed in a human-readable format:
        ASK 200 @ 11.5
        ASK 100 @ 11.0
        ASK 50  @ 10.5 <--- top of book
        BID 60  @ 10.2 <--- top of book
        BID 100 @ 10.1
        BID 200 @ 10.0

    Internally, this is represented as:
    asks = {
        11.5: [
          (maker=1, quantity=50), <-------- entries are ordered FIFO
          (maker=2, quantity=150),
        ]
        ...,
    }
    bids = {
        10.2: [
          (maker=3, quantity=40),
          (maker=4, quantity=20),
        ]
        ...,
    }
    """

    securities_id: int
    asks: OrderedDict[float, List[OrderBookEntry]]
    bids: OrderedDict[float, List[OrderBookEntry]]


@dataclass
class Execution:
    """
    An execution of a trade between two parties.
    :param maker_id: The ID of the client whose order was sitting in the order book.
    :param taker_id: The ID of the client whose incoming order matched with the maker's order.
    :param price: The price at which the trade was executed.
    """

    maker_id: int
    taker_id: int
    price: float
    quantity: int


@dataclass
class MatchResult:
    orderBook: OrderBook
    executions: List[Execution]


class Matcher:
    """
    Matching Engine responsible for matching buy and sell orders for a given securities.
    """

    def __init__(self, asks=None, bids=None):
        self.asks: OrderedDict[float, List[OrderBookEntry]] = (
            OrderedDict() if asks is None else asks
        )
        self.bids: OrderedDict[float, List[OrderBookEntry]] = (
            OrderedDict() if bids is None else bids
        )

    def match(self, order: Order) -> MatchResult:
        """
        Match the order against the current order book, producing a new order book and a series of executions.
        The final execution price will be the new market price of the securities.
        """
        if order.side == Side.BUY:
            # Incoming bid
            bid = OrderBookEntry(
                maker_id=order.client_id, quantity=order.quantity, price=order.price
            )

            if order.price not in self.bids:
                self.bids[order.price] = [bid]
            else:
                self.bids[order.price].append(bid)

            # Look for a matching ask
            executions = []

            # bid = 120 @ 11.0
            # asks = { 11.5: 200, 11.0: 100, 10.5: 50 }
            # executions: [ 100 @ 11.0, 20 @ 10.5 ]
            # order book: { 11.5: 200, 10.5: 30 }
            for ask_price in list(self.asks):
                asks = self.asks[ask_price]
                for ask in asks:
                    if bid.price >= ask_price:
                        # Match is found, we can execute
                        quantity = min(bid.quantity, ask.quantity)
                        executions.append(
                            Execution(
                                maker_id=1,
                                taker_id=2,
                                price=ask_price,
                                quantity=quantity,
                            )
                        )
                        bid.quantity -= quantity
                        ask.quantity -= quantity

                        # Remove the ask if it's empty
                        if ask.quantity == 0:
                            del self.asks[ask_price]

                        if bid.quantity == 0:
                            # Remove from order book
                            del self.bids[bid.price]
                            break

            return MatchResult(
                orderBook=OrderBook(
                    securities_id=order.securities_id, asks=self.asks, bids=self.bids
                ),
                executions=executions,
            )


class RootMatcher:
    """
    Root matcher responsible for managing multiple matching engines.
    """

    def __init__(self):
        # TODO: Read the securities from the securities service and create a matcher for each securities.
        self.matchers = {
            1: Matcher(),
            2: Matcher(),
            3: Matcher(),
        }

    def get_matcher(self, securities_id: int) -> Matcher:
        """
        Get the matcher for a given securities.
        """
