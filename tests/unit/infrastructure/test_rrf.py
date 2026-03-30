"""Unit tests for the reciprocal_rank_fusion pure function.

All tests are pure Python — no database, no mocks, no async.
"""

from documentor.domain.models.chunk import Chunk, ChunkContent
from documentor.infrastructure.persistence.pg_chunk_repository import (
    reciprocal_rank_fusion,
)


def _make_chunk(chunk_id: str, text: str = "sample text") -> Chunk:
    return Chunk(
        id=chunk_id,
        document_id="doc-1",
        content=ChunkContent(text=text, token_count=5),
        position=0,
        embedding=None,
    )


def _make_ranked_list(
    items: list[tuple[str, str]],
) -> list[tuple[str, Chunk, float]]:
    """Build a ranked list from (chunk_id, text) pairs."""
    return [(cid, _make_chunk(cid, text), 0.9 - i * 0.1) for i, (cid, text) in enumerate(items)]


def test_rrf_should_return_top_k_results_when_both_lists_have_items() -> None:
    list1 = _make_ranked_list([("a", "chunk a"), ("b", "chunk b"), ("c", "chunk c")])
    list2 = _make_ranked_list([("b", "chunk b"), ("c", "chunk c"), ("d", "chunk d")])

    results = reciprocal_rank_fusion([list1, list2], top_k=2)

    assert len(results) == 2
    ids = [chunk.id for chunk, _ in results]
    # "b" and "c" appear in both lists — they should dominate
    assert "b" in ids
    assert "c" in ids


def test_rrf_should_rank_items_in_both_lists_higher_when_appearing_in_multiple() -> None:
    # "x" appears in both lists at rank 1; "y" appears only in list1 at rank 1
    list1 = _make_ranked_list([("x", "chunk x"), ("y", "chunk y")])
    list2 = _make_ranked_list([("x", "chunk x"), ("z", "chunk z")])

    results = reciprocal_rank_fusion([list1, list2], top_k=3)

    chunks_by_id = {chunk.id: score for chunk, score in results}
    # "x" is in both lists, should score higher than single-list items
    assert chunks_by_id["x"] > chunks_by_id["y"]
    assert chunks_by_id["x"] > chunks_by_id["z"]


def test_rrf_should_handle_disjoint_lists_when_no_overlap() -> None:
    list1 = _make_ranked_list([("a", "chunk a"), ("b", "chunk b")])
    list2 = _make_ranked_list([("c", "chunk c"), ("d", "chunk d")])

    results = reciprocal_rank_fusion([list1, list2], top_k=4)

    # All 4 unique items returned, no deduplication needed
    assert len(results) == 4
    ids = {chunk.id for chunk, _ in results}
    assert ids == {"a", "b", "c", "d"}


def test_rrf_should_deduplicate_by_chunk_id_when_same_chunk_in_multiple_lists() -> None:
    # Same chunk_id "x" appears in both lists
    chunk_x = _make_chunk("x", "chunk x")
    list1 = [("x", chunk_x, 0.9), ("y", _make_chunk("y"), 0.8)]
    list2 = [("x", chunk_x, 0.7), ("z", _make_chunk("z"), 0.6)]

    results = reciprocal_rank_fusion([list1, list2], top_k=3)

    ids = [chunk.id for chunk, _ in results]
    # "x" must appear exactly once
    assert ids.count("x") == 1
    # Total results: x, y, z = 3 unique chunks
    assert len(results) == 3


def test_rrf_should_normalize_scores_to_unit_interval_when_fusing() -> None:
    # Best case: chunk at rank 1 in both lists → normalized score = 1.0
    chunk_top = _make_chunk("top")
    list1 = [("top", chunk_top, 0.99)]
    list2 = [("top", chunk_top, 0.99)]

    results = reciprocal_rank_fusion([list1, list2], top_k=1, k=60)

    assert len(results) == 1
    _, score = results[0]
    # With k=60 and num_lists=2: max_score = 2/(60+1) = 2/61
    # chunk score = 1/(60+1) + 1/(60+1) = 2/61
    # normalized = (2/61) / (2/61) = 1.0
    assert abs(score - 1.0) < 1e-9
    assert 0.0 <= score <= 1.0


def test_rrf_should_return_empty_when_all_lists_empty() -> None:
    results = reciprocal_rank_fusion([[], []], top_k=5)
    assert results == []


def test_rrf_should_handle_single_list_when_one_search_returns_empty() -> None:
    list1 = _make_ranked_list([("a", "chunk a"), ("b", "chunk b"), ("c", "chunk c")])
    empty: list[tuple[str, Chunk, float]] = []

    results = reciprocal_rank_fusion([list1, empty], top_k=3)

    assert len(results) == 3
    ids = [chunk.id for chunk, _ in results]
    assert ids == ["a", "b", "c"]

    # Single-list items: rank 1 in one list of 2 → normalized score = (1/61) / (2/61) = 0.5
    _, score_a = results[0]
    assert abs(score_a - 0.5) < 1e-9
