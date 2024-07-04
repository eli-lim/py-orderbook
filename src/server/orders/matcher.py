from dataclasses import dataclass
from typing import List

from .model import Order, Side


@dataclass
class OrderBookEntry:
    """
    An entry in the order book.
    """

    price: float
    quantity: int
    side: Side


@dataclass
class OrderBook:
    """
    Order book for a given securities.
    """

    securities_id: int
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]


class Matcher:
    """
    Matching Engine responsible for matching buy and sell orders for a given securities.
    """

    def match(self, order: Order) -> OrderBook:
        """
        Match the order against the current order book, producing a new order book and a series of executions.
        The final execution price will be the new market price of the securities.
        """


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
