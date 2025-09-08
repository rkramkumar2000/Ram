import unittest
import decimal
from accounts import Account, get_share_price

class TestGetSharePrice(unittest.TestCase):
    def test_valid_symbol(self):
        self.assertEqual(get_share_price("AAPL"), decimal.Decimal(150.0))
        self.assertEqual(get_share_price("TSLA"), decimal.Decimal(1000.0))
        self.assertEqual(get_share_price("GOOGL"), decimal.Decimal(2500.0))

    def test_invalid_symbol(self):
        with self.assertRaises(ValueError):
            get_share_price(123)
        self.assertIsNone(get_share_price("MSFT"))

    def test_invalid_symbol_type(self):
        with self.assertRaises(ValueError):
            get_share_price(123)

class TestAccount(unittest.TestCase):
    def test_initial_deposit(self):
        account = Account(1000)
        self.assertEqual(account.balance, decimal.Decimal(1000))
        self.assertEqual(len(account.transactions),1)
        self.assertEqual(account.transactions[0]["amount"], decimal.Decimal(1000))

    def test_deposit(self):
        account = Account()
        account.deposit(500)
        self.assertEqual(account.balance, decimal.Decimal(500))
        self.assertEqual(len(account.transactions), 1)
        self.assertEqual(account.transactions[0]["amount"], decimal.Decimal(500))

    def test_deposit_invalid_amount(self):
        account = Account()
        with self.assertRaises(ValueError):
            account.deposit(-100)
        with self.assertRaises(ValueError):
            account.deposit(0)

    def test_withdraw(self):
        account = Account(1000)
        account.withdraw(200)
        self.assertEqual(account.balance, decimal.Decimal(800))
        self.assertEqual(len(account.transactions), 2)
        self.assertEqual(account.transactions[1]["amount"], decimal.Decimal(200))

    def test_withdraw_invalid_amount(self):
        account = Account(1000)
        with self.assertRaises(ValueError):
            account.withdraw(-100)
        with self.assertRaises(ValueError):
            account.withdraw(0)


    def test_withdraw_insufficient_funds(self):
        account = Account(1000)
        with self.assertRaises(ValueError):
            account.withdraw(1500)

    def test_buy(self):
        account = Account(2000)
        account.buy("AAPL", 5)
        self.assertEqual(account.balance, decimal.Decimal(1250))
        self.assertEqual(account.holdings["AAPL"], 5)
        self.assertEqual(len(account.transactions), 2)
        self.assertEqual(account.transactions[1]["amount"], decimal.Decimal(750))


    def test_buy_insufficient_funds(self):
        account = Account(100)
        with self.assertRaises(ValueError):
            account.buy("GOOGL", 1)

    def test_buy_unknown_symbol(self):
        account = Account(2000)
        with self.assertRaises(ValueError):
            account.buy("MSFT", 5)

    def test_buy_invalid_quantity(self):
        account = Account(2000)
        with self.assertRaises(ValueError):
            account.buy("AAPL", -5)
        with self.assertRaises(ValueError):
            account.buy("AAPL", 0)


    def test_sell(self):
        account = Account(1000)
        account.buy("AAPL", 10)
        account.sell("AAPL", 5)
        self.assertEqual(account.balance, decimal.Decimal(1750))
        self.assertEqual(account.holdings["AAPL"], 5)
        self.assertEqual(len(account.transactions), 3)
        self.assertEqual(account.transactions[2]["amount"], decimal.Decimal(750))

    def test_sell_insufficient_shares(self):
        account = Account(1000)
        account.buy("AAPL", 10)
        with self.assertRaises(ValueError):
            account.sell("AAPL", 15)

    def test_sell_unknown_symbol(self):
        account = Account(1000)
        with self.assertRaises(ValueError):
            account.sell("MSFT",5)

    def test_sell_invalid_quantity(self):
        account = Account(1000)
        account.buy("AAPL",10)
        with self.assertRaises(ValueError):
            account.sell("AAPL",-5)
        with self.assertRaises(ValueError):
            account.sell("AAPL",0)

    def test_get_portfolio_value(self):
        account = Account(1000)
        account.buy("AAPL", 10)
        account.buy("TSLA", 2)
        self.assertEqual(account.get_portfolio_value(), decimal.Decimal(3500))

    def test_get_profit_loss(self):
        account = Account(1000)
        account.buy("AAPL", 10)
        account.buy("TSLA", 2)
        account.sell("AAPL", 5)
        self.assertEqual(account.get_profit_loss(), decimal.Decimal(3250))

    def test_get_holdings(self):
        account = Account(1000)
        account.buy("AAPL", 10)
        account.buy("TSLA", 2)
        self.assertEqual(account.get_holdings(), {"AAPL": 10, "TSLA": 2})

    def test_get_transactions(self):
        account = Account(1000)
        account.deposit(500)
        account.buy("AAPL", 10)
        self.assertEqual(len(account.get_transactions()),3)


if __name__ == '__main__':
    unittest.main()