# NASA data, coordinates and provenance

The main project document requires all eight source families. Their status is explicit below; a source link or importer is not equivalent to validated operational integration.

| Source | Current status / use | Scientific completion requirement |
|---|---|---|
| CTX | Cached NASA Mars Trek controlled ortho mosaic crop, hashes and WMTS capabilities; regional context | Validate mission interpretation independently of imagery |
| HiRISE imagery | Cached controlled ortho mosaic crop; switchable map layer | Native-resolution hazard analysis and registration accuracy |
| HiRISE DTM | Attached PDS label and exact byte ranges sampled for candidate DTEEC_048842_1985_048908_1985_U01; sampled extent is no-data | Acquire a covering Jezero controlled DTM, verify units/coverage and activate slope |
| MOLA | Real 9×9 native regional elevation crop from MEGT44N000HB, exact source ranges and label | Regional fallback only; retain interpolation/resolution caveats |
| Navcam | Real NASA/JPL public-release PIA26072 mosaic, source hash, sol and attribution | Calibrated PDS product and validated camera/pose footprint |
| Mastcam-Z | Required, not yet ingested | Select calibrated PDS imagery, normalize camera metadata and ground registration |
| PLACES | Actual PDS best-tactical localization CSV/XML and bounded local rover-pose GeoJSON | Join real image SCLK/site/drive, mechanism angles and camera pointing; do not assign the demo image these poses |
| AI4Mars | Tested local training/evaluation/export pipeline; genuine dataset/checkpoint not bundled | Acquire labeled corpus, disjoint evaluation and Perseverance transfer validation |
| CRISM | Required mineral/science context, not yet ingested | Validated MTRDR/MRDR product/summary bands and georegistered science context; no RGB mineral inference |

HiRISE imagery and DTM are separate products within the HiRISE family. Demo habitat, delta target, low-obstacle soil prior and all observation footprints are illustrative. Navcam PIA26072 is Snowdrift Peak on sol 866 (2023-07-28); it is not the mission area's actual image. The UI and evidence metadata disclose that registration is simulated.

`data/processed/manifest.json` preserves source URLs, product IDs, capabilities, source bytes/ranges, SHA-256 hashes, crop bounds and coordinate notes. `python scripts/cache_nasa.py --hirise-layer JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd --hirise-zoom 14` regenerates the bounded imagery cache. `python -m scripts.cache_context` regenerates the DTM/MOLA/PLACES cache. Existing exact-range assets are reused. Servers must return the requested 206 range; otherwise the script refuses a whole-archive fallback.

Analysis uses an explicit local equirectangular Mars sphere with radius 3,396,190 m, central longitude 77.45° E, latitude of true scale 18.44° N and false northing placing the origin at 18.44° N. Coordinates are meters over 1200×800 m. Source products retain their own declared radii/projection/datum; DEM reprojecting requires a Mars CRS. Rendering converts local coordinates into longitude/latitude for MapLibre's visual projection. It is not used for scientific distances, slope or scale. The map's 40 m grid label refers to the analysis grid, not an Earth scale bar. PLACES uses planetocentric latitude; planetodetic latitude is not substituted.

MOLA is about 463 m per native pixel at the equator; resampling cannot increase information. The candidate DTM has nominal ~1 m native spacing but no valid sampled pixels here. Neither is silently presented as operational hazard ground truth.

Primary sources:

- [NASA Mars Trek API](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars)
- [HiRISE candidate Jezero DTM](https://hirise.lpl.arizona.edu/dtm/ESP_048842_1985)
- [PDS MOLA MEGDR](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html)
- [NASA/JPL Navcam PIA26072](https://www.jpl.nasa.gov/images/pia26072-perseverance-makes-tracks-in-boulder-field/)
- [PDS Mars 2020 PLACES](https://pds-geosciences.wustl.edu/missions/mars2020/places.htm)
- [AI4Mars NASA dataset](https://data.nasa.gov/dataset/ai4mars-a-dataset-for-terrain-aware-autonomous-driving-on-mars)
- [PDS Mars 2020 Navcam calibrated bundle](https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn:nasa:pds:mars2020_navcam_ops_calibrated)
- [PDS Mars 2020 Mastcam-Z calibrated bundle](https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn:nasa:pds:mars2020_mastcamz_sci_calibrated)
- [PDS CRISM](https://pds-geosciences.wustl.edu/missions/mro/crism.htm)

Resumption update: scripts/cache_hirise_dtm.py obtained DTEEC_045994_1985_046060_1985_U01 by exact ranges, with 100% valid mission-node coverage. PDS label verifies source CRS, meter elevation and Mars 2000 datum. The 40 m nearest-sample/gradient products are coarse planning context and are not silently applied to existing routes. Original zero-coverage candidate remains retained. CTX/HiRISE corners now reflect actual rounded pixels and effective resolution. See root NASA_DATA.md for official source links and remaining required gaps.
