"""
Visualize A* pathfinding results on a map.
Shows the proposed route with existing vs new canal segments.
"""

import pickle
import json
import folium
from folium import plugins
from folium.plugins import AntPath, BeautifyIcon

# Load data
print("Loading data...")
with open("attanagalu_directed_graph.pkl", "rb") as f:
    G = pickle.load(f)

with open("astar_results.json", "r") as f:
    astar_results = json.load(f)

with open("flood_simulation_results.json", "r") as f:
    flood_results = json.load(f)

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# Extract path info
# Extract solutions
solutions = astar_results['solutions']

print(f"Solutions found: {len(solutions)}")

# Build set of proposed canal edges for quick lookup
# Build set of proposed canal edges for quick lookup
proposed_edges = set()
for sol in solutions:
    for canal in sol['proposed_canals']:
        proposed_edges.add((canal['from_node'], canal['to_node']))

# Calculate map center (center of path)
# Calculate map center (center of first path or graph center)
if solutions and solutions[0]['path']:
    path_lons = [G.nodes[n]['lon'] for n in solutions[0]['path']]
    path_lats = [G.nodes[n]['lat'] for n in solutions[0]['path']]
    center_lon = sum(path_lons) / len(path_lons)
    center_lat = sum(path_lats) / len(path_lats)
else:
    center_lon = 79.9
    center_lat = 7.1

# Create map
m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles='OpenStreetMap')

# Add all existing edges as light gray background
print("Adding background edges...")
for u, v, data in G.edges(data=True):
    lon_u, lat_u = G.nodes[u]['lon'], G.nodes[u]['lat']
    lon_v, lat_v = G.nodes[v]['lon'], G.nodes[v]['lat']
    
    folium.PolyLine(
        [[lat_u, lon_u], [lat_v, lon_v]],
        color='#cccccc',
        weight=1,
        opacity=0.5
    ).add_to(m)

# Add paths for each solution
colors = ['#0066ff', '#9900cc', '#ff6600']  # Blue, Purple, Orange

for idx, sol in enumerate(solutions):
    if not sol['path_found']:
        continue
        
    path = sol['path']
    start_node = sol['start_node']
    goal_node = sol['reached_goal']
    path_color = colors[idx % len(colors)]
    
    print(f"Adding path #{sol['rank']}...")
    
    # Add path lines
    for i in range(len(path) - 1):
        from_node = path[i]
        to_node = path[i + 1]
        
        lon1, lat1 = G.nodes[from_node]['lon'], G.nodes[from_node]['lat']
        lon2, lat2 = G.nodes[to_node]['lon'], G.nodes[to_node]['lat']
        
        # Check if this is a proposed new canal
        is_new = (from_node, to_node) in proposed_edges or (to_node, from_node) in proposed_edges
        
        if is_new:
            # New canal - bright green, dashed
            color = '#00ff00'
            weight = 5
            dash_array = '10, 10'
            edge_type = "PROPOSED NEW CANAL"
            
            popup_text = f"""
            <b>{edge_type}</b><br>
            From: Node {from_node}<br>
            To: Node {to_node}
            """
            
            folium.PolyLine(
                [[lat1, lon1], [lat2, lon2]],
                color=color,
                weight=weight,
                dash_array=dash_array,
                opacity=0.8,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(m)
            
        else:
            # Existing edge - Use AntPath for flow animation
            color = path_color
            weight = 4
            edge_type = f"Path #{sol['rank']} (Existing)"
            
            popup_text = f"""
            <b>{edge_type}</b><br>
            From: Node {from_node}<br>
            To: Node {to_node}
            """
            
            AntPath(
                locations=[[lat1, lon1], [lat2, lon2]],
                color=color,
                weight=weight,
                opacity=0.8,
                pulse_color='#FFFFFF',
                delay=1000,
                popup=folium.Popup(popup_text, max_width=300)
            ).add_to(m)

    # Add markers
    # Start node
    start_lon, start_lat = G.nodes[start_node]['lon'], G.nodes[start_node]['lat']
    folium.Marker(
        [start_lat, start_lon],
        icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa'),
        popup=f"<b>FLOOD POINT #{sol['rank']}</b><br>Node {start_node}"
    ).add_to(m)
    
    # Goal node
    goal_lon, goal_lat = G.nodes[goal_node]['lon'], G.nodes[goal_node]['lat']
    folium.Marker(
        [goal_lat, goal_lon],
        icon=folium.Icon(color='green', icon='flag-checkered', prefix='fa'),
        popup=f"<b>OUTLET</b><br>Node {goal_node}"
    ).add_to(m)
    
    # Proposed canals markers
    for i, canal in enumerate(sol['proposed_canals'], 1):
        mid_lon = (canal['from_coord'][0] + canal['to_coord'][0]) / 2
        mid_lat = (canal['from_coord'][1] + canal['to_coord'][1]) / 2
        
        popup_text = f"""
        <b>PROPOSED CANAL (Path #{sol['rank']})</b><br>
        Length: {canal['distance_km']:.2f} km
        """
        
        folium.Marker(
            [mid_lat, mid_lon],
            icon=folium.Icon(color='green', icon='plus', prefix='fa'),
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 200px;
            border:2px solid grey; z-index:9999; font-size:12px;
            background-color:white; padding: 10px;
            border-radius: 5px;">
<b>A* Pathfinding Results</b><br><br>
<i style="background:#cccccc; width:30px; height:3px; display:inline-block;"></i> Existing network<br>
<i style="background:#0066ff; width:30px; height:3px; display:inline-block;"></i> Drainage Artery (Blue)<br>
<i style="background:#9900cc; width:30px; height:3px; display:inline-block;"></i> Drainage Artery (Purple)<br>
<i style="background:#ff6600; width:30px; height:3px; display:inline-block;"></i> Drainage Artery (Orange)<br>
<i style="background:#00ff00; width:30px; height:3px; display:inline-block; border-style:dashed;"></i> NEW Canal<br><br>
<b>Markers</b><br>
<span style="color:red;">&#9650;</span> Flood Point<br>
<span style="color:green;">&#9650;</span> Outlet<br>
<span style="color:green;">+</span> Proposed canal
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Calculate summary stats
total_canals = sum(len(s['proposed_canals']) for s in solutions)
total_new_km = sum(sum(c['distance_km'] for c in s['proposed_canals']) for s in solutions)

# Add info box
info_html = f'''
<div style="position: fixed; 
            top: 10px; right: 10px; width: 220px;
            border:2px solid grey; z-index:9999; font-size:12px;
            background-color:white; padding: 10px;
            border-radius: 5px;">
<b>Multi-Path Summary</b><br><br>
Paths calculated: {len(solutions)}<br>
Total new canals: {total_canals}<br>
Total new length: {total_new_km:.2f} km<br>
</div>
'''
m.get_root().html.add_child(folium.Element(info_html))

# Save map
output_file = "astar_route_map.html"
m.save(output_file)

print(f"\nSaved map to: {output_file}")
print("Open this file in your browser to see the proposed route!")
print(f"\nSummary:")
print(f"  Visualized {len(solutions)} paths")
print(f"  Total new canals proposed: {total_canals} ({total_new_km:.2f} km)")