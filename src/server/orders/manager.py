from dataclasses import dataclass
from typing import List
from uuid import uuid4

from .model import OrderRepository, Order, OrderType, Side


@dataclass
class CreateOrderInput:
    client_id: int
    securities_id: int
    side: Side
    quantity: int
    type: OrderType
    price: float


class OrderManager:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def create_order(self, order: CreateOrderInput):
        # 1. Persist the order in the repository
        order = self.order_repository.create_order(
            Order(
                id=str(uuid4()),
                client_id=order.client_id,
                securities_id=order.securities_id,
                side=order.side,
                quantity=order.quantity,
                type=order.type,
                price=order.price,
            )
        )

        # 2. Send the order to the matching engine to produce the new order book

        return order

    def get_order(self, order_id: int) -> Order:
        return self.order_repository.get_order(order_id)

    def list_orders(self) -> List[Order]:
        return self.order_repository.list_orders()
