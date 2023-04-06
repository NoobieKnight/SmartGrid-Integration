from threading import Thread
import signal
import time
import tibber
import ShellyPy
from http.server import HTTPServer, BaseHTTPRequestHandler
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
priceArrayToday = []


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global rActTemp
        temp = self.path.rsplit("=")
        if temp[0] == "/t":
            rActTemp = float(temp[1])


def handler_stop_signals(signum, frame):
    global run
    run = False


def getTibberData():
    global home
    global tibberUpToDate
    global priceArrayToday
    while run:
        try:
            # Get Tibber data
            tibberAccount = tibber.Account(args.api_token)
            home = tibberAccount.homes[args.home_id]
        except:
            print("Tibber: Connection error")
            tibberUpToDate = False
        else:
            # Declare lists
            priceArrayToday = []
            priceArrayToday_AM = []
            priceArrayToday_PM = []

            # Copy data from Tibber
            for i in range(len(home.current_subscription.price_info.today)):

                # Copy to standard list
                priceArrayToday.append(1)

                # Copy to list for before midday
                if i < 12:
                    priceArrayToday_AM.append([0.0, 0])
                    priceArrayToday_AM[i][0] = home.current_subscription.price_info.today[i].total
                    priceArrayToday_AM[i][1] = i

                # Copy to list for after midday
                else:
                    priceArrayToday_PM.append([0.0, 0])
                    priceArrayToday_PM[i - 12][0] = home.current_subscription.price_info.today[i].total
                    priceArrayToday_PM[i - 12][1] = i

            # Sort the lists according to price (Descending)
            priceArrayToday_AM.sort(reverse=True, key=lambda l: l[0])
            priceArrayToday_PM.sort(reverse=True, key=lambda l: l[0])

            # Turn off heatpump for the 3 most expensive hours in both before and after midday
            for i in range(3):
                # Most expensive, Turn heatpump off
                priceArrayToday[priceArrayToday_AM[i][1]] = 0
                priceArrayToday[priceArrayToday_PM[i][1]] = 0
                # Cheapest, Turn heatpump on
                priceArrayToday[priceArrayToday_AM[len(priceArrayToday_AM) - i - 1][1]] = 3
                priceArrayToday[priceArrayToday_PM[len(priceArrayToday_PM) - i - 1][1]] = 3

            tibberUpToDate = True
        time.sleep(args.upd_interval)


def main():
    iCurrentState = 1
    iNextHourState = 1
    sCurrentHour = "NaN"
    sNextHour = "NaN"
    rActTemp_last = rActTemp
    iCurrentState_last = iCurrentState
    iNextHourState_last = iNextHourState
    q = [False, False]

    while run:
        if tibberUpToDate:
            sCurrentHour = home.current_subscription.price_info.current.starts_at
            # Loop list until current hour found in array
            for i in range(len(home.current_subscription.price_info.today)):
                if home.current_subscription.price_info.current.starts_at == home.current_subscription.price_info.today[i].starts_at:
                    iCurrentState = priceArrayToday[i]
                    try:
                      iNextHourState = priceArrayToday[i + 1]
                      sNextHour = home.current_subscription.price_info.today[i + 1].starts_at
                    except:
                      pass
                    break
        else:
            iCurrentState = 1

        if iCurrentState == 0 and rActTemp >= args.min_temp:
            # Turn off heating
            q[0] = False
            q[1] = True
        elif iCurrentState == 1:
            # Normal operation
            q[0] = False
            q[1] = False
        elif iCurrentState == 2:
            # DHW temp increased
            q[0] = True
            q[1] = False
        elif iCurrentState == 3 and rActTemp <= args.max_temp:
            # Heat to max temperature
            q[0] = True
            q[1] = True
        else:
            q[0] = False
            q[1] = False

        if rActTemp != rActTemp_last or iCurrentState != iCurrentState_last or iNextHourState != iNextHourState_last:
            print(f"Current temperature = {rActTemp}")
            print(f"Current state = {iCurrentState} @ {sCurrentHour}")
            print(f"Next state = {iNextHourState} @ {sNextHour}")
            print(f"Q0 = {q[0]}")
            print(f"Q1 = {q[1]}")
            try:
                cShelly_Relay1.relay(0, turn=q[0])
                cShelly_Relay2.relay(0, turn=q[1])
            except:
                print("Unable to send data to relays")

        rActTemp_last = rActTemp
        iCurrentState_last = iCurrentState
        iNextHourState_last = iNextHourState


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

