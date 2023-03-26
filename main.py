
import tibber

import ntp


tCurrentHour = ntp.getNTPTime("pool.ntp.org",+1)
tNextHour = ntp.getNTPTime("pool.ntp.org",+2)


account = tibber.Account("xdZ5baalsmyHerIU629KPR_dMfuewosNllYTzhCq8E8")
home = account.homes[0]

print(len(home.current_subscription.price_info.today))
sCurrentPriceLevel = home.current_subscription.price_info.current.level
# sNextHourPriceLevel =

if sCurrentPriceLevel == "NORMAL":
    Q0 = False
    Q1 = False
elif sCurrentPriceLevel == "CHEAP":
    Q0 = True
    Q1 = False
elif sCurrentPriceLevel == "VERY_CHEAP":
    Q0 = True
    Q1 = True
elif sCurrentPriceLevel == "EXPENSIVE":
    Q0 = False
    Q1 = True
elif sCurrentPriceLevel == "VERY_EXPENSIVE":
    Q0 = False
    Q1 = True
else:
    Q0 = False
    Q1 = False

print(f"Curent level = {sCurrentPriceLevel}")
# print(f"Next level = {sNextHourPriceLevel}")


print(f"Q0 = {Q0}")
print(f"Q1 = {Q1}")
