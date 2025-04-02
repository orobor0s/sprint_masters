from datetime import datetime, timedelta
import json
import requests
import urllib.parse


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
            input = input.upper()
            key = "source"
        else:
            key = "category"
        input_check = input.split(',')
        for item in input_check:
            if item in globals().get(keyword, "Variable not found"):
                valid.append(item)
            else:
                errors.append(item)
        if errors:
                print(f"{keyword} input errors: {errors}")
        if valid:
            return {key: ",".join(valid)}
        else:
            return {}
    else:
        return {}

def sanitize_status(status):
    '''Sanitize status input'''
    return {"status": status} if status in {"open", "closed", "all"} else {}

def sanitize_limit(limit):
    '''Sanitize limit input'''
    return {"limit": limit} if limit.isdigit() else {}

def sanitize_date_range(start, end):
    '''Sanitize date range input'''
    if is_valid_date(start) and is_valid_date(end) and end >= start:
        return {"start": start, "end": end}
    return {}

def sanitize_magID(magID):
    '''Sanitize magID'''
    if magID and magID in magnitudes:
        return {"magID": magID}
    else:
        return {}

def sanitize_magnitudes(mag, keyword):
    '''Sanitize magnitudes'''
    if mag and is_float(mag) and float(mag) > 0:
        return {keyword: mag}
    else:
        return {}
    
def sanitize_scale(scale):
    '''Sanitize scale input'''
    if is_float(scale) and float(scale) >= 0:
        return {"bbox": calc_bbox(scale)}
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
        params.update(magMin_dict)
        params.update(magMax_dict)
    params.update(sanitize_scale(scale))
    
    # Generate API query
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe=",")
    return f"{eonet_query_url}{query_string}"


# API queries
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

def get_eonet_data(url):
    '''Gets EONET event data based on the client's location and customized parameters'''
    reply_data = requests.get(url)
    json_data = reply_data.json()
    json_status = reply_data.status_code

    if json_status == 200:
       return json_data
    else:
        print("Error message: " + json_data["message"])


client_data = get_ip_data()
sources = generate_eonet_dictionaries(eonet_source_url, "sources")
categories = generate_eonet_dictionaries(eonet_categories_url, "categories")
magnitudes = generate_eonet_dictionaries(eonet_magnitudes_url, "magnitudes")


if client_data != None:
    query_url = generate_eonet_query(
        source="IRWIN,abfire,test",
        category="drought,wildfires",
        status="all",
        limit="20",
        start="2000-01-01",
        end=default_end_date,
        magID="ac",
        magMin="0",
        magMax="100",
        scale=20)
    print(query_url)
    print(json.dumps(get_eonet_data(query_url), indent=4))

# Placeholder for GUI