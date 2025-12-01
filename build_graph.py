import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString
import json
from collections import defaultdict
import math
from scipy.spatial import cKDTree
import numpy as np
import pickle

# Load the GeoJSON file
gdf = gpd.read_file("data/attanagalu.geojson")

# Filter to only linear features (the flow network)
# Polygons (lakes/reservoirs) don't have "flow" - they store water
linear = gdf[gdf.geometry.geom_type.isin(['LineString', 'MultiLineString'])].copy()
print(f"Loaded {len(linear)} linear waterway features")

# Relative capacities (arbitrary units for MVP)
# Higher number = can carry more water before flooding
CAPACITY_BY_TYPE = {
    'river': 100,    # Main rivers - highest capacity
    'canal': 60,     # Man-made canals - designed for good flow
    'drain': 30,     # Drainage channels - medium capacity
    'stream': 20,    # Natural streams - smaller
    'ditch': 10,     # Small ditches - easily overwhelmed
    'dam': 200,      # Dams - control structures (special case)
    None: 15         # Unknown type - assume low capacity
}

# Snap threshold in degrees (approximately 100 meters at this latitude)
# At latitude 7°N: 1 degree ≈ 111 km, so 0.001° ≈ 111m
SNAP_THRESHOLD_DEGREES = 0.001

print("Capacity values by waterway type:")
for wtype, cap in CAPACITY_BY_TYPE.items():
    print(f"  {wtype}: {cap}")

print(f"\nSnap threshold: {SNAP_THRESHOLD_DEGREES} degrees (~100 meters)")


def haversine_distance_km(coord1, coord2):
    """Calculate distance between two lon/lat points in kilometers."""
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


# First pass: collect ALL endpoints from all waterways
# We store: (lon, lat, waterway_index, is_start_point)
all_endpoints = []
waterway_data = []

print("\nExtracting endpoints from waterways...")

for idx, row in linear.iterrows():
    geom = row.geometry
    waterway_type = row.get('waterway', None)
    name = row.get('name', None)
    osm_id = row.get('@id', str(idx))
    
    if geom.geom_type == 'MultiLineString':
        lines = list(geom.geoms)
    else:
        lines = [geom]
    
    for line in lines:
        coords = list(line.coords)
        if len(coords) < 2:
            continue
        
        waterway_idx = len(waterway_data)
        waterway_data.append({
            'coords': coords,
            'waterway_type': waterway_type,
            'name': name,
            'osm_id': osm_id,
            'capacity': CAPACITY_BY_TYPE.get(waterway_type, 15)
        })
        
        # Store start and end points with reference to their waterway
        all_endpoints.append((coords[0][0], coords[0][1], waterway_idx, True))   # start
        all_endpoints.append((coords[-1][0], coords[-1][1], waterway_idx, False)) # end

print(f"Collected {len(all_endpoints)} endpoints from {len(waterway_data)} waterway segments")


# Use KD-Tree to efficiently find all nearby endpoint pairs
# This is much faster than checking every pair manually
endpoint_coords = np.array([(ep[0], ep[1]) for ep in all_endpoints])
tree = cKDTree(endpoint_coords)

# Find all pairs of endpoints within snap threshold
pairs = tree.query_pairs(r=SNAP_THRESHOLD_DEGREES)
print(f"Found {len(pairs)} pairs of endpoints within snap threshold")


# Union-Find algorithm to cluster connected endpoints into single nodes
# If endpoint A is near B, and B is near C, then A, B, C all become one node
parent = list(range(len(all_endpoints)))

def find(x):
    """Find the root parent of element x (with path compression)"""
    if parent[x] != x:
        parent[x] = find(parent[x])
    return parent[x]

def union(x, y):
    """Merge the clusters containing x and y"""
    px, py = find(x), find(y)
    if px != py:
        parent[px] = py

# Union all nearby endpoint pairs
for i, j in pairs:
    union(i, j)


# Group endpoints by their cluster (each cluster becomes one node)
clusters = defaultdict(list)
for i in range(len(all_endpoints)):
    clusters[find(i)].append(i)

print(f"Clustered endpoints into {len(clusters)} unique nodes")


# Create node mapping and compute centroid for each cluster
# The centroid is the average position of all endpoints in the cluster
cluster_to_node = {}
node_to_coord = {}
node_counter = 0

for cluster_id, members in clusters.items():
    lons = [endpoint_coords[m][0] for m in members]
    lats = [endpoint_coords[m][1] for m in members]
    centroid = (sum(lons)/len(lons), sum(lats)/len(lats))
    
    cluster_to_node[cluster_id] = node_counter
    node_to_coord[node_counter] = centroid
    node_counter += 1

# Map each endpoint index to its final node ID
endpoint_to_node = {}
for i in range(len(all_endpoints)):
    cluster_id = find(i)
    endpoint_to_node[i] = cluster_to_node[cluster_id]

print(f"Created {len(node_to_coord)} nodes")


# Build edges from waterway data
# Each waterway becomes an edge connecting its start node to its end node
edges_data = []

for ww_idx, ww in enumerate(waterway_data):
    start_ep_idx = ww_idx * 2      # Start endpoint index
    end_ep_idx = ww_idx * 2 + 1    # End endpoint index
    
    start_node = endpoint_to_node[start_ep_idx]
    end_node = endpoint_to_node[end_ep_idx]
    
    # Skip self-loops (when start and end snapped to same node)
    if start_node == end_node:
        continue
    
    # Calculate actual length along the waterway path
    coords = ww['coords']
    length_km = 0
    for i in range(len(coords) - 1):
        length_km += haversine_distance_km(coords[i], coords[i+1])
    
    edges_data.append({
        'start_node': start_node,
        'end_node': end_node,
        'waterway_type': ww['waterway_type'],
        'name': ww['name'],
        'osm_id': ww['osm_id'],
        'length_km': length_km,
        'capacity': ww['capacity']
    })

print(f"Created {len(edges_data)} edges")


# Build the NetworkX graph
# Using undirected graph since water can flow both ways in most waterways
G = nx.Graph()

# Add nodes with their coordinates
for node_id, coord in node_to_coord.items():
    G.add_node(node_id, lon=coord[0], lat=coord[1])

print(f"Added {G.number_of_nodes()} nodes to graph")

# Add edges with attributes
# If duplicate edge exists, keep the one with higher capacity
for edge in edges_data:
    u, v = edge['start_node'], edge['end_node']
    if not G.has_edge(u, v):
        G.add_edge(u, v,
                   waterway_type=edge['waterway_type'],
                   name=edge['name'],
                   osm_id=edge['osm_id'],
                   length_km=edge['length_km'],
                   capacity=edge['capacity'])
    else:
        existing_cap = G[u][v].get('capacity', 0)
        if edge['capacity'] > existing_cap:
            G[u][v].update(edge)

print(f"Added {G.number_of_edges()} edges to graph")


# Analyze connectivity
num_components = nx.number_connected_components(G)
components = sorted(nx.connected_components(G), key=len, reverse=True)

print(f"\nNumber of connected components: {num_components}")

if num_components == 1:
    print("   Graph is fully connected!")
else:
    print(f"  Graph has {num_components} components")
    print("\n  Largest components:")
    for i, comp in enumerate(components[:10]):
        pct = 100 * len(comp) / G.number_of_nodes()
        print(f"    Component {i+1}: {len(comp)} nodes ({pct:.1f}%)")
    
    main_component_size = len(components[0])
    total_nodes = G.number_of_nodes()
    print(f"\n  Main component: {main_component_size}/{total_nodes} nodes ({100*main_component_size/total_nodes:.1f}%)")


# Graph statistics
print(f"\nGraph statistics:")
print(f"  Total nodes: {G.number_of_nodes()}")
print(f"  Total edges: {G.number_of_edges()}")
avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
print(f"  Average degree: {avg_degree:.2f}")

# Count edges by waterway type
edge_types = defaultdict(int)
for u, v, data in G.edges(data=True):
    edge_types[data.get('waterway_type', None)] += 1

print(f"\nEdges by waterway type:")
for wtype, count in sorted(edge_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {wtype}: {count}")


# Find most connected nodes (major junctions)
degrees = dict(G.degree())
top_junctions = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]

print("\nTop 10 most connected nodes (major junctions):")
for node_id, degree in top_junctions:
    lon = G.nodes[node_id]['lon']
    lat = G.nodes[node_id]['lat']
    print(f"  Node {node_id}: {degree} connections at ({lon:.4f}, {lat:.4f})")

# Find westernmost nodes (potential outlets to Negombo Lagoon)
nodes_sorted_by_lon = sorted(node_to_coord.items(), key=lambda x: x[1][0])
westernmost = nodes_sorted_by_lon[:5]

print("\nWesternmost nodes (potential outlets):")
for node_id, coord in westernmost:
    degree = G.degree(node_id)
    print(f"  Node {node_id}: ({coord[0]:.4f}, {coord[1]:.4f}), {degree} connections")


# Save graph as pickle (preserves all Python data types)
with open("attanagalu_graph.pkl", "wb") as f:
    pickle.dump(G, f)
print("\nSaved graph to: attanagalu_graph.pkl")

# Save node coordinates as JSON for easy access
with open("attanagalu_nodes.json", "w") as f:
    json.dump({str(k): {'lon': v[0], 'lat': v[1]} for k, v in node_to_coord.items()}, f, indent=2)
print("Saved node coordinates to: attanagalu_nodes.json")

# Save summary statistics
summary = {
    'total_nodes': G.number_of_nodes(),
    'total_edges': G.number_of_edges(),
    'connected_components': num_components,
    'main_component_size': len(components[0]) if components else 0,
    'main_component_percentage': 100 * len(components[0]) / G.number_of_nodes() if components else 0,
    'snap_threshold_degrees': SNAP_THRESHOLD_DEGREES,
    'edge_types': dict(edge_types)
}
with open("attanagalu_graph_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("Saved summary to: attanagalu_graph_summary.json")

print("\nCOMPLETE!")