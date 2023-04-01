# SmartGrid-Integration

This Python script controls two shelly relays to integrate smart grid integration in to compatible heat pumps, with the help of the Tibber API

# Things needed

* A Tibber subscription
* 2 Shelly one
* 1 Shelly plus H/T (optional)
  Or other smart temperature sensor. Temperature is used to make sure that temperature does not go below or higher then specified temperature.
  

# Installation

I run the script in a docker container on my unraid server, but it's also possible to run on real hardware or vm

Update actual temperature by sending a GET request to [IP]:[PORT]/t=[temperature]
This can be done by setting up a webhook in a shelly plus H/T
  

My steps (probably not the most efficant/best)
1. docker build -t tibber_smartgrid https://github.com/NoobieKnight/SmartGrid-Integration.git
2. docker images (To figure out the image id)
3. docker run -d --name=tibber_smartgrid --net=bridge -p 5000:5000 [image id from previus step] \
                 --api_token "[API token for Tibber]" \
                 --relay_1 "[Shelly relay 1 IP]" \
                 --relay_2 "[Shelly relay 2 IP]"

Arguments avalible:
--api_token

Tibber API token
  
  
--relay_1

IP for Shelly relay 1
  
  
--relay_2

IP for Shelly relay 2
  
  
--home_id

Home ID from Tibber (Default = 0) Use this if you have multiple houses with Tibber subscription
  
  
--min_temp

Lowest temperature to allow no production (Default = 18.0)
  
  
--max_temp

Maximum temperature to allow for extra production (Default = 22.0)
  
  
--port

Port for webhook server (Default = 5000)
  
  
--upd_interval

Update interval for Tibber (Default = 120)
  
