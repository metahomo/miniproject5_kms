"""6판 데이터: 한 어댑터·두 과제 혼합. 과제 A = 운영 v3 묶음 정리(data_v3 정답 그대로), 과제 B = 한계 발췌(논문 1편 초록 → {"own_limitations": [...]}).

    ~/miniproject-kms/.venv/bin/python reportlm/prepare_v6.py     (먼저 prepare_v3.py --aug 2 --oversample-lim 1 --out data_v3 로 과제 A 를 만든다)
B 정답 = 교사 캐시 own_limitations ∪ enrich 규칙 발췌(둘 다 초록 부분 문자열인 것만, 최대 2개). 학습·검증 분할의 논문만 쓰고 양성:음성 = 1:1,
게이트 298편은 B 학습에 절대 섞지 않는다. 게이트 B(gate_b.jsonl)는 게이트 298편 전부(양성·음성 라벨 포함).
"""
import json, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KMS = Path.home() / "miniproject-kms"
sys.path.insert(0, str(KMS)); sys.path.insert(0, str(HERE))
from common import WORK, split_of  # noqa: E402
from prepare_v3 import TOPIC, valid_of  # noqa: E402
from kms.cli import REPO_ROOT  # noqa: E402
from kms.config import load_config  # noqa: E402
from kms.research import facts, mapcache, mapstep  # noqa: E402
from kms.research.enrich import _LIM_CUE, extract_quotes  # noqa: E402
from kms.research.verify import quote_in_abstract  # noqa: E402
from kms.storage.factory import open_store  # noqa: E402

B_INSTRUCTION = ("아래 논문 제목·초록에서, 이 논문이 자기 한계 또는 후속 연구 필요성으로 쓴 문장을 초록에 적힌 그대로(한 글자도 바꾸지 않고) 최대 2개 인용한다. "
                 "그런 문장이 없으면 빈 목록으로 답한다. JSON 으로만 답한다: {{\"own_limitations\": [\"초록 문장\"]}}\n\n[논문]\n{paper}")


def main() -> int:
    cfg_path = KMS / "config.yaml"
    config, _ = load_config(cfg_path, REPO_ROOT)
    store = open_store(config)
    from kms.services.container import Services
    model = Services(config, config_path=cfg_path).research_writer().model
    cdir = mapcache.cache_dir(config.paths.vault, TOPIC)
    rows = {"gate": [], "valid": [], "train": []}
    for w in facts.collect_pool(store, TOPIC, year_from=None, year_to=None):
        if not mapstep._eligible(w):
            continue
        seen = mapstep.abstract_seen(w)
        e = mapcache.load_entry(cdir, w.id, prompt=mapcache.MAP_PROMPT, model=model, abstract_sha256=mapcache.abstract_hash(w.title, seen))
        if not e:
            continue
        items = []
        for q in list(e[0].get("own_limitations") or []) + extract_quotes(seen, _LIM_CUE):
            if q not in items and quote_in_abstract(q, seen):
                items.append(q)
        s = split_of(w.id)
        part = "gate" if s == "gate" else ("valid" if valid_of(w.id) else "train")
        rows[part].append({"work_ids": [w.id], "prompt": B_INSTRUCTION.format(paper=mapstep.paper_input(w)), "abstracts": {str(w.id): seen},
                           "target": json.dumps({"own_limitations": items[:2]}, ensure_ascii=False), "positive": bool(items)})
    rng = random.Random(6)
    out = WORK / "data_v6"; out.mkdir(parents=True, exist_ok=True)
    chat = lambda r: {"messages": [{"role": "user", "content": r["prompt"]}, {"role": "assistant", "content": r["target"]}]}
    stats = {}
    for name in ("train", "valid"):
        pos = [r for r in rows[name] if r["positive"]]
        neg = [r for r in rows[name] if not r["positive"]]
        rng.shuffle(neg)
        b = pos + neg[: len(pos)]
        a = [json.loads(l) for l in (WORK / "data_v3" / f"{name}.jsonl").open(encoding="utf-8")]
        mixed = a + [chat(r) for r in b]
        rng.shuffle(mixed)
        (out / f"{name}.jsonl").write_text("".join(json.dumps(m, ensure_ascii=False) + "\n" for m in mixed), encoding="utf-8")
        stats[name] = {"A": len(a), "B": len(b), "B_pos": len(pos)}
    gb = rows["gate"]
    (out / "gate_b.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in gb), encoding="utf-8")
    (out / "gate.jsonl").write_text((WORK / "data_v3" / "gate.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    stats["gate_b"] = {"papers": len(gb), "positive": sum(r["positive"] for r in gb)}
    (out / "dataset.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
