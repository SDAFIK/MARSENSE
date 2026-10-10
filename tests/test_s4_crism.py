from pathlib import Path

from backend.science import crism_context


def test_real_crism_target_and_missing_coverage():
    result = crism_context((1080, 400))
    assert result is not None
    assert result['product_id'] == 'FRT000047A3_07_BRTANJ_MTR3'
    assert result['classification'] == 'DERIVED'
    assert result['target']['valid_pixel']
    assert result['target']['mineral_identity'] is None
    assert result['resolution_m'] == 18
    # The operational rectangle extends below the scene; no fake full coverage.
    assert not crism_context((1080, 0))['target']['valid_pixel']


def test_missing_crism_is_optional_context(tmp_path):
    assert crism_context((1080, 400), tmp_path / 'missing.json') is None


def test_crism_cache_and_geometry_provenance():
    result = crism_context((1080, 400))
    assert Path(result['source']['file']).is_file()
    assert len(result['source']['sha256']) == 64
    assert result['coverage']['type'] == 'MultiPolygon'
    assert result['target']['source_pixel'] == [298, 795]


def test_crism_api_provenance_and_missing_layer_preserve_mission(client, monkeypatch):
    response = client.get('/api/missions/eva-01')
    assert response.status_code == 200
    crism = response.json()['data_status']['manifest']['crism']
    assert crism['target']['valid_pixel'] and crism['target']['mineral_identity'] is None
    assert client.get(crism['preview']).status_code == 200
    import backend.service
    monkeypatch.setattr(backend.service, 'crism_context', lambda location: None)
    missing = client.get('/api/missions/eva-01')
    assert missing.status_code == 200
    assert missing.json()['data_status']['manifest']['crism'] is None
    assert missing.json()['target']['id'] == response.json()['target']['id']
