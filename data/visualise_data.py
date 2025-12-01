import geopandas as gpd
import folium
from folium import plugins

gdf = gpd.read_file("attanagalu.geojson")

linear = gdf[gdf.geometry.geom_type.isin(['LineString', 'MultiLineString'])].copy()
polygons = gdf[gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])].copy()

print(f"Linear features: {len(linear)}")
print(f"Polygon features: {len(polygons)}")

print("Creating map...")

bounds = gdf.total_bounds
center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles='OpenStreetMap'
)

waterway_colors = {
    'river': '#08306b',      # Dark blue - main rivers
    'canal': '#2171b5',      # Medium blue - canals
    'drain': '#4292c6',      # Light-medium blue - drains
    'stream': '#6baed6',     # Light blue - streams
    'ditch': '#9ecae1',      # Very light blue - ditches
    'dam': '#d62728',        # Red - dams (control structures)
    None: '#cccccc'          # Gray - unclassified
}

waterway_weights = {
    'river': 4,
    'canal': 3,
    'drain': 2,
    'stream': 2,
    'ditch': 1,
    'dam': 5,
    None: 1
}

for idx, row in linear.iterrows():
    waterway_type = row.get('waterway', None)
    name = row.get('name', 'Unnamed')
    
    color = waterway_colors.get(waterway_type, '#cccccc')
    weight = waterway_weights.get(waterway_type, 1)
    
    # Create popup with feature info
    popup_text = f"""
    <b>Type:</b> {waterway_type}<br>
    <b>Name:</b> {name}<br>
    <b>ID:</b> {row.get('@id', 'N/A')}
    """
    
    # Convert geometry to folium format and add to map
    if row.geometry.geom_type == 'LineString':
        coords = [(point[1], point[0]) for point in row.geometry.coords]
        folium.PolyLine(
            coords,
            color=color,
            weight=weight,
            opacity=0.8,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)


print("Adding water bodies to map...")

for idx, row in polygons.iterrows():
    name = row.get('name', 'Unnamed water body')
    water_type = row.get('water', row.get('natural', 'unknown'))
    
    popup_text = f"""
    <b>Name:</b> {name}<br>
    <b>Type:</b> {water_type}
    """
    
    # Add polygon
    if row.geometry.geom_type == 'Polygon':
        coords = [(point[1], point[0]) for point in row.geometry.exterior.coords]
        folium.Polygon(
            coords,
            color='#08519c',
            fill=True,
            fill_color='#6baed6',
            fill_opacity=0.4,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)

legend_html = '''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 150px; height: 180px; 
            border:2px solid grey; z-index:9999; font-size:12px;
            background-color:white; padding: 10px;
            border-radius: 5px;">
<b>Waterway Types</b><br>
<i style="background:#08306b; width:20px; height:10px; display:inline-block;"></i> River<br>
<i style="background:#2171b5; width:20px; height:10px; display:inline-block;"></i> Canal<br>
<i style="background:#4292c6; width:20px; height:10px; display:inline-block;"></i> Drain<br>
<i style="background:#6baed6; width:20px; height:10px; display:inline-block;"></i> Stream<br>
<i style="background:#9ecae1; width:20px; height:10px; display:inline-block;"></i> Ditch<br>
<i style="background:#d62728; width:20px; height:10px; display:inline-block;"></i> Dam<br>
<i style="background:#6baed6; width:20px; height:10px; opacity:0.4; display:inline-block;"></i> Water Body
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

output_file = "attanagalu_waterways_map.html"
m.save(output_file)
print(f"\nMap saved to: {output_file}")