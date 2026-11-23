"""5판 1단계: 교사 캐시 확대 — KMS mapstep.map_papers 로 포함 판정·초록 100자 이상 논문 전부를 3편 묶음으로 정리한다.

    ~/miniproject-kms/.venv/bin/python reportlm/fill_cache_v3.py [--limit N]
KMS 코드는 import 만 한다(읽기). 캐시는 mapstep 이 볼트 _map 폴더에 쓴다. 공용 Ollama 에 한 번에 한 건(순차) 호출한다.
"""
import argparse, sys, time
from pathlib import Path

KMS = Path.home() / "miniproject-kms"
sys.path.insert(0, str(KMS))
from kms.cli import REPO_ROOT  # noqa: E402
from kms.config import load_config  # noqa: E402
from kms.research import facts, mapcache, mapstep  # noqa: E402
from kms.services.container import Services  # noqa: E402
from kms.storage.factory import open_store  # noqa: E402

TOPIC = "coaching-leadership"
LOG = Path.home() / "reportlm-work" / "v5-cache-fill.log"


def log(msg: str) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    cfg_path = KMS / "config.yaml"
    config, _ = load_config(cfg_path, REPO_ROOT)
    store = open_store(config)
    pool = facts.collect_pool(store, TOPIC, year_from=None, year_to=None)
    works = [w for w in pool if len(mapstep.abstract_seen(w)) >= mapstep.MIN_ABSTRACT_CHARS]
    if a.limit:
        works = works[: a.limit]
    log(f"pool={len(pool)} eligible={len(works)}")
    writer = Services(config, config_path=cfg_path).research_writer()
    if writer is None:
        log("research_writer 없음(모델 꺼짐)"); return 2
    cdir = mapcache.cache_dir(config.paths.vault, TOPIC)
    t0 = time.time()
    last = [0.0]

    def prog(k, total):
        if time.time() - last[0] > 60 or k == total:
            last[0] = time.time()
            log(f"group {k}/{total} elapsed={int(time.time()-t0)}s")

    try:
        res = mapstep.map_papers(works, ask_json=writer.ask_json, model=writer.model, model_version=writer.model_version,
                                 cache_dir=cdir, group_size=config.research.group_size, min_papers=1, progress=prog)
        log(f"DONE stats={res.stats.as_dict()} elapsed={int(time.time()-t0)}s")
    except Exception as e:  # 저장한 캐시는 남는다
        log(f"ERROR {type(e).__name__}: {e} elapsed={int(time.time()-t0)}s")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
