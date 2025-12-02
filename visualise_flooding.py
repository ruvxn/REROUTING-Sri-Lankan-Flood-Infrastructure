"""
Visualize flood simulation results on an interactive map.
Shows which edges flooded and their severity.
"""

import pickle
import json
import folium

# Load the directed graph
print("Loading graph...")
with open("attanagalu_directed_graph.pkl", "rb") as f:
    G = pickle.load(f)

# Load flood simulation results
print("Loading flood results...")
with open("flood_simulation_results.json", "r") as f:
    flood_results = json.load(f)

with open("edge_flows.json", "r") as f:
    edge_flows = json.load(f)

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
print(f"Flooded edges: {flood_results['flooded_edge_count']}")

# Calculate map center
lons = [G.nodes[n]['lon'] for n in G.nodes()]
lats = [G.nodes[n]['lat'] for n in G.nodes()]
center_lon = sum(lons) / len(lons)
center_lat = sum(lats) / len(lats)

# Create map
m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles='OpenStreetMap')

# Create a set of flooded edges for quick lookup
flooded_edge_set = set()
flooded_edge_data = {}
for fe in flood_results['flooded_edges']:
    key = (fe['from_node'], fe['to_node'])
    flooded_edge_set.add(key)
    flooded_edge_data[key] = fe

# Color function based on flood severity
def get_edge_color(u, v, data):
    key = (u, v)
    if key in flooded_edge_set:
        overflow = flooded_edge_data[key]['overflow']
        capacity = flooded_edge_data[key]['capacity']
        severity = overflow / capacity if capacity > 0 else 1
        
        # Red gradient based on severity
        if severity > 2:
            return '#67000d'  # Very dark red - severe flooding
        elif severity > 1:
            return '#a50f15'  # Dark red
        elif severity > 0.5:
            return '#ef3b2c'  # Red
        else:
            return '#fc9272'  # Light red
    else:
        return '#2171b5'  # Blue - no flooding

def get_edge_weight(u, v, data):
    key = (u, v)
    if key in flooded_edge_set:
        return 4  # Thicker line for flooded edges
    else:
        return 2

print("Adding edges to map...")

# Add all edges
for u, v, data in G.edges(data=True):
    lon_u, lat_u = G.nodes[u]['lon'], G.nodes[u]['lat']
    lon_v, lat_v = G.nodes[v]['lon'], G.nodes[v]['lat']
    
    color = get_edge_color(u, v, data)
    weight = get_edge_weight(u, v, data)
    
    # Build popup content
    key = (u, v)
    edge_key = f"{u}-{v}"
    
    if key in flooded_edge_set:
        fe = flooded_edge_data[key]
        popup_text = f"""
        <b>STATUS: FLOODED</b><br>
        <b>Type:</b> {data.get('waterway_type', 'unknown')}<br>
        <b>Name:</b> {data.get('name', 'unnamed')}<br>
        <b>Flow:</b> {fe['flow']:.1f}<br>
        <b>Capacity:</b> {fe['capacity']}<br>
        <b>Overflow:</b> {fe['overflow']:.1f}<br>
        <b>Severity:</b> {fe['overflow']/fe['capacity']*100:.0f}% over capacity
        """
    else:
        flow_info = edge_flows.get(edge_key, {})
        popup_text = f"""
        <b>STATUS: OK</b><br>
        <b>Type:</b> {data.get('waterway_type', 'unknown')}<br>
        <b>Name:</b> {data.get('name', 'unnamed')}<br>
        <b>Flow:</b> {flow_info.get('flow', 0):.1f}<br>
        <b>Capacity:</b> {data.get('capacity', 15)}<br>
        <b>Utilization:</b> {flow_info.get('utilization', 0)*100:.0f}%
        """
    
    folium.PolyLine(
        [[lat_u, lon_u], [lat_v, lon_v]],
        color=color,
        weight=weight,
        opacity=0.8,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

# Add markers for worst flooded locations
print("Adding flood markers...")

worst_floods = sorted(flood_results['flooded_edges'], key=lambda x: x['overflow'], reverse=True)[:10]

for i, fe in enumerate(worst_floods, 1):
    node = fe['from_node']
    lon = G.nodes[node]['lon']
    lat = G.nodes[node]['lat']
    
    popup_text = f"""
    <b>CRITICAL FLOOD #{i}</b><br>
    <b>Type:</b> {fe['waterway_type']}<br>
    <b>Name:</b> {fe['name'] or 'unnamed'}<br>
    <b>Overflow:</b> {fe['overflow']:.1f} units<br>
    <b>Flow/Capacity:</b> {fe['flow']:.1f}/{fe['capacity']}
    """
    
    folium.Marker(
        [lat, lon],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
    ).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 180px;
            border:2px solid grey; z-index:9999; font-size:12px;
            background-color:white; padding: 10px;
            border-radius: 5px;">
<b>Flood Severity</b><br>
<i style="background:#2171b5; width:40px; height:4px; display:inline-block;"></i> No flooding<br>
<i style="background:#fc9272; width:40px; height:4px; display:inline-block;"></i> Minor (0-50% over)<br>
<i style="background:#ef3b2c; width:40px; height:4px; display:inline-block;"></i> Moderate (50-100%)<br>
<i style="background:#a50f15; width:40px; height:4px; display:inline-block;"></i> Severe (100-200%)<br>
<i style="background:#67000d; width:40px; height:4px; display:inline-block;"></i> Critical (>200%)<br>
<br>
<b>Markers</b><br>
Red markers = Top 10 worst floods
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save map
output_file = "flood_simulation_map.html"
m.save(output_file)
print(f"\nSaved map to: {output_file}")
print("Open this file in your browser to explore the flood simulation results!")
print(f"\nKey findings:")
print(f"  - {flood_results['flooded_edge_count']} edges flooded ({flood_results['flood_rate_percent']:.1f}%)")
print(f"  - Total overflow: {flood_results['total_overflow']:.1f} units")
print(f"  - Red markers show critical flood points")