
import tibber

account = tibber.Account("xdZ5baalsmyHerIU629KPR_dMfuewosNllYTzhCq8E8")
home = account.homes[0]

sCurrentHour = home.current_subscription.price_info.current.starts_at
sCurrentLevel = home.current_subscription.price_info.current.level

for i in range(len(home.current_subscription.price_info.today)):
    if home.current_subscription.price_info.current.starts_at == home.current_subscription.price_info.today[i].starts_at :
        if i < len(home.current_subscription.price_info.today) - 1:
            sNextHourLevel = home.current_subscription.price_info.today[i + 1].level
            sNextHour = home.current_subscription.price_info.today[i + 1].starts_at
        else:
            sNextHourLevel = home.current_subscription.price_info.tomorrow[0].level
            sNextHour = home.current_subscription.price_info.tomorrow[0].starts_at
        break

print(len(home.current_subscription.price_info.today))

if sCurrentLevel == "NORMAL":
    # Normal operation
    Q0 = False
    Q1 = False
elif sCurrentLevel == "CHEAP":
    # DHW temp increased
    Q0 = True
    Q1 = False
elif sCurrentLevel == "EXPENSIVE" or sCurrentLevel == "VERY_EXPENSIVE":
    # Turn off heating
    Q0 = False
    Q1 = True
elif (sCurrentLevel == "VERY_CHEAP" and sNextHourLevel != "VERY_CHEAP") or \
        (sCurrentLevel == "NORMAL" and (sNextHourLevel != "EXPENSIVE" or "VERY_EXPENSIVE")):
    # Heat to max temperature
    Q0 = True
    Q1 = True
else:
    Q0 = False
    Q1 = False

print(f"Current level = {sCurrentLevel}")
print(f"Next level = {sNextHourLevel}")


print(f"Q0 = {Q0}")
print(f"Q1 = {Q1}")
