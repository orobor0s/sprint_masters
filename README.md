# 🌍 EONET Natural Events Viewer

Welcome to the **EONET Natural Events Viewer** — a Streamlit app designed to explore and visualize natural events occurring around the world using NASA's EONET (Earth Observatory Natural Event Tracker) API.

---

## 🔗 Live Sources
- **EONET API:** https://eonet.gsfc.nasa.gov/api/v3/events/geojson
- **IPAPI Geolocation:** https://ipapi.co/json

---

## 🔍 Features
- **Auto-Detect Location:** Instantly identifies your current location using your IP address.
- **Smart Filters:** Search by event type, source agency, event status, date range, magnitude, or bounding box.
- **Interactive Map:** Visualize natural events geographically with folium maps.
- **Sidebar Panel:** Easy input of filters and exploration of event categories.
- **Dynamic JSON Data:** Full raw API data available for advanced users.

---

## ▶️ Inputs
- **Sources:** Select one or more source agencies.
- **Categories:** Choose event types like Wildfires, Volcanoes, Storms, etc.
- **Status:** Open, Closed, or All events.
- **Date Range:** Specify a start and end date.
- **Magnitude Filters:** Set minimum and maximum magnitude levels.
- **Scale:** Define a radius around your detected location.

---

## 🔎 Categories

| Category | Description |
|:---|:---|
| 🔥 Wildfires | Wildfires includes all nature of fire, including forest and plains fires, as well as urban and industrial fire events. Fires may be naturally caused or manmade |
| ⛈️ Severe Storms | Related to the atmospheric aspect of storms (hurricanes, cyclones, tornadoes, etc.). Results of storms may be included under floods, landslides, etc |
| 🌋 Volcanoes | Related to both the physical effects of an eruption (rock, ash, lava) and the atmospheric (ash and gas plumes) |
| 🌊 Floods | Related to aspects of actual flooding--e.g., inundation, water extending beyond river and lake extents |
| 🌎 Earthquakes | Related to all manner of shaking and displacement. Certain aftermath of earthquakes may also be found under landslides and floods |
| ❄️ Sea and Lake Ice | Related to all ice that resides on oceans and lakes, including sea and lake ice (permanent and seasonal) and icebergs |
| ❄️ Snow | Related to snow events, particularly extreme/anomalous snowfall in either timing or extent/depth |
| ♨️ Temperature Extremes | Related to anomalous land temperatures, either heat or cold |
| ☀️ Drought | Long lasting absence of precipitation affecting agriculture and livestock, and the overall availability of food and water |
| 🌫️ Dust and Haze | Related to dust storms, air pollution and other non-volcanic aerosols. Volcano-related plumes shall be included with the originating eruption event |
| ⚙️ Manmade Events | Events that have been human-induced and are extreme in their extent |
| 🗻 Landslides | Related to landslides and variations thereof: mudslides, avalanche |
| 💧 Water Color | Events that alter the appearance of water: phytoplankton, red tide, algae, sediment, whiting, etc |

---

## 🔇 Disclosure
- **IP Geolocation:** Uses approximate IP-based geolocation and may vary slightly.
- **Event Data:** Based on publicly available NASA EONET datasets.

---

## 🚀 Installation Guide

1. Clone the repository:
```bash
git clone https://github.com/orobor0s/sprint_masters.git
cd sprint_masters
```

2. Install the required libraries:
```bash
pip install -r requirements.txt
```

3. Run the Streamlit app:
```bash
streamlit run app.py
```

4. Open your browser at `http://localhost:8501`

---

## 🌐 Repository
- GitHub Repo: [sprint_masters](https://github.com/orobor0s/sprint_masters)

---

## 💛 Acknowledgments
- NASA Earth Observatory Natural Event Tracker (EONET)
- IPAPI Geolocation API
- Streamlit
- Folium and Streamlit-Folium integration for mapping

---

Thank you for using **EONET Natural Events Viewer**!
