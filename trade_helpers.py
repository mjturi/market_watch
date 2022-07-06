# specific data for each thread, needed to initialize
class trade_worker_data:
    def __init__(self):
        self.ticker = ""
        self.tweet = ""
        self.starting_cap = 0

# shared memory and lock for all threads
# access -> gain lock, then can update variables
# threads read-only on keep_running for thread status
class trade_worker_shared_mem:
    def __init__(self):
        self.lock = None
        self.total_profit = 0
        self.keep_running = None
        self.trade_counter = 0

# terminal coloring options
# usage: print(style.BLACK + "text" + style.RESET)
class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    ORANGE = "\033[48:5:208m%s\033[m\n"
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'