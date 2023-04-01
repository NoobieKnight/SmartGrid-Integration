from threading import Thread
import signal
import time
import tibber
import ShellyPy
from http.server import HTTPServer, BaseHTTPRequestHandler
import logic
import argparse


# Initialize parser
parser = argparse.ArgumentParser()

# Adding optional argument
parser.add_argument("--api_token", type=str, required=True, help = "Tibber API token")
parser.add_argument("--relay_1", type=str, required=True, help = "IP for Shelly relay 1")
parser.add_argument("--relay_2", type=str, required=True, help = "IP for Shelly relay 2")
parser.add_argument("--home_id", type=int, default=0, help = "Home ID from Tibber (Default = 0)")
parser.add_argument("--min_temp", type=float, default=18.0,
                    help = "Lowest temperature to allow no production (Default = 18.0)")
parser.add_argument("--max_temp", type=float, default=22.0,
                    help = "Maximum temperature to allow for extra production (Default = 22.0)")
parser.add_argument("--port", type=int, default=5000, help = "Port for webhook server (Default = 5000)")
parser.add_argument("--upd_interval", type=int, default=120, help = "Update interval for Tibber (Default = 120)")

args = parser.parse_args()

# IP Shelly devices
cShelly_Relay1 = ShellyPy.Shelly(args.relay_1)
cShelly_Relay2 = ShellyPy.Shelly(args.relay_2)

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
            tibberAccount = tibber.Account(args.api_token)
            home = tibberAccount.homes[args.home_id]
        except:
            print("Tibber: Connection error")
            tibberUpToDate = False
        else:
            tibberUpToDate = True
        time.sleep(args.upd_interval)


def main():
    iCurrentLevel = 0
    iNextHourLevel = 0
    sCurrentHour = "NaN"
    sNextHour = "NaN"
    rActTemp_last = rActTemp
    iCurrentLevel_last = iCurrentLevel
    iNextHourLevel_last = iNextHourLevel

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

        q = logic.main(iCurrentLevel, iNextHourLevel, rActTemp, args.min_temp, args.max_temp)

        if rActTemp != rActTemp_last or iCurrentLevel != iCurrentLevel_last or iNextHourLevel != iNextHourLevel_last
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

        rActTemp_last = rActTemp
        iCurrentLevel_last = iCurrentLevel
        iNextHourLevel_last = iNextHourLevel


        time.sleep(cInterval)


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

# Declare threads
t1_tibber = Thread(target=getTibberData)
t2_main = Thread(target=main)

try:
    t1_tibber.start()
    t2_main.start()
except:
    print("Unable to start threads")

httpd = HTTPServer(('', args.port), SimpleHTTPRequestHandler)
httpd.serve_forever()

