import json
import os
from pathlib import Path

import numpy as np
import pytest

DATA = Path(__file__).parent / 'data'
MODELS = sorted(p.stem for p in DATA.glob('*.json'))
HEX = [m for m in MODELS if m.startswith('sp_2p5d_')]


def load_case(model):
    meta = json.loads((DATA / f'{model}.json').read_text(encoding='utf-8'))
    return meta, np.load(DATA / f'{model}.npz')


def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: Hex27 (2.5D) sweeps, minutes each; run with SAWSIM_TEST_ALL=1')


def pytest_collection_modifyitems(config, items):
    if os.environ.get('SAWSIM_TEST_ALL'):
        return
    skip = pytest.mark.skip(reason='Hex27 case; set SAWSIM_TEST_ALL=1 to run')
    for item in items:
        if 'slow' in item.keywords:
            item.add_marker(skip)
