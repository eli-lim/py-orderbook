from blacksheep import get, json

from .model import SecuritiesRepository


@get("/securities")
def list_securities(repo: SecuritiesRepository):
    """
    List all available securities for trading.
    """
    return json(repo.list_securities())


@get("/securities/:security_id")
def get_security(security_id: int, repo: SecuritiesRepository):
    """
    Get the details of a security.
    """
    return json(repo.get_security(security_id))
