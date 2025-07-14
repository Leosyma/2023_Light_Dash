⚡ Field Asset Inventory Dashboard
An interactive web application developed using Streamlit to visualize and analyze assets collected in the field during the electrical network inventory. The tool enables intuitive access to georeferenced data, allowing users to filter, explore, and monitor the status of surveyed infrastructure assets.

🔐 Authentication
Secure access via login screen using streamlit-authenticator.

Credentials are managed via a YAML configuration file.

🌍 Interactive Mapping
The app features a dynamic map powered by Folium, offering:

🗺️ Multiple base maps (Google Maps, Satellite, Terrain, Esri, CartoDB).

🟩 Layered visualization of:

Medium-voltage segments (Trecho MT)

Utility poles (Postes)

Risk areas (Áreas de risco) from shapefiles

🧭 Custom map legend indicating asset status:

N – Not inventoried

D – Deleted

U – Updated

I – Inserted

🔎 Filtering by:

Region (Regional)

Substation (Subestação)

Feeder line (Linha)

Asset status (STATUSIN)

Asset type (Segment, Pole, or Both)

📊 Dashboard Integration
A separate tab provides access to a Power BI dashboard, offering complementary analytical views of inventory metrics and progress.

💾 Downloadable Output
Users can:

Export the map as an .html file.

Customize the filename within the app.

🧰 Tech Stack
Streamlit

Folium

Geopandas

Pandas

Branca

PyYAML

Shapely

streamlit-authenticator

Power BI (external integration)
