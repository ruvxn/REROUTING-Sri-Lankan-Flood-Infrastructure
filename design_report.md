# Flood Infrastructure Design Report

**Status**: DRAFT PROPOSAL
**Scenario**: Current Simulation
**Currency**: Sri Lankan Rupees (LKR)

## Executive Summary

This report proposes a comprehensive drainage infrastructure plan to mitigate critical flooding in the Attanagalu Oya basin. The plan identifies **10 strategic drainage arteries** that connect major flood zones to western outlets.

*   **Total Investment Required**: 3,670.17 Million LKR
*   **Total New Canal Construction**: 4.59 km
*   **Total Flood Relief Volume**: 13,161 units
*   **Coverage**: 10 Critical Flood Zones addressed

## Prioritized Project List

Projects are ranked by ROI (Flood Relief per Million LKR).

### 1. Project Zone #4 (Node 644 -> Node 208)
*   **ROI**: inf units/Million LKR
*   **Estimated Cost**: 0.00 Million LKR
*   **Flood Relief**: 1215 units
*   **New Construction**: 0.00 km
*   **Description**: Creates a drainage artery from the flood zone at Node 644 to the outlet at Node 208.
    *   **Optimization**: Utilizes existing waterways exclusively (requires dredging/widening only).
### 2. Project Zone #5 (Node 477 -> Node 208)
*   **ROI**: inf units/Million LKR
*   **Estimated Cost**: 0.00 Million LKR
*   **Flood Relief**: 863 units
*   **New Construction**: 0.00 km
*   **Description**: Creates a drainage artery from the flood zone at Node 477 to the outlet at Node 208.
    *   **Optimization**: Utilizes existing waterways exclusively (requires dredging/widening only).
### 3. Project Zone #2 (Node 574 -> Node 208)
*   **ROI**: 5.46 units/Million LKR
*   **Estimated Cost**: 249.35 Million LKR
*   **Flood Relief**: 1362 units
*   **New Construction**: 0.31 km
*   **Description**: Creates a drainage artery from the flood zone at Node 574 to the outlet at Node 208.
    *   **Key Construction**: Includes new canal segments to bridge gaps in the existing network.
### 4. Project Zone #12 (Node 345 -> Node 208)
*   **ROI**: 5.05 units/Million LKR
*   **Estimated Cost**: 353.25 Million LKR
*   **Flood Relief**: 1783 units
*   **New Construction**: 0.44 km
*   **Description**: Creates a drainage artery from the flood zone at Node 345 to the outlet at Node 208.
    *   **Key Construction**: Includes new canal segments to bridge gaps in the existing network.
### 5. Project Zone #10 (Node 206 -> Node 208)
*   **ROI**: 4.41 units/Million LKR
*   **Estimated Cost**: 345.80 Million LKR
*   **Flood Relief**: 1524 units
*   **New Construction**: 0.43 km
*   **Description**: Creates a drainage artery from the flood zone at Node 206 to the outlet at Node 208.
    *   **Key Construction**: Includes new canal segments to bridge gaps in the existing network.
### 6. Project Zone #11 (Node 399 -> Node 208)
*   **ROI**: 2.87 units/Million LKR
*   **Estimated Cost**: 695.90 Million LKR
*   **Flood Relief**: 1994 units
*   **New Construction**: 0.87 km
*   **Description**: Creates a drainage artery from the flood zone at Node 399 to the outlet at Node 208.
    *   **Key Construction**: Includes new canal segments to bridge gaps in the existing network.
### 7. Project Zone #8 (Node 128 -> Node 208)
*   **ROI**: 2.69 units/Million LKR
*   **Estimated Cost**: 527.14 Million LKR
*   **Flood Relief**: 1420 units
*   **New Construction**: 0.66 km
*   **Description**: Creates a drainage artery from the flood zone at Node 128 to the outlet at Node 208.
    *   **Key Construction**: Includes new canal segments to bridge gaps in the existing network.
### 8. Project Zone #1 (Node 444 -> Node 208)
*   **ROI**: 2.64 units/Million LKR
*   **Estimated Cost**: 374.10 Million LKR
*   **Flood Relief**: 988 units
*   **New Construction**: 0.47 km
*   **Description**: Creates a drainage artery from the flood zone at Node 444 to the outlet at Node 208.
    *   **Key Construction**: Includes new canal segments to bridge gaps in the existing network.
### 9. Project Zone #13 (Node 397 -> Node 208)
*   **ROI**: 2.56 units/Million LKR
*   **Estimated Cost**: 656.29 Million LKR
*   **Flood Relief**: 1677 units
*   **New Construction**: 0.82 km
*   **Description**: Creates a drainage artery from the flood zone at Node 397 to the outlet at Node 208.
    *   **Key Construction**: Includes new canal segments to bridge gaps in the existing network.
### 10. Project Zone #14 (Node 175 -> Node 208)
*   **ROI**: 0.72 units/Million LKR
*   **Estimated Cost**: 468.34 Million LKR
*   **Flood Relief**: 335 units
*   **New Construction**: 0.59 km
*   **Description**: Creates a drainage artery from the flood zone at Node 175 to the outlet at Node 208.
    *   **Key Construction**: Includes new canal segments to bridge gaps in the existing network.

## Next Steps
1.  **Feasibility Study**: Conduct ground surveys for the proposed new canal routes.
2.  **Hydraulic Modeling**: Verify flow capacities of the proposed arteries.
3.  **Stakeholder Review**: Present this prioritized list to local authorities.

## Technical Implementation

### 1. Algorithmic Core
*   **Graph Theory**: The canal network is modeled as a **Directed Graph (DiGraph)** where nodes represent junctions and edges represent canal segments.
*   **Pathfinding**: We utilize the **A* (A-Star) Search Algorithm** to find optimal drainage routes.
    *   **Heuristic**: Euclidean distance to the nearest western outlet.
    *   **Cost Function**: `f(n) = g(n) + h(n)`, where `g(n)` is the traversal cost.

### 2. Strategic Optimization
*   **Inverted Cost Logic**: To maximize flood relief, we invert the cost for traversing flooded edges.
    *   **Flooded Edge Cost**: `Length * 0.1` (Incentivizes routing through floods).
    *   **Normal Edge Cost**: `Length * 1.0`.
    *   **New Construction Cost**: `Length * 5.0` (Penalizes land acquisition).
*   **Spatial Diversity**: The algorithm enforces a minimum separation of **1.0 km** between selected flood points to ensure a distributed drainage network, avoiding clustered solutions.

### 3. Simulation Engine
*   **Hydraulic Modeling**: A flow simulation propagates rainfall runoff through the graph. Edges exceeding their capacity (`Q > Q_max`) are flagged as "Flooded".
*   **Dynamic Scenarios**: The system supports variable `STORM_INTENSITY` inputs (0-500) to test infrastructure resilience under different climate scenarios.

### 4. Technology Stack
*   **Backend**: Python (NetworkX, Folium, Flask).
*   **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript.
*   **Visualization**: Interactive Leaflet maps with AntPath animations.
