"""5판 2단계: 검증된 v3 캐시 → 학습 쌍(chat). 입력 = 운영 v3 묶음 프롬프트(mapstep 묶음·프롬프트 재사용, 3편), 정답 = 검증된 record 의 MAP_SCHEMA JSON.

    ~/miniproject-kms/.venv/bin/python reportlm/prepare_v3.py [--aug 2]
분할: common.split_of(key hash % 5 == 0 → gate). 학습 안에서 검증용 10%(논문 단위, 다른 해시)는 따로 뺀다. 묶음은 같은 분할 안에서만 만들고,
학습 묶음은 --aug 번 다른 순서로 다시 묶어(같은 논문·다른 짝) 늘린다. 산출물은 $REPORTLM_WORK/data_v3/ (공개 저장소 밖).
"""
import argparse, hashlib, json, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KMS = Path.home() / "miniproject-kms"
sys.path.insert(0, str(KMS)); sys.path.insert(0, str(HERE))
from common import WORK, split_of  # noqa: E402
from kms.cli import REPO_ROOT  # noqa: E402
from kms.config import load_config  # noqa: E402
from kms.research import facts, mapcache, mapstep  # noqa: E402
from kms.storage.factory import open_store  # noqa: E402

TOPIC = "coaching-leadership"
KEYS = ("work_id", "study_type", "design", "sample_size", "variables", "quant_results", "own_limitations", "reported_gaps", "findings", "implications")


def valid_of(work_id: int) -> bool:
    h = int.from_bytes(hashlib.blake2b(f"V{work_id}".encode(), digest_size=8).digest(), "little")
    return h % 10 == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aug", type=int, default=2)
    ap.add_argument("--oversample-lim", type=int, default=1)
    ap.add_argument("--enrich", action="store_true", help="운영과 같이 enrich_record(초록 규칙 보강, C8)를 적용한 record 를 정답으로 쓴다(filled_by 는 뺀다)")
    ap.add_argument("--out", default="data_v3")
    a = ap.parse_args()
    OUT = WORK / a.out
    cfg_path = KMS / "config.yaml"
    config, _ = load_config(cfg_path, REPO_ROOT)
    store = open_store(config)
    from kms.services.container import Services
    model = Services(config, config_path=cfg_path).research_writer().model
    cdir = mapcache.cache_dir(config.paths.vault, TOPIC)
    template = mapstep._load_prompt()
    recs, works = {}, {}
    for w in facts.collect_pool(store, TOPIC, year_from=None, year_to=None):
        if not mapstep._eligible(w):
            continue
        e = mapcache.load_entry(cdir, w.id, prompt=mapcache.MAP_PROMPT, model=model, abstract_sha256=mapcache.abstract_hash(w.title, mapstep.abstract_seen(w)))
        if e:
            rec = e[0]
            if a.enrich:
                from kms.research.enrich import enrich_record
                rec = enrich_record(rec, mapstep.abstract_seen(w), w.title or "")
            recs[w.id], works[w.id] = rec, w
    parts = {"gate": [], "valid": [], "train": []}
    for i in sorted(recs):
        s = split_of(i)
        parts["gate" if s == "gate" else ("valid" if valid_of(i) else "train")].append(i)

    def rows_for(ids, seed):
        ids = list(ids); random.Random(seed).shuffle(ids)
        out = []
        for g in mapstep.build_groups([works[i] for i in ids], group_size=3):
            gid = [w.id for w in g]
            prompt = template.format(context="\n\n".join(mapstep.paper_input(w) for w in g))
            target = json.dumps({"papers": [{"work_id": i, **{k: recs[i][k] for k in KEYS[1:]}} for i in gid]}, ensure_ascii=False)
            out.append({"work_ids": gid, "prompt": prompt, "target": target, "abstracts": {str(i): mapstep.abstract_seen(works[i]) for i in gid}})
        return out

    gate = rows_for(parts["gate"], 0)
    valid = rows_for(parts["valid"], 1)
    train = [r for k in range(a.aug) for r in rows_for(parts["train"], 100 + k)]
    if a.oversample_lim > 1:
        lim = [r for r in train if any(p["own_limitations"] for p in json.loads(r["target"])["papers"])]
        train += lim * (a.oversample_lim - 1)
    OUT.mkdir(parents=True, exist_ok=True)
    chat = lambda r: {"messages": [{"role": "user", "content": r["prompt"]}, {"role": "assistant", "content": r["target"]}]}
    for name, part in (("train", train), ("valid", valid)):
        (OUT / f"{name}.jsonl").write_text("".join(json.dumps(chat(r), ensure_ascii=False) + "\n" for r in part), encoding="utf-8")
    (OUT / "gate.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in gate), encoding="utf-8")
    nlim = sum(bool(recs[i]["own_limitations"]) for i in recs)
    summary = {"model": model, "cached_papers": len(recs), "papers": {k: len(v) for k, v in parts.items()}, "rows": {"train": len(train), "valid": len(valid), "gate": len(gate)},
               "aug": a.aug, "enrich": a.enrich, "oversample_lim": a.oversample_lim, "papers_with_limitations": nlim,
               "gate_papers_with_limitations": sum(bool(recs[i]["own_limitations"]) for i in parts["gate"])}
    (OUT / "dataset.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
