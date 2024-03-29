# We first import the Client from the python-binance package
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import SIDE_BUY, ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC, SIDE_SELL
import math
import time
import statistics


def find_pair_price_from_tickers(prices, pair):
    pair_price = None

    # Iterate over the prices data
    for item in prices:
        # If the symbol is "BTCUSDT", save the price and break the loop
        if item['symbol'] == pair:
            pair_price = item['price']
            break

    # Check if we found the price
    return pair_price


def get_p_reference(coin, d_bar_array, k1, k2, d_bar_array_length):
    prices = coin.guarantee_get_all_tickers()
    p2 = coin.guaranteed_get_avg_price("USDT")
    p3 = coin.guaranteed_get_avg_price("TUSD")
    p1 = float(find_pair_price_from_tickers(prices, "TUSDUSDT"))
    p3_star = float(p2 / p1)
    d_bar_array.append(p3 - p2)
    if len(d_bar_array) > d_bar_array_length:
        d_bar_array.pop(0)
    d_bar = statistics.mean(d_bar_array)
    p3_bar = p2 + d_bar
    return p3_bar * k1 + p3_star * k2, p3


def get_balance(client, asset):
    time.sleep(0.05)
    try:
        balance_info = client.get_asset_balance(asset=asset)
        if balance_info is not None:
            return balance_info['free'], balance_info['locked']
    except BinanceAPIException as e:
        print(f"An error occurred while fetching the balance: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None, None


class Coin:
    def __init__(self, symbol: str, client: Client):
        self.symbol = symbol
        self.client = client
        self.pairs = {}  # This dictionary will store the symbol pair info

    def get_my_trades(self, pair: str):
        # Create the symbol pair string
        symbol_pair = f"{self.symbol}{pair}"

        try:
            # Attempt to get your recent trades for this coin pair
            my_trades = self.client.get_my_trades(symbol=symbol_pair)
            return my_trades

        except BinanceAPIException as e:
            print(f"An error occurred: {e}")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        return None

    def guarantee_get_my_trades(self, pair: str):
        trades = self.get_my_trades(pair)
        while trades is None:
            trades = self.get_my_trades(pair)
        return trades

    def get_symbol_info(self, pair: str):
        symbol_pair = f"{self.symbol}{pair}"

        try:
            # Attempt to get information for this symbol pair
            symbol_info = self.client.get_symbol_info(symbol_pair)
            return symbol_info

        except BinanceAPIException as e:
            print(f"An error occurred while fetching symbol info: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return None

    def guarantee_get_symbol_info(self, pair: str):
        info = self.get_symbol_info(pair)
        while info is None:
            info = self.get_symbol_info(pair)
        return info

    def get_all_tickers(self):
        try:
            # Attempt to get all tickers
            tickers = self.client.get_all_tickers()
            return tickers

        except BinanceAPIException as e:
            print(f"An error occurred while fetching tickers: {e}")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return None

    def guarantee_get_all_tickers(self):
        tickers = self.get_all_tickers()
        while tickers is None:
            tickers = self.get_all_tickers()
        return tickers

    def add_pair(self, pair):
        try:
            # Attempt to get information for this symbol pair
            symbol_info = self.guarantee_get_symbol_info(pair)
            self.pairs[pair] = symbol_info  # Store the symbol pair info in the pairs dictionary

        except BinanceAPIException as e:
            print(f"An error occurred while fetching symbol info: {e}")

    def get_step_size(self, pair):
        try:
            # Attempt to get symbol info from the pairs dictionary
            symbol_info = self.pairs.get(pair)

            # If symbol info was found
            if symbol_info:
                # Find the step size
                for filter_info in symbol_info['filters']:
                    if filter_info['filterType'] == 'LOT_SIZE':
                        return float(filter_info['stepSize'])

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        return None

    def place_buy_limit_order(self, pair, quantity, price):
        symbol_info = self.pairs.get(pair)

        # If symbol info is not available, return early
        if symbol_info is None:
            print(f"Couldn't fetch the symbol info for {self.symbol}/{pair}")
            return

        # Get the filters for the symbol
        filters = symbol_info['filters']

        # Find the price filter and lot size filter
        price_filter = next((f for f in filters if f['filterType'] == 'PRICE_FILTER'), None)
        lot_size_filter = next((f for f in filters if f['filterType'] == 'LOT_SIZE'), None)

        # Get the tick size and step size from the filters
        tick_size = float(price_filter['tickSize'])
        step_size = float(lot_size_filter['stepSize'])

        # Calculate the number of decimal places for the tick size and step size
        tick_size_decimals = int(round(-math.log(tick_size, 10)))
        step_size_decimals = int(round(-math.log(step_size, 10)))

        # Format the price and quantity
        formatted_price = "{:0.0{}f}".format(price, tick_size_decimals)
        formatted_quantity = "{:0.0{}f}".format(quantity, step_size_decimals)

        try:
            order = self.client.create_order(
                symbol=f"{self.symbol}{pair}",
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=formatted_quantity,
                price=formatted_price
            )
            return order
        except BinanceAPIException as e:
            print(f"An error occurred while placing the order: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def place_sell_limit_order(self, pair, quantity, price):
        symbol_info = self.pairs.get(pair)

        # Get the filters for the symbol
        filters = symbol_info['filters']

        # Find the price filter and lot size filter
        price_filter = next((f for f in filters if f['filterType'] == 'PRICE_FILTER'), None)
        lot_size_filter = next((f for f in filters if f['filterType'] == 'LOT_SIZE'), None)

        # Get the tick size and step size from the filters
        tick_size = float(price_filter['tickSize'])
        step_size = float(lot_size_filter['stepSize'])

        # Calculate the number of decimal places for the tick size and step size
        tick_size_decimals = int(round(-math.log(tick_size, 10)))
        step_size_decimals = int(round(-math.log(step_size, 10)))

        # Format the price and quantity
        formatted_price = "{:0.0{}f}".format(price, tick_size_decimals)
        formatted_quantity = "{:0.0{}f}".format(quantity, step_size_decimals)

        try:
            order = self.client.create_order(
                symbol=f"{self.symbol}{pair}",
                side=SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=formatted_quantity,
                price=formatted_price
            )
            return order
        except BinanceAPIException as e:
            print(f"An error occurred while placing the order: {e}")
            return None

    def guaranteed_get_balance(self, asset):
        free_balance, locked_balance = get_balance(self.client, asset)
        while free_balance is None or locked_balance is None:
            free_balance, locked_balance = get_balance(self.client, asset)
        return float(free_balance), float(locked_balance)

    def get_open_orders(self, pair):
        try:
            open_orders = self.client.get_open_orders(symbol=f"{self.symbol}{pair}")
            return open_orders
        except BinanceAPIException as e:
            print(f"An error occurred while fetching the open orders: {e}")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return None

    def guaranteed_get_open_orders(self, pair):
        open_orders = self.get_open_orders(pair)
        while open_orders is None:
            open_orders = self.get_open_orders(pair)
        return open_orders

    def guaranteed_cancel_orders_above_threshold(self, pair, threshold):
        while True:
            open_orders = self.guaranteed_get_open_orders(pair)
            # filter the orders whose price is higher than the threshold
            high_price_orders = [order for order in open_orders if float(order['price']) > threshold]

            # break the loop if no high price orders are left
            if len(high_price_orders) == 0:
                break

            for order in high_price_orders:
                while True:
                    try:
                        self.client.cancel_order(
                            symbol=f"{self.symbol}{pair}",
                            orderId=order['orderId']
                        )
                        # Break the inner loop if the cancellation was successful
                        break
                    except BinanceAPIException as e:
                        print(f"An error occurred while cancelling the order {order['orderId']}: {e}")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")

        return None

    def guaranteed_cancel_all_open_orders(self, pair):
        while True:
            open_orders = self.guaranteed_get_open_orders(pair)

            if len(open_orders) == 0:
                break  # break the loop if no open orders are left

            for order in open_orders:
                try:
                    self.client.cancel_order(
                        symbol=f"{self.symbol}{pair}",
                        orderId=order['orderId']
                    )
                except BinanceAPIException as e:
                    print(f"An error occurred while cancelling the order {order['orderId']}: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
        return None

    def guaranteed_cancel_all_buy_orders(self, pair):
        while True:
            open_orders = self.guaranteed_get_open_orders(pair)

            # filter out the 'SELL' orders
            buy_orders = [order for order in open_orders if order['side'] == 'BUY']

            if len(buy_orders) == 0:
                break  # break the loop if no 'BUY' orders are left

            for order in buy_orders:
                try:
                    self.client.cancel_order(
                        symbol=f"{self.symbol}{pair}",
                        orderId=order['orderId']
                    )
                except BinanceAPIException as e:
                    print(f"An error occurred while cancelling the order {order['orderId']}: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")

        return None

    def blocked_for_sell_all(self, pair, price, order_bias, qty_min, d_bar_array, k1, k2, d_bar_array_length, TIME_OUT):
        start_time = time.time()  # Get the current time
        ul, _ = self.guaranteed_get_balance(self.symbol)
        while self.place_sell_limit_order(pair, ul * order_bias, price) is None:
            print("Blocked_for_sell_all function error")
        _, l = self.guaranteed_get_balance(self.symbol)
        while l > qty_min:
            if time.time() - start_time > TIME_OUT:
                return False
            get_p_reference(self, d_bar_array, k1, k2, d_bar_array_length)
            _, l = self.guaranteed_get_balance(self.symbol)
            # wait for sell orders to be filled....
        return True

    def get_avg_price(self, pair):
        try:
            ticker = self.client.get_ticker(symbol=f"{self.symbol}{pair}")
            bid_price = float(ticker['bidPrice'])
            ask_price = float(ticker['askPrice'])
            avg_price = (bid_price + ask_price) / 2
            return avg_price
        except BinanceAPIException as e:
            print(f"An error occurred while fetching the ticker: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return None

    def guaranteed_get_avg_price(self, pair):
        avg_price = self.get_avg_price(pair)
        while avg_price is None:
            avg_price = self.get_avg_price(pair)
        return avg_price

    def sell_at_market_price(self, pair, quantity):
        #print(self.pairs)
        #print(pair)
        symbol = f"{self.symbol}{pair}"
        symbol_info = self.pairs.get(pair)
        #print(symbol_info)
        # Get the filters for the symbol
        filters = symbol_info['filters']

        # Find the lot size filter
        lot_size_filter = next((f for f in filters if f['filterType'] == 'LOT_SIZE'), None)

        # Get the step size from the filter
        step_size = float(lot_size_filter['stepSize'])

        # Calculate the number of decimal places for the step size
        step_size_decimals = int(round(-math.log(step_size, 10)))

        # Format the quantity
        formatted_quantity = "{:0.0{}f}".format(quantity, step_size_decimals)

        try:
            order = self.client.order_market_sell(symbol=symbol, quantity=formatted_quantity)
            return order
        except BinanceAPIException as e:
            print(f"An error occurred while placing the order: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return None

    def get_last_buy_average_price(self, pair: str):
        trades = self.guarantee_get_my_trades(pair)
        if trades is None or len(trades) == 0:
            print(f"No trade history found for pair: {pair}")
            return None

        # Finding the most recent sell trade
        sell_trades = [trade for trade in trades if not trade['isBuyer']]
        sell_trades.sort(key=lambda x: x['time'], reverse=True)
        if len(sell_trades) == 0:
            print(f"No sell trade found for pair: {pair}")
            return None
        last_sell_timestamp = sell_trades[0]['time']  # The timestamp of the most recent sell order

        # Finding all buy orders occurred after the most recent sell order
        buy_trades_after_last_sell = [trade for trade in trades if
                                      trade['isBuyer'] and trade['time'] > last_sell_timestamp]
        if len(buy_trades_after_last_sell) == 0:
            print(f"No buy orders found after the last sell order for pair: {pair}")
            return None

        # Calculating the average price of these buy trades
        total_cost = 0.0
        total_qty = 0.0
        for trade in buy_trades_after_last_sell:
            total_cost += float(trade['price']) * float(trade['qty'])
            total_qty += float(trade['qty'])

        average_price = total_cost / total_qty if total_qty else 0.0

        return average_price

    def place_buy_grid(self, pair, grid_size, total_quantity, h24_low, middle_price, min_step):
        # Calculate grid_spacing, if it's smaller than min_step, use min_step instead
        grid_spacing = (middle_price - h24_low) / grid_size
        if grid_spacing < min_step:
            grid_spacing = min_step
            grid_size = math.ceil((middle_price - h24_low) / grid_spacing)

        # Calculate quantity for each buy so that they are evenly spaced
        quantity_per_buy = total_quantity / grid_size

        # Define the grid
        buy_prices = [middle_price - grid_spacing * i for i in range(grid_size)]

        # Place the orders
        for price in buy_prices:
            self.place_buy_limit_order(pair, quantity_per_buy, price)

    def place_sell_grid(self, pair, grid_size, total_quantity, h24_high, middle_price, min_step):
        # Calculate grid_spacing, if it's smaller than min_step, use min_step instead
        grid_spacing = (h24_high - middle_price) / grid_size
        if grid_spacing < min_step:
            grid_spacing = min_step
            grid_size = math.ceil((h24_high - middle_price) / grid_spacing)

        # Calculate quantity for each sell so that they are evenly spaced
        quantity_per_sell = total_quantity / grid_size

        # Define the grid
        sell_prices = [middle_price + grid_spacing * i for i in range(grid_size)]

        # Place the orders
        for price in sell_prices:
            self.place_sell_limit_order(pair, quantity_per_sell, price)

