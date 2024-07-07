from blacksheep import Application
from blacksheep.server.openapi.v3 import OpenAPIHandler
from openapidocs.v3 import Info

from .securities.model import SecuritiesRepository
from .orders.manager import OrderManager
from .orders.model import OrderRepository

app = Application()

app.services.add_scoped(OrderRepository)
app.services.add_scoped(OrderManager)
app.services.add_scoped(SecuritiesRepository)

docs = OpenAPIHandler(info=Info(title="Example API", version="0.0.1"))
docs.bind_app(app)

class A:
    pass
