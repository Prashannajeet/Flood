# NITA AI - Mohanpura Kundaliya Dam Break & EAP Project

Streamlit deployment package for the NITA AI branded GIS dashboard.

## Streamlit Cloud settings

- Main file path: `streamlit_app.py`
- Requirements file: `requirements.txt`
- Add app secret: `MAPBOX_TOKEN`

The dashboard is embedded from `dashboard.html`; the Mapbox token is injected from Streamlit secrets at runtime.

## Dashboard pages

- **Flood & Hydrology** retains the original `dashboard.html` unchanged.
- **Drone Terrain** uses `drone_terrain.html` with the R04 Mohanpura flights 01-27 survey.
  The final survey AOI, DEM, hillshade and orthomosaic are enabled initially.
  Orthomosaic transparency starts at 50%; each raster has a 0-100% transparency slider.
  Grey and satellite basemaps are available, with Mapbox Outdoors when configured.

Drone sources are UTM 43N (EPSG:32643). Tiles are reprojected to EPSG:3857 for web
basemap alignment, while the cursor displays UTM 43N coordinates. Native zoom levels
11-16 have approximately 2 m ground pixels at maximum zoom; higher zooms overzoom
these display tiles. Source DEM (0.50 m) and ortho (0.2053 m) stay on D: unchanged.
The R04 relative elevation adjustment, remaining AOI gaps and imagery alignment
limitations are retained in the embedded survey details and manifest.

The deployed app only requires Streamlit and the prepared PNG tiles. GIS dependencies
are required locally to regenerate them, not on Streamlit Cloud:

```powershell
python tools_prepare_drone_layers.py --source "D:\01 Project\Development\Mohan_Kundaliya\Drone_Merged_Flights_01_27\R04_Part1_Referenced" --work "D:\01 Project\Development\Mohan_Kundaliya\Data\drone_web_work" --gis-deps "D:\01 Project\Development\Mohan_Kundaliya\MKP_Dam_Break\tools\building_fusion_deps"
```

Regeneration writes `static/drone_terrain/manifest.json` and each layer's PNG tile
pyramid. Intermediate projected rasters stay outside this repository on D:.
