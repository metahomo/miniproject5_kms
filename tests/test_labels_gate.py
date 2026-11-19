from paperclf.labels import EXCLUDE, INCLUDE, UNCERTAIN, label_for, split_of
from training.metrics import baseline_f1, score
from training.validate_model import check

import numpy as np


def test_label_thresholds_match_kms_topic():
    assert label_for(0.7) == INCLUDE
    assert label_for(0.3) == EXCLUDE
    assert label_for(0.5) == UNCERTAIN


def test_split_is_fixed_by_key():
    assert split_of("openalex:W1") == split_of("openalex:W1")
    share = sum(split_of(f"k{i}") == "gate" for i in range(5000)) / 5000
    assert 0.17 < share < 0.23


def test_score_and_baseline():
    y = np.array([1, 1, 0, 0])
    assert score(y, np.array([0.9, 0.8, 0.1, 0.2]))["f1"] == 1.0
    assert baseline_f1(y) == round(2 * 0.5 / 1.5, 4)


def _m(f1, base=0.5):
    return {"gate": {"f1": f1}, "baseline_f1": base}


TH = dict(min_f1=0.8, margin=0.05, max_drop=0.02)


def test_gate_passes_good_model():
    assert check(_m(0.9), None, **TH) == []


def test_gate_blocks_weak_model():
    assert check(_m(0.7), None, **TH)
    assert check(_m(0.82, base=0.8), None, **TH)  # 기준선 + 여유를 못 넘음


def test_gate_blocks_regression_against_production():
    prod = {"model_version": "m20261119-1", "metrics": {"gate": {"f1": 0.95}}}
    assert check(_m(0.9), prod, **TH)
    assert check(_m(0.94), prod, **TH) == []
