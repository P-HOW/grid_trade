# Press the green button in the gutter to run the script.
import time

from binance.client import Client
from core.coin import Coin
from core import utils

if __name__ == '__main__':
    api_key = ''
    api_secret = ''
    client = Client(api_key, api_secret)

    symbol = "XRPBUSD"
    min_token_to_sell = 1000
    min_USD_to_buy = 1000
    grid_ratio_token = 200
    order_bias = 0.999
    min_token_price_step = 0.0002
    grid_size_buy = 20
    time_to_check_trading_status_and_operate = 1800
    time_to_update_system_params = 3600 * 6
    # Fetch 24h ticker data
    ticker_24h = client.get_ticker(symbol=symbol)
    # Initialize Trading tokens and pairs
    coin = Coin("XRP", client)
    coin.add_pair("BUSD")

    coin_USDT = Coin("BUSD", client)

    start_value = utils.currentHoldingInUSD(coin)

    while True:
        # OUTER LOOP: fetch crucial system params:
        high_24h, low_24h, middle_price, log_time = utils.guaranteeGetGridParams(client, symbol)
        coin.guaranteed_cancel_all_buy_orders("BUSD")
        outer_loop_time = time.time()
        print("system params updated: ")
        print(f'24h High: {high_24h}, 24h Low: {low_24h}, Middle Price: {middle_price}, Log Time: {log_time}')

        while time.time() - outer_loop_time < time_to_update_system_params:
            # print("entering trading loop now... ")
            # STEP 1:
            ul, _ = coin.guaranteed_get_balance("XRP")
            if ul >= min_token_to_sell:
                coin.place_sell_grid("BUSD", ul / grid_ratio_token, ul * order_bias, high_24h, middle_price,
                                     min_token_price_step)

            # STEP 2:
            ul, _ = coin.guaranteed_get_balance("BUSD")
            if ul >= min_USD_to_buy:
                p = coin.guaranteed_get_avg_price("BUSD")
                coin.place_buy_grid("BUSD", grid_size_buy, ul / p * order_bias, low_24h, middle_price,
                                    min_token_price_step)

            start_time = time.time()
            while time.time() - start_time < time_to_check_trading_status_and_operate:
                time.sleep(2)
                current_value = utils.currentHoldingInUSD(coin)
                print(f'\rInitial Holding: {start_value} USD, Current Holding: {current_value}', end='', flush=True)