from threading import Thread
import signal
import time
import tibber
import ShellyPy
from http.server import HTTPServer, BaseHTTPRequestHandler
import logic
import sys
import getopt

# Default values of arguments
arg_api_token = "xdZ5baalsmyHerIU629KPR_dMfuewosNllYTzhCq8E8"
arg_upd = 120
arg_home = 0
arg_relay_1 = "192.168.20.18"
arg_relay_2 = "192.168.20.19"
arg_port = 5000
arg_min_temp = 18.0
arg_max_temp = 22.0


def get_arg(argv):
    global arg_api_token
    global arg_upd
    global arg_home
    global arg_relay_1
    global arg_relay_2
    global arg_port
    global arg_min_temp
    global arg_max_temp

    arg_help = "{0} -api <input> -upd <Update interval for tibber data> -h <Home ID> -r1 <IP for relay 1>" \
               "-r2 <IP for relay 2> -p <Port for webhook server (default = 5000)>" \
               "--min_temp <Lowest temperature to allow no production>" \
               "--max_temp <Maximum temperature to allow for extra production" \
               .format(argv[0])

    try:
        opts, args = getopt.getopt(argv[1:], "h:api:h:upd:r1:r2:p", ["help", "api_token", "home_id=" "relay_1=",
                                                                     "relay_2=", "upd_interval", "port", "min_temp",
                                                                     "max_temp"])
    except:
        print(arg_help)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)  # print the help message
            sys.exit(2)
        elif opt in ("-api", "--api_token"):
            arg_api_token = arg
        elif opt in ("-upd", "--upd_interval"):
            arg_upd = arg
        elif opt in ("-h", "--home_id"):
            arg_home = arg
        elif opt in ("-r1", "--relay_1"):
            arg_relay_1 = arg
        elif opt in ("-r2", "--relay_2"):
            arg_relay_2 = arg
        elif opt in ("-p", "--port"):
            arg_port = arg
        elif opt in "--min_temp":
            arg_min_temp = arg
        elif opt in "--max_temp":
            arg_max_temp = arg

    if arg_api_token == "":
        print("Please enter a valid Tibber API token with -api (--api_token)")
        sys.exit(2)
    elif arg_relay_1 == "":
        print("Please enter a valid IPv4 address with -r1 (--relay_1)")
        sys.exit(2)
    elif arg_relay_2 == "":
        print("Please enter a valid IPv4 address with -r2 (--relay_2)")
        sys.exit(2)


# IP Shelly devices
cShelly_Relay1 = ShellyPy.Shelly(arg_relay_1)
cShelly_Relay2 = ShellyPy.Shelly(arg_relay_2)

cInterval = 10

# Declare variables
rActTemp = 20.0
tibberUpToDate = False
run = True



class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global rActTemp
        temp = self.path.rsplit("=")
        if temp[0] == "/t":
            rActTemp = float(temp[1])


def handler_stop_signals(signum, frame):
    global run
    run = False


def stringLevelToInt(string):
    if string == "VERY_CHEAP":
        return 1
    elif string == "CHEAP":
        return 2
    elif string == "NORMAL":
        return 3
    elif string == "EXPENSIVE":
        return 4
    elif string == "VERY_EXPENSIVE":
        return 5
    else:
        return 0


def getTibberData():
    global home
    global tibberUpToDate

    while run:
        try:
            # Get Tibber data
            tibberAccount = tibber.Account(arg_api_token)
            home = tibberAccount.homes[arg_home]
        except:
            print("Tibber: Connection error")
            tibberUpToDate = False
        else:
            tibberUpToDate = True
        time.sleep(arg_upd)


def main():
    iCurrentLevel = 0
    iNextHourLevel = 0
    sCurrentHour = "NaN"
    sNextHour = "NaN"

    while run:
        if tibberUpToDate:
            sCurrentHour = home.current_subscription.price_info.current.starts_at
            iCurrentLevel = stringLevelToInt(home.current_subscription.price_info.current.level)

            for i in range(len(home.current_subscription.price_info.today)):
                if home.current_subscription.price_info.current.starts_at == home.current_subscription.price_info.today[i].starts_at:
                    if i < len(home.current_subscription.price_info.today) - 1:
                        iNextHourLevel = stringLevelToInt(home.current_subscription.price_info.today[i + 1].level)
                        sNextHour = home.current_subscription.price_info.today[i + 1].starts_at
                    else:
                        iNextHourLevel = stringLevelToInt(home.current_subscription.price_info.tomorrow[0].level)
                        sNextHour = home.current_subscription.price_info.tomorrow[0].starts_at
                    break

        q = logic.main(iCurrentLevel, iNextHourLevel, rActTemp, arg_min_temp, arg_max_temp)

        print(f"Current temperature = {rActTemp}")
        print(f"Current level = {iCurrentLevel} @ {sCurrentHour}")
        print(f"Next level = {iNextHourLevel} @ {sNextHour}")
        print(f"Q0 = {q[0]}")
        print(f"Q1 = {q[1]}")

        try:
            cShelly_Relay1.relay(0, turn=q[0])
            cShelly_Relay2.relay(0, turn=q[1])
        except:
            print("Unable to send data to relays")

        time.sleep(cInterval)


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

if __name__ == "__main__":
    get_arg(sys.argv)

# Declare threads
t1_tibber = Thread(target=getTibberData)
t2_main = Thread(target=main)

try:
    t1_tibber.start()
    t2_main.start()
except:
    print("Unable to start threads")

httpd = HTTPServer(('', arg_port), SimpleHTTPRequestHandler)
httpd.serve_forever()

