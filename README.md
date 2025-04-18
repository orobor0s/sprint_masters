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
| 🔥 Wildfires | Fires in forests, grasslands, or natural areas |
| ⛈️ Severe Storms | Hurricanes, cyclones, thunderstorms |
| 🌋 Volcanoes | Volcanic eruptions and activity |
| 🌊 Floods | Overflow of water onto land |
| 🌎 Earthquakes | Sudden ground shaking |
| ❄️ Sea and Lake Ice | Ice coverage and melting |
| ❄️ Snow | Heavy snowfall or snow cover changes |
| ♨️ Temperature Extremes | Heatwaves and cold spells |
| ☀️ Drought | Prolonged dry conditions |
| 🌫️ Dust and Haze | Visibility reduction due to dust, smoke, or haze |
| ⚙️ Manmade Events | Human-caused incidents like industrial accidents |

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
