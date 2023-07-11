import datetime
import time


def getGridParams(client, symbol):
    # Fetch 24h ticker data
    try:
        ticker_24h = client.get_ticker(symbol=symbol)

        # Calculate variables
        high_24h = float(ticker_24h['highPrice'])
        low_24h = float(ticker_24h['lowPrice'])
        middle_price = (high_24h + low_24h) / 2
        log_time = str(datetime.datetime.now())
        return high_24h, low_24h, middle_price, log_time
    except:
        return None, None, None, None


def guaranteeGetGridParams(client, symbol):
    high_24h, low_24h, middle_price, log_time = getGridParams(client, symbol)

    while high_24h is None:
        print("errors when fetching grid params, trying again...")
        time.sleep(1)
        high_24h, low_24h, middle_price, log_time = getGridParams(client, symbol)
    return high_24h, low_24h, middle_price, log_time


def currentHoldingInUSD(coin):
    ul1, l1 = coin.guaranteed_get_balance("XRP")
    ul2, l2 = coin.guaranteed_get_balance("BUSD")
    p_temp = coin.guaranteed_get_avg_price("BUSD")
    return ul2 + l2 + (ul1 + l1) * p_temp


def printHoldings(coin, start_value):
    time.sleep(2)
    current_value = currentHoldingInUSD(coin)
    print(f'Initial Holding: {start_value} USD, Current Holding: {current_value} USD', end='\r',
          flush=True)
