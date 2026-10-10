# Calibrated cameras and PLACES

Official frozen sources and exact byte hashes: `data/nasa/cameras/source.json`.
Replay PIA26072 remains an illustrative replay; these calibrated products do not
replace saved observations or silently acquire mission verification.

Navcam: `NLF_0013_0668099766_737FDR_N0030028NCAM00112_0A00LLJ05`,
PDS version 5.0, Sol 13, Navigation Camera Left, 1280×960×3 SignedMSB2 DN,
Derived FDR from the calibrated collection. Label SCLK 668099766.737–668099766.957,
site 3/drive 28/pose 4/RSM 2. Exact PLACES RMC validity interval and NAVCAM_LEFT
observation clock match. Camera model CAHVORE and original coordinate references,
transform, articulation and calibration metadata remain in the preserved XML.

Mastcam-Z: `ZL0_0015_0668273255_213RAD_N0030110ZCAM08000_1000LUA01`,
PDS version 1.0, Sol 15, Mast Camera Zoom Left, 1648×1200 SignedMSB2 RAD,
Calibrated processing level. Stored scaling factor 2.014896381e-06 and offset
0.001318487572 are applied to valid numeric pixels; missing/invalid DN=0 stays
masked. Do not invent a physical radiance unit absent from the array label.
Mission SCLK 668273442.102–668273442.119 differs from mini-header
668273438.367. Both original clocks are retained. The corresponding exact
RMC interval covers mission SCLK; no exact observation-clock row matches the
mini-header, so the observation association is explicitly unresolved.

The [official PLACES SIS](https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_rover_places/document/Mars2020_Rover_PLACES_PDS_SIS.pdf),
sections 5.2 and 5.6, distinguishes site/drive anchors, exact versus approximate
clock bounds and early Mastcam-Z clock changes. `best_tactical.csv` SCLK is the
earliest site/drive time; pose=-1 is a wildcard, not an image orientation solution.
The original detailed site 3 XML solution confirms that wildcard. Exact intervals
must contain the entire label interval, match every supplied RMC component and
have one unique static ROVER candidate. Dynamic, missing, ambiguous or merely
approximate matches cannot authorize registration.

The [official camera keyword definitions](https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_mission/document_camera/Mars2020_Camera_SIS_Labels_sort_pds.html)
specify command-dispatch tick notation separately from decimal mission SCLK.
No unverified time conversion is used to force a Mastcam observation match.

Both drive anchors overlap the orbital operational rectangle. Position conversion
uses planetocentric latitude, east longitude and the explicit Mars metric CRS.
Best tactical quaternion/Euler orientation is retained as a drive anchor only.
Mechanism table candidates are retained, but their exact time bounds are empty;
they are not treated as fully validated camera pointing solutions.

No reliable ground footprint follows from this ingestion: distortion/depth and
camera-to-world uncertainty remain unvalidated. `footprint=null` and
`spatial_uncertainty_m=null` mean unavailable/unknown, never zero or an invented
radius. The calibrated data cannot update terrain coverage without a separately
supported observation footprint and human verification.

Reproduce frozen bytes with `python -m scripts.cache_cameras`; changed upstream
bytes fail hash validation. Decode offline with `python -m scripts.process_cameras`.
Original image arrays remain separate from NPZ calibrated values/masks and the
1–99 percentile DERIVED display PNGs. Diagnostic:
`docs/science/s3-camera-diagnostic.png`; quantitative metadata:
`data/processed/cameras.json`. Evidence Inspector exposes provenance and limits.
