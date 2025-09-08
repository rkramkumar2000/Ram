from flask import Flask, request, jsonify
from flask_cors import CORS
import decimal
import json

from accounts import Account, get_share_price

app = Flask(__name__)
CORS(app)

accounts = {}

@app.route('/account', methods=['POST'])
def create_account():
    try:
        data = json.loads(request.data)
        initial_deposit = decimal.Decimal(data.get('initial_deposit', 0))
        account_id = len(accounts) +1
        accounts[account_id] = Account(initial_deposit)
        return jsonify({'account_id': account_id}), 201
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/account/<int:account_id>/deposit', methods=['POST'])
def deposit(account_id):
    try:
        data = json.loads(request.data)
        amount = decimal.Decimal(data['amount'])
        accounts[account_id].deposit(amount)
        return jsonify({'message': 'Deposit successful'}), 200
    except (KeyError, json.JSONDecodeError):
        return jsonify({'error': 'Invalid JSON'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except KeyError:
        return jsonify({'error': 'Account not found'}), 404


@app.route('/account/<int:account_id>/withdraw', methods=['POST'])
def withdraw(account_id):
    try:
        data = json.loads(request.data)
        amount = decimal.Decimal(data['amount'])
        accounts[account_id].withdraw(amount)
        return jsonify({'message': 'Withdrawal successful'}), 200
    except (KeyError, json.JSONDecodeError):
        return jsonify({'error': 'Invalid JSON'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except KeyError:
        return jsonify({'error': 'Account not found'}), 404

@app.route('/account/<int:account_id>/buy', methods=['POST'])
def buy(account_id):
    try:
        data = json.loads(request.data)
        symbol = data['symbol']
        quantity = int(data['quantity'])
        accounts[account_id].buy(symbol, quantity)
        return jsonify({'message': 'Buy successful'}), 200
    except (KeyError, json.JSONDecodeError):
        return jsonify({'error': 'Invalid JSON'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except KeyError:
        return jsonify({'error': 'Account not found'}), 404

@app.route('/account/<int:account_id>/sell', methods=['POST'])
def sell(account_id):
    try:
        data = json.loads(request.data)
        symbol = data['symbol']
        quantity = int(data['quantity'])
        accounts[account_id].sell(symbol, quantity)
        return jsonify({'message': 'Sell successful'}), 200
    except (KeyError, json.JSONDecodeError):
        return jsonify({'error': 'Invalid JSON'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except KeyError:
        return jsonify({'error': 'Account not found'}), 404

@app.route('/account/<int:account_id>/portfolio', methods=['GET'])
def get_portfolio(account_id):
    try:
        value = accounts[account_id].get_portfolio_value()
        return jsonify({'portfolio_value': float(value)}), 200
    except KeyError:
        return jsonify({'error': 'Account not found'}), 404

@app.route('/account/<int:account_id>/profit_loss', methods=['GET'])
def get_profit_loss(account_id):
    try:
        profit_loss = accounts[account_id].get_profit_loss()
        return jsonify({'profit_loss': float(profit_loss)}), 200
    except KeyError:
        return jsonify({'error': 'Account not found'}), 404

@app.route('/account/<int:account_id>/holdings', methods=['GET'])
def get_holdings(account_id):
    try:
        holdings = accounts[account_id].get_holdings()
        return jsonify({'holdings': holdings}), 200
    except KeyError:
        return jsonify({'error': 'Account not found'}), 404

@app.route('/account/<int:account_id>/transactions', methods=['GET'])
def get_transactions(account_id):
    try:
        transactions = accounts[account_id].get_transactions()
        return jsonify({'transactions': transactions}), 200
    except KeyError:
        return jsonify({'error': 'Account not found'}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)