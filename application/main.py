from datetime import datetime, timedelta
import json
import requests
import urllib.parse
import streamlit as st


# Variables
ipapi_url = "https://ipapi.co/json"
eonet_source_url = "https://eonet.gsfc.nasa.gov/api/v3/sources"
eonet_categories_url = "https://eonet.gsfc.nasa.gov/api/v3/categories"
eonet_magnitudes_url = "https://eonet.gsfc.nasa.gov/api/v3/magnitudes"
eonet_query_url = "https://eonet.gsfc.nasa.gov/api/v3/events/geojson?"
default_start_date = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
default_end_date = datetime.today().strftime('%Y-%m-%d')


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
    min_lon, max_lon = wrap_lon(lon - scale), wrap_lon(lon + scale)
    min_lat, max_lat = max(-90, lat - scale), min(90, lat + scale)
    return ",".join(map(str, [min_lon, max_lat, max_lon, min_lat]))


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
                print(f"{keyword} input errors: {errors}, {keyword} must be in {check.keys()}")
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
        print(f"Status input error: {status}, status must be open, closed, or all (leaving status blank defaults to open)")
    return {}

def sanitize_limit(limit):
    '''Sanitize limit input'''
    if limit:
        if limit.isdigit():
            return {"limit": limit}
        print(f"Limit input error: {limit}, limit must be a positive integer")
    return {}

def sanitize_date_range(start, end):
    '''Sanitize date range input'''
    if is_valid_date(start) and is_valid_date(end) and end >= start:
        return {"start": start, "end": end}
    print(f"Date range input error: {start} - {end}, each date must be in the YYYY-MM-DD format and the start date must be before or equal to the end date")
    return {}

def sanitize_magID(magID):
    '''Sanitize magID'''
    if magID:
        if magID in magnitudes:
            return {"magID": magID}
        print(f"magID input error: {magID}, magID must be in {magnitudes.keys()}")
    return {}

def sanitize_magnitudes(mag, keyword):
    '''Sanitize magnitudes'''
    if mag:
        if is_float(mag) and float(mag) >= 0:
            return {keyword: mag}
        print(f"{keyword} input error: {mag}, mag must be a float or integer that is greater than or equal to 0")
    return {}
    
def sanitize_scale(scale):
    '''Sanitize scale input'''
    if is_float(scale) and float(scale) >= 0:
        return {"bbox": calc_bbox(scale)}
    print(f"Scale input error: {scale}, scale must be a float or integer that is greater than or equal to 0")
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
    '''Generates EONET query url based on sanitized user input'''
    # Set parameters
    params = {}
    params.update(sanitize_list_input(source,"sources"))
    params.update(sanitize_list_input(category,"categories"))
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
            print(f"magMax {magMax} must be greater than or equal to magMin {magMin}")
    else:
        params.update(magMin_dict)
        params.update(magMax_dict)
    params.update(sanitize_scale(scale))
    
    # Generate API query
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe=",")
    return f"{eonet_query_url}{query_string}"


# API queries
@st.cache_data
def get_ip_data():
    '''Gets the client's IP data'''
    # Needs a User-Agent header in the request to circumvent rate limiting
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    reply_data = requests.get(f"{ipapi_url}", headers=headers)
    json_data = reply_data.json()
    json_status = reply_data.status_code

    if json_status == 200:
        return json_data
    else:
        print("Error message: " + json_data["message"])

def get_eonet_data(url):
    '''Gets EONET event data based on the client's location and customized parameters'''
    reply_data = requests.get(url)
    json_data = reply_data.json()
    json_status = reply_data.status_code

    if json_status == 200:
       return json_data
    else:
        print("Error message: " + json_data["message"])


# Streamlit UI
st.title("EONET Natural Events Viewer")


client_data = get_ip_data()
sources = generate_eonet_dictionaries(eonet_source_url, "sources")
categories = generate_eonet_dictionaries(eonet_categories_url, "categories")
magnitudes = generate_eonet_dictionaries(eonet_magnitudes_url, "magnitudes")

# Get user location
if client_data:
   st.write(f"Your detected location: {client_data.get('city', 'Unknown')}, {client_data.get('region', 'Unknown')}, {client_data.get('country_name', 'Unknown')}")

# User inputs
with st.sidebar:
    with st.form("Inputs"):
        source_input = st.multiselect("Sources", list(sources.keys()), default=None, format_func=lambda k: sources[k]["title"])
        category_input = st.multiselect("Categories", list(categories.keys()), default=None, format_func=lambda k: categories[k]["title"])
        status_input = st.selectbox("Status", ["open","closed","all"])
        limit_input = st.number_input("Limit", min_value=1, value=5)
        start_input = st.date_input("Start Date", value=default_start_date, format="YYYY-MM-DD")
        end_input = st.date_input("End Date", value=default_end_date, format="YYYY-MM-DD")
        magID_input = st.selectbox("magID", list(magnitudes.keys()), format_func=lambda k: magnitudes[k]["name"])
        magMin_input = st.number_input("magMin", min_value=0.0, value=0.0, step=0.01)
        magMax_input = st.number_input("magMax", min_value=0.0, value=10.0, step=0.01)
        scale_input = st.number_input("Limit", min_value=1.0, value=10.0, step=0.01)

        submitted = st.form_submit_button("Submit")
        if submitted:
            source_input = ",".join(source_input)
            category_input = ",".join(category_input)
            query_url = generate_eonet_query(
                source=source_input,
                category=category_input,
                status=status_input,
                limit=str(limit_input),
                start=str(start_input),
                end=str(end_input),
                magID=str(magID_input),
                magMin=str(magMin_input),
                magMax=str(magMax_input),
                scale=str(scale_input)
            )
            st.write(query_url)
        

st.write(f"Query URL: {query_url}")  # Show the API request URL

data = get_eonet_data(query_url)

if data and "features" in data:
    for event in data["features"][:5]:  # Display first 5 events
        properties = event["properties"]
        geometry = event["geometry"]

        st.subheader(properties["title"])
        st.write(f"Category: {properties.get('categories', 'Unknown')}")
        st.write(f"Date: {properties['date']}")
        if "coordinates" in geometry:
            st.write(f"Location: {geometry['coordinates']}")
        st.write(f"[More Info]({properties['link']})")
        st.markdown("---")
else:
    st.error("No data found or API request failed.")

# Display raw JSON data
st.subheader("Raw JSON Data")
st.json(data)