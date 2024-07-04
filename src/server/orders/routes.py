from blacksheep.server.bindings import FromJSON
from blacksheep import get, post, json

from .manager import CreateOrderInput, OrderManager


@post("/orders")
async def create_order(
    order_input: FromJSON[CreateOrderInput],
    order_manager: OrderManager,
):
    """
    Place a new order to buy or sell an securities.
    :param order_input: The order input data.
    """
    return json(order_manager.create_order(order_input.value))


@get("/orders")
def list_orders(order_manager: OrderManager):
    """
    List all orders
    """
    return json(order_manager.list_orders())


@get("/orders/{order_id}")
def get_order(order_id: int, order_manager: OrderManager):
    """
    Get an order by ID
    """
    return json(order_manager.get_order(order_id))
