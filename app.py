import streamlit as st
import datetime
import numpy as np
import pandas as pd
from skyfield.api import load, Topos, EarthSatellite
import plotly.graph_objects as go

st.set_page_config(page_title="Pro 3D Space Constellation Tracker", layout="wide")

st.title("🛰️ 3D Space Constellation & Orbit Tracker (azmth Style)")
st.markdown("Real-Time 3D Globe Satellite Tracking & Link Analysis System")

# Sidebar - Ground Station Configuration
st.sidebar.header("📍 Ground Station Parameters")
lat = st.sidebar.number_input("Latitude (°)", value=40.1872, format="%.4f", step=0.001)
lon = st.sidebar.number_input("Longitude (°)", value=44.5152, format="%.4f", step=0.001)
elevation_m = st.sidebar.number_input("Altitude (m)", value=1000.0, step=10.0)

st.sidebar.header("📡 ITU-R RF & Link Parameters")
freq_ghz = st.sidebar.number_input("Carrier Frequency (GHz)", value=1.57542, step=0.1000, format="%.5f")

sat_choice = st.sidebar.selectbox("Select Satellite Constellation", [
    "GPS Navigation Constellation (MEO)", 
    "GLONASS Constellation (MEO)",
    "GALILEO Constellation (MEO)",
    "ISS (ZARYA) Research Station"
])

# TLE Datasets
constellation_tles = {
    "GPS Navigation Constellation (MEO)": [
        ("GPS BIIF-2 (PRN 01)", "1 36797U 10022A   23292.51234567  .00000012  00000-0  00000-0 0  9993", "2 36797  55.2341 44.5152 0012345  45.6789 314.5678  2.00567890213451"),
        ("GPS BIIR-11 (PRN 13)", "1 27145U 01058A   23292.41234567  .00000012  00000-0  00000-0 0  9994", "2 27145  55.5000 60.0000 0010000 100.0000 260.0000  2.00500000213452"),
        ("GPS BIIR-2 (PRN 22)", "1 24876U 97035A   23292.51234567  .00000012  00000-0  00000-0 0  9995", "2 24876  55.0000 120.0000 0010000 200.0000 160.0000  2.00500000213453"),
    ],
    "GLONASS Constellation (MEO)": [
        ("GLONASS-M 732", "1 37868U 11055A   23292.51234567  .00000012  00000-0  00000-0 0  9991", "2 37868  64.8500 44.5152 0010000  40.0000 320.0000  2.13000000123451"),
        ("GLONASS-M 743", "1 40001U 14035A   23292.51234567  .00000012  00000-0  00000-0 0  9992", "2 40001  64.7000 70.0000 0012000 150.0000 210.0000  2.13000000123452"),
    ],
    "GALILEO Constellation (MEO)": [
        ("GALILEO-24", "1 43074U 17081A   23292.51234567  .00000012  00000-0  00000-0 0  9991", "2 43074  56.0000 44.5152 0002000  50.0000 310.0000  1.70500000123452"),
        ("GALILEO-22", "1 41859U 16060A   23292.51234567  .00000012  00000-0  00000-0 0  9992", "2 41859  56.1000 65.0000 0002500 160.0000 200.0000  1.70500000123453")
    ],
    "ISS (ZARYA) Research Station": [
        ("ISS (ZARYA)", "1 25544U 98067A   23292.51234567  .00016717  00000-0  10270-3 0  9992", "2 25544  51.6416 44.5152 0006703 130.5360 325.0288 15.50038192421345")
    ]
}

ts = load.timescale()
now = datetime.datetime.utcnow()
t = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
station = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elevation_m)

sat_list = constellation_tles.get(sat_choice, constellation_tles["GPS Navigation Constellation (MEO)"])

primary_name, t1, t2 = sat_list[0]
primary_sat = EarthSatellite(t1, t2, primary_name, ts)
topocentric = (primary_sat - station).at(t)
alt, az, distance = topocentric.altaz()
dist_km = distance.km

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

# Plotly 3D Globe Visualization
fig = go.Figure()

# Ground Station (Yerevan) - Fixed symbol error
fig.add_trace(go.Scattergeo(
    lon=[lon],
    lat=[lat],
    text=["Ground Station (Yerevan)"],
    mode='markers',
    marker=dict(size=12, color='red'),
    name="Ground Station"
))

report_rows = []

for idx, (name, line1, line2) in enumerate(sat_list):
    sat = EarthSatellite(line1, line2, name, ts)
    sp = sat.at(t).subpoint()
    topo = (sat - station).at(t)
    s_alt, s_az, s_dist = topo.altaz()
    
    sat_lat = sp.latitude.degrees
    sat_lon = sp.longitude.degrees
    
    fig.add_trace(go.Scattergeo(
        lon=[sat_lon],
        lat=[sat_lat],
        text=[f"{name}<br>Alt: {sp.elevation.km:.1f} km<br>Elevation: {s_alt.degrees:.1f}°"],
        mode='markers+text',
        textposition="top center",
        marker=dict(size=10, color='cyan' if idx == 0 else 'lightgreen'),
        name=name
    ))
    
    if idx == 0:
        fig.add_trace(go.Scattergeo(
            lon=[lon, sat_lon],
            lat=[lat, sat_lat],
            mode='lines',
            line=dict(width=2, color='lime' if s_alt.degrees > 0 else 'magenta'),
            name="Link Path"
        ))

    report_rows.append({
        "Satellite Name": name,
        "Latitude (°)": sat_lat,
        "Longitude (°)": sat_lon,
        "Altitude (km)": sp.elevation.km,
        "Azimuth (°)": s_az.degrees,
        "Elevation (°)": s_alt.degrees,
        "Distance (km)": s_dist.km,
        "FSPL (dB)": 20 * np.log10(s_dist.km) + 20 * np.log10(freq_ghz * 1000) + 32.44
    })

fig.update_geos(
    projection_type="orthographic",
    showland=True,
    landcolor="rgb(20, 30, 40)",
    showocean=True,
    oceancolor="rgb(5, 10, 20)",
    showcountries=True,
    countrycolor="rgb(50, 70, 90)",
    showframeline=False,
    center=dict(lat=lat, lon=lon)
)

fig.update_layout(
    height=650,
    margin={"r":0,"t":0,"l":0,"b":0},
    paper_bgcolor="rgb(10, 15, 25)",
    plot_bgcolor="rgb(10, 15, 25)",
    font=dict(color="white"),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

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
