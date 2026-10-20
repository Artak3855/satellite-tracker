import streamlit as st
import datetime
import numpy as np
import pandas as pd
from skyfield.api import load, Topos, EarthSatellite
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Satellite Real-Time Tracker", layout="wide")

st.title("🛰️ Real-Time Satellite Pass & Link Budget Tracker")
st.markdown("Արբանյակի հետագծման, նավիգացիոն անկյունների և կապի պարամետրերի real-time հաշվարկ")

# 1. Վերգետնյա Կայանի Կոորդինատները (Default: Yerevan)
st.sidebar.header("📍 Վերգետնյա Կայան (Ground Station)")
lat = st.sidebar.number_input("Lat (Լայնություն)", value=40.1872, format="%.4f")
lon = st.sidebar.number_input("Lon (Երկայնություն)", value=44.5152, format="%.4f")
elevation_m = st.sidebar.number_input("Alt (Բարձրություն, մ)", value=1000)
freq_ghz = st.sidebar.number_input("Կապի Հաճախականություն (GHz)", value=1.57542)

# TLE Տվյալներ (GPS արբանյակ)
tle_line1 = "1 36797U 10022A   23292.51234567  .00000012  00000-0  00000-0 0  9993"
tle_line2 = "2 36797  55.2341 123.4567 0012345  45.6789 314.5678  2.00567890213451"
sat_name = "GPS BIIF-2 (PRN 01)"

ts = load.timescale()
satellite = EarthSatellite(tle_line1, tle_line2, sat_name, ts)
station = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elevation_m)

now = datetime.datetime.utcnow()
t = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)

difference = satellite - station
topocentric = difference.at(t)
alt, az, distance = topocentric.altaz()

dist_km = distance.km
fspl_db = 20 * np.log10(dist_km) + 20 * np.log10(freq_ghz * 1000) + 32.44

geocentric = satellite.at(t)
subpoint = geocentric.subpoint()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Azimuth (Ազիմուտ)", f"{az.degrees:.2f}°")
col2.metric("Elevation (Բարձրություն)", f"{alt.degrees:.2f}°")
col3.metric("Distance (Հեռավորություն)", f"{dist_km:.1f} km")
col4.metric("Path Loss (FSPL)", f"{fspl_db:.1f} dB")
col5.metric("Status", "🟢 Visible (Կապը կա)" if alt.degrees > 0 else "🔴 Below Horizon")

m = folium.Map(location=[subpoint.latitude.degrees, subpoint.longitude.degrees], zoom_start=3)

folium.Marker([lat, lon], popup="Ground Station (Yerevan)", icon=folium.Icon(color="red", icon="home")).add_to(m)
folium.Marker([subpoint.latitude.degrees, subpoint.longitude.degrees], popup=f"{sat_name}", icon=folium.Icon(color="blue", icon="globe")).add_to(m)

folium.Circle(
    location=[subpoint.latitude.degrees, subpoint.longitude.degrees],
    radius=2500 * 1000,
    color="blue",
    fill=True,
    fill_opacity=0.1
).add_to(m)

st_folium(m, width=1200, height=500)
