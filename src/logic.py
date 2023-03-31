

def main(current_level, next_level, actTemp, minTemp, maxTemp):

    if current_level == 1:
        # Normal operation
        Q0 = False
        Q1 = False
    elif current_level == 2:
        # DHW temp increased
        Q0 = True
        Q1 = False
    elif current_level == 4 or current_level == 5 and actTemp >= minTemp:
        # Turn off heating
        Q0 = False
        Q1 = True
    elif (current_level == 1 and next_level != 1) or \
            (current_level == 3 and (next_level != 4 or 5)) and actTemp <= maxTemp:
        # Heat to max temperature
        Q0 = True
        Q1 = True
    else:
        Q0 = False
        Q1 = False

    output = Q0, Q1

    return output
