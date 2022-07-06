import threading
import trade_worker
import time
import trade_helpers
import signal
import sys

def parse_tickers():
    tickers = []
    tweets = []
    with open('tickers.txt') as f:
        lines = f.read().splitlines()
        for line in lines:
            currentline = line.split(",")
            tickers.append(currentline[0])
            tweets.append(currentline[-1])
        f.close()
    return tickers, tweets


tickers, tweets = parse_tickers()
thread_list = []

lock = threading.Lock()
keep_running = True
total_profit = 0
trade_counter = 0
starting_capital = 10000/(len(tickers))
print_lock = threading.Lock()
trade_mem = trade_helpers.trade_worker_shared_mem()
trade_mem.lock = lock
trade_mem.total_profit = total_profit
trade_mem.keep_running = keep_running
trade_mem.trade_counter = trade_counter

def signal_handler(sig, frame):
    print("\nExiting smoothly\n")
    trade_mem.keep_running = False
    for thread in thread_list:
        thread.join()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

for ticker,tweet in zip(tickers,tweets):
    trade_data = trade_helpers.trade_worker_data()
    trade_data.ticker = ticker
    trade_data.tweet = tweet
    trade_data.starting_cap = starting_capital
    t = threading.Thread(target=trade_worker.trade_work, args=(trade_data,trade_mem,))
    thread_list.append(t)
    t.start()
    time.sleep(1)

while(1):
    for x in range(0, len(thread_list)):
        if (not thread_list[x].is_alive()):
            print("DEAD THREAD!!!")
            thread_list[x].join()
            trade_data.ticker = tickers[x]
            trade_data.tweet = tweets[x]
            trade_data.starting_cap = starting_capital + (total_profit/len(tickers))
            t = threading.Thread(target=trade_worker.trade_work, args=(trade_data,trade_mem,))
            t.start()
            thread_list[x] = t
            time.sleep(1)

    color = trade_helpers.style.WHITE
    if (trade_mem.total_profit > 0):
        color = trade_helpers.style.GREEN
    elif(trade_mem.total_profit < 0):
        color= trade_helpers.style.RED
    print(color + "TOTAL PROFIT: " + str(trade_mem.total_profit) + trade_helpers.style.RESET + "\nTOTAL TRADES: " + str(trade_mem.trade_counter) + "\n")

    time.sleep(30)