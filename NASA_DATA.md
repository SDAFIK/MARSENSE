> **Current prototype checkpoint — 2026-10-10:** S1–S10 workflow implementation,
> source matrix, claim audit and deployment preparation are recorded in
> [FINAL_AUDIT.md](FINAL_AUDIT.md). Validation: 70 backend tests, 3 component tests,
> 24 browser checks plus 1 authenticated browser flow; static checks and build pass.
> Source reliability remains partial: weak model classification is disabled,
> camera footprints are unknown, and CRISM coverage/registration limits remain.
> This is a research and mission-concept prototype, not full scientific validation.
> Nothing is publicly deployed. Earlier counts/gaps below are historical snapshots.

# NASA data, ingestion and scientific provenance

Evidence inventory reviewed 2026-10-10. Real NASA imagery is distinct from
illustrative mission terrain assumptions and simulated camera registration.

## Cached assets

| Dataset | Exact product / location | Use and provenance limitation |
| --- | --- | --- |
| CTX controlled Jezero mosaic | JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0; data/nasa/jezero-ctx.png | Mars Trek bounded crop; illustrative soil prior is not a NASA terrain measurement |
| HiRISE controlled Jezero mosaic | JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd; data/nasa/jezero-hirise.png | Bounded display crop at cached WMTS level 14; do not describe delivered crop as native 25 cm pixels |
| Navcam public-release mosaic | PIA26072, data/nasa/PIA26072.jpg and ground-navcam.jpg | Real boulder-field image, fictional EVA footprint; resized JPEG derivative, not calibrated PDS image |

The [official JPL product page](https://www.jpl.nasa.gov/images/pia26072-perseverance-makes-tracks-in-boulder-field/)
identifies PIA26072 as Perseverance Navcam imagery acquired on 2023-07-28, sol 866,
showing Snowdrift Peak. Original source URL is recorded in
data/processed/manifest.json. This is not a helmet camera measurement and its
simulated Jezero footprint is not its actual PLACES location.

Current manifest records source layer, bounds, render corners, analysis/source
CRS description, cached WMTS capability file, tile URLs/files/SHA-256, crop hash,
pixel dimensions, ground credit/acquisition and processing/registration notes.
Ground derivative hash, explicit effective crop resolution, typed classification,
per-evidence provenance and schema validation are still required.

## Bounded flow and reproducibility

NASA source → bounded adapter → product validation → normalization to Mars CRS →
crop/processing → provenance → local cache → backend → domain → frontend.

The existing script is runnable from the repository root:

```powershell
.venv\Scripts\python.exe scripts/cache_nasa.py --hirise-layer JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd --hirise-zoom 14
```

It reads cached downloads when present; downloads at most 16 tiles per crop;
caps each download at 10 MiB; uses a 40-second timeout; rejects unsupported matrix
dimensions/fully transparent coverage; crops the 1,200 × 800 m region. Existing
raw tiles and capabilities are retained. Runtime mission requests make no NASA
calls. Record processing version and validate SHA-256 before accepting the cache;
download/crop replacement should be atomic to prevent a partial cache on failure.

WMTS current source endpoints:

- [CTX capabilities](https://trek.nasa.gov/tiles/Mars/EQ/JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0/1.0.0/WMTSCapabilities.xml)
- [HiRISE capabilities](https://trek.nasa.gov/tiles/Mars/EQ/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/1.0.0/WMTSCapabilities.xml)

Live capability fetching could not be verified by the web reader in this audit.
Local cached XML is the inspectable integration evidence. Service metadata uses
IAU2000 Mars equirectangular display tiles. Scientific analysis uses the explicit
local metric CRS in ROUTING_LOGIC.md. The initial manifest omitted the y_0 offset
present in backend/spatial.py. CTX was corrected during concurrent work; HiRISE
still differs from the backend CRS in the isolated audit. Reconcile both before
the coordinate gate passes.
Pixel-rounded crop bounds must describe the actual crop geotransform, rather than
silently claiming the requested bounds are exact at coarse resolution.

## Required data not yet integrated

| Source | Required next adapter/validation | Status |
| --- | --- | --- |
| HiRISE DTM | Product label, coverage/NoData/vertical datum, bounded raster window, Mars reprojection, slope derivation and sample validation | Candidate label/range sampler and DEM adapter now exist; cached candidate reports zero valid coverage, so no active DEM slope |
| MOLA MEGDR | Bounded topography/areoid product and source resolution, regional context fallback | Native 9×9 topography context crop now cached; coarse data cannot justify astronaut-scale slope |
| CRISM processed product | Selected mapped spectral/browse product with label and defensible science-target linkage | Not implemented; camera imagery cannot identify minerals |
| Calibrated Navcam/Mastcam-Z | PDS product identifiers and calibration metadata, cached bounded selections | Not implemented; PIA26072 does not satisfy calibrated imagery requirement |
| Mars 2020 PLACES | Product label, frame/pose/time/site-drive interpretation; explicit map frame conversion | Tactical CSV/XML and 42 local rover poses now cached; camera/image registration remains incomplete |
| AI4Mars | Bounded labeled subset, license/provenance, versioned train/validation/test split and model contract | Four-class adapter and training/export pipeline exist; no genuine dataset/validated checkpoint cached |

[PDS Mars 2020 archive documentation](https://pds-geosciences.wustl.edu/missions/mars2020/index.htm)
provides official engineering-camera, Mastcam-Z and PLACES archive entry points.
[PLACES documents](https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_rover_places/document/)
include its software interface specification; use frame definitions, not arbitrary
CSV column assumptions.

[PDS MOLA MEGDR documentation](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html)
distinguishes radius, areoid, topography and observation counts; retain the exact
selected product label and units. The archive page currently points to maintained
PDS4 products. [PDS CRISM documentation](https://pds-geosciences.wustl.edu/missions/mro/crism.htm)
is the authoritative starting point for processed spectral products; no selected
Jezero CRISM product has been verified in this checkpoint.

[NASA AI4Mars catalog](https://data.nasa.gov/dataset/ai4mars-a-dataset-for-terrain-aware-autonomous-driving-on-mars)
describes terrain-model training and validation data, including expert labels.
The [AI4Mars research paper](https://openaccess.thecvf.com/content/CVPR2021W/AI4Space/papers/Swan_AI4MARS_A_Dataset_for_Terrain-Aware_Autonomous_Driving_on_Mars_CVPRW_2021_paper.pdf)
defines soil, bedrock, sand and big-rock classes. Compatibility with those classes
does not establish performance on Perseverance or astronaut imagery.

Optional MEDA, MCS, MARCI, SuperCam, SHARAD and SPICE are deferred. Never download
entire archives to satisfy a checklist. No required source is silently marked
optional or replaced by fabricated data; unresolved products keep Gate 4 open.

## Concurrent-work update

Resumed implementation: actual pixel-rounded CTX/HiRISE crop bounds and effective
display resolution are now recorded; both analysis CRSs match the independent
PROJ-engine check. Source tiles were reused, with no new imagery downloads.
scripts/cache_hirise_dtm.py acquired bounded native ranges from
DTEEC_045994_1985_046060_1985_U01. All 651 mission grid nodes contain valid
elevation. Its PDS label verifies PC_REAL, source sphere/projection, meter units
and Mars 2000 equipotential datum. Raw range hashes and the 40 m nearest-sample
processing are in manifest.dtm_covering; slope is a coarse planning derivative,
not astronaut-scale hazard certification. Existing mission routes are preserved;
the new grid is not silently activated against saved routes.
The original zero-coverage candidate remains retained separately.

The official [USGS STAC catalog](https://stac.astrogeology.usgs.gov/api/collections/mro_hirise_socet_dtms)
and [HiRISE source page](https://hirise.lpl.arizona.edu/dtm/ESP_045994_1985)
provided the product selection. NASA's AI4Mars resource now points to
[release 0.6 on Zenodo](https://zenodo.org/records/15995036), whose metadata reports
CC BY 4.0. The merged ZIP is 16,232,481,989 bytes; a bounded HTTP-range probe
returned 206. No full archive is downloaded and no model validation is claimed
from this access check.

The user confirmed another chat is implementing in this workspace. During this
audit scripts/cache_context.py, scripts/process_dem.py and the above partial
products appeared. Exact byte-range downloads refuse a server that does not
return the requested 206 range. Current candidate DTM
DTEEC_048842_1985_048908_1985_U01 has coverage_fraction=0.0; a cache file is not
proof of usable mission elevation. MOLA MEGT44N000HB.IMG retains a roughly 463 m
native pixel; PLACES best_tactical records do not prove image pointing/footprint.
See docs/NASA_DATA.md for the other chat's detailed adapter notes; the present
root document records required final acceptance and the observed checkpoint.

## Scientific completion S1 — current checkpoint

Official covering product: DTEEC_045994_1985_046060_1985_U01, selected from
https://hirise.lpl.arizona.edu/dtm/ESP_045994_1985 . Attached PDS metadata
and source byte hashes are retained in data/processed/hirise-covering-slope.json.
Native coverage bounds, equirectangular planetocentric source CRS, 1.0096633268711 m
pixel size, IEEE missing constant and Mars 2000 equipotential vertical datum
are recorded. Native source radius differs from the mission analysis radius;
sampling explicitly converts through planetocentric longitude/latitude.

Reproduce with `.venv\Scripts\python.exe -m scripts.cache_hirise_dtm`; cached
exact PDS ranges enable offline reuse. Raw range bytes, sampled elevation TIFF
and derived slope NPZ remain separate. All 651 operational cells have valid
elevation. Ingestion and configured slope loading now reject incomplete
operational coverage; loader requires matching Mars analysis CRS metadata.
Missing configured files are errors. Empty slope configuration remains visibly
unavailable rather than measured zero slope.

Enable explicitly for a new/local validation run using
`MARSENSE_SLOPE_PATH=data/processed/hirise-covering-slope.npz`. Existing services
and saved routes were not silently restarted or rewritten. MARSENSE prototype
route weights: slope cost = edge length * slope degrees / 10; slopes above
20 degrees excluded. These are configuration choices, not NASA EVA-safe limits.

Diagnostic: docs/science/s1-dtm-alignment.png and s1-route.geojson, generated
by `python -m scripts.debug_dtm`. White route overlays the identical 40 m
node grid on elevation and slope. GeoJSON rendering longitude/latitude is
presentation only; metric coordinates remain in feature properties. HiRISE
rendering now uses its own actual crop bounds; CTX/HiRISE switching updates
the image coordinates together with the URL. No product redesign.

Checks cover real cached coverage and known samples, grid/route intersection,
partial no-data refusal, CRS mismatch, independent PROJ round trip, synthetic
plane gradient sanity and cost changes. The coarse 40 m slope cannot validate
foot-scale obstacles or operational EVA safety. Complete regression results
are recorded in STATUS.md after execution. S2 remains pending until S1 review passes.

## S2 acquisition source

NASA Open Data links Zenodo record 15995036 (DOI 10.5281/zenodo.15995036), merged AI4Mars 0.6. Original release record, label key, info/changelog, archive index and exact bounded range cache are retained in data/nasa/ai4mars. NAV 0..3/255 only; M2020 geology taxonomy excluded. Subset acquisition separates complete MSL site groups, expert held-out sites and independent Perseverance transfer. Source research: docs/science/S2_RESEARCH.md. Checkpoint/model card remain pending genuine evaluation; synthetic unit metrics are never benchmark metrics.
# S3 calibrated camera ingestion

Two actual calibrated PDS Navcam/Mastcam-Z products are cached with byte hashes,
original XML and numeric arrays; see docs/science/S3_RESEARCH.md and
data/nasa/cameras/source.json. Exact clock/RMC intervals support drive-anchor
context. Navcam observation time matches; Mastcam mini-header/observation time
association remains unresolved. No exact camera footprint or centimeter accuracy
is claimed. DERIVED previews and quantitative calibrated arrays are separate.
