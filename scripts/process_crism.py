"""Official MTRDR browse coverage, without mineral classification."""

import hashlib
import json

import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.features import shapes
from shapely.geometry import MultiPolygon, shape
from shapely.ops import transform

from backend.config import ROOT
from scripts.cache_crism import main as verify_sources

STEM = 'frt000047a3_07_brtanj_mtr3'


def main() -> None:
    verify_sources()
    source = ROOT / 'data/nasa/crism'
    png = source / (STEM+'.png')
    pixels = np.asarray(Image.open(png))
    if pixels.shape != (808, 847, 4):
        raise ValueError('Unexpected official browse dimensions or alpha mask')
    with rasterio.open(source / (STEM+'.lbl')) as pds:
        rgb = pds.read().transpose(1, 2, 0)
        if not np.array_equal(rgb, pixels[:, :, :3]):
            raise ValueError('PNG and raw browse IMG disagree')
        crs, affine = pds.crs, pds.transform
    with rasterio.open(source / (STEM+'.img')) as envi:
        alternate = envi.transform
    mask = (pixels[:, :, 3] > 0).astype('uint8')
    if not mask.any():
        raise ValueError('CRISM has no valid scene pixels')
    target = ROOT / 'data/processed/crism-browse.tif'
    with rasterio.open(target, 'w', driver='GTiff', width=847, height=808,
                       count=4, dtype='uint8', crs=crs, transform=affine) as out:
        out.write(pixels.transpose(2, 0, 1))
    converter = Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True)
    polygons = [transform(converter.transform, shape(geometry))
                for geometry, value in shapes(mask, mask=mask > 0, transform=affine)
                if value == 1]
    coverage = MultiPolygon(polygons).__geo_interface__
    metadata = {
        'available': True, 'product_id': STEM.upper(), 'observation_id': 'FRT000047A3',
        'processing_level': 'MTRDR processed TAN browse', 'classification': 'DERIVED',
        'resolution_m': 18, 'projection': crs.to_wkt(), 'transform': list(affine)[:6],
        'alternate_envi_transform': list(alternate)[:6],
        'mapping_disagreement_m': [alternate.c-affine.c, alternate.f-affine.f],
        'channels': ['R2529', 'R1330', 'R770'], 'coverage': coverage,
        'bounds_lon_lat': list(shape(coverage).bounds),
        'source': {'file': png.relative_to(ROOT).as_posix(),
                   'sha256': hashlib.sha256(png.read_bytes()).hexdigest(),
                   'url': 'https://pds-geosciences.wustl.edu/mro/'
                          'mro-m-crism-5-rdr-mptargeted-v1/mrocr_4001/'
                          'browse/2007/2007_057/frt000047a3/'+STEM+'.png'},
        'processed_file': target.relative_to(ROOT).as_posix(),
        'processed_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'preview': '/api/assets/crism-preview.png',
        'limitations': [
            'False-color browse channels are display values, not mineral identification.',
            'PDS and ENVI header mappings differ by one 18 m pixel in each axis; '
            'PDS label mapping is used. This does not establish ground registration accuracy.',
            'Partial operational coverage: transparent non-scene pixels remain missing.',
            'The mission science waypoint is illustrative, not a measured mineral discovery.',
        ],
    }
    (ROOT / 'data/processed/crism.json').write_text(json.dumps(metadata, indent=2))
    print(json.dumps({'product': metadata['product_id'], 'valid_pixels': int(mask.sum()),
                      'mapping_disagreement_m': metadata['mapping_disagreement_m']}))


if __name__ == '__main__':
    main()
