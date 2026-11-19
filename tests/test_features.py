from paperclf.features import N_FEATURES, _bucket, counts, doc_text, normalize, to_dense, vectorize


def test_bucket_is_stable_across_runs():
    # blake2b 기반이라 파이썬 실행·플랫폼과 무관하게 같은 값이어야 한다(학습 ↔ 서버).
    assert _bucket(" co") == _bucket(" co")
    assert _bucket(" co") == 11822
    assert _bucket("코칭") == 5154


def test_counts_char_ngrams_inside_words():
    c = counts("ab")
    # " ab " → 2-gram 3개, 3-gram 2개, 4-gram 1개
    assert sum(c.values()) == 6


def test_korean_and_nfkc_normalization():
    assert normalize("ＣＯＡＣＨ") == "coach"
    assert counts("코칭리더십") and all(0 <= k < N_FEATURES for k in counts("코칭리더십"))


def test_title_weighted_twice():
    assert doc_text("T", "A") == "T T A"
    assert doc_text(None, None).strip() == ""


def test_dense_from_sparse_pairs_matches_vectorize():
    v = vectorize("Managerial coaching", "work engagement")
    pairs = sorted(counts(doc_text("Managerial coaching", "work engagement")).items())
    assert (to_dense([[i, c] for i, c in pairs]) == v).all()
    assert v.shape == (N_FEATURES,) and v.dtype.name == "float32"
