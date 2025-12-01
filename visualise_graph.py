"""
Visualize the working graph on an interactive map.
Shows nodes, edges, and component structure.
"""

import pickle
import networkx as nx
import folium
from collections import defaultdict

# Load the working graph
print("Loading working graph...")
with open("attanagalu_working_graph.pkl", "rb") as f:
    G = pickle.load(f)

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# Calculate center of the graph
lons = [G.nodes[n]['lon'] for n in G.nodes()]
lats = [G.nodes[n]['lat'] for n in G.nodes()]
center_lon = sum(lons) / len(lons)
center_lat = sum(lats) / len(lats)

# Create map
m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles='OpenStreetMap')

# Color scheme for waterway types
waterway_colors = {
    'river': '#08306b',
    'canal': '#2171b5',
    'drain': '#4292c6',
    'stream': '#6baed6',
    'ditch': '#9ecae1',
    'dam': '#d62728',
    None: '#999999'
}

waterway_weights = {
    'river': 5,
    'canal': 4,
    'drain': 3,
    'stream': 3,
    'ditch': 2,
    'dam': 6,
    None: 2
}

# Get connected components for coloring
components = list(nx.connected_components(G))
node_to_component = {}
for i, comp in enumerate(components):
    for node in comp:
        node_to_component[node] = i

# Generate colors for components
import colorsys
def get_component_color(comp_idx, total_comps):
    hue = comp_idx / max(total_comps, 1)
    rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

print("Adding edges to map...")

# Add edges
for u, v, data in G.edges(data=True):
    lon1, lat1 = G.nodes[u]['lon'], G.nodes[u]['lat']
    lon2, lat2 = G.nodes[v]['lon'], G.nodes[v]['lat']
    
    waterway_type = data.get('waterway_type', None)
    name = data.get('name', 'Unnamed')
    length = data.get('length_km', 0)
    capacity = data.get('capacity', 0)
    
    color = waterway_colors.get(waterway_type, '#999999')
    weight = waterway_weights.get(waterway_type, 2)
    
    popup_text = f"""
    <b>Type:</b> {waterway_type}<br>
    <b>Name:</b> {name}<br>
    <b>Length:</b> {length:.2f} km<br>
    <b>Capacity:</b> {capacity}<br>
    <b>Nodes:</b> {u} → {v}
    """
    
    folium.PolyLine(
        [[lat1, lon1], [lat2, lon2]],
        color=color,
        weight=weight,
        opacity=0.8,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

print("Adding nodes to map...")

# Add nodes (as small circles)
for node in G.nodes():
    lon = G.nodes[node]['lon']
    lat = G.nodes[node]['lat']
    degree = G.degree(node)
    comp_idx = node_to_component[node]
    
    # Size based on degree (more connections = bigger)
    radius = 3 + degree * 2
    
    # Color based on component
    color = get_component_color(comp_idx, len(components))
    
    popup_text = f"""
    <b>Node:</b> {node}<br>
    <b>Connections:</b> {degree}<br>
    <b>Component:</b> {comp_idx + 1}<br>
    <b>Location:</b> ({lon:.4f}, {lat:.4f})
    """
    
    folium.CircleMarker(
        [lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 160px;
            border:2px solid grey; z-index:9999; font-size:12px;
            background-color:white; padding: 10px;
            border-radius: 5px;">
<b>Waterway Types</b><br>
<i style="background:#08306b; width:30px; height:3px; display:inline-block;"></i> River<br>
<i style="background:#2171b5; width:30px; height:3px; display:inline-block;"></i> Canal<br>
<i style="background:#4292c6; width:30px; height:3px; display:inline-block;"></i> Drain<br>
<i style="background:#6baed6; width:30px; height:3px; display:inline-block;"></i> Stream<br>
<i style="background:#9ecae1; width:30px; height:3px; display:inline-block;"></i> Ditch<br>
<br>
<b>Nodes</b><br>
Colored by component<br>
Size = connections
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save map
output_file = "attanagalu_graph_map.html"
m.save(output_file)
print(f"\nSaved map to: {output_file}")
print("Open this file in your browser to explore the graph!")