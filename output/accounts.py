import decimal

def get_share_price(symbol):
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a string")
    prices = {"AAPL": decimal.Decimal(150.0), "TSLA": decimal.Decimal(1000.0), "GOOGL": decimal.Decimal(2500.0)}
    return prices.get(symbol)

class Account:
    def __init__(self, initial_deposit=0):
        self.balance = decimal.Decimal(initial_deposit)
        self.holdings = {}
        self.transactions = []
        self.initial_deposit = decimal.Decimal(initial_deposit)
        if initial_deposit > 0:
            self.transactions.append({"type": "deposit", "amount": decimal.Decimal(initial_deposit)})

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.balance += decimal.Decimal(amount)
        self.transactions.append({"type": "deposit", "amount": decimal.Decimal(amount)})

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance - decimal.Decimal(amount) < 0:
            raise ValueError("Withdrawal would result in negative balance")
        self.balance -= decimal.Decimal(amount)
        self.transactions.append({"type": "withdrawal", "amount": decimal.Decimal(amount)})

    def buy(self, symbol, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        price = get_share_price(symbol)
        if price is None:
            raise ValueError("Unknown symbol")
        cost = price * decimal.Decimal(quantity)
        if self.balance - cost < 0:
            raise ValueError("Insufficient funds")
        self.balance -= cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append({"type": "buy", "symbol": symbol, "quantity": quantity, "price": price, "amount": cost})

    def sell(self, symbol, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise ValueError("Insufficient shares")
        price = get_share_price(symbol)
        if price is None:
            raise ValueError("Unknown symbol")
        proceeds = price * decimal.Decimal(quantity)
        self.balance += proceeds
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        self.transactions.append({"type": "sell", "symbol": symbol, "quantity": quantity, "price": price, "amount": proceeds})

    def get_portfolio_value(self):
        value = decimal.Decimal(0)
        for symbol, quantity in self.holdings.items():
            price = get_share_price(symbol)
            if price is not None:
                value += price * decimal.Decimal(quantity)
        return value

    def get_profit_loss(self):
        return self.get_portfolio_value() + self.balance - self.initial_deposit

    def get_holdings(self):
        return self.holdings

    def get_transactions(self):
        return self.transactions