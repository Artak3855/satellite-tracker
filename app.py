import streamlit as st
import datetime
import numpy as np
import pandas as pd
from skyfield.api import load, Topos, EarthSatellite
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Pro Satellite & Constellation Tracker", layout="wide")

st.title("🛰️ Professional Satellite Constellation & Link Budget Tracker")
st.markdown("International Standard Satellite Navigation, Constellation Tracking & Link Analysis System")

# Sidebar - Ground Station Configuration
st.sidebar.header("📍 Ground Station Parameters")
lat = st.sidebar.number_input("Latitude (°)", value=40.1872, format="%.4f", step=0.1)
lon = st.sidebar.number_input("Longitude (°)", value=44.5152, format="%.4f", step=0.1)
elevation_m = st.sidebar.number_input("Altitude (m)", value=1000.0, step=50.0)

st.sidebar.header("📡 RF & Frequency Parameters")
freq_ghz = st.sidebar.number_input("Frequency (GHz)", value=1.57542, step=0.01, format="%.5f") # GPS L1

sat_choice = st.sidebar.selectbox("Select Satellite Constellation", [
    "GPS Constellation", 
    "GLONASS Constellation",
    "GALILEO Constellation",
    "ISS (ZARYA)"
])

# Multi-satellite TLE database for constellations
constellation_tles = {
    "GPS Constellation": [
        ("GPS BIIF-2 (PRN 01)", "1 36797U 10022A   23292.51234567  .00000012  00000-0  00000-0 0  9993", "2 36797  55.2341 123.4567 0012345  45.6789 314.5678  2.00567890213451"),
        ("GPS BIIR-11 (PRN 13)", "1 27145U 01058A   23292.41234567  .00000012  00000-0  00000-0 0  9994", "2 27145  55.5000 200.0000 0010000 100.0000 260.0000  2.00500000213452"),
        ("GPS BIIF-12 (PRN 24)", "1 39166U 13023A   23292.61234567  .00000012  00000-0  00000-0 0  9995", "2 39166  55.1000 300.0000 0015000  50.0000 310.0000  2.00500000213453")
    ],
    "GLONASS Constellation": [
        ("GLONASS-M 732", "1 37868U 11055A   23292.51234567  .00000012  00000-0  00000-0 0  9991", "2 37868  64.8500 120.0000 0010000  40.0000 320.0000  2.13000000123451"),
        ("GLONASS-M 743", "1 40001U 14035A   23292.51234567  .00000012  00000-0  00000-0 0  9992", "2 40001  64.7000 240.0000 0012000 150.0000 210.0000  2.13000000123452"),
        ("GLONASS-K 701", "1 43685U 18073A   23292.51234567  .00000012  00000-0  00000-0 0  9993", "2 43685  64.9000 350.0000 0008000 260.0000 100.0000  2.13000000123453")
    ],
    "GALILEO-24": [
        ("GALILEO-24", "1 43074U 17081A   23292.51234567  .00000012  00000-0  00000-0 0  9991", "2 43074  56.0000 100.0000 0002000  50.0000 310.0000  1.70500000123452"),
        ("GALILEO-22", "1 41859U 16060A   23292.51234567  .00000012  00000-0  00000-0 0  9992", "2 41859  56.1000 220.0000 0002500 160.0000 200.0000  1.70500000123453")
    ],
    "ISS (ZARYA)": [
        ("ISS (ZARYA)", "1 25544U 98067A   23292.51234567  .00016717  00000-0  10270-3 0  9992", "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.50038192421345")
    ]
}

ts = load.timescale()
now = datetime.datetime.utcnow()
t = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
station = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elevation_m)

sat_list = constellation_tles.get(sat_choice, constellation_tles["GPS Constellation"])

# Calculate primary satellite for metrics
primary_name, t1, t2 = sat_list[0]
primary_sat = EarthSatellite(t1, t2, primary_name, ts)
topocentric = (primary_sat - station).at(t)
alt, az, distance = topocentric.altaz()
dist_km = distance.km
fspl_db = 20 * np.log10(dist_km) + 20 * np.log10(freq_ghz * 1000) + 32.44
velocity = topocentric.velocity.km_per_s
doppler_hz = - (freq_ghz * 1e9) * (velocity[2] / 299792.458)
subpoint = primary_sat.at(t).subpoint()

# Professional Metrics Dashboard (English)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Azimuth", f"{az.degrees:.2f}°")
col2.metric("Elevation", f"{alt.degrees:.2f}°")
col3.metric("Distance", f"{dist_km:.1f} km")
col4.metric("Path Loss (FSPL)", f"{fspl_db:.1f} dB")
col5.metric("Doppler Shift", f"{doppler_hz:.1f} Hz")

status_msg = "🟢 Visible (Link Active)" if alt.degrees > 0 else "🔴 Below Horizon (No Direct Line of Sight)"
st.info(f"**Status:** {status_msg} | **Primary Satellite Altitude:** {subpoint.elevation.km:.1f} km | **Constellation:** {sat_choice}")

# Map Visualization with Multiple Satellites (Constellation View)
m = folium.Map(location=[lat, lon], zoom_start=3)

# Ground Station Marker
folium.Marker(
    [lat, lon], 
    popup=f"Ground Station<br>Lat: {lat}, Lon: {lon}", 
    icon=folium.Icon(color="red", icon="home")
).add_to(m)

# Plot all satellites in the selected constellation network
report_rows = []
for name, line1, line2 in sat_list:
    sat = EarthSatellite(line1, line2, name, ts)
    sp = sat.at(t).subpoint()
    topo = (sat - station).at(t)
    s_alt, s_az, s_dist = topo.altaz()
    
    # Add Marker for each satellite in network
    folium.Marker(
        [sp.latitude.degrees, sp.longitude.degrees],
        popup=f"<b>{name}</b><br>Alt: {sp.elevation.km:.1f} km<br>Elevation: {s_alt.degrees:.1f}°",
        icon=folium.Icon(color="blue", icon="globe")
    ).add_to(m)
    
    # Coverage Footprint Circle
    folium.Circle(
        location=[sp.latitude.degrees, sp.longitude.degrees],
        radius=2000 * 1000,
        color="blue",
        fill=True,
        fill_opacity=0.05
    ).add_to(m)
    
    report_rows.append({
        "Satellite Name": name,
        "Latitude (°)": sp.latitude.degrees,
        "Longitude (°)": sp.longitude.degrees,
        "Altitude (km)": sp.elevation.km,
        "Azimuth (°)": s_az.degrees,
        "Elevation (°)": s_alt.degrees,
        "Distance (km)": s_dist.km,
        "FSPL (dB)": 20 * np.log10(s_dist.km) + 20 * np.log10(freq_ghz * 1000) + 32.44
    })

st_folium(m, width=1200, height=450, returned_objects=[])

# Export Report Section (English)
st.markdown("---")
st.subheader("📥 Export Constellation Link Report")

report_df = pd.DataFrame(report_rows)
csv_data = report_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Constellation & Link Budget Report (.csv)",
    data=csv_data,
    file_name='satellite_constellation_report.csv',
    mime='text/csv',
)
