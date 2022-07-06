from nltk.probability import ImmutableProbabilisticMixIn
from numpy.core.numeric import Inf
import yfinance as yf
import robin_stocks as rs
import pandas as pd
import time
import twitter_worker
import trade_helpers

# for non-dev purchases eventually:
# https://algotrading101.com/learn/robinhood-api-guide/

def setup_dev_purchase(curr_level, fib_interactions, fib_levels, curr_sentiment, slopes, capital, buys, sells, stops):
    if (capital <= 0):
        capital = 0
        return
    if (slopes[0] >= 0 and slopes[1] >= 0):
        investment = capital * curr_sentiment
        # mins since changed -> max 180, positive interactions, negative interactions
        if (fib_interactions[curr_level][1] + fib_interactions[curr_level][2] >= 2): # and fib_interactions[curr_level][1] >= fib_interactions[curr_level][2]):
            # if this check passes, we are ready to buy
            if (curr_level == 4):
                # 2 transactions for this level
                buys.append([fib_levels[curr_level], investment/2,0])
                sells.append(fib_levels[curr_level-1])
                stops.append(fib_levels[curr_level+1])

                buys.append([fib_levels[curr_level], investment/2, 0])
                sells.append(fib_levels[curr_level-2])
                stops.append(fib_levels[curr_level+1])

            else:
                buys.append([fib_levels[curr_level], investment,0])
                sells.append(fib_levels[curr_level-2])
                stops.append(fib_levels[curr_level+1])

            capital -= investment
        else:
            print(trade_helpers.style.BLUE + "Skipping buy due to low fib interaction" + trade_helpers.style.RESET)
    else:
        print(trade_helpers.style.RED + "Skipping buy due to downward trend, " + str(slopes[0]) + ", " + str(slopes[1]) + trade_helpers.style.RESET)


# executed buys, updates data to reflect what happens
def handle_dev_purchase_list(curr_price, buys, pers_capital):
    capital_spent = 0
    total_buys = 0
    for buy in buys:
        if (buy[2] == 0):
            if (curr_price >= buy[0]):
                if (pers_capital - capital_spent - buy[1] > 0):
                    capital_spent += (buy[1])
                    print(trade_helpers.style.ORANGE + "BUY EXECUTING: " + str(buy[1]) + " at " + str(curr_price) + trade_helpers.style.RESET)
                    buy[0] = curr_price # buy[0] holds buy in price
                    buy[1] = buy[1]/curr_price # buy[1] will now store the percentage we hold
                    buy[2] = 1 # buy[2] shows executed
                    total_buys += 1
    return total_buys, capital_spent


# returns total profit change, cleans up orders as they are terminated
def handle_dev_sell_list(curr_price, buys, sells, stops):
    investment_gain = 0
    sellout_price = 0
    index = 0
    for sell, stop in zip(sells, stops):
        if (buys[index][2] == 1 and curr_price >= sell or curr_price <= stop): # % of stock * curr price - % of stock * buy in price
            investment_gain += ((buys[index][1] * curr_price) - (buys[index][1] * buys[index][0]))
            sellout_price += (buys[index][1] * curr_price)
            print("SELL:")
            print("CURR PRICE:", curr_price)
            print("STAKE:" + str(buys[index][1]) + "%")
            print("BUY PRICE:", buys[index][0])

            color = trade_helpers.style.RED
            if (investment_gain >= 0):
                color = trade_helpers.style.GREEN

            print(color + "INVESTMENT GAIN:" + str(investment_gain) + trade_helpers.style.RESET)
            buys.pop(index)
            sells.pop(index)
            stops.pop(index)
        index += 1
    return investment_gain, sellout_price


def update_fib_interactions(fib_interactions, level, prev_level, close_price, fib_levels):
    dif = prev_level - level

    if (dif == 0):
        top_lvl_perc_change = fib_levels[level] - close_price / fib_levels[level]
        btm_lvl_perc_change = fib_levels[level + 1] - close_price / fib_levels[level+1]
        if (top_lvl_perc_change >= -0.1 and top_lvl_perc_change < 0):
            fib_interactions[level][2] += 1
            fib_interactions[level][0] += 0
        elif (top_lvl_perc_change <= 0.1 and top_lvl_perc_change > 0):
            fib_interactions[level][1] += 1
            fib_interactions[level][0] += 0
        elif (btm_lvl_perc_change >= -0.1 and btm_lvl_perc_change < 0):
            fib_interactions[level+1][2] += 1
            fib_interactions[level+1][0] += 0
        elif (btm_lvl_perc_change <= 0.1 and btm_lvl_perc_change > 0):
            fib_interactions[level+1][1] += 1
            fib_interactions[level+1][0] += 0
        else:
            fib_interactions[level][0] += 1

    elif(dif < 0):
        top_lvl_perc_change = fib_levels[level] - close_price / fib_levels[level]
        btm_lvl_perc_change = fib_levels[level + 1] - close_price / fib_levels[level+1]
        if ((top_lvl_perc_change >= -0.1 and top_lvl_perc_change < 0) or (top_lvl_perc_change <= 0.1 and top_lvl_perc_change > 0)):
            fib_interactions[level][2] += 1
            fib_interactions[level][0] += 0
        elif ((btm_lvl_perc_change >= -0.1 and btm_lvl_perc_change < 0) or (btm_lvl_perc_change <= 0.1 and btm_lvl_perc_change > 0)):
            fib_interactions[level+1][2] += 1
            fib_interactions[level+1][0] += 0
        while (dif < 0):
            fib_interactions[level + dif][2] += 1
            fib_interactions[level + dif][0] = 0
            dif += 1
    elif(dif > 0):
        top_lvl_perc_change = fib_levels[level] - close_price / fib_levels[level]
        btm_lvl_perc_change = fib_levels[level + 1] - close_price / fib_levels[level+1]
        if ((top_lvl_perc_change >= -0.1 and top_lvl_perc_change < 0) or (top_lvl_perc_change <= 0.1 and top_lvl_perc_change > 0)):
            fib_interactions[level][2] += 1
            fib_interactions[level][0] += 0
        elif ((btm_lvl_perc_change >= -0.1 and btm_lvl_perc_change < 0) or (btm_lvl_perc_change <= 0.1 and btm_lvl_perc_change > 0)):
            fib_interactions[level+1][2] += 1
            fib_interactions[level+1][0] += 0
        while (dif > 0):
            fib_interactions[level + dif][1] += 1
            fib_interactions[level + dif][0] = 0
            dif -= 1

    return fib_interactions


def trade_work(trade_data, trade_mem):
    personal_capital = trade_data.starting_cap
    init_capital = personal_capital
    target = yf.Ticker(trade_data.ticker)

    pers_trades = 0

    # dataframes
    one_d_frame = pd.DataFrame(columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'])
    five_d_frame = pd.DataFrame(columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'])
    one_m_frame = pd.DataFrame(columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'])

    peak = [0, 0]
    low = [Inf, 0]
    slope = 0

    # mins since changed -> max 180, positive interactions, negative interactions
    fib_interactions = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
    fib_levels = [0, 0, 0, 0, 0, 0, 0]
    prev_fib_level = 0
    changed = False

    # sentiment
    prev_sent = 0
    mins_waited = 10

    MINS_IN_WINDOW = 45

    new_trades = 0
    sell_val = 0

    buys = []
    sells = []
    stops = []

    while(trade_mem.keep_running):
        if (mins_waited < 10):
            mins_waited += 1
        else:
            prev_sent = twitter_worker.twitter_worker(trade_data.tweet)
            mins_waited = 0

        # get historical market data
        day_one = target.history(period="1hr", interval="1m")
        day_five = target.history(period="5d", interval="1m")
        month_one = target.history(period="1mo", interval="5m")

        # fill dfs
        one_d_frame = one_d_frame.merge(day_one, on=['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'], how='right')
        one_d_frame.drop_duplicates(keep=False, inplace=True)

        five_d_frame = five_d_frame.merge(day_five, on=['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'], how='right')
        five_d_frame.drop_duplicates(keep=False, inplace=True)

        one_m_frame = one_m_frame.merge(month_one, on=['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'], how='right')
        one_m_frame.drop_duplicates(keep=False, inplace=True)

        # running high/low, sliding window here looking at last MINS_IN_WINDOW entries
        last_row = one_d_frame.iloc[-MINS_IN_WINDOW:]

        curr_min = last_row.min(axis=0)['Low']
        curr_index = last_row.index[last_row.Low == curr_min][0]
        if (curr_min < low[0]):
            low[0] = curr_min
            low[1] = curr_index
            changed = True
        elif (curr_min > low[0]):
            low[0] = curr_min
            low[1] = curr_index
            changed = True

        curr_max = last_row.max(axis=0)['High']
        curr_index = last_row.index[last_row.High == curr_max][0]
        if (curr_max > peak[0]):
            peak[0] = curr_max
            peak[1] = curr_index
            changed = True
        elif (curr_max < peak[0]):
            peak[0] = curr_max
            peak[1] = curr_index
            changed = True

        slope = (peak[0] - low[0])/(peak[1] - low[1])
        perc_change = (peak[0] - low[0]) / peak[0]
        candle_slope = last_row['Open'].iloc[-1] - last_row['Close'].iloc[-1]

        # calc fib levels, only need to recalc if updated
        if (changed):
            fib_levels[0] = peak[0]
            fib_levels[1] = (peak[0] - low[0]) * 0.764 + low[0]
            fib_levels[2] = (peak[0] - low[0]) * 0.618 + low[0]
            fib_levels[3] = (peak[0] - low[0]) * 0.50 + low[0]
            fib_levels[4] = (peak[0] - low[0]) * 0.382 + low[0]
            fib_levels[5] = (peak[0] - low[0]) * 0.214 + low[0]
            fib_levels[6] = low[0]

        last_close = last_row['Close'].iloc[-1]

        investment_gain, sell_val =  handle_dev_sell_list(last_close, buys, sells, stops)
        personal_capital += sell_val

        # handle buy setup
        if(last_close <= fib_levels[5]):
            fib_interactions = update_fib_interactions(fib_interactions, 5, prev_fib_level, last_close, fib_levels)
            prev_fib_level = 5
        elif (last_close <= fib_levels[4] and last_close > fib_levels[5]):
            fib_interactions = update_fib_interactions(fib_interactions, 4, prev_fib_level, last_close, fib_levels)
            setup_dev_purchase(4, fib_interactions, fib_levels, prev_sent, [slope, candle_slope], personal_capital, buys, sells, stops)
            prev_fib_level = 4
        elif (last_close <= fib_levels[3] and last_close > fib_levels[4]):
            fib_interactions = update_fib_interactions(fib_interactions, 3, prev_fib_level, last_close, fib_levels)
            setup_dev_purchase(3, fib_interactions, fib_levels, prev_sent, [slope, candle_slope], personal_capital, buys, sells, stops)
            prev_fib_level = 3
        elif (last_close <= fib_levels[2] and last_close > fib_levels[3]):
            fib_interactions = update_fib_interactions(fib_interactions, 2, prev_fib_level, last_close, fib_levels)
            setup_dev_purchase(2, fib_interactions, fib_levels, prev_sent, [slope, candle_slope], personal_capital, buys, sells, stops)
            prev_fib_level = 2
        elif (last_close <= fib_levels[1] and last_close > fib_levels[2]):
            fib_interactions = update_fib_interactions(fib_interactions, 1, prev_fib_level, last_close, fib_levels)
            prev_fib_level = 1
        elif (last_close <= fib_levels[0] and last_close > fib_levels[1]):
            fib_interactions = update_fib_interactions(fib_interactions, 0, prev_fib_level, last_close, fib_levels)
            prev_fib_level = 0

        if (personal_capital > 0):
            new_trades, capital_spent = handle_dev_purchase_list(last_close, buys, personal_capital)
            pers_trades += new_trades
            personal_capital -= capital_spent

        print(trade_data.ticker + "\nTRADES: " + str(pers_trades))
        color = trade_helpers.style.RED
        if (personal_capital > init_capital):
            color = trade_helpers.style.GREEN
        elif (personal_capital == init_capital):
            color = trade_helpers.style.WHITE
        print(color + "CAPITAL REMAINING: " + str(personal_capital) + trade_helpers.style.RESET)
        print("\n")

        # trim dfs, make sure only retaining accurate window
        if (one_d_frame.shape[0] > 1440):
            one_d_frame.drop(index=one_d_frame.index[:one_d_frame.shape[0] - 1440], axis=0, inplace=True)

        if (five_d_frame.shape[0] > 7200):
            five_d_frame.drop(index=five_d_frame.index[:five_d_frame.shape[0] - 7200], axis=0, inplace=True)

        if (one_m_frame.shape[0] > 8640):
            one_m_frame.drop(index=one_m_frame.index[:one_m_frame.shape[0] - 8640], axis=0, inplace=True)

        # check if we can execute a buy, increment trades by buys executed
        with trade_mem.lock:
            trade_mem.total_profit += investment_gain
            trade_mem.trade_counter += new_trades
            investment_gain = 0
            new_trades = 0

        for fib in fib_interactions:
            if (fib[0] >= MINS_IN_WINDOW):
                fib[0] = 0
                fib[1] = 0
                fib[2] = 0

        # sleep, checking outer status
        ctr = 0
        while (ctr < 50):
            time.sleep(2)
            if (not trade_mem.keep_running):
                return
            ctr+=2