import pandas as pd
import geopandas as gpd
from collections import Counter 

print("importing data")

gdf = gpd.read_file("attanagalu.geojson")
#print(gdf.head())

print(f"Total features loaded: {len(gdf)}")
print(f"Coordinate Reference System (CRS): {gdf.crs}")
print()

print("data structure")
print("Columns in the dataset:")
for col in gdf.columns:
    print(f"  - {col}")
print()

print("First 5 features (preview):")
print(gdf.head())
print()

print("FEATURE TYPE ANALYSIS")
geom_types = gdf.geometry.geom_type.value_counts()
print("Geometry types:")
print(geom_types)
print()

if 'waterway' in gdf.columns:
    waterway_counts = gdf['waterway'].value_counts(dropna=False)
    print("Waterway types:")
    print(waterway_counts)
    print()
else:
    print("No 'waterway' column found")
    print()

if 'natural' in gdf.columns:
    natural_counts = gdf['natural'].value_counts(dropna=False)
    print("Natural features:")
    print(natural_counts)
    print()

if 'water' in gdf.columns:
    water_counts = gdf['water'].value_counts(dropna=False)
    print("Water body types:")
    print(water_counts)
    print()

print("NAMED FEATURES (Rivers, Canals with Names)")

if 'name' in gdf.columns:
    named_features = gdf[gdf['name'].notna()][['name', 'waterway', 'natural']].drop_duplicates()
    print(f"Found {len(named_features)} unique named features:")
    print(named_features.head(20))  # Show first 20
    print()
else:
    print("No 'name' column found")
    print()

print("GEOGRAPHIC EXTENT")

bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
print(f"Bounding Box:")
print(f"  Min Longitude: {bounds[0]:.4f}")
print(f"  Min Latitude:  {bounds[1]:.4f}")
print(f"  Max Longitude: {bounds[2]:.4f}")
print(f"  Max Latitude:  {bounds[3]:.4f}")
print()

print("LINEAR FEATURES (Rivers, Streams, Canals)")

linear_features = gdf[gdf.geometry.geom_type.isin(['LineString', 'MultiLineString'])]
print(f"Total linear features (potential flow network): {len(linear_features)}")

if len(linear_features) > 0 and 'waterway' in linear_features.columns:
    print("\nBreakdown by waterway type:")
    print(linear_features['waterway'].value_counts())
print()

summary = {
    'total_features': len(gdf),
    'linear_features': len(linear_features),
    'polygon_features': len(gdf) - len(linear_features),
    'geometry_types': geom_types.to_dict(),
    'bounds': {
        'min_lon': bounds[0],
        'min_lat': bounds[1],
        'max_lon': bounds[2],
        'max_lat': bounds[3]
    }
}

print(f"Summary: {len(linear_features)} linear features (rivers/canals/streams)")
print(f"         {len(gdf) - len(linear_features)} polygon features (water bodies)")
print()