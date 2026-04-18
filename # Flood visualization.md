# Flood visualization

## Status: Initial build complete — `flood_risk_gatineau_ottawa.html`

### What was built
4-tab self-contained HTML dashboard:
1. **Britannia Gauge** — draggable slider (58.0–62.0m MASL) updates a horizontal bar chart with threshold annotations (59.60m watch, 60.44m 2017 peak, 60.70m 2019 peak). Color-coded risk badge.
2. **Historical Floods** — Chart.js bar chart for notable years (1974, 1976, 1998, 2008, 2017, 2019, 2020, 2023) with red/orange/blue coloring vs. the 59.60m threshold.
3. **Snowpack Risk** — SWE % of normal line chart (Oct–Apr) showing 2017 season, 2019 season, current (simulated), and long-term average. Risk interpretation box below.
4. **Flood Map** — Leaflet.js map (OpenStreetMap tiles) with gauge station markers (02KF005 Britannia, 02KF009 Hull) and approximate 2019 flood extent polygons for Britannia Village and Pointe-Gatineau.

### Libraries
- Chart.js 4.4.0 + chartjs-plugin-annotation 3.0.1
- Leaflet 1.9.4

### TODO / Future enhancements
- [ ] Fetch live gauge data from Water Survey of Canada datamart (CORS proxy needed, or JSONP)
- [ ] Import official shapefile polygons from Open Ottawa / Données Québec
- [ ] Add real weekly SWE data from ORRPB "Snow Conditions" reports
- [ ] Add precipitation overlay (Environment Canada station 6106000)
- [ ] Add Carillon Dam discharge data
- [ ] Generate preview image for OG/social tags

---


I want to make a visualization for the flood risk of gatineau ottawa based on the snow pake in the north and the rainy season. I want it to be also historical and present information on past flooding for the region. What are the dataset I should be looking into importing. I want to make a britannia gauge.

To build a flood risk visualization for the Gatineau-Ottawa region that replicates the "Britannia Gauge" simulator, you need to integrate three specific data layers: Real-Time Hydrometry (River Levels), Snow Water Equivalent (Predictive Volume), and Geospatial Flood Polygons (Impact Zones).
The primary datasets you must import are:
1. River Levels & Flow (The "Gauge" Data)
Source: Water Survey of Canada (Environment & Climate Change Canada)
Dataset: Real-Time Hydrometric Data (API or CSV).
Key Station: 02KF005 (Ottawa River at Britannia).
Variables: Water Level (m) and Discharge (m³/s).
Historical Context: You must manually scrape or import the "Annual Extremes" from the Ottawa River Regulation Planning Board (ORRPB) to mark the critical thresholds:
2017 Peak: 60.44m
2019 Peak: 60.70m
Flood Threshold (Britannia): ~59.60m (Start of minor flooding).

AI-generated, may include mistakes. Don't enter sensitive personal info.
2. Predictive Data (Snowpack & Melt)
To model the "risk" component based on the north's snowpack, you need SWE (Snow Water Equivalent) data. This determines the potential volume of water waiting to melt.
Source: Canadian Cryospheric Information Network (CCIN) or ECCC.
Dataset: Snow Water Equivalent (SWE) Maps.
Specific Metric: Look for "Percent of Normal" or "Snow Depth" for the Upper Ottawa River Basin.
Integration: Correlate high SWE (>150% of normal) in the Timiskaming and Cabonga reservoir areas with forecast temperature to predict rapid level rises at Britannia.
3. Impact Zones (Geospatial Visualization)
To visualize where the water goes (the map portion of your dashboard), you need the municipal flood polygons.
City of Ottawa: Import the "Flood Plain Mapping (1 in 100 year & 1 in 350 year)" shapefiles from Open Ottawa.
Ville de Gatineau: Import "Zones inondables" from the Données Québec portal.
Mapping: Overlay these polygons on a Leaflet or Mapbox base. When your "Gauge" data hits 59.6m, program your map to highlight the Pointe-Gatineau and Britannia Village polygons in red.
Data Dictionary for Import
Use this schema to structure your database for the visualization:
Metric
Unit
Source / Station ID
Water Level
Meters (MASL)
Water Survey Canada: 02KF005 (Britannia), 02KF009 (Hull)
Flow Rate
m³/s
Carillon Dam (Total Discharge)
Snowpack
mm (SWE)
ORRPB "Snow Conditions" Reports (Weekly)
Precipitation
mm (Rain)
Environment Canada: Ottawa CDA (Climate ID 6106000)
