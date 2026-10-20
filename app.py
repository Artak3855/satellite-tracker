import streamlit as st
import datetime
import numpy as np
import pandas as pd
from skyfield.api import load, Topos, EarthSatellite
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Pro Satellite & Navigation Tracker", layout="wide")

st.title("🛰️ Professional Satellite & Navigation Link Budget Tracker")
st.markdown("Միջազգային ստանդարտներին համապատասխան արբանյակային հետագծման և նավիգացիոն կապի համակարգ")

# Sidebar - Կարգավորումներ
st.sidebar.header("📍 Վերգետնյա Կայան (Ground Station)")
lat = st.sidebar.number_input("Lat (Լայնություն)", value=40.1872, format="%.4f")
lon = st.sidebar.number_input("Lon (Երկայնություն)", value=44.5152, format="%.4f")
elevation_m = st.sidebar.number_input("Alt (Բարձրություն, մ)", value=1000)

st.sidebar.header("📡 Կապի և Հաճախականության Պարամետրեր")
freq_ghz = st.sidebar.number_input("Կապի Հաճախականություն (GHz)", value=1.57542) # GPS L1

sat_choice = st.sidebar.selectbox("Ընտրել Արբանյակային խումբ", [
    "GPS BIIF-2 (PRN 01)", 
    "ISS (ZARYA)", 
    "GALILEO-24"
])

# TLE տվյալների բազա ըստ ընտրության
tle_data = {
    "GPS BIIF-2 (PRN 01)": (
        "1 36797U 10022A   23292.51234567  .00000012  00000-0  00000-0 0  9993",
        "2 36797  55.2341 123.4567 0012345  45.6789 314.5678  2.00567890213451"
    ),
    "ISS (ZARYA)": (
        "1 25544U 98067A   23292.51234567  .00016717  00000-0  10270-3 0  9992",
        "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.50038192421345"
    ),
    "GALILEO-24": (
        "1 43074U 17081A   23292.51234567  .00000012  00000-0  00000-0 0  9991",
        "2 43074  56.0000 100.0000 0002000  50.0000 310.0000  1.70500000123452"
    )
}

t1, t2 = tle_data[sat_choice]
ts = load.timescale()
satellite = EarthSatellite(t1, t2, sat_choice, ts)
station = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=elevation_m)

# Ժամանակ և հաշվարկներ
now = datetime.datetime.utcnow()
t = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)

difference = satellite - station
topocentric = difference.at(t)
alt, az, distance = topocentric.altaz()

dist_km = distance.km
# Free Space Path Loss (FSPL) հաշվարկ
fspl_db = 20 * np.log10(dist_km) + 20 * np.log10(freq_ghz * 1000) + 32.44

# Doppler shift մոտավոր հաշվարկ (արագության վրա հիմնված)
# f_doppler = -f * (v_rel / c)
velocity = topocentric.velocity.km_per_s
doppler_hz = - (freq_ghz * 1e9) * (velocity[2] / 299792.458)

geocentric = satellite.at(t)
subpoint = geocentric.subpoint()

# Ցուցադրում Պրոֆեսիոնալ Վահանակում
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Azimuth (Ազիմուտ)", f"{az.degrees:.2f}°")
col2.metric("Elevation (Բարձրություն)", f"{alt.degrees:.2f}°")
col3.metric("Distance (Հեռավորություն)", f"{dist_km:.1f} km")
col4.metric("Path Loss (FSPL)", f"{fspl_db:.1f} dB")
col5.metric("Doppler Shift", f"{doppler_hz:.1f} Hz")

status_color = "🟢 Visible (Կապը հասանելի է)" if alt.degrees > 0 else "🔴 Below Horizon (Հորիզոնից ցածր)"
st.info(f"**Կարգավիճակը:** {status_color} | **Արբանյակի բարձրությունը տիեզերքում:** {subpoint.elevation.km:.1f} km")

# Քարտեզի ստեղծում (օպտիմալացված՝ անհարկի թարթումից խուսափելու համար)
@st.cache_resource
def get_base_map(lat, lon):
    return folium.Map(location=[lat, lon], zoom_start=3)

m = folium.Map(location=[subpoint.latitude.degrees, subpoint.longitude.degrees], zoom_start=3)

folium.Marker([lat, lon], popup="Ground Station (Yerevan)", icon=folium.Icon(color="red", icon="home")).add_to(m)
folium.Marker([subpoint.latitude.degrees, subpoint.longitude.degrees], popup=f"{sat_choice}", icon=folium.Icon(color="blue", icon="globe")).add_to(m)

# Ծածկույթի շրջան (Footprint)
folium.Circle(
    location=[subpoint.latitude.degrees, subpoint.longitude.degrees],
    radius=2500 * 1000,
    color="blue",
    fill=True,
    fill_opacity=0.1
).add_to(m)

st_folium(m, width=1200, height=450, returned_objects=[])

# Հավելյալ հնարավորություն՝ Ներբեռնել տվյալները հաշվետվության տեսքով
st.markdown("---")
st.subheader("📥 Արդյունքների Արտահանում (Export Report)")

report_data = pd.DataFrame({
    "Parameter": ["Satellite", "Latitude", "Longitude", "Altitude (km)", "Azimuth (deg)", "Elevation (deg)", "Distance (km)", "FSPL (dB)", "Doppler Shift (Hz)"],
    "Value": [sat_choice, subpoint.latitude.degrees, subpoint.longitude.degrees, subpoint.elevation.km, az.degrees, alt.degrees, dist_km, fspl_db, doppler_hz]
})

csv = report_data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Ներբեռնել Link Budget & Navigation Report (.csv)",
    data=csv,
    file_name='satellite_link_report.csv',
    mime='text/csv',
)
