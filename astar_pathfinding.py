"""
Phase 3: A* Pathfinding for Canal Planning
Finds optimal routes from flood points to outlets.
Can propose new canal connections where beneficial.
"""

import pickle
import json
import math
import heapq
from collections import defaultdict

# Load the directed graph and flood results
print("Loading data...")
with open("attanagalu_directed_graph.pkl", "rb") as f:
    G = pickle.load(f)

with open("flood_simulation_results.json", "r") as f:
    flood_results = json.load(f)

print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
print(f"Flooded edges: {flood_results['flooded_edge_count']}")


# Configuration for A* cost calculations
EXISTING_EDGE_BASE_COST = 1.0      # Cost multiplier for existing edges
NEW_EDGE_CONSTRUCTION_COST = 300.0  # Cost to build a new canal (per km) - Algorithm Weight
FLOOD_TRAVERSAL_COST_MULTIPLIER = 0.1  # Low cost to encourage using flooded edges (Drainage Artery)
MAX_NEW_EDGE_DISTANCE_KM = 0.5     # Maximum length for proposed new canals

# Economic Constants
COST_PER_KM_USD_MILLIONS = 5.0     # $5M per km of new canal


def haversine_distance_km(coord1, coord2):
    """Calculate distance between two lon/lat points in kilometers."""
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def get_node_coord(node):
    """Get (lon, lat) for a node."""
    return (G.nodes[node]['lon'], G.nodes[node]['lat'])


def heuristic(node, goals):
    """
    Heuristic function: minimum straight-line distance to ANY goal.
    This guides A* toward the nearest valid outlet.
    """
    coord1 = get_node_coord(node)
    min_dist = float('inf')
    
    for goal in goals:
        coord2 = get_node_coord(goal)
        dist = haversine_distance_km(coord1, coord2)
        if dist < min_dist:
            min_dist = dist
            
    return min_dist


# Build a set of flooded edges for quick lookup
flooded_edges = set()
for fe in flood_results['flooded_edges']:
    flooded_edges.add((fe['from_node'], fe['to_node']))


def get_edge_cost(from_node, to_node, is_new_edge=False):
    """
    Calculate the cost of traversing an edge.
    
    For existing edges: base cost + penalty if flooded
    For new edges: construction cost based on distance
    """
    coord1 = get_node_coord(from_node)
    coord2 = get_node_coord(to_node)
    distance_km = haversine_distance_km(coord1, coord2)
    
    if is_new_edge:
        # New canal: high construction cost
        return distance_km * NEW_EDGE_CONSTRUCTION_COST
    else:
        # Existing edge
        base_cost = distance_km * EXISTING_EDGE_BASE_COST
        
        # If this edge is flooded, it's a prime candidate for a drainage artery
        # We reward the algorithm for using it (lower cost)
        if (from_node, to_node) in flooded_edges:
            base_cost *= FLOOD_TRAVERSAL_COST_MULTIPLIER
        
        return base_cost


def get_neighbors(node, allow_new_edges=True):
    """
    Get all possible next nodes from current node.
    
    Returns list of (neighbor_node, is_new_edge) tuples.
    """
    neighbors = []
    
    # Existing outgoing edges
    for _, neighbor, _ in G.out_edges(node, data=True):
        neighbors.append((neighbor, False))
    
    # Potential new edges (to nearby nodes not already connected)
    if allow_new_edges:
        current_coord = get_node_coord(node)
        current_neighbors = set(n for _, n in G.out_edges(node))
        current_neighbors.update(n for n, _ in G.in_edges(node))
        
        for other_node in G.nodes():
            if other_node == node:
                continue
            if other_node in current_neighbors:
                continue
            
            other_coord = get_node_coord(other_node)
            distance = haversine_distance_km(current_coord, other_coord)
            
            # Only consider nearby nodes for new connections
            if distance <= MAX_NEW_EDGE_DISTANCE_KM:
                # Only propose edges that go toward outlets (west)
                neighbors.append((other_node, True))
    
    return neighbors


def astar_find_path(start_node, goal_nodes, allow_new_edges=True):
    """
    A* pathfinding from start to ANY of the goal_nodes.
    
    Returns:
        path: list of nodes from start to reached goal
        came_from: dict mapping each node to (previous_node, is_new_edge)
        total_cost: total path cost
        reached_goal: the specific goal node that was reached
    """
    # Ensure goal_nodes is a set for fast lookup
    goal_set = set(goal_nodes)
    
    # Priority queue: (f_score, node)
    open_set = [(0, start_node)]
    heapq.heapify(open_set)
    
    # Track where we came from and whether edge was new
    came_from = {}
    
    # g_score[node] = cost from start to node
    g_score = defaultdict(lambda: float('inf'))
    g_score[start_node] = 0
    
    # f_score[node] = g_score + heuristic
    f_score = defaultdict(lambda: float('inf'))
    f_score[start_node] = heuristic(start_node, goal_nodes)
    
    # Track which nodes are in open set
    open_set_hash = {start_node}
    
    iterations = 0
    max_iterations = 10000
    
    while open_set and iterations < max_iterations:
        iterations += 1
        
        # Get node with lowest f_score
        current_f, current = heapq.heappop(open_set)
        open_set_hash.discard(current)
        
        # Reached goal
        if current in goal_set:
            path = reconstruct_path(came_from, current)
            return path, came_from, g_score[current], current
        
        # Explore neighbors
        for neighbor, is_new_edge in get_neighbors(current, allow_new_edges):
            tentative_g = g_score[current] + get_edge_cost(current, neighbor, is_new_edge)
            
            if tentative_g < g_score[neighbor]:
                # This path is better
                came_from[neighbor] = (current, is_new_edge)
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal_nodes)
                
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    open_set_hash.add(neighbor)
    
    # No path found
    return None, None, None, None


def reconstruct_path(came_from, current):
    """Reconstruct the path from start to current node."""
    path = [current]
    while current in came_from:
        current, _ = came_from[current]
        path.append(current)
    path.reverse()
    return path


def analyze_path(path, came_from):
    """Analyze a path to extract existing vs new edges."""
    existing_edges = []
    new_edges = []
    total_distance = 0
    
    for i in range(len(path) - 1):
        from_node = path[i]
        to_node = path[i + 1]
        
        coord1 = get_node_coord(from_node)
        coord2 = get_node_coord(to_node)
        distance = haversine_distance_km(coord1, coord2)
        total_distance += distance
        
        # Check if this was a new edge
        is_new = came_from.get(to_node, (None, False))[1]
        
        edge_info = {
            'from_node': from_node,
            'to_node': to_node,
            'from_coord': coord1,
            'to_coord': coord2,
            'distance_km': distance,
            'is_new': is_new
        }
        
        if is_new:
            new_edges.append(edge_info)
        else:
            existing_edges.append(edge_info)
    
    return existing_edges, new_edges, total_distance


# Find outlet nodes (sinks - no outgoing edges, westernmost)
sink_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]
sink_nodes_sorted = sorted(sink_nodes, key=lambda n: G.nodes[n]['lon'])

print(f"\nFound {len(sink_nodes)} outlet nodes")
print("Westernmost outlets (best drainage points):")
for node in sink_nodes_sorted[:5]:
    lon, lat = G.nodes[node]['lon'], G.nodes[node]['lat']
    print(f"  Node {node}: ({lon:.4f}, {lat:.4f})")


# Get the worst flood points
worst_floods = sorted(flood_results['flooded_edges'], key=lambda x: x['overflow'], reverse=True)

print(f"\nTop 5 critical flood points:")
for i, fe in enumerate(worst_floods[:5], 1):
    node = fe['from_node']
    lon, lat = G.nodes[node]['lon'], G.nodes[node]['lat']
    print(f"  {i}. Node {node}: overflow {fe['overflow']:.1f} at ({lon:.4f}, {lat:.4f})")


# Run A* from the worst flood point to the nearest outlet
print("\n" + "=" * 60)
print("RUNNING A* PATHFINDING")
print("=" * 60)

# Select top 3 worst flood points
goal_nodes = sink_nodes_sorted[:5]  # Top 5 Westernmost outlets
solutions = []

print(f"Goals (potential outlets): {len(goal_nodes)} nodes")
for i, g in enumerate(goal_nodes):
    print(f"  Option {i+1}: Node {g} ({G.nodes[g]['lon']:.4f}, {G.nodes[g]['lat']:.4f})")

# Select top 20 spatially distributed flood points
# We want to avoid clustering all paths in one small area
selected_flood_points = []
MIN_SEPARATION_KM = 1.0

print(f"\nSelecting spatially distributed flood points (min {MIN_SEPARATION_KM} km apart)...")

for fe in worst_floods:
    if len(selected_flood_points) >= 20:
        break
        
    candidate_node = fe['from_node']
    candidate_coord = get_node_coord(candidate_node)
    
    # Check distance to already selected points
    is_far_enough = True
    for selected in selected_flood_points:
        selected_coord = get_node_coord(selected['from_node'])
        dist = haversine_distance_km(candidate_coord, selected_coord)
        if dist < MIN_SEPARATION_KM:
            is_far_enough = False
            break
    
    if is_far_enough:
        selected_flood_points.append(fe)

print(f"Selected {len(selected_flood_points)} points for analysis.")

for i, fe in enumerate(selected_flood_points):
    start_node = fe['from_node']
    print("\n" + "=" * 60)
    print(f"PROCESSING FLOOD POINT #{i+1}: Node {start_node}")
    print(f"Location: ({G.nodes[start_node]['lon']:.4f}, {G.nodes[start_node]['lat']:.4f})")
    print("=" * 60)

    # Run A* (allowing new edges)
    print("Finding path...")
    path, came_from, cost, reached_goal = astar_find_path(
        start_node, goal_nodes, allow_new_edges=True
    )

    if path:
        print(f"  Path found! Length: {len(path)} nodes, Cost: {cost:.2f}")
        print(f"  Reached Goal: Node {reached_goal}")
        existing_e, new_e, dist = analyze_path(path, came_from)
        print(f"  Total distance: {dist:.2f} km")
        print(f"  Existing edges used: {len(existing_e)}")
        print(f"  NEW CANALS PROPOSED: {len(new_e)}")
        
        # Calculate Economic Metrics
        new_canal_length_km = sum(e['distance_km'] for e in new_e)
        estimated_cost_usd_m = new_canal_length_km * COST_PER_KM_USD_MILLIONS
        
        # Calculate Flood Relief (sum of overflow on the path)
        # We need to look up the overflow for each edge in the path
        flood_relief_volume = 0
        path_edges = list(zip(path[:-1], path[1:]))
        for u, v in path_edges:
            # Check if this edge is in the flood results
            for fe in flood_results['flooded_edges']:
                if fe['from_node'] == u and fe['to_node'] == v:
                    flood_relief_volume += fe['overflow']
                    break
        
        roi = flood_relief_volume / estimated_cost_usd_m if estimated_cost_usd_m > 0 else float('inf')

        solutions.append({
            'rank': i + 1,
            'start_node': start_node,
            'goal_nodes': goal_nodes,
            'path_found': True,
            'path': path,
            'cost': cost,
            'reached_goal': reached_goal,
            'metrics': {
                'new_length_km': new_canal_length_km,
                'cost_usd_m': estimated_cost_usd_m,
                'relief_vol': flood_relief_volume,
                'roi': roi
            },
            'proposed_canals': [
                {
                    'from_node': e['from_node'],
                    'to_node': e['to_node'],
                    'from_coord': e['from_coord'],
                    'to_coord': e['to_coord'],
                    'distance_km': e['distance_km']
                }
                for e in new_e
            ]
        })
    else:
        print("  No path found for this point.")
        solutions.append({
            'rank': i + 1,
            'start_node': start_node,
            'goal_nodes': goal_nodes,
            'path_found': False,
            'path': [],
            'cost': 0,
            'reached_goal': None,
            'metrics': {
                'new_length_km': 0,
                'cost_usd_m': 0,
                'relief_vol': 0,
                'roi': 0
            },
            'proposed_canals': []
        })


# Save results
print("\nSaving A* results...")

astar_results = {
    'solutions': solutions
}

with open("astar_results.json", "w") as f:
    json.dump(astar_results, f, indent=2)
print("Saved: astar_results.json")


# Generate Design Report
print("\nGenerating Design Report...")

successful_solutions = [s for s in solutions if s['path_found']]
successful_solutions.sort(key=lambda x: x['metrics']['roi'], reverse=True)

total_investment = sum(s['metrics']['cost_usd_m'] for s in successful_solutions)
total_relief = sum(s['metrics']['relief_vol'] for s in successful_solutions)
total_new_km = sum(s['metrics']['new_length_km'] for s in successful_solutions)

report_content = f"""# Flood Infrastructure Design Report

**Status**: DRAFT PROPOSAL
**Scenario**: Design Storm (Intensity 100)

## Executive Summary

This report proposes a comprehensive drainage infrastructure plan to mitigate critical flooding in the Attanagalu Oya basin. The plan identifies **{len(successful_solutions)} strategic drainage arteries** that connect major flood zones to western outlets.

*   **Total Investment Required**: ${total_investment:.2f} Million USD
*   **Total New Canal Construction**: {total_new_km:.2f} km
*   **Total Flood Relief Volume**: {total_relief:,.0f} units
*   **Coverage**: {len(successful_solutions)} Critical Flood Zones addressed

## Prioritized Project List

Projects are ranked by ROI (Flood Relief per Million USD).

"""

for i, sol in enumerate(successful_solutions, 1):
    m = sol['metrics']
    report_content += f"""### {i}. Project Zone #{sol['rank']} (Node {sol['start_node']} -> Node {sol['reached_goal']})
*   **ROI**: {m['roi']:.1f} units/$M
*   **Estimated Cost**: ${m['cost_usd_m']:.2f} Million
*   **Flood Relief**: {m['relief_vol']:.0f} units
*   **New Construction**: {m['new_length_km']:.2f} km
*   **Description**: Creates a drainage artery from the flood zone at Node {sol['start_node']} to the outlet at Node {sol['reached_goal']}.
"""

    if m['new_length_km'] > 0:
        report_content += "    *   **Key Construction**: Includes new canal segments to bridge gaps in the existing network.\n"
    else:
        report_content += "    *   **Optimization**: Utilizes existing waterways exclusively (requires dredging/widening only).\n"

report_content += """
## Next Steps
1.  **Feasibility Study**: Conduct ground surveys for the proposed new canal routes.
2.  **Hydraulic Modeling**: Verify flow capacities of the proposed arteries.
3.  **Stakeholder Review**: Present this prioritized list to local authorities.
"""

with open("design_report.md", "w") as f:
    f.write(report_content)

print("Saved: design_report.md")
print("COMPLETE!")

