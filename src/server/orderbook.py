from blacksheep import json, get


@get("/orderbook")
def get_orderbook():
    """
    Get the current orderbook for the securities.
    """
    return json({})
