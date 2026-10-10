import csv
import json
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest

from backend.camera import exact_clock_join, parse_label

LABEL = Path('data/nasa/cameras/NLF_0013_0668099766_737FDR_N0030028NCAM00112_0A00LLJ05.xml')


def test_real_label_preserves_geometry_and_clock():
    image = parse_label(LABEL)
    assert image['sclk'] == '668099766.737'
    assert image['rmc']['SITE'] == 3
    assert image['rmc']['DRIVE'] == 28
    assert image['dimensions'] == {'Band': 3, 'Line': 960, 'Sample': 1280}
    assert image['camera_model']['model_type'] == 'CAHVORE'
    assert image['footprint'] is None
    assert image['spatial_uncertainty_m'] is None


def test_clock_join_rejects_approximate_and_mismatched_pose():
    rmc = {'SITE': 3, 'DRIVE': 28, 'POSE': 4}
    row = {'frame': 'ROVER', 'site': '3', 'drive': '28', 'pose': '4',
           'min_sclk': '100.1', 'max_sclk': '100.2',
           'min_approx_sclk': '100', 'max_approx_sclk': '101'}
    assert exact_clock_join(rmc, Decimal('100.15'), Decimal('100.16'), [row]) == row
    assert exact_clock_join(rmc, Decimal('100.3'), Decimal('100.4'), [row]) is None
    assert exact_clock_join({**rmc, 'POSE': 6}, Decimal('100.15'), Decimal('100.16'), [row]) is None
    assert exact_clock_join(rmc, Decimal('100.15'), Decimal('100.16'), [row, row]) is None


def test_invalid_label_is_rejected(tmp_path):
    path = tmp_path / 'bad.xml'
    path.write_text('<Product_Observational/>')
    with pytest.raises(ValueError):
        parse_label(path)


def test_mastcam_preserves_distinct_clocks_and_array_scaling():
    image = parse_label(Path('data/nasa/cameras/'
                            'ZL0_0015_0668273255_213RAD_N0030110ZCAM08000_1000LUA01.xml'))
    assert image['sclk'] == '668273442.102'
    assert image['mini_header_sclk'] == '668273438.367'
    assert image['processing_level'] == 'Calibrated'
    assert image['scaling_factor'] == '2.014896381e-06'
    assert image['dimensions'] == {'Line': 1200, 'Sample': 1648}


def test_real_exact_interval_missing_pose_and_drive_location():
    image = parse_label(LABEL)
    with Path('data/nasa/cameras/sclk_table.csv').open() as source:
        rows = list(csv.DictReader(source))
    start, stop = Decimal(image['sclk']), Decimal(image['sclk_stop'])
    result = exact_clock_join(image['rmc'], start, stop, rows)
    assert result is not None and result['pose'] == '4' and result['rsm'] == '2'
    assert exact_clock_join({**image['rmc'], 'POSE': 999}, start, stop, rows) is None
    processed = json.loads(Path('data/processed/cameras.json').read_text())['products']
    for product in processed.values():
        assert product['operational_region_overlap']
        x, y = product['rover_local_m']
        assert 0 < x < 1200 and 0 < y < 800
        assert product['drive_anchor']['pose'] == '-1'
        assert product['spatial_uncertainty_m'] is None
        assert product['footprint'] is None
    assert processed['mastcamz']['places_observations'] == []
    raw = Path(processed['mastcamz']['raw_file']).read_bytes()
    meta = processed['mastcamz']
    dn = np.frombuffer(raw, dtype='>i2', offset=meta['array_offset'], count=1200*1648)
    with np.load(meta['processed_file']) as cache:
        assert cache['values'].shape == (1, 1200, 1648)
        assert cache['values'][0, 30, 30] == pytest.approx(
            float(dn.reshape(1200, 1648)[30, 30])*float(meta['scaling_factor'])
            + float(meta['value_offset']), rel=1e-6)


def test_camera_cache_is_visible_without_becoming_mission_evidence(client):
    result = client.get('/api/missions/eva-01')
    assert result.status_code == 200
    snapshot = result.json()
    cameras = snapshot['data_status']['manifest']['cameras']
    assert len(cameras) == 2
    assert all(c['clock_interval_matched'] for c in cameras)
    assert all(c['region_overlap'] for c in cameras)
    assert all(e['source_type'] == 'orbital' for e in snapshot['evidence'])
    for camera in cameras:
        response = client.get(camera['preview'])
        assert response.status_code == 200
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n'
