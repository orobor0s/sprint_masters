import json
import requests
import urllib.parse

def getIPData():
    '''Fetch the client's IP data'''

    # Need a User-Agent header in the request to circumvent rate limiting
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    replydata = requests.get("https://ipapi.co/json/", headers=headers)
    json_data = replydata.json()
    json_status = replydata.status_code

    if json_status == 200:
        return json_data

def wrapLon(lon):
    '''Wrap longitude to support bboxes that cross the international date line'''
    return ((lon + 180) % 360) - 180

def getEONETData(scale=10):
    '''Fetch EONET event data based on the client's location and customized parameters'''

    # Calculate coordinate pair to bound bbox
    lon, lat = clientData["longitude"], clientData["latitude"]
    min_lon, max_lon = wrapLon(lon - scale), wrapLon(lon + scale)
    min_lat, max_lat = max(-90, lat - scale), min(90, lat + scale)
    bbox = ",".join(map(str, [min_lon, max_lat, max_lon, min_lat]))

    # Generate API query
    params = {"bbox":bbox}
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe=",")
    url = f"https://eonet.gsfc.nasa.gov/api/v3/events?{query_string}"
    
    replydata = requests.get(url)
    json_data = replydata.json()
    json_status = replydata.status_code

    if json_status == 200:
       return json_data
    else:
        print("Error message: " + json_data["message"])

clientData = getIPData()
if clientData != None:
    print(json.dumps(getEONETData(), indent=4))

# route_url = "https://graphhopper.com/api/1/route?"
# key = "9b36e834-2f7d-494e-bc6c-bee36b11090e"
# 
# def geocoding(location, key):
#     while location == "":
#         location = input("Enter the location again: ")
#     geocode_url = "https://graphhopper.com/api/1/geocode?"
#     url = geocode_url + urllib.parse.urlencode({"q":location, "limit": "1", "key":key})
# 
#     replydata = requests.get(url)
#     json_data = replydata.json()
#     json_status = replydata.status_code
# 
#     if json_status == 200 and len(json_data["hits"]) != 0:
#         json_data = requests.get(url).json()
#         lat = json_data["hits"][0]["point"]["lat"]
#         lng = json_data["hits"][0]["point"]["lng"]
#         name = json_data["hits"][0]["name"]
#         value = json_data["hits"][0]["osm_value"]
#         
#         if "country" in json_data["hits"][0]:
#             country = json_data["hits"][0]["country"]
#         else:
#             country = ""
# 
#         if "state" in json_data["hits"][0]:
#             state = json_data["hits"][0]["state"]
#         else:
#             state = ""
# 
#         if len(state) != 0 and len(country) != 0:
#             new_loc = name + ", " + state + ", " + country
#         elif len(state) != 0:
#             new_loc = name + ", " + country
#         else:
#             new_loc = name
# 
#         print("Geocoding API URL for " + new_loc + " (Location Type: " + value + ")\n" + url)
#     else:
#         lat = "null"
#         lng = "null"
#         new_loc = location
#         if json_status != 200:
#             print("Geocode API status: " + str(json_status) + "\nError message: " + json_data["message"])
#     return json_status,lat,lng,new_loc
# 
# while True:
#     print("\n+++++++++++++++++++++++++++++++++++++++++++++")
#     print("Vehicle profiles available on Graphhopper:")
#     print("+++++++++++++++++++++++++++++++++++++++++++++")
#     print("car, bike, foot")
#     print("+++++++++++++++++++++++++++++++++++++++++++++")
#     profile=["car", "bike", "foot"]
#     vehicle = input("Enter a vehicle profile from the list above: ")
#     if vehicle == "quit" or vehicle == "q":
#         break
#     elif vehicle in profile:
#         vehicle = vehicle
#     else:
#         vehicle = "car"
#         print("No valid vehicle profile was entered. Using the car profile.")
#     loc1 = input("Starting Location: ")
#     if loc1 == "quit" or loc1 == "q":
#         break
#     orig = geocoding(loc1,key)
#     loc2 = input("Destination: ")
#     if loc2 == "quit" or loc2 == "q":
#         break
#     dest = geocoding(loc2,key)
#     print("=================================================")
#     if orig[0] == 200 and dest[0] == 200:
#         op="&point="+str(orig[1])+"%2C"+str(orig[2])
#         dp="&point="+str(dest[1])+"%2C"+str(dest[2])
#         paths_url = route_url + urllib.parse.urlencode({"key":key, "vehicle":vehicle}) + op + dp
#         paths_status = requests.get(paths_url).status_code
#         paths_data = requests.get(paths_url).json()
#         print("Routing API Status: " + str(paths_status) + "\nRouting API URL:\n" + paths_url)
#         print("=================================================")
#         print("Directions from " + orig[3] + " to " + dest[3] + " by " + vehicle)
#         print("=================================================")
#         if paths_status == 200:
#             miles = (paths_data["paths"][0]["distance"])/1000/1.61
#             km = (paths_data["paths"][0]["distance"])/1000
#             sec = int(paths_data["paths"][0]["time"]/1000%60)
#             min = int(paths_data["paths"][0]["time"]/1000/60%60)
#             hr = int(paths_data["paths"][0]["time"]/1000/60/60)
#             print("Distance Traveled: {0:.1f} miles / {1:.1f} km".format(miles, km))
#             print("Trip Duration: {0:02d}:{1:02d}:{2:02d}".format(hr, min, sec))
#             print("=================================================")
#             for each in range(len(paths_data["paths"][0]["instructions"])):
#                 path = paths_data["paths"][0]["instructions"][each]["text"]
#                 distance = paths_data["paths"][0]["instructions"][each]["distance"]
#                 print("{0} ( {1:.1f} km / {2:.1f} miles )".format(path, distance/1000, distance/1000/1.61))
#             print("=================================================")
#         else:
#             print("Error message: " + paths_data["message"])
#             print("*************************************************")
# 