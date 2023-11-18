# SmartGrid-Integration

This Python script controls two shelly relays to integrate smart grid integration in to compatible heat pumps

This is the first thing I've done in python, so it's quite rough

# Things needed

* 2 Shelly relays
* 1 Shelly plus H/T (optional)
  Or other smart temperature sensor. Temperature is used to make sure that temperature does not go below or higher then specified temperature.
  

# Installation

I run the script in a docker container on my unraid server, but it's also possible to run on real hardware or vm

Update actual temperature by sending a GET request to < IP >:< PORT >/t=<temperature>

This can be done by setting up a webhook in a shelly plus H/T.
  http://< IP >:< PORT >/t=$temperature
  

My steps (probably not the most efficant/best)
1. docker build -t heatpump_smartgrid https://github.com/NoobieKnight/SmartGrid-Integration.git
2. docker images (To figure out the image id)
3. docker run -d --name=heatpump_smartgrid --net=bridge -p 5000:5000 <image id from previus step> \
                 --area "< Price area >" \
                 --relay_1 "< Shelly relay 1 IP >" \
                 --relay_2 "< Shelly relay 2 IP >" \
                 --highPrice < 0.8 >

Arguments available:

--area

Price area SE1=North Sweden, SE2=North middle Sweden, SE3=South middle Sweden, SE4=South Sweden"
  
  
--relay_1

IP for Shelly relay 1
  
  
--relay_2

IP for Shelly relay 2
  
  
--min_temp

Lowest temperature to allow no production (Default = 18.0)
  
  
--max_temp

Maximum temperature to allow for extra production (Default = 22.0)
  
  
--port

Port for webhook server (Default = 5000)
  
  
--highPrice

The price has to be higher than this to stop heatpump for more than just the most expensive hour in AM and PM (Before taxes (Default = 0.0))


--hours

Number of hours to turn off and on heatpump 2 = Decrease setpoint 2 hours AM and 2 hours PM Increase setpoint 2 hours AM and 2 hours PM

  
--TZ

Timezone as TZ identifier (Default = Europe/Stockholm)
