from dataclasses import dataclass
from enum import Enum
from typing import List


class Side(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    limit = "limit"
    market = "market"


@dataclass
class Order:
    id: str
    client_id: int
    securities_id: int
    side: Side
    quantity: int
    type: OrderType
    price: float


class OrderRepository:
    """
    An in-memory store for orders.
    """

    def __init__(self):
        self.orders = {}

    def create_order(self, order: Order) -> Order:
        self.orders[order.id] = order
        return order

    def get_order(self, order_id: int) -> Order:
        return self.orders.get(order_id)

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())
