"""Offline calibrated camera decoding and conservative PLACES association."""

import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from backend.camera import exact_clock_join, parse_label
from backend.config import ROOT
from backend.spatial import to_local
from scripts.cache_cameras import main as verify_sources

CAMERAS = ROOT / 'data/nasa/cameras'
PRODUCTS = {
    'navcam': ('NLF_0013_0668099766_737FDR_N0030028NCAM00112_0A00LLJ05',
               'mars2020_navcam_ops_calibrated/data/sol/00013/ids/fdr/ncam/'),
    'mastcamz': ('ZL0_0015_0668273255_213RAD_N0030110ZCAM08000_1000LUA01',
                'mars2020_mastcamz_sci_calibrated/data/0015/rad/'),
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline='') as source:
        return list(csv.DictReader(source))


def main() -> None:
    verify_sources()
    intervals = rows(CAMERAS / 'sclk_table.csv')
    observations = rows(CAMERAS / 'observations.csv')
    mechanisms = rows(CAMERAS / 'mech_rsm.csv')
    positions = rows(ROOT / 'data/nasa/places-best-tactical.csv')
    records = {}
    for key, (stem, archive) in PRODUCTS.items():
        label = CAMERAS / (stem + '.xml')
        metadata = parse_label(label)
        raw_path = CAMERAS / metadata['file_name']
        raw = raw_path.read_bytes()
        if metadata['array_type'] != 'SignedMSB2':
            raise ValueError('Unsupported calibrated array type')
        if metadata['axis_index_order'] != 'Last Index Fastest':
            raise ValueError('Unsupported calibrated axis order')
        dim = metadata['dimensions']
        expected_axes = ['Band', 'Line', 'Sample'] if 'Band' in dim else ['Line', 'Sample']
        if metadata['axis_order'] != expected_axes:
            raise ValueError('Unsupported calibrated array sequence')
        shape = (dim.get('Band', 1), dim['Line'], dim['Sample'])
        count = int(np.prod(shape))
        offset = metadata['array_offset']
        if len(raw) < offset + count * 2:
            raise ValueError('Truncated calibrated image')
        dn = np.frombuffer(raw, dtype='>i2', count=count, offset=offset).reshape(shape)
        valid = dn != 0  # Official image labels: missing_constant and invalid_constant = 0.
        values = dn.astype('float32') * float(metadata['scaling_factor'])
        values += float(metadata['value_offset'])
        target = ROOT / 'data/processed' / (key + '-calibrated.npz')
        np.savez_compressed(target, values=values, valid=valid)
        low, high = np.percentile(values[valid], [1, 99])
        preview = (np.clip((values - low) / max(high - low, 1e-9), 0, 1) * 255)
        preview[~valid] = 0
        pixels = preview.astype('uint8')
        if shape[0] == 3:
            image = Image.fromarray(pixels.transpose(1, 2, 0))
        elif shape[0] == 1:
            image = Image.fromarray(pixels[0]).convert('RGB')
        else:
            raise ValueError('Unsupported display band count')
        preview_path = ROOT / 'data/processed' / (key + '-preview.png')
        image.save(preview_path)
        start, stop = Decimal(metadata['sclk']), Decimal(metadata['sclk_stop'])
        interval = (exact_clock_join(metadata['rmc'], start, stop, intervals)
                    if metadata['clock_partition'] == 1 else None)
        observation = [r for r in observations
                       if r['sclk'] == metadata['places_observation_sclk']]
        rmc = metadata['rmc']
        candidates = [r for r in positions if r['frame'] == 'ROVER'
                      and r['site'] == str(rmc['SITE']) and r['drive'] == str(rmc['DRIVE'])]
        position = candidates[0] if interval and len(candidates) == 1 else None
        mechanism = [r for r in mechanisms if r['site'] == str(rmc['SITE'])
                     and r['drive'] == str(rmc['DRIVE']) and r['rsm'] == str(rmc['RSM'])]
        metadata.update({
            'source_url': 'https://planetarydata.jpl.nasa.gov/img/data/mars2020/' + archive,
            'raw_file': raw_path.relative_to(ROOT).as_posix(),
            'raw_sha256': hashlib.sha256(raw).hexdigest(),
            'processed_file': target.relative_to(ROOT).as_posix(),
            'processed_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'preview_file': preview_path.relative_to(ROOT).as_posix(),
            'preview_processing': '1–99 percentile display stretch; not quantitative radiometry',
            'places_exact_interval': interval, 'places_observations': observation,
            'mechanism_candidates': mechanism, 'drive_anchor': position,
            'orientation_scope': 'Best tactical site/drive anchor; pose=-1, not exact image pose',
        })
        if position:
            lon, lat = float(position['longitude']), float(position['planetocentric_latitude'])
            x, y = to_local(lon, lat)
            metadata['rover_local_m'] = [x, y]
            metadata['operational_region_overlap'] = 0 <= x <= 1200 and 0 <= y <= 800
        else:
            metadata['rover_local_m'] = None
            metadata['operational_region_overlap'] = False
        if not observation:
            metadata['limitations'].append('No exact PLACES observation-clock match; '
                                           'label clock variants remain unresolved.')
        metadata['limitations'].append('Mechanism values have no exact validity interval '
                                       'in this table; retained as candidates only.')
        records[key] = metadata
    provenance = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in CAMERAS.iterdir() if p.suffix in ('.csv', '.xml', '.pdf')}
    output = ROOT / 'data/processed/cameras.json'
    output.write_text(json.dumps({'products': records, 'source_hashes': provenance}, indent=2))
    canvas = Image.new('RGB', (1150, 720), '#111827')
    draw = ImageDraw.Draw(canvas)
    orbital = Image.open(ROOT / 'data/nasa/jezero-ctx-controlled.png').convert('RGB')
    orbital_manifest = json.loads((ROOT / 'data/processed/manifest.json').read_text())
    bounds = orbital_manifest['ctx']['bounds_lon_lat']
    canvas.paste(orbital.resize((550, 370)), (20, 50))
    draw.text((20, 15), 'NASA CTX orbital context / Mars metric operational rectangle',
              fill='white')
    for index, (key, record) in enumerate(records.items()):
        if record['rover_local_m']:
            x, y = record['rover_local_m']
            anchor = record['drive_anchor']
            lon, lat = float(anchor['longitude']), float(anchor['planetocentric_latitude'])
            px = 20+(lon-bounds[0])/(bounds[2]-bounds[0])*550
            py = 50+(bounds[3]-lat)/(bounds[3]-bounds[1])*370
            draw.ellipse((px-5, py-5, px+5, py+5), fill='yellow')
            draw.text((20, 430+index*15), key+f' drive anchor: ({x:.1f}, {y:.1f}) m',
                      fill='yellow')
        img = Image.open(ROOT / record['preview_file'])
        img.thumbnail((520, 250))
        canvas.paste(img, (610, 50+index*320))
        draw.text((610, 25+index*320), key+' calibrated data / DERIVED display', fill='white')
    draw.text((20, 480), 'Footprint: unavailable. Spatial uncertainty: unknown, not zero.',
              fill='white')
    draw.text((20, 510), 'Yellow points are drive anchors; not observed terrain coverage.',
              fill='white')
    draw.text((20, 540), 'Navcam exact clock/RMC match. Mastcam observation clock unresolved.',
              fill='white')
    canvas.save(ROOT / 'docs/science/s3-camera-diagnostic.png')
    print(json.dumps({k: {'interval': bool(v['places_exact_interval']),
                         'observation_clock_match': bool(v['places_observations']),
                         'overlap': v['operational_region_overlap']} for k, v in records.items()}))


if __name__ == '__main__':
    main()
