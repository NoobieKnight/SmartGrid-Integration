from threading import Thread
import signal
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse
import requests
import os


# Initialize parser
parser = argparse.ArgumentParser()

# Adding optional argument
parser.add_argument("--area", type=str, required=True, help="Price area (SE1=North Sweden,"
                                                            "SE2=North middle Sweden,"
                                                            "SE3=South middle Sweden,"
                                                            "SE3=South Sweden")
parser.add_argument("--relay_1", type=str, required=True, help="IP for Shelly relay 1")
parser.add_argument("--relay_2", type=str, required=True, help="IP for Shelly relay 2")
parser.add_argument("--min_temp", type=float, default=18.0,
                    help="Lowest temperature to allow no production (Default = 18.0)")
parser.add_argument("--max_temp", type=float, default=22.0,
                    help="Maximum temperature to allow for extra production (Default = 22.0)")
parser.add_argument("--port", type=int, default=5000, help="Port for webhook server (Default = 5000)")
parser.add_argument("--highPrice", type=float, default=0.0, help="The price has to be higher than this to stop heatpump for more than just the most expensive hour in AM and PM"
                                                               "(Before taxes (Default = 0.0))")
parser.add_argument("--hours", type=int, default=3, help="Number of hours to turn off and on heatpump"
                                                         "2 = Decrease setpoint 2 hours AM and 2 hours PM"
                                                         "Increase setpoint 2 hours AM and 2 hours PM)")

args = parser.parse_args()

cInterval = 10

# Declare variables
rActTemp = 20.0
priceUpToDate = False
run = True
priceArrayToday = []

os.environ['TZ'] = 'Europe/Stockholm'
time.tzset()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global rActTemp
        temp = self.path.rsplit("=")
        if temp[0] == "/t":
            rActTemp = float(temp[1])


def handler_stop_signals(signum, frame):
    global run
    run = False


def sendShellyCommand(ip, state):
    try:
        if state:
            url = 'http://' + ip + '/relay/0?turn=on'
        else:
            url = 'http://' + ip + '/relay/0?turn=off'
        response = requests.get(url)
        result = True
    except:
        result = False
    return result


def getPriceData():
    global priceUpToDate
    global priceArrayToday
    try:
            urlCurrentDay = time.strftime('%Y/%m-%d', time.localtime())

            url = 'https://www.elprisetjustnu.se/api/v1/prices/' + urlCurrentDay + '_' + args.area + '.json'
            response = requests.get(url)

            # Declare lists
            priceArrayToday = []
            priceArrayToday_AM = []
            priceArrayToday_PM = []

            # Copy data from price data
            for i in range(len(response.json())):

                # Copy to standard list
                priceArrayToday.append([response.json()[i]['time_start'], 1])

                # Copy to list for before midday
                if i < 12:
                    priceArrayToday_AM.append([0.0, 0])
                    priceArrayToday_AM[i][0] = response.json()[i]['SEK_per_kWh']
                    priceArrayToday_AM[i][1] = i

                # Copy to list for after midday
                else:
                    priceArrayToday_PM.append([0.0, 0])
                    priceArrayToday_PM[i - 12][0] = response.json()[i]['SEK_per_kWh']
                    priceArrayToday_PM[i - 12][1] = i

            # Sort the lists according to price (Descending)
            priceArrayToday_AM.sort(reverse=True, key=lambda l: l[0])
            priceArrayToday_PM.sort(reverse=True, key=lambda l: l[0])

            # Turn off heatpump for the x most expensive hours in both before and after midday
            for i in range(args.hours):
                # Most expensive, Turn heatpump off
                if priceArrayToday_AM[i][0] > args.highPrice or i == 0:
                    priceArrayToday[priceArrayToday_AM[i][1]][1] = 0
                if priceArrayToday_PM[i][0] > args.highPrice or i == 0:
                    priceArrayToday[priceArrayToday_PM[i][1]][1] = 0
                # Cheapest, Turn heatpump on
                priceArrayToday[priceArrayToday_AM[len(priceArrayToday_AM) - i - 1][1]][1] = 3
                priceArrayToday[priceArrayToday_PM[len(priceArrayToday_PM) - i - 1][1]][1] = 3

            priceUpToDate = True

    except:
        print("Price data: Connection error")
        priceUpToDate = False


def main():
    global priceUpToDate

    iCurrentState = 1
    rActTemp_last = rActTemp
    iCurrentState_last = iCurrentState
    sCurrentHour_last = 'NaN'
    q = [False, False]

    while run:

        if not priceUpToDate:
            getPriceData()

        tempCurrentHour = time.strftime('%Y-%m-%dT%H:00:00%z', time.localtime())
        sCurrentHour = tempCurrentHour[:22] + ':' + tempCurrentHour[22:]
        if priceUpToDate:
            try:
                # Loop list until current hour found in array
                for i in range(len(priceArrayToday)):
                    if priceArrayToday[i][0] == sCurrentHour:
                        iCurrentState = priceArrayToday[i][1]

                        break
                if i > len(priceArrayToday):
                    priceUpToDate = False
            except:
                priceUpToDate = False
        else:
            sCurrentHour = 'NaN'
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

        if rActTemp != rActTemp_last or iCurrentState != iCurrentState_last or sCurrentHour != sCurrentHour_last:
            print(f"Current temperature = {rActTemp}")
            print(f"Current state = {iCurrentState} @ {sCurrentHour}")
            print(f"Q0 = {q[0]} Q1 = {q[1]}")

            retval = sendShellyCommand(args.relay_1, q[0])
            if not retval:
                print('Failed to send data to relay 1')
            else:
                retval = sendShellyCommand(args.relay_2, q[1])
                if not retval:
                    print('Failed to send data to relay 2')

        rActTemp_last = rActTemp
        iCurrentState_last = iCurrentState
        sCurrentHour_last = sCurrentHour

        time.sleep(cInterval)


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

# Declare threads
t1_main = Thread(target=main)

try:
    # Start threads
    t1_main.start()
    try:
        # Start http server
        httpd = HTTPServer(('', args.port), SimpleHTTPRequestHandler)
        httpd.serve_forever()
    except:
        print("Unable to start http server")
except:
    print("Unable to start threads")
