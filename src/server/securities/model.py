from dataclasses import dataclass


@dataclass
class Security:
    id: int
    symbol: str


class SecuritiesRepository:
    def __init__(self):
        self.securities = {
            0: Security(0, "DEW"),
            1: Security(1, "AAPL"),
            2: Security(2, "MSFT"),
            3: Security(3, "GOOGL"),
        }

    def list_securities(self):
        return self.securities.values()

    def get_security(self, security_id):
        return self.securities[security_id]
