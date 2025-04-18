from datetime import datetime, timedelta
import requests
import urllib.parse
import folium
from folium.plugins import Fullscreen
import streamlit as st
from streamlit_folium import st_folium
from streamlit.components.v1 import html
from streamlit_js_eval import streamlit_js_eval
import webbrowser
import os

# Styling
st.markdown(
    """
    <style>
    body {
        background-color: #F5F5F5; /* Light gray clean background */
        font-family: 'Arial', sans-serif;
    }
    .stApp {
        background-color: rgba(255, 255, 255, 1); /* Solid white */
        color: #000000; /* Black text */
    }
    h1, h2, h3, h4, h5, h6 {
        color: #000000; /* Black headers */
        font-weight: 700;
    }
    p, label, .css-1v3fvcr {
        color: #000000; /* Black labels, paragraph text */
        font-size: 1.05rem;
    }
    .stButton>button {
        background-color: #000000; /* Black buttons */
        color: white; /* White text on buttons */
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Variables
ipapi_url = "https://ipapi.co/json"
eonet_source_url = "https://eonet.gsfc.nasa.gov/api/v3/sources"
eonet_categories_url = "https://eonet.gsfc.nasa.gov/api/v3/categories"
eonet_magnitudes_url = "https://eonet.gsfc.nasa.gov/api/v3/magnitudes"
eonet_query_url = "https://eonet.gsfc.nasa.gov/api/v3/events/geojson?"
default_start_date = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
default_end_date = datetime.today().strftime('%Y-%m-%d')
submitted = ""
query_url = ""
global_errors = []

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
    "manmade": "Manmade Events ⚙️ — Human-caused incidents"
}

# Utility
def is_float(n):
    try:
        float(n)
        return True
    except ValueError:
        return False

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
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

# Input sanitization
def sanitize_list_input(input, keyword):
    '''Sanitize item and category inputs'''
    if input:
        valid, errors = [], []
        key = "source" if keyword == "sources" else "category"
        input_check = input.split(',')
        check = globals().get(keyword, {})
        for item in input_check:
            if item in check:
                valid.append(item)
            else:
                errors.append(item)
        if errors:
            global_errors.append(f"{keyword} input errors: {errors}")
        return {key: ",".join(valid)} if valid else {}
    return {}

def sanitize_status(status):
    '''Sanitize status input'''
    if status in {"open", "closed", "all"}:
        return {"status": status}
    global_errors.append("Status input error: must be open, closed, or all.")
    return {}

def sanitize_limit(limit):
    '''Sanitize limit input'''
    if limit and int(limit) > 0:
        return {"limit": limit}
    global_errors.append("Limit must be a positive integer.")
    return {}

def sanitize_date_range(start, end):
    '''Sanitize date range input'''
    if is_valid_date(start) and is_valid_date(end) and end >= start:
        return {"start": start, "end": end}
    global_errors.append("Date range error: Invalid dates or start date after end date.")
    return {}

def sanitize_magID(magID):
    '''Sanitize magID input'''
    if magID and magID in magnitudes:
        return {"magID": magID}
    global_errors.append("Invalid magID.")
    return {}

def sanitize_magnitudes(mag, key):
    '''Sanitize magnitudes input'''
    if mag and is_float(mag) and float(mag) >= 0:
        return {key: mag}
    global_errors.append(f"{key} must be a float or integer >= 0.")
    return {}

def sanitize_scale(scale):
    '''Sanitize scale input'''
    if is_float(scale) and float(scale) >= 0:
        return {"bbox": calc_bbox(scale)}
    global_errors.append("Scale must be a positive number.")
    return {}

# EONET enabling infrastructure

@st.cache_data
def generate_eonet_dictionaries(url, keyword):
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
        magID="",
        magMin="",
        magMax="",
        scale=10):
    '''Generates EONET query URL based on sanitized user input'''
    params = {}
    params.update(sanitize_list_input(source, "sources"))
    params.update(sanitize_list_input(category, "categories"))
    params.update(sanitize_status(status))
    params.update(sanitize_limit(limit))
    params.update(sanitize_date_range(start, end))
    params.update(sanitize_magID(magID))
    magMin_dict = sanitize_magnitudes(magMin, "magMin")
    magMax_dict = sanitize_magnitudes(magMax, "magMax")
    if magMin_dict and magMax_dict:
        if float(magMax_dict["magMax"]) >= float(magMin_dict["magMin"]):
            params.update(magMin_dict)
            params.update(magMax_dict)
        else:
            global_errors.append(f"magMax {magMax} must be greater than or equal to magMin {magMin}")
    else:
        params.update(magMin_dict)
        params.update(magMax_dict)
    params.update(sanitize_scale(scale))

    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe=",")
    return f"{eonet_query_url}{query_string}"

# API queries
@st.cache_data
def get_ip_data():
    '''Gets the client's IP data'''
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(ipapi_url, headers=headers)
    return response.json() if response.status_code == 200 else {}

@st.cache_data
def get_eonet_data(url):
    '''Fetch EONET event data'''
    response = requests.get(url)
    return response.json() if response.status_code == 200 else {}

# Map
@st.cache_resource
def generate_folium_map(data):
    m = folium.Map(location=(client_data["latitude"], client_data["longitude"]), zoom_start=9)
    Fullscreen().add_to(m)
    folium.Marker(
        (client_data["latitude"], client_data["longitude"]),
        popup="Your Location",
        tooltip="Your Location",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)

    for event in data["features"]:
        coords = event["geometry"]["coordinates"]
        title = event["properties"]["title"]
        if event["geometry"]["type"] == "Point":
            folium.Marker((coords[1], coords[0]), tooltip=title, popup=title,
                          icon=folium.Icon(color="blue")).add_to(m)
        elif event["geometry"]["type"] == "LineString":
            line = [(lat, lon) for lon, lat in coords]
            folium.PolyLine(line, color="blue", weight=3, opacity=0.7, popup=title).add_to(m)
    return map
# Streamlit UI
try:
    with open("README.md", "r", encoding="utf-8") as f:
        st.markdown(f.read(), unsafe_allow_html=True)
except:
    pass

client_data = get_ip_data()
sources = generate_eonet_dictionaries(eonet_source_url, "sources")
categories = generate_eonet_dictionaries(eonet_categories_url, "categories")
magnitudes = generate_eonet_dictionaries(eonet_magnitudes_url, "magnitudes")

# User inputs
with st.sidebar:
    with st.form("Inputs"):
        st.markdown("<h2 style='color:#333'>🌐 Filter Natural Events</h2>", unsafe_allow_html=True)

        source_input = st.multiselect("Sources", list(sources.keys()), format_func=lambda k: sources[k]["title"], help="Choose data providers.")
        category_input = st.multiselect("Categories", list(category_labels.keys()), format_func=lambda k: category_labels[k].split(" — ")[0], help="Select event types.")
        status_input = st.selectbox("Status", ["open", "closed", "all"], help="Event status.")
        limit_input = st.number_input("Limit", min_value=1, value=10, help="Max number of events.")
        start_input = st.date_input("Start Date", value=datetime.strptime(default_start_date, "%Y-%m-%d"), help="Beginning date.")
        end_input = st.date_input("End Date", value=datetime.strptime(default_end_date, "%Y-%m-%d"), help="End date.")
        magID_input = st.selectbox("magID", list(magnitudes.keys()), index=None, format_func=lambda k: magnitudes[k]["name"], help="Magnitude scale.")
        magMin_input = st.number_input("magMin", min_value=0.0, value=0.0, help="Minimum magnitude.")
        magMax_input = st.number_input("magMax", min_value=0.0, value=10.0, help="Maximum magnitude.")
        scale_input = st.number_input("Scale", min_value=1.0, value=10.0, help="Map radius scale.")

        submitted = st.form_submit_button("Submit")
        open_map = st.form_submit_button("Open Map in New Tab")

    if st.button("🔄 Reset"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

    if category_input:
        st.markdown("### 📖 Category Descriptions")
        for cat in category_input:
            st.info(category_labels[cat])

# Output
if submitted or open_map:
    # Output errors
    for error in global_errors:
        st.error(error)

    # Getting user location
    if client_data:
        st.write(f"Your detected location: {client_data.get('city', 'Unknown')}, {client_data.get('region', 'Unknown')}, {client_data.get('country_name', 'Unknown')}")

        query_url = generate_eonet_query(
            source=",".join(source_input),
            category=",".join(category_input),
            status=status_input,
            limit=limit_input,
            start=str(start_input),
            end=str(end_input),
            magID=magID_input,
            magMin=magMin_input,
            magMax=magMax_input,
            scale=scale_input
        )

        st.write(f"Query URL: {query_url}")

        # Fetch data
        data = get_eonet_data(query_url)
        if data and "features" in data:
            map = generate_folium_map(data)

            if open_map:
                map.save("map.html")
                webbrowser.open("map.html")
            else:
                html_string = map._repr_html_()  # Get map HTML as string
                html(html_string, height=500, width=700)
            event_set = set()
            for event in data["features"]:
                properties = event["properties"]
                if properties["id"] not in event_set:
                    event_set.add(properties["id"])
                    geometry = event["geometry"]

                    st.subheader(properties["title"])
                    st.write(f"Category: {properties['categories'][0]['title']}")

                    try:
                        st.write(f"Date: {properties['date']}")
                        st.write(f"Location: {geometry['coordinates']}")
                    except Exception:
                        st.write(f"Most recent date: {properties['geometryDates'][-1]}")
                        st.write(f"Last location: {geometry['coordinates'][-1]}")

                    st.write(f"[More Info]({properties['link']})")
                    st.markdown("---")
        else:
            st.error("No data found or API request failed.")

        # Display raw JSON data
        st.subheader("Raw JSON Data")
        st.json(data)
