from dataclasses import dataclass

from sortedcontainers import SortedDict
from typing import List

from .model import Order, Side, OrderType


@dataclass
class OrderBookOrder:
    """
    An entry in the order book.
    """

    maker_id: int
    quantity: int
    price: float


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

    security_id: int
    asks: SortedDict[float, List[OrderBookOrder]]
    bids: SortedDict[float, List[OrderBookOrder]]


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
    order_book: OrderBook
    executions: List[Execution]


class Matcher:
    """
    Matching Engine responsible for matching buy and sell orders for a given securities.
    """

    def __init__(self, order_book=None):
        self.order_book = (
            OrderBook(security_id=1, asks=SortedDict(), bids=SortedDict())
            if order_book is None
            else order_book
        )
        self.asks: SortedDict[float, List[OrderBookOrder]] = self.order_book.asks
        self.bids: SortedDict[float, List[OrderBookOrder]] = self.order_book.bids

    def add(self, order: Order) -> MatchResult:
        """
        Match the order against the current order book, producing a new order book and a series of executions.
        The final execution price will be the new market price of the securities.
        """

        if order.type == OrderType.market:
            return self.match_market_order(order)
        elif order.type == OrderType.limit:
            return self.match_limit_order(order)
        else:
            raise ValueError("Unsupported order type")

    def match_limit_order(self, order: Order) -> MatchResult:
        if order.side == Side.BUY:
            # Incoming bid
            bid = OrderBookOrder(
                maker_id=order.client_id,
                quantity=order.quantity,
                price=order.price,
            )

            # Look for a matching ask
            executions = []

            for ask_price in self.asks:
                asks = self.asks[ask_price]

                i = 0
                while i < len(asks):
                    ask = asks[i]

                    if bid.price >= ask.price and bid.quantity > 0:
                        # Match is found, we can execute
                        execution = Execution(
                            maker_id=ask.maker_id,
                            taker_id=bid.maker_id,
                            price=max(ask_price, bid.price),  # favour the maker
                            quantity=min(ask.quantity, bid.quantity),
                        )
                        executions.append(execution)
                        bid.quantity -= execution.quantity
                        ask.quantity -= execution.quantity

                        # Remove depleted orders
                        if ask.quantity == 0:
                            del asks[i]
                            i -= 1
                    i += 1

            # If the bid is not fully matched, add it to the order book
            if bid.quantity > 0:
                if bid.price not in self.bids:
                    self.bids[bid.price] = []
                self.bids[bid.price].append(bid)

            return MatchResult(
                order_book=self.order_book,
                executions=executions,
            )

        elif order.side == Side.SELL:
            # Incoming ask
            ask = OrderBookOrder(
                maker_id=order.client_id, quantity=order.quantity, price=order.price
            )

            # Look for a matching bid
            executions = []

            for bid_price in reversed(self.bids):
                bids = self.bids[bid_price]

                i = 0
                while i < len(bids):
                    bid = bids[i]

                    if ask.price <= bid_price and ask.quantity > 0:
                        # Match is found, we can execute
                        execution = Execution(
                            maker_id=bid.maker_id,
                            taker_id=ask.maker_id,
                            price=min(ask.price, bid_price),  # favour the maker
                            quantity=min(ask.quantity, bid.quantity),
                        )
                        executions.append(execution)

                        ask.quantity -= execution.quantity
                        bid.quantity -= execution.quantity

                        # Remove depleted orders
                        if bid.quantity == 0:
                            del bids[i]
                            i -= 1

                    i += 1

            # If the ask is not fully matched, add it to the order book
            if ask.quantity > 0:
                if ask.price not in self.asks:
                    self.asks[ask.price] = []
                self.asks[ask.price].append(ask)

            return MatchResult(
                order_book=self.order_book,
                executions=executions,
            )

        else:
            raise ValueError(f'Unsupported order side "{order.side}"')

    def match_market_order(self, order: Order) -> MatchResult:
        if order.side == Side.BUY:
            # Incoming market bid
            bid = OrderBookOrder(
                maker_id=order.client_id,
                quantity=order.quantity,
                price=0,
            )

            # Look for a matching ask
            executions = []

            for ask_price in self.asks:
                asks = self.asks[ask_price]

                i = 0
                while i < len(asks):
                    ask = asks[i]

                    if bid.quantity > 0:
                        # Match is found against the top of the book (best ask); we can execute
                        bid.price = ask_price
                        execution = Execution(
                            maker_id=ask.maker_id,
                            taker_id=bid.maker_id,
                            price=ask_price,  # market price
                            quantity=min(ask.quantity, bid.quantity),
                        )
                        executions.append(execution)
                        bid.quantity -= execution.quantity
                        ask.quantity -= execution.quantity

                        # Remove depleted orders
                        if ask.quantity == 0:
                            del asks[i]
                            i -= 1
                    i += 1

            # If the bid is not fully matched, add it to the order book
            if bid.quantity > 0:
                if bid.price not in self.bids:
                    self.bids[bid.price] = []
                self.bids[bid.price].append(bid)

            return MatchResult(
                order_book=self.order_book,
                executions=executions,
            )

        elif order.side == Side.SELL:
            # Incoming ask
            ask = OrderBookOrder(
                maker_id=order.client_id, quantity=order.quantity, price=order.price
            )

            # Look for a matching bid
            executions = []

            for bid_price in reversed(self.bids):
                bids = self.bids[bid_price]

                i = 0
                while i < len(bids):
                    bid = bids[i]

                    if ask.quantity > 0:
                        # Match is found at the top of the book (best bid); we can execute
                        ask.price = bid_price
                        execution = Execution(
                            maker_id=bid.maker_id,
                            taker_id=ask.maker_id,
                            price=bid_price,  # market price
                            quantity=min(ask.quantity, bid.quantity),
                        )
                        executions.append(execution)

                        ask.quantity -= execution.quantity
                        bid.quantity -= execution.quantity

                        # Remove depleted orders
                        if bid.quantity == 0:
                            del bids[i]
                            i -= 1

                    i += 1

            # If the ask is not fully matched, add it to the order book
            if ask.quantity > 0:
                if ask.price not in self.asks:
                    self.asks[ask.price] = []
                self.asks[ask.price].append(ask)

            return MatchResult(
                order_book=self.order_book,
                executions=executions,
            )

        else:
            raise ValueError(f'Unsupported order side "{order.side}"')


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

    def get_matcher(self, security_id: int) -> Matcher:
        """
        Get the matcher for a given securities.
        """
