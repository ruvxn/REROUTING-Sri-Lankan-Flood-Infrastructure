"""
Extract the top N largest components and combine them into a working graph.
This gives us more of the basin to work with while keeping it manageable.
"""

import pickle
import networkx as nx
import json
from collections import defaultdict

# Load the full graph
print("Loading full graph...")
with open("attanagalu_graph.pkl", "rb") as f:
    G_full = pickle.load(f)

print(f"Full graph: {G_full.number_of_nodes()} nodes, {G_full.number_of_edges()} edges")

# Get all connected components, sorted by size (largest first)
components = sorted(nx.connected_components(G_full), key=len, reverse=True)
print(f"Found {len(components)} connected components")

# Take the top N components (adjust this number as needed)
TOP_N = 50  # Take top 50 components

# Collect all nodes from top N components
selected_nodes = set()
for i, comp in enumerate(components[:TOP_N]):
    selected_nodes.update(comp)
    if i < 10:  # Print info for top 10
        print(f"  Component {i+1}: {len(comp)} nodes")

print(f"\nSelected top {TOP_N} components: {len(selected_nodes)} total nodes")

# Extract subgraph with selected nodes
G = G_full.subgraph(selected_nodes).copy()

print(f"\nWorking graph extracted:")
print(f"  Nodes: {G.number_of_nodes()}")
print(f"  Edges: {G.number_of_edges()}")
print(f"  Connected components: {nx.number_connected_components(G)}")

# Analyze the working graph
avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
print(f"  Average degree: {avg_degree:.2f}")

# Count edge types
edge_types = defaultdict(int)
total_length_km = 0
for u, v, data in G.edges(data=True):
    edge_types[data.get('waterway_type', None)] += 1
    total_length_km += data.get('length_km', 0)

print(f"\nEdges by waterway type:")
for wtype, count in sorted(edge_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {wtype}: {count}")

print(f"\nTotal waterway length: {total_length_km:.2f} km")

# Find key nodes
degrees = dict(G.degree())
top_junctions = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]

print(f"\nTop 10 junctions (most connected nodes):")
for node_id, degree in top_junctions:
    lon = G.nodes[node_id]['lon']
    lat = G.nodes[node_id]['lat']
    print(f"  Node {node_id}: {degree} connections at ({lon:.4f}, {lat:.4f})")

# Find geographic extent
lons = [G.nodes[n]['lon'] for n in G.nodes()]
lats = [G.nodes[n]['lat'] for n in G.nodes()]
print(f"\nGeographic extent:")
print(f"  Longitude: {min(lons):.4f} to {max(lons):.4f}")
print(f"  Latitude:  {min(lats):.4f} to {max(lats):.4f}")

# Find westernmost and easternmost nodes
nodes_by_lon = sorted(G.nodes(), key=lambda n: G.nodes[n]['lon'])
outlet_candidates = nodes_by_lon[:5]   # 5 westernmost
source_candidates = nodes_by_lon[-5:]  # 5 easternmost

print(f"\nPotential OUTLETS (westernmost nodes):")
for node in outlet_candidates:
    lon, lat = G.nodes[node]['lon'], G.nodes[node]['lat']
    print(f"  Node {node}: ({lon:.4f}, {lat:.4f}), {G.degree(node)} connections")

print(f"\nPotential SOURCES (easternmost nodes):")
for node in source_candidates:
    lon, lat = G.nodes[node]['lon'], G.nodes[node]['lat']
    print(f"  Node {node}: ({lon:.4f}, {lat:.4f}), {G.degree(node)} connections")

# Save the working graph
with open("attanagalu_working_graph.pkl", "wb") as f:
    pickle.dump(G, f)
print(f"\nSaved working graph to: attanagalu_working_graph.pkl")

# Save node coordinates
node_coords = {str(n): {'lon': G.nodes[n]['lon'], 'lat': G.nodes[n]['lat']} for n in G.nodes()}
with open("attanagalu_working_nodes.json", "w") as f:
    json.dump(node_coords, f, indent=2)
print("Saved node coordinates to: attanagalu_working_nodes.json")

# Save summary
summary = {
    'total_nodes': G.number_of_nodes(),
    'total_edges': G.number_of_edges(),
    'connected_components': nx.number_connected_components(G),
    'average_degree': avg_degree,
    'total_length_km': total_length_km,
    'edge_types': dict(edge_types),
    'bounds': {
        'min_lon': min(lons),
        'max_lon': max(lons),
        'min_lat': min(lats),
        'max_lat': max(lats)
    }
}
with open("attanagalu_working_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("Saved summary to: attanagalu_working_summary.json")

print("\n" + "=" * 60)
print("WORKING GRAPH EXTRACTION COMPLETE!")
print("=" * 60)
print(f"""
Working graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges
Components: {nx.number_connected_components(G)} (disconnected, but that's OK!)

The disconnected components represent real waterways that SHOULD connect.
Your A* algorithm can later propose new canals to connect them!

Files created:
  - attanagalu_working_graph.pkl   (the working graph)
  - attanagalu_working_nodes.json  (node coordinates)  
  - attanagalu_working_summary.json (statistics)

Next step: Visualize this on a map!
""")