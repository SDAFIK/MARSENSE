from math import cos, degrees, radians

from backend.domain import Footprint

# Mars Trek IAU2000 Mars sphere. Scientific analysis never uses the map renderer's CRS.
MARS_RADIUS_M = 3396190.0
ORIGIN_LON = 77.45
ORIGIN_LAT = 18.44
ANALYSIS_CRS = (
    f"+proj=eqc +lat_ts={ORIGIN_LAT} +lat_0=0 +lon_0={ORIGIN_LON} "
    f"+R={MARS_RADIUS_M} +y_0={-MARS_RADIUS_M * radians(ORIGIN_LAT)} +units=m +no_defs"
)


def to_local(lon: float, lat: float) -> tuple[float, float]:
    return (
        MARS_RADIUS_M * radians(lon - ORIGIN_LON) * cos(radians(ORIGIN_LAT)),
        MARS_RADIUS_M * radians(lat - ORIGIN_LAT),
    )


def to_mars(x: float, y: float) -> tuple[float, float]:
    return (
        ORIGIN_LON + degrees(x / (MARS_RADIUS_M * cos(radians(ORIGIN_LAT)))),
        ORIGIN_LAT + degrees(y / MARS_RADIUS_M),
    )


def render_geometry(footprint: Footprint) -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [[to_mars(x, y) for x, y in ring] for ring in footprint.coordinates],
    }
