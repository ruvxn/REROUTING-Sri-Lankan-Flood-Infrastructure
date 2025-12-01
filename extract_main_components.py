"""
Extract the largest connected component and save it as the working graph.
This gives us a clean, connected network for A* pathfinding.
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

# Extract the largest component
main_component_nodes = components[0]
G = G_full.subgraph(main_component_nodes).copy()

print(f"\nMain component extracted:")
print(f"  Nodes: {G.number_of_nodes()}")
print(f"  Edges: {G.number_of_edges()}")

# Verify it's connected
assert nx.is_connected(G), "Error: extracted graph is not connected!"
print("  ✓ Graph is fully connected")

# Analyze the main component
avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
print(f"  Average degree: {avg_degree:.2f}")

# Count edge types
edge_types = defaultdict(int)
for u, v, data in G.edges(data=True):
    edge_types[data.get('waterway_type', None)] += 1

print(f"\nEdges by waterway type:")
for wtype, count in sorted(edge_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {wtype}: {count}")

# Find key nodes in this component
degrees = dict(G.degree())
top_junctions = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]

print(f"\nTop junctions in main component:")
for node_id, degree in top_junctions:
    lon = G.nodes[node_id]['lon']
    lat = G.nodes[node_id]['lat']
    print(f"  Node {node_id}: {degree} connections at ({lon:.4f}, {lat:.4f})")

# Find geographic extent
lons = [G.nodes[n]['lon'] for n in G.nodes()]
lats = [G.nodes[n]['lat'] for n in G.nodes()]
print(f"\nGeographic extent of main component:")
print(f"  Longitude: {min(lons):.4f} to {max(lons):.4f}")
print(f"  Latitude:  {min(lats):.4f} to {max(lats):.4f}")

# Find westernmost and easternmost nodes (potential outlet and source)
nodes_by_lon = sorted(G.nodes(), key=lambda n: G.nodes[n]['lon'])
outlet_node = nodes_by_lon[0]   # Westernmost = closest to sea
source_node = nodes_by_lon[-1]  # Easternmost = upstream source

print(f"\nKey nodes for A* pathfinding:")
print(f"  Potential OUTLET (westernmost): Node {outlet_node}")
print(f"    Location: ({G.nodes[outlet_node]['lon']:.4f}, {G.nodes[outlet_node]['lat']:.4f})")
print(f"    Connections: {G.degree(outlet_node)}")

print(f"  Potential SOURCE (easternmost): Node {source_node}")
print(f"    Location: ({G.nodes[source_node]['lon']:.4f}, {G.nodes[source_node]['lat']:.4f})")
print(f"    Connections: {G.degree(source_node)}")

# Save the main component as the working graph
with open("attanagalu_main_graph.pkl", "wb") as f:
    pickle.dump(G, f)
print(f"\nSaved main component to: attanagalu_main_graph.pkl")

# Save node coordinates for the main component
node_coords = {str(n): {'lon': G.nodes[n]['lon'], 'lat': G.nodes[n]['lat']} for n in G.nodes()}
with open("attanagalu_main_nodes.json", "w") as f:
    json.dump(node_coords, f, indent=2)
print("Saved node coordinates to: attanagalu_main_nodes.json")

# Save summary
summary = {
    'total_nodes': G.number_of_nodes(),
    'total_edges': G.number_of_edges(),
    'is_connected': True,
    'average_degree': avg_degree,
    'edge_types': dict(edge_types),
    'outlet_node': outlet_node,
    'source_node': source_node,
    'bounds': {
        'min_lon': min(lons),
        'max_lon': max(lons),
        'min_lat': min(lats),
        'max_lat': max(lats)
    }
}
with open("attanagalu_main_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("Saved summary to: attanagalu_main_summary.json")
\
print("MAIN COMPONENT EXTRACTION COMPLETE!")
