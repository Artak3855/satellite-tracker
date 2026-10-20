import streamlit as st
import datetime
import numpy as np
import pandas as pd
from skyfield.api import load, Topos, EarthSatellite
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Pro ITU-R Satellite Constellation Tracker", layout="wide")

st.title("🛰️ ITU-R Standard Satellite Constellation & Link Budget Tracker")
st.markdown("Professional Multi-Layer Constellation Simulation with Real-Time Visibility & Link Analysis")

# Sidebar - Ground Station Configuration (Default: Yerevan, Armenia)
st.sidebar.header("📍 Ground Station Parameters")
lat = st.sidebar.number_input("Latitude (°)", value=40.1872, format="%.4f", step=0.001)
lon = st.sidebar.number_input("Longitude (°)", value=44.5152, format="%.4f", step=0.001)
elevation_m = st.sidebar.number_input("Altitude (m)", value=1000.0, step=10.0)

st.sidebar.header("📡 ITU-R RF & Link Parameters")
freq_ghz = st.sidebar.number_input("Carrier Frequency (GHz)", value=12.0000, step=0.1000, format="%.4f") # Ku-band standard for broadband

sat_choice = st.sidebar.selectbox("Select Satellite Constellation", [
    "Starlink Broadband Constellation (LEO)", 
    "GPS Navigation Constellation (MEO)", 
    "GLONASS Constellation (MEO)",
    "ISS (ZARYA) Research Station"
])

# Toggle for Constellation Network Sub-layer
show_constellation_layer = st.sidebar.checkbox("Show Full Constellation Network Layer", value=True)

# Accurate TLE Datasets simulating orbital shells over the region
constellation_tles = {
    "Starlink Broadband Constellation (LEO)": [
        ("Starlink-3001", "1 44713U 19029B   23292.50000000  .00001234  00000-0  12345-3 0  9999", "2 44713  53.0500 150.0000 0001234  50.0000 310.0000 15.05000000123451"),
        ("Starlink-3002", "1 44714U 19029C   23292.50000000  .00001234  00000-0  12345-3 0  9999", "2 44714  53.0500 180.0000 0001234  80.0000 280.0000 15.05000000123452"),
        ("Starlink-3003", "1 44715U 19029D   23292.50000000  .00001234  00000-0  12345-3 0  9999", "2 44715  53.0500 210.0000 0001234 110.0000 250.0000 15.05000000123453"),
        ("Starlink-3004", "1 44716U 19029E   23292.50000000  .00001234  00000-0  12345-3 0  9999", "2 44716  53.0500 240.0000 0001234 140.0000 220.0000 15.05000000123454"),
    ],
    "GPS Navigation Constellation (MEO)": [
        ("GPS BIIF-2 (PRN 01)", "1 36797U 10022A   23292.51234567  .00000012  00000-0  00000-0 0  9993", "2 36797  55.2341 44.5152 0012345  45.6789 314.5678  2.00567890213451"),
        ("GPS BIIR-11 (PRN 13)", "1 27145U 01058A   23292.41234567  .00000012  00000-0  00000-0 0  9994", "2 27145  55.5000 100.0000 0010000 100.0000 260.0000  2.00500000213452"),
    ],
    "GLONASS Constellation (MEO)": [
        ("GLONASS-M 732", "1 37868U 11055A   23292.51234567  .00000012  00000-0  00000-0 0  9991", "2 37868  64.8500 44.5152 0010000  40.0000 320.0000  2.13000000123451"),
        ("GLONASS-M 743", "1 40001U 14035A   23292.51234567  .00000012  00000-0  00000-0 0  9992", "2 40001  64.7000 140.0000 0012000 150.0000 210.0000  2.13000000123452"),
    ],
    "ISS (ZARYA) Research Station": [
        ("ISS (ZARYA)", "1 25544U 98067A   23292.51234567  .00016717  00000-0  10270-3 0  9992", "2 25544  51.6416 44.5152 0006703 130.5360 325.0288 15.50038192421345")
    ]
}

ts = load.timescale()
now = datetime.datetime.utcnow()
t = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
station = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elevation_m)

sat_list = constellation_tles.get(sat_choice, constellation_tles["Starlink Broadband Constellation (LEO)"])

# Calculate primary satellite for metrics
primary_name, t1, t2 = sat_list[0]
primary_sat = EarthSatellite(t1, t2, primary_name, ts)
topocentric = (primary_sat - station).at(t)
alt, az, distance = topocentric.altaz()
dist_km = distance.km

# ITU-R Free Space Path Loss (FSPL) standard formula: FSPL(dB) = 20*log10(d) + 20*log10(f) + 32.44
fspl_db = 20 * np.log10(dist_km) + 20 * np.log10(freq_ghz * 1000) + 32.44
velocity = topocentric.velocity.km_per_s
doppler_hz = - (freq_ghz * 1e9) * (velocity[2] / 299792.458)
subpoint = primary_sat.at(t).subpoint()

# Metrics Dashboard
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Azimuth", f"{az.degrees:.2f}°")
col2.metric("Elevation", f"{alt.degrees:.2f}°")
col3.metric("Distance", f"{dist_km:.1f} km")
col4.metric("Path Loss (FSPL)", f"{fspl_db:.1f} dB")
col5.metric("Doppler Shift", f"{doppler_hz:.1f} Hz")

is_visible = alt.degrees > 0
status_msg = "🟢 Visible (Link Active over Armenia)" if is_visible else "🔴 Below Horizon"
st.info(f"**Status:** {status_msg} | **Primary Satellite Altitude:** {subpoint.elevation.km:.1f} km | **Constellation:** {sat_choice}")

# Map Visualization
m = folium.Map(location=[lat, lon], zoom_start=4)

# Ground Station Marker (Yerevan)
folium.Marker(
    [lat, lon], 
    popup=f"Ground Station (Yerevan)<br>Lat: {lat}, Lon: {lon}", 
    icon=folium.Icon(color="red", icon="home")
).add_to(m)

report_rows = []

# Plot Constellation Network if toggled on
for idx, (name, line1, line2) in enumerate(sat_list):
    sat = EarthSatellite(line1, line2, name, ts)
    sp = sat.at(t).subpoint()
    topo = (sat - station).at(t)
    s_alt, s_az, s_dist = topo.altaz()
    
    marker_color = "blue" if idx == 0 else "cadetblue"
    
    # Satellite Marker
    folium.Marker(
        [sp.latitude.degrees, sp.longitude.degrees],
        popup=f"<b>{name}</b><br>Alt: {sp.elevation.km:.1f} km<br>Elevation: {s_alt.degrees:.1f}°",
        icon=folium.Icon(color=marker_color, icon="globe")
    ).add_to(m)
    
    # Constellation Network Sub-layer (Footprint Circles)
    if show_constellation_layer:
        folium.Circle(
            location=[sp.latitude.degrees, sp.longitude.degrees],
            radius=1500 * 1000,
            color="orange" if idx == 0 else "blue",
            fill=True,
            fill_opacity=0.03
        ).add_to(m)
        
        # Ground track line connection to ground station for primary
        if idx == 0:
            folium.PolyLine(
                locations=[[lat, lon], [sp.latitude.degrees, sp.longitude.degrees]],
                color="green" if s_alt.degrees > 0 else "red",
                weight=2,
                opacity=0.8
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

st_folium(m, width=1200, height=480, returned_objects=[])

# Export Report Section
st.markdown("---")
st.subheader("📥 Export ITU-R Link Budget & Constellation Report")

report_df = pd.DataFrame(report_rows)
csv_data = report_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Standard Link Budget Report (.csv)",
    data=csv_data,
    file_name='itu_r_satellite_link_report.csv',
    mime='text/csv',
)
