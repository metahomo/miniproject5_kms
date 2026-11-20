"""운영 장부 기록 스크립트(deploy/lightsail/ledger/ledger.py) — DB 없이, 행을 만드는 부분만 시험한다."""
import gzip
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("ledger", Path("deploy/lightsail/ledger/ledger.py"))
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


def make_snapshot(d: Path) -> Path:
    p = d / "topic-20261119.jsonl.gz"
    rows = [{"_meta": {"topic": "t", "teacher": {"model": "m"}}}, {"label": "include"}, {"label": "include"}, {"label": "exclude"}, {"label": "uncertain"}]
    with gzip.open(p, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return p


def test_snapshot_stats(tmp_path):
    s = ledger.snapshot_stats(make_snapshot(tmp_path))
    assert (s["n_rows"], s["n_include"], s["n_exclude"]) == (4, 2, 1)
    assert s["dataset_id"] == f"topic-20261119-{s['sha256'][:12]}"
    assert s["label_source"]["topic"] == "t" and s["label_source"]["files"] == ["topic-20261119.jsonl.gz"]


def test_run_record_passed(tmp_path):
    make_snapshot(tmp_path)
    art = tmp_path / "art"
    art.mkdir()
    (art / "metrics.json").write_text(json.dumps({"gate": {"f1": 0.96}, "baseline_f1": 0.88, "gate_result": {"passed": True, "fails": []},
                                                  "data": {"snapshots": ["topic-20261119.jsonl.gz"]}}))
    (art / "model.onnx").write_bytes(b"onnx")
    (art / "parity.json").write_text(json.dumps({"targets": {"img": {"gate_max_diff": 5e-7, "text_max_diff": 2e-7}}, "passed": True}))
    ds, mv = ledger.run_record(art, tmp_path, "m20261119-9", "https://x/run", "abc")
    assert mv["gate_passed"] and mv["parity_passed"]
    assert float(mv["parity_max_diff"]) == 5e-7
    assert len(mv["onnx_sha256"]) == 64 and mv["dataset_id"] == ds["dataset_id"]


def test_run_record_gate_failed(tmp_path):
    """게이트에서 멈춘 실행: ONNX·parity 없음 → 통과 아님, onnx_sha256 빈 값(DB 에서 NULL)"""
    make_snapshot(tmp_path)
    art = tmp_path / "art"
    art.mkdir()
    (art / "metrics.json").write_text(json.dumps({"gate": {"f1": 0.90}, "gate_result": {"passed": False, "fails": ["F1 0.9021 < 기준선 0.8805 + 0.05"]},
                                                  "data": {"snapshots": ["topic-20261119.jsonl.gz"]}}))
    _, mv = ledger.run_record(art, tmp_path, "m20261119-10", "", "")
    assert not mv["gate_passed"] and not mv["parity_passed"]
    assert mv["onnx_sha256"] == "" and mv["parity_max_diff"] == ""
    assert mv["metrics"]["fails"]


def test_snapshot_stats_multi_later_wins(tmp_path):
    """스냅숏 여러 개: 같은 key 는 이름순으로 뒤 파일이 이기고, 데이터셋 하나로 센다."""
    def write(name, rows):
        p = tmp_path / name
        with gzip.open(p, "wt", encoding="utf-8") as f:
            for r in [{"_meta": {"topic": "t"}}] + rows:
                f.write(json.dumps(r) + "\n")
        return p
    a = write("t-20261119.jsonl.gz", [{"key": "a", "label": "include"}, {"key": "b", "label": "exclude"}])
    b = write("t-20261120.jsonl.gz", [{"key": "b", "label": "include"}, {"key": "c", "label": "exclude"}])
    s = ledger.snapshot_stats([b, a])
    assert (s["n_rows"], s["n_include"], s["n_exclude"]) == (3, 2, 1)
    assert s["bucket_key"] == "snapshots/t-20261119.jsonl.gz+t-20261120.jsonl.gz" and len(s["sha256"]) == 64

