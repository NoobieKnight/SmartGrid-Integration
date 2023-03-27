
import tibber
import time
import signal


rActTemp = 18.0
run = True


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


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

iWaitTime = 0
while run:
    if iWaitTime <= 0:
        account = tibber.Account("xdZ5baalsmyHerIU629KPR_dMfuewosNllYTzhCq8E8")
        home = account.homes[0]

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
        if iCurrentLevel == 1:
            # Normal operation
            Q0 = False
            Q1 = False
        elif iCurrentLevel == 2:
            # DHW temp increased
            Q0 = True
            Q1 = False
        elif iCurrentLevel == 4 or iCurrentLevel == 5 and rActTemp >= 18.0:
            # Turn off heating
            Q0 = False
            Q1 = True
        elif (iCurrentLevel == 1 and iNextHourLevel != 1) or \
                (iCurrentLevel == 3 and (iNextHourLevel != 4 or 5)) and rActTemp <= 22.0:
            # Heat to max temperature
            Q0 = True
            Q1 = True
        else:
            Q0 = False
            Q1 = False

        # print(f"Current level = {sCurrentLevel}")
        # print(f"Next level = {sNextHourLevel}")
        print(f"Q0 = {Q0}")
        print(f"Q1 = {Q1}")

        iWaitTime = 10
    time.sleep(1)
    iWaitTime -= 1
    print(iWaitTime)
