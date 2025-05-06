from datetime import datetime, timedelta
import folium
from folium.plugins import Fullscreen
import json
import math
import requests
import streamlit as st
from streamlit_javascript import st_javascript
from streamlit.components.v1 import html
import urllib.parse


# Variables
ipapi_url = "https://ipapi.co"
eonet_source_url = "https://eonet.gsfc.nasa.gov/api/v3/sources"
eonet_categories_url = "https://eonet.gsfc.nasa.gov/api/v3/categories"
eonet_query_url = "https://eonet.gsfc.nasa.gov/api/v3/events/geojson?"
default_start_date = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
default_end_date = datetime.today().strftime('%Y-%m-%d')
submitted = ""
query_url = ""
global_errors = []

# Mapping for category titles
category_icons = {
    "Wildfires": {"icon": "fire", "color": "red"},
    "Severe Storms": {"icon": "bolt", "color": "orange"},
    "Volcanoes": {"icon": "warning", "color": "darkred"},
    "Floods": {"icon": "tint", "color": "blue"},
    "Earthquakes": {"icon": "globe", "color": "green"},
    "Sea and Lake Ice": {"icon": "snowflake", "color": "lightblue"},
    "Snow": {"icon": "snowflake", "color": "lightgrey"},
    "Temperature Extremes": {"icon": "thermometer-three-quarters", "color": "yellow"},
    "Drought": {"icon": "sun", "color": "brown"},
    "Dust and Haze": {"icon": "cloud", "color": "grey"},
    "Manmade": {"icon": "cog", "color": "purple"},
    "Landslides": {"icon": "hill-rockslide", "color": "brown"},
    "Water Color": {"icon": "water", "color": "green"}
}

#Added some styling
category_labels = {
    "wildfires": "Wildfires 🔥 — Fires in forests, grasslands",
    "severeStorms": "Severe Storms ⛈️ — Hurricanes, cyclones, thunderstorms",
    "volcanoes": "Volcanoes 🌋 — Volcanic eruptions",
    "floods": "Floods 🌊 — Overflow of water onto land",
    "earthquakes": "Earthquakes 🌎 — Sudden ground shaking",
    "seaLakeIce": "Sea and Lake Ice ❄️ — Ice formation and melting",
    "snow": "Snow ❄️ — Heavy snowfall events",
    "temperatureExtremes": "Temperature Extremes ♨️ — Heatwaves or cold spells",
    "drought": "Drought ☀️ — Prolonged dry periods",
    "dustHaze": "Dust and Haze 🌫️ — Reduced visibility events",
    "manmade": "Manmade Events ⚙️ — Human-caused incidents",
    "landslides": "Landslides 🗻 — Landslides, mudslides, avalanches",
    "waterColor": "Water Color 💧 — Alteration of appearance of water"
}


# Utility
def is_float(n):
    '''Check if string is float'''
    try:
        float(n)
        return True
    except ValueError:
        return False

def is_valid_date(date_str):
    '''Determines if a date is valid'''
    try:
        datetime.strptime(date_str, "%Y-%m-%d")  # Attempt to parse
        return True
    except ValueError:
        return False

def wrap_lon(lon):
    '''Wraps longitude to support a bbox that crosses the international date line'''
    return ((lon + 180) % 360) - 180

def calc_bbox(scale):
    '''Calculates coordinate pair to bound bbox based on the client's location and scale setting'''
    lon, lat = client_data["longitude"], client_data["latitude"]
    min_lon, max_lon = wrap_lon(float(lon) - scale), wrap_lon(float(lon) + scale)
    min_lat, max_lat = max(-90, float(lat) - scale), min(90, float(lat) + scale)
    return ",".join(map(str, [min_lon, max_lat, max_lon, min_lat]))

def calc_bbox_corners(bbox_string):
    '''Calculates the four corners of bbox'''
    bbox_list = list(map(float, bbox_string.split(",")))
    min_lon, max_lat, max_lon, min_lat = bbox_list[0], bbox_list[1], bbox_list[2], bbox_list[3]
    upper_left = (max_lat, min_lon)
    upper_right = (max_lat, max_lon)
    lower_left = (min_lat, min_lon)
    lower_right = (min_lat, max_lon)
    return [upper_left, upper_right, lower_right, lower_left, upper_left]

def haversine_distance(coord1, coord2):
    '''
    Calculate the great-circle distance between two points on the Earth using the Haversine formula.

    Parameters:
        coord1: tuple of float (lat1, lon1) in decimal degrees
        coord2: tuple of float (lat2, lon2) in decimal degrees

    Returns:
        Distance in kilometers (float)
    '''
    # Radius of the Earth in kilometers
    R = 6371.0

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Convert latitude and longitude from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in kilometers
    distance = R * c
    return distance

def filter_linstring(event):
    '''Filters LineString geometry type events'''
    return event["geometry"]["type"] != "LineString"

# Input sanitization
def sanitize_list_input(input,keyword):
    '''Sanitize item and category inputs'''
    if input:
        valid = []
        errors = []
        if keyword == "sources":
            key = "source"
        else:
            key = "category"
        input_check = input.split(',')
        check = globals().get(keyword, "Variable not found")
        for item in input_check:
            if item in check:
                valid.append(item)
            else:
                errors.append(item)
        if errors:
                global_errors.append(f"{keyword} input errors: {errors}, {keyword} must be in {check.keys()}")
        if valid:
            return {key: ",".join(valid)}
        else:
            return {}
    else:
        return {}

def sanitize_status(status):
    '''Sanitize status input'''
    if status:
        if status in {"open", "closed", "all"}:
            return {"status": status}
        global_errors.append(f"Status input error: {status}, status must be open, closed, or all (leaving status blank defaults to open)")
    return {}

def sanitize_limit(limit):
    '''Sanitize limit input'''
    if limit:
        if limit > 0 and int(limit):
            return {"limit": limit}
        global_errors.append(f"Limit input error: {limit}, limit must be a positive integer")
    return {}

def sanitize_date_range(start, end):
    '''Sanitize date range input'''
    if is_valid_date(start) and is_valid_date(end) and end >= start:
        return {"start": start, "end": end}
    global_errors.append(f"Date range input error: {start} - {end}, each date must be in the YYYY-MM-DD format and the start date must be before or equal to the end date")
    return {}
    
def sanitize_scale(scale):
    '''Sanitize scale input'''
    if scale:
        if is_float(scale) and float(scale) >= 0:
            return {"bbox": calc_bbox(scale)}
        global_errors.append(f"Scale input error: {scale}, scale must be a float or integer that is greater than or equal to 0")
    return {}


# EONET enabling infrastructure
def generate_eonet_dictionaries(url,keyword):
    '''Generates a dictionary that contains eonet sources or categories'''
    eonet_data = get_eonet_data(url)[keyword]
    data = {}
    for item in eonet_data:
        item_id = item["id"]
        del item["id"]
        data[item_id] = item
    return data

@st.cache_data
def generate_eonet_query(
        source="",
        category="",
        status="",
        limit="",
        start=default_start_date,
        end=default_end_date,
        scale=10):
    '''Generates EONET query url based on sanitized user input'''
    # Set parameters
    params = {}
    params.update(sanitize_list_input(source,"sources"))
    params.update(sanitize_list_input(category,"categories"))
    params.update(sanitize_status(status))
    params.update(sanitize_limit(limit))
    params.update(sanitize_date_range(start, end))
    params.update(sanitize_scale(scale))
    
    # Generate API query
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe=",")
    return f"{eonet_query_url}{query_string}"


# API queries
@st.cache_data
def get_ip_data(client_ip):
    '''Gets the client's IP data'''
    # Needs a User-Agent header in the request to circumvent rate limiting
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    reply_data = requests.get(f"{ipapi_url}/{client_ip}/json", headers=headers)
    if str(reply_data) == "<Response [200]>":
        json_data = reply_data.json()
        json_status = reply_data.status_code

        if json_status == 200:
            return json_data
    else:
        st.error("ipapi API request failed.")

@st.cache_data
def get_eonet_data(url):
    '''Gets EONET event data based on the client's location and customized parameters'''
    reply_data = requests.get(url)
    json_data = reply_data.json()
    json_status = reply_data.status_code

    if json_status == 200:
       return json_data
    else:
        print("Error message: " + json_data["message"])


# Augment data
@st.cache_data
def augment_data(data):
    '''Adds distance from user to point data'''
    client_location = (client_data["latitude"],client_data["longitude"])
    for event in data:
        geometry_type = event["geometry"]["type"]
        coordinates = event["geometry"]["coordinates"]
        if geometry_type == "Point":
            event_location = coordinates[1], coordinates[0]
            distance = haversine_distance(client_location, event_location)
            event["properties"]["distance"] = distance
        
    return data


# Generate map
@st.cache_resource
def generate_folium_map(data,show_bbox):
    '''Generates the folium map centered on the client's location and including events from the data'''
    client_location = (client_data["latitude"],client_data["longitude"])
    map = folium.Map(location=client_location, zoom_start=9)
    Fullscreen().add_to(map)
    folium.Marker(
        client_location, 
        popup="User's Location", 
        tooltip="User's Location", 
        icon=folium.Icon(color="red", icon="home")
    ).add_to(map)

    if show_bbox:
        bbox_string = sanitize_scale(scale_input)
        if bbox_string:
            bbox_corners = calc_bbox_corners(bbox_string["bbox"])
            folium.PolyLine(
                bbox_corners,
                color="red",
                weight=5
            ).add_to(map)

    for event in data:
        geometry_type = event["geometry"]["type"]
        coordinates = event["geometry"]["coordinates"]
        title = event["properties"]["title"]
        
        # Get the icon and color from the category_icons dictionary
        category_title = event["properties"]["categories"][0]["title"]
        category_info = category_icons.get(category_title, {"icon": "info-sign", "color": "blue"})  # Fallback to blue if not found
        icon_name = category_info["icon"]
        icon_color = category_info["color"]

        if geometry_type == "Point":
            event_location = coordinates[1], coordinates[0]
            popup_list = [
                title,
                f"Category: {category_title}",
                f"Distance from user: {round(event["properties"]["distance"], 2)}km",
                f'<a target="_blank" rel="noopener noreferrer" href={event["properties"]['link']}>Raw JSON</a>'
            ]

            folium.Marker(
                event_location,
                popup="<br>".join(popup_list),
                tooltip=title,
                 icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")  # Use color and icon from category
            ).add_to(map)

        elif geometry_type == "Polygon":
            # GeoJSON expects "coordinates" to be nested as a list of linear rings
            geojson = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates
                },
                "properties": {
                    "popup": title
                }
            }
            folium.GeoJson(
                geojson,
                tooltip=title,
                style_function=lambda x: {
                    "fillColor": icon_color,
                    "color": "red",
                    "weight": 2,
                    "fillOpacity": 0.3
                }
            ).add_to(map)

        elif geometry_type == "LineString":
            line_coords = [(lat, lon) for lon, lat in coordinates]  # Swap [lon, lat] to [lat, lon]
            folium.PolyLine(
                line_coords,
                color="blue",
                weight=3,
                opacity=0.7,
                tooltip=title,
                popup=folium.Popup(title)
            ).add_to(map)

    return map


# Gathering initial data
client_ip = st_javascript("await fetch('https://api.ipify.org?format=json').then(res => res.json()).then(data => data.ip)") # Get client IP
client_data = get_ip_data(client_ip) # Get client location
sources = generate_eonet_dictionaries(eonet_source_url, "sources") # Generate list of EONET sources
categories = generate_eonet_dictionaries(eonet_categories_url, "categories") # Generate list of EONET categories


# Streamlit UI
# User inputs
with st.sidebar:
    with st.form("Inputs"):
        st.markdown("🌐 Filter Natural Events")
        source_input = st.multiselect("Data Sources", list(sources.keys()), default=None, format_func=lambda k: sources[k]["title"])
        category_input = st.multiselect("Event Types", list(category_labels.keys()), format_func=lambda k: category_labels[k].split(" — ")[0])
        status_input = st.selectbox("Event Status", ["open","closed","all"])
        limit_input = st.number_input("Maximum Number of Events", min_value=1, value=None, placeholder="5")
        start_input = st.date_input("Start of Date Range", value=default_start_date, min_value="2002-01-04", max_value=default_end_date, format="YYYY-MM-DD")
        end_input = st.date_input("End of Date Range", value=default_end_date, min_value="2002-01-04", max_value=default_end_date, format="YYYY-MM-DD")
        scale_input = st.number_input("Search Area Scale", min_value=1.0, value=None, placeholder="10.0", step=0.01)
        show_bbox = st.checkbox("Delineate Search Area")

        submitted = st.form_submit_button("Submit")
        reset = st.form_submit_button("Reset")
        if submitted:
            source_input = ",".join(source_input)
            category_input = ",".join(category_input)
            query_url = generate_eonet_query(
                source=source_input,
                category=category_input,
                status=status_input,
                limit=limit_input,
                start=str(start_input),
                end=str(end_input),
                scale=scale_input
            )   

# Displaying data
if submitted:
    st.title("🌍 EONET Natural Events Viewer")
    # Output errors
    for error in global_errors:
        st.error(error)
    if client_data:
        st.write(f"Your detected location: {client_data.get('city', 'Unknown')}, {client_data.get('region', 'Unknown')}, {client_data.get('country_name', 'Unknown')}")
        st.write(f"Query URL: {query_url}")  # Show the API request URL
        data = get_eonet_data(query_url)
        if data and "features" in data:
            data_copy = data["features"][:]
            augmented_data = augment_data(data_copy)
            map = generate_folium_map(augmented_data,show_bbox)
            html_string = map.get_root().render()
            html(html_string, height=500, width=700)
            export = st.download_button("Export Raw JSON Data", json.dumps(data, indent=2), file_name="raw-eonet-json-data.json", mime="application/json", on_click="ignore")
            st.markdown("")
            st.markdown("")
            st.header("EONET Events")
            st.write("Sorted by most recent date.")
            st.markdown("---")
            filtered_data = filter(filter_linstring, augmented_data)
            sorted_data = sorted(filtered_data, key=lambda x: x["properties"]["date"], reverse=True)
            event_set = set()
            for event in sorted_data:
                properties = event["properties"]
                if properties["id"] not in event_set:
                    event_set.add(properties["id"])
                    geometry = event["geometry"]
                    st.subheader(properties["title"])
                    st.write(f"Category: {properties["categories"][0]["title"]}")
                    if event["geometry"]["type"] == "Point":
                        st.write(f"Date: {properties['date']}")
                        st.write(f"Location: {geometry['coordinates'][1]}, {geometry['coordinates'][0]}")
                        st.write(f"Distance from user: {round(event["properties"]["distance"], 2)}km")
                    elif event["geometry"]["type"] == "Polygon":
                        st.write(f"Date: {properties['date']}")
                        st.write("Boundary points:")
                        for point in geometry["coordinates"][0][:-1]:
                            st.write(f"- {point[1]}, {point[0]}")
                    if properties["magnitudeValue"] != "null" and properties["magnitudeValue"] != None:
                        st.write(f"Magnitude: {properties["magnitudeValue"]} {properties["magnitudeUnit"]}")
                    st.write(f"[Raw JSON]({properties['link']})")
                    st.markdown("---")
            st.subheader("Raw JSON Data")
            st.json(data)
        else:
            st.error("No data found or API request failed.")
else:
    with open("README.md", "r", encoding="utf-8") as f:
        st.markdown(f.read(), unsafe_allow_html=True)