import streamlit as st
import datetime
import numpy as np
import pandas as pd
from skyfield.api import load, Topos, EarthSatellite
import plotly.graph_objects as go

st.set_page_config(page_title="Pro 3D Space Constellation & Link Analyzer", layout="wide")

# CSS Injection for Deep Space Background Theme
st.markdown("""
    <style>
    .stApp {
        background-color: #030712;
        background-image: radial-gradient(white 1px, transparent 0);
        background-size: 40px 40px;
        color: #f3f4f6;
    }
    .sidebar .st-bg {
        background-color: #0b0f19;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛰️ Advanced 3D Space Constellation & ITU-R Link Budget Analyzer")
st.markdown("Professional Multi-Constellation Telecommunications & Orbital Tracking System")

# Sidebar - Ground Station Configuration
st.sidebar.header("📍 Ground Station Parameters")
lat = st.sidebar.number_input("Latitude (°)", value=40.1872, format="%.4f", step=0.001)
lon = st.sidebar.number_input("Longitude (°)", value=44.5152, format="%.4f", step=0.001)
elevation_m = st.sidebar.number_input("Altitude (m)", value=1000.0, step=10.0)

st.sidebar.header("📡 ITU-R RF & Link Parameters")
freq_ghz = st.sidebar.number_input("Carrier Frequency (GHz)", value=12.5000, step=0.2500, format="%.4f")
tx_power_dbw = st.sidebar.number_input("Transmitter Power (dBW)", value=10.0, step=1.0)
antenna_gain_dBi = st.sidebar.number_input("Receiver Antenna Gain (dBi)", value=35.0, step=0.5)
system_noise_temp_k = st.sidebar.number_input("System Noise Temp (K)", value=150.0, step=10.0)

sat_choice = st.sidebar.selectbox("Select Satellite Constellation", [
    "GPS Navigation Constellation (MEO)", 
    "GLONASS Constellation (MEO)",
    "GALILEO Constellation (MEO)",
    "Starlink Broadband Shell (LEO)",
    "ISS (ZARYA) Research Station"
])

# Expanded TLE Datasets
constellation_tles = {
    "GPS Navigation Constellation (MEO)": [
        ("GPS PRN 01", "1 36797U 10022A   23292.51234567  .00000012  00000-0  00000-0 0  9993", "2 36797  55.2341 44.5152 0012345  45.6789 314.5678  2.00567890213451"),
        ("GPS PRN 13", "1 27145U 01058A   23292.41234567  .00000012  00000-0  00000-0 0  9994", "2 27145  55.5000 90.0000 0010000 100.0000 260.0000  2.00500000213452"),
        ("GPS PRN 22", "1 24876U 97035A   23292.51234567  .00000012  00000-0  00000-0 0  9995", "2 24876  55.0000 180.0000 0010000 200.0000 160.0000  2.00500000213453"),
        ("GPS PRN 32", "1 32711U 08012A   23292.51234567  .00000012  00000-0  00000-0 0  9996", "2 32711  55.1000 270.0000 0011000 140.0000 220.0000  2.00500000213454"),
    ],
    "GLONASS Constellation (MEO)": [
        ("GLONASS-732", "1 37868U 11055A   23292.51234567  .00000012  00000-0  00000-0 0  9991", "2 37868  64.8500 44.5152 0010000  40.0000 320.0000  2.13000000123451"),
        ("GLONASS-743", "1 40001U 14035A   23292.51234567  .00000012  00000-0  00000-0 0  9992", "2 40001  64.7000 120.0000 0012000 150.0000 210.0000  2.13000000123452"),
        ("GLONASS-701", "1 43685U 18073A   23292.51234567  .00000012  00000-0  00000-0 0  9993", "2 43685  64.9000 200.0000 0008000 260.0000 100.0000  2.13000000123453"),
    ],
    "GALILEO Constellation (MEO)": [
        ("GALILEO-24", "1 43074U 17081A   23292.51234567  .00000012  00000-0  00000-0 0  9991", "2 43074  56.0000 44.5152 0002000  50.0000 310.0000  1.70500000123452"),
        ("GALILEO-22", "1 41859U 16060A   23292.51234567  .00000012  00000-0  00000-0 0  9992", "2 41859  56.1000 140.0000 0002500 160.0000 200.0000  1.70500000123453"),
        ("GALILEO-19", "1 40889U 15050A   23292.51234567  .00000012  00000-0  00000-0 0  9993", "2 40889  56.2000 250.0000 0002000 110.0000 250.0000  1.70500000123454"),
    ],
    "Starlink Broadband Shell (LEO)": [
        ("Starlink-3001", "1 44713U 19029B   23292.50000000  .00001234  00000-0  12345-3 0  9999", "2 44713  53.0500 44.5152 0001234  50.0000 310.0000 15.05000000123451"),
        ("Starlink-3002", "1 44714U 19029C   23292.50000000  .00001234  00000-0  12345-3 0  9999", "2 44714  53.0500 100.0000 0001234  80.0000 280.0000 15.05000000123452"),
        ("Starlink-3003", "1 44715U 19029D   23292.50000000  .00001234  00000-0  12345-3 0  9999", "2 44715  53.0500 160.0000 0001234 110.0000 250.0000 15.05000000123453"),
        ("Starlink-3004", "1 44716U 19029E   23292.50000000  .00001234  00000-0  12345-3 0  9999", "2 44716  53.0500 220.0000 0001234 140.0000 220.0000 15.05000000123454"),
        ("Starlink-3005", "1 44717U 19029F   23292.50000000  .00001234  00000-0  12345-3 0  9999", "2 44717  53.0500 280.0000 0001234 170.0000 190.0000 15.05000000123455"),
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

boltzmann_dbw = -228.6
k_noise_power = 10 * np.log10(system_noise_temp_k) + boltzmann_dbw
received_power_dbw = tx_power_dbw + antenna_gain_dBi - fspl_db
c_n0_dbhz = received_power_dbw - k_noise_power

# Metrics Dashboard
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Azimuth", f"{az.degrees:.2f}°")
col2.metric("Elevation", f"{alt.degrees:.2f}°")
col3.metric("Distance", f"{dist_km:.1f} km")
col4.metric("Path Loss (FSPL)", f"{fspl_db:.1f} dB")
col5.metric("Doppler Shift", f"{doppler_hz:.1f} Hz")
col6.metric("Est. C/N₀", f"{c_n0_dbhz:.1f} dB-Hz")

is_visible = alt.degrees > 0
status_msg = "🟢 Visible (Link Active over Armenia)" if is_visible else "🔴 Below Horizon"
st.info(f"**Status:** {status_msg} | **Primary Satellite Altitude:** {subpoint.elevation.km:.1f} km | **Active Constellation:** {sat_choice}")

# Plotly 3D Globe with Space Theme
fig = go.Figure()

fig.add_trace(go.Scattergeo(
    lon=[lon],
    lat=[lat],
    text=["Ground Station (Yerevan)"],
    mode='markers',
    marker=dict(size=10, color='red'),
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
        text=[f"{name}<br>Alt: {sp.elevation.km:.1f} km<br>El: {s_alt.degrees:.1f}°"],
        mode='markers+text',
        textposition="top center",
        marker=dict(size=8, color='cyan' if idx == 0 else 'lightgreen'),
        name=name
    ))
    
    if idx == 0:
        fig.add_trace(go.Scattergeo(
            lon=[lon, sat_lon],
            lat=[lat, sat_lat],
            mode='lines',
            line=dict(width=2, color='lime' if s_alt.degrees > 0 else 'magenta'),
            name="Active Link"
        ))

    report_rows.append({
        "Satellite Name": name,
        "Latitude (°)": sat_lat,
        "Longitude (°)": sat_lon,
        "Altitude (km)": sp.elevation.km,
        "Azimuth (°)": s_az.degrees,
        "Elevation (°)": s_alt.degrees,
        "Distance (km)": s_dist.km,
        "FSPL (dB)": 20 * np.log10(s_dist.km) + 20 * np.log10(freq_ghz * 1000) + 32.44,
        "C/N0 (dB-Hz)": c_n0_dbhz
    })

fig.update_geos(
    projection_type="orthographic",
    showland=True,
    landcolor="rgb(15, 23, 42)",
    showocean=True,
    oceancolor="rgb(2, 6, 23)",
    showcountries=True,
    countrycolor="rgb(51, 65, 85)",
    showframe=False,
    bgcolor="rgba(0,0,0,0)",
    center=dict(lat=lat, lon=lon)
)

fig.update_layout(
    height=680,
    margin={"r":0,"t":0,"l":0,"b":0},
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# Export Report Section
st.markdown("---")
st.subheader("📥 Export Advanced ITU-R Link Budget & Constellation Report")

report_df = pd.DataFrame(report_rows)
csv_data = report_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Advanced Link Budget Report (.csv)",
    data=csv_data,
    file_name='advanced_satellite_link_report.csv',
    mime='text/csv',
)
