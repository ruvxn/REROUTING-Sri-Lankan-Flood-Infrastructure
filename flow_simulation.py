"""
Phase 2: Flow Simulation
Simulates water flow through the network during a storm event.
Identifies which edges exceed capacity (flooding).
"""

import pickle
import networkx as nx
import json
from collections import defaultdict

# Load the working graph
print("Loading working graph...")
with open("attanagalu_working_graph.pkl", "rb") as f:
    G = pickle.load(f)

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
print(f"Connected components: {nx.number_connected_components(G)}")

# Determine flow direction (East to West)
# Water flows from higher longitude (east) to lower longitude (west)
# This is a simplification - real models use elevation data
print("\nDetermining flow directions...")

G_directed = nx.DiGraph()

# Add all nodes with their attributes
for node in G.nodes():
    G_directed.add_node(node, **G.nodes[node])

# Add directed edges (from east to west, i.e., from higher lon to lower lon)
for u, v, data in G.edges(data=True):
    lon_u = G.nodes[u]['lon']
    lon_v = G.nodes[v]['lon']
    
    if lon_u > lon_v:
        # u is east of v, water flows u -> v
        G_directed.add_edge(u, v, **data)
    elif lon_v > lon_u:
        # v is east of u, water flows v -> u
        G_directed.add_edge(v, u, **data)
    else:
        # Same longitude - use latitude (north to south)
        lat_u = G.nodes[u]['lat']
        lat_v = G.nodes[v]['lat']
        if lat_u > lat_v:
            G_directed.add_edge(u, v, **data)
        else:
            G_directed.add_edge(v, u, **data)

print(f"Created directed graph with {G_directed.number_of_edges()} directed edges")

# Identify source nodes (no incoming edges) and sink nodes (no outgoing edges)
source_nodes = [n for n in G_directed.nodes() if G_directed.in_degree(n) == 0]
sink_nodes = [n for n in G_directed.nodes() if G_directed.out_degree(n) == 0]

print(f"Source nodes (upstream): {len(source_nodes)}")
print(f"Sink nodes (outlets): {len(sink_nodes)}")


# Define storm scenario
print("\nDefining storm scenario...")

# Storm intensity: how much water enters at each node
# Higher values = more severe storm
STORM_INTENSITY = 100

def calculate_rainfall(node, is_source):
    """
    Calculate rainfall amount for a node.
    Source nodes (upstream) receive more water as they drain larger areas.
    """
    if is_source:
        return STORM_INTENSITY * 2.0
    else:
        return STORM_INTENSITY * 0.5

# Calculate total rainfall input
total_rainfall = 0
node_rainfall = {}

for node in G_directed.nodes():
    is_source = node in source_nodes
    rainfall = calculate_rainfall(node, is_source)
    node_rainfall[node] = rainfall
    total_rainfall += rainfall

print(f"Storm intensity: {STORM_INTENSITY} units")
print(f"Total rainfall entering network: {total_rainfall:.1f} units")


# Run flow simulation
print("\nRunning flow simulation...")

# Initialize tracking variables
edge_flow = {}
node_water = dict(node_rainfall)
node_excess = defaultdict(float)
flooded_edges = []

# Get nodes in topological order (upstream to downstream)
# For disconnected components, we process each separately
processing_order = []

for component in nx.weakly_connected_components(G_directed):
    subgraph = G_directed.subgraph(component)
    try:
        order = list(nx.topological_sort(subgraph))
        processing_order.extend(order)
    except nx.NetworkXUnfeasible:
        # Graph has cycles - fall back to sorting by longitude
        order = sorted(component, key=lambda n: -G_directed.nodes[n]['lon'])
        processing_order.extend(order)

print(f"Processing {len(processing_order)} nodes in upstream-to-downstream order")

# Simulate flow propagation
for node in processing_order:
    current_water = node_water[node]
    out_edges = list(G_directed.out_edges(node, data=True))
    
    if not out_edges:
        # This is a sink node - water exits the system here
        continue
    
    # Distribute water to outgoing edges proportionally to their capacity
    total_capacity = sum(data.get('capacity', 15) for _, _, data in out_edges)
    
    for u, v, data in out_edges:
        capacity = data.get('capacity', 15)
        
        proportion = capacity / total_capacity if total_capacity > 0 else 1 / len(out_edges)
        flow = current_water * proportion
        
        edge_flow[(u, v)] = flow
        
        # Check if edge is flooded (flow exceeds capacity)
        if flow > capacity:
            flooded_edges.append({
                'edge': (u, v),
                'flow': flow,
                'capacity': capacity,
                'overflow': flow - capacity,
                'waterway_type': data.get('waterway_type'),
                'name': data.get('name')
            })
            
            node_excess[u] += (flow - capacity)
            actual_flow = capacity
        else:
            actual_flow = flow
        
        node_water[v] = node_water.get(v, 0) + actual_flow

print("Simulation complete!")


# Analyze results
print("\nSIMULATION RESULTS:")
print(f"Total edges: {G_directed.number_of_edges()}")
print(f"Flooded edges: {len(flooded_edges)}")
print(f"Flood rate: {100 * len(flooded_edges) / G_directed.number_of_edges():.1f}%")

total_overflow = sum(e['overflow'] for e in flooded_edges)
print(f"Total overflow volume: {total_overflow:.1f} units")

flooded_nodes = [n for n, excess in node_excess.items() if excess > 0]
print(f"Nodes with local flooding: {len(flooded_nodes)}")

print("\nFLOODED EDGES BY TYPE:")
flood_by_type = defaultdict(list)
for f in flooded_edges:
    flood_by_type[f['waterway_type']].append(f)

for wtype, floods in sorted(flood_by_type.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {wtype}: {len(floods)} edges flooded")

print("\nTOP 10 WORST FLOODED EDGES:")
worst_floods = sorted(flooded_edges, key=lambda x: x['overflow'], reverse=True)[:10]
for i, f in enumerate(worst_floods, 1):
    u, v = f['edge']
    lon_u, lat_u = G_directed.nodes[u]['lon'], G_directed.nodes[u]['lat']
    print(f"{i}. {f['waterway_type']} ({f['name'] or 'unnamed'})")
    print(f"   Flow: {f['flow']:.1f} / Capacity: {f['capacity']} / Overflow: {f['overflow']:.1f}")
    print(f"   Location: ({lon_u:.4f}, {lat_u:.4f})")


# Save results
print("\nSaving results...")

flood_results = {
    'storm_intensity': STORM_INTENSITY,
    'total_rainfall': total_rainfall,
    'total_edges': G_directed.number_of_edges(),
    'flooded_edge_count': len(flooded_edges),
    'flood_rate_percent': 100 * len(flooded_edges) / G_directed.number_of_edges(),
    'total_overflow': total_overflow,
    'flooded_edges': [
        {
            'from_node': int(f['edge'][0]),
            'to_node': int(f['edge'][1]),
            'flow': f['flow'],
            'capacity': f['capacity'],
            'overflow': f['overflow'],
            'waterway_type': f['waterway_type'],
            'name': f['name']
        }
        for f in flooded_edges
    ],
    'flooded_nodes': [int(n) for n in flooded_nodes],
    'node_excess': {str(k): v for k, v in node_excess.items() if v > 0}
}

with open("flood_simulation_results.json", "w") as f:
    json.dump(flood_results, f, indent=2)
print("Saved: flood_simulation_results.json")

edge_flow_data = {
    f"{u}-{v}": {
        'flow': flow,
        'capacity': G_directed[u][v].get('capacity', 15),
        'utilization': flow / G_directed[u][v].get('capacity', 15),
        'flooded': flow > G_directed[u][v].get('capacity', 15)
    }
    for (u, v), flow in edge_flow.items()
}

with open("edge_flows.json", "w") as f:
    json.dump(edge_flow_data, f, indent=2)
print("Saved: edge_flows.json")

with open("attanagalu_directed_graph.pkl", "wb") as f:
    pickle.dump(G_directed, f)
print("Saved: attanagalu_directed_graph.pkl")

print("\nCOMPLETE!")
print(f"Summary: {len(flooded_edges)} edges flooded, {len(flooded_nodes)} nodes with local flooding")
print("Next step: Run visualize_flooding.py to see results on a map")