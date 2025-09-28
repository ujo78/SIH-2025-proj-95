# simulate_india_traffic_iter_popup.py
import random
from typing import List, Tuple, Iterable

import osmnx as ox
import networkx as nx
from shapely.geometry import LineString, MultiLineString, GeometryCollection
import folium
import simpy

from helpers import *
from routers import *
from traffic_model import *



ox.settings.use_cache = True


CENTER_LAT = 20.2590372
CENTER_LON = 85.79181
CENTER = (CENTER_LAT, CENTER_LON)

# Compact drivable network around ITER to keep it snappy
G = ox.graph_from_point(CENTER, dist=2000, network_type="drive", simplify=True)
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

Gp = ox.projection.project_graph(G)




model = TrafficModel(G, max_vehicles=14, spawn_rate_per_s=1/18.0, sim_seconds=240)
model.run()

# -----------------------------
# 5) Folium map and rendering
# -----------------------------
m = folium.Map(location=CENTER, zoom_start=14, tiles="OpenStreetMap", prefer_canvas=True)

# Mark ITER vicinity
folium.Marker(
    location=CENTER,
    tooltip="ITER / SOA vicinity",
    icon=folium.Icon(color="green", icon="university", prefix="fa"),
).add_to(m)

# Colors and offset parameters
route_colors = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
    "#a65628", "#f781bf", "#999999", "#66c2a5", "#fc8d62",
    "#8da0cb", "#e78ac3", "#a6cee3", "#b2df8a"
]
OFFSET_SPACING_M = 1.5  # base offset spacing in meters

# Draw offset routes (MultiLineString-safe)
for vid, path in model.routes.items():
    color = route_colors[vid % len(route_colors)]

    segs_m = route_geoms_projected(Gp, path)
    ls_m = concat_lines(segs_m)

    side = "left" if (vid % 2 == 0) else "right"
    offset_m = ((vid % 5) - 2) * OFFSET_SPACING_M
    if offset_m == 0:
        side = "left"
        offset_m = OFFSET_SPACING_M
    ls_off_m = offset_route_linestring(ls_m, offset_m=abs(offset_m), side=side)

    ls_ll = to_latlon(ls_off_m)
    ls_ll = simplify_linestring_deg_latlon(ls_ll, tol=1e-5)

    for segment in iter_lines_latlon(ls_ll):
        folium.PolyLine(
            locations=segment,
            color=color,
            weight=3,
            opacity=0.9
        ).add_to(m)

# Start and End markers for every vehicle (node IDs guaranteed)
for vid in model.routes.keys():
    s_id = model.start_nodes[vid]
    e_id = model.end_nodes[vid]
    s_lat, s_lon = node_latlon(G, s_id)
    e_lat, e_lon = node_latlon(G, e_id)

    # Start (blue)
    folium.CircleMarker(
        location=(s_lat, s_lon),
        radius=5,
        color="#1f78b4",
        fill=True,
        fill_color="#1f78b4",
        fill_opacity=0.95,
        tooltip=f"Vehicle {vid} start"
    ).add_to(m)

    # End (red)
    folium.CircleMarker(
        location=(e_lat, e_lon),
        radius=6,
        color="#e31a1c",
        fill=True,
        fill_color="#e31a1c",
        fill_opacity=0.95,
        tooltip=f"Vehicle {vid} end"
    ).add_to(m)

# -----------------------------
# 6) Pop-out container + scrollable legend injection
# -----------------------------
map_id = m.get_name()

legend_items_html = "".join(
    f'<div class="item"><span class="swatch" style="background:{route_colors[vid % len(route_colors)]}"></span>Vehicle {vid} route</div>'
    for vid in sorted(model.routes.keys())
)

legend_html = f"""
<style>
  /* Bottom-right pop-out container */
  #map-frame {{
    position: fixed;
    bottom: 16px;
    right: 16px;
    width: 260px;
    height: 180px;
    z-index: 9999;
    box-shadow: 0 6px 24px rgba(0,0,0,.2);
    border-radius: 10px;
    overflow: hidden;
    transition: all .25s ease;
    cursor: pointer;
    background: #fff;
  }}
  #map-frame.open {{
    width: 80vw;
    height: 70vh;
    cursor: default;
  }}
  #backdrop {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.25);
    z-index: 9998;
  }}
  #map-frame.open + #backdrop {{ display: block; }}
  #close-btn {{
    position: absolute;
    top: 8px;
    right: 8px;
    background: #fff;
    border: 1px solid #ccc;
    border-radius: 16px;
    padding: 2px 8px;
    font-size: 18px;
    line-height: 1;
    box-shadow: 0 2px 6px rgba(0,0,0,.2);
    display: none;
    z-index: 10000;
  }}
  #map-frame.open #close-btn {{ display: inline-block; }}

  /* Legend inside the map frame (scrollable) */
  #legend {{
    position: absolute;
    top: 10px;
    left: 10px;
    background: rgba(255,255,255,.95);
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 12px;
    line-height: 1.3;
    max-width: 280px;
    max-height: 45vh;
    overflow-y: auto; /* scrollable legend */
    z-index: 1000;
  }}
  #legend .title {{
    font-weight: 600;
    margin-bottom: 6px;
  }}
  #legend .item {{
    display: flex;
    align-items: center;
    margin: 3px 0;
    white-space: nowrap;
  }}
  #legend .swatch {{
    width: 12px;
    height: 12px;
    margin-right: 6px;
    border: 1px solid #999;
    flex: 0 0 auto;
  }}
  #legend .marker {{
    display: inline-block;
    width: 12px; height: 12px;
    margin-right: 6px;
    border-radius: 50%;
    border: 1px solid #999;
  }}
</style>

<!-- Pop-out frame and backdrop -->
<div id="map-frame">
  <button id="close-btn" title="Close">×</button>
  <div id="legend">
    <div class="title">Legend</div>
    <div class="item"><span class="marker" style="background:#1f78b4"></span>Start position</div>
    <div class="item"><span class="marker" style="background:#e31a1c"></span>End position</div>
    {legend_items_html}
  </div>
</div>
<div id="backdrop"></div>

<script>
(function() {{
  var frame = document.getElementById('map-frame');
  var backdrop = document.getElementById('backdrop');
  var closeBtn = document.getElementById('close-btn');
  var mapDiv = document.getElementById('{map_id}');
  // Ensure the Leaflet map div fills the frame
  mapDiv.style.width = '100%';
  mapDiv.style.height = '100%';
  frame.appendChild(mapDiv);

  function openMap() {{
    frame.classList.add('open');
    setTimeout(function() {{
      var leafletMap = window['{map_id}'];
      if (leafletMap && leafletMap.invalidateSize) leafletMap.invalidateSize();
    }}, 300);
  }}
  function closeMap(ev) {{
    ev.stopPropagation();
    frame.classList.remove('open');
  }}

  frame.addEventListener('click', function() {{
    if (!frame.classList.contains('open')) openMap();
  }});
  closeBtn.addEventListener('click', closeMap);
  backdrop.addEventListener('click', closeMap);
}})();
</script>
"""

m.get_root().html.add_child(folium.Element(legend_html))
m.save("map.html")
print("Done. Open 'map.html' for a bottom-right pop-out map with start/end markers, offset routes, and a scrollable legend.")
