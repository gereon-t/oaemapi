# Obstruction Adaptive Elevation Mask API
![](images/oaemapi.jpg)
This API computes an Obstruction Adaptive Elevation Mask (OAEM) for a given position using CityGML models. An OAEM describes the obstruction of the sky view, e.g. due to buildings, using azimuth and elevation pairs. The term Obstruction Adaptive Elevation Mask was first used by [Zimmermann 2019](https://www.researchgate.net/publication/329833465_GPS-Multipath_Analysis_using_Fresnel-Zones). The CityGML models can either be retrieved from [local file storage](https://www.opengeodata.nrw.de/produkte/geobasis/3dg/lod2_gml/lod2_gml/) or from the [Web-Feature-Service (WFS) of Geobasis North Rhine-Westphalia (NRW)](https://www.wfs.nrw.de/geobasis/wfs_nw_3d-gebaeudemodell_lod1).

Geoid information are provived by:

> © [BKG](https://www.bkg.bund.de/) (Jahr des letzten Datenbezugs) [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), Datenquellen: https://sgx.geodatenzentrum.de/web_public/Datenquellen_Quasigeoid.pdf

The code is designed for LOD1 or LOD2 building models from Geobasis NRW, Germany. In its current state, it is therefore only applicable within North Rhine-Westphalia, Germany.

An OAEM can be useful in various scenarios including GNSS Signal filtering:

![](images/oaem.gif)



## Installation

```bash
git clone https://github.com/gereon-t/oaemapi.git
```

```bash	
cd oaemapi
```

```bash
poetry install
```

## Usage
Run the server with
```bash
uvicorn main:app --host 0.0.0.0
```

You can find information about the Endpoints at http://127.0.0.1:8000/docs after starting the server.