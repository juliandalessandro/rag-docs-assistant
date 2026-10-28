import pytest

from app.chunking import split_text


def test_split_text_returns_empty_list_for_empty_text():
    assert split_text("") == []


def test_split_text_returns_single_chunk_for_short_text():
    text = "Hello world"

    chunks = split_text(text, chunk_size=20, overlap=5)

    assert chunks == ["Hello world"]


def test_split_text_splits_long_text():
    text = "ABCDEFGHIJKLMNO"

    chunks = split_text(text, chunk_size=6, overlap=2)

    assert chunks == [
        "ABCDEF",
        "EFGHIJ",
        "IJKLMN",
        "MNO",
    ]


def test_split_text_preserves_exact_size_text():
    text = "ABCDEFGHIJ"

    chunks = split_text(text, chunk_size=5, overlap=0)

    assert chunks == ["ABCDE", "FGHIJ"]


def test_split_text_rejects_zero_chunk_size():
    with pytest.raises(ValueError):
        split_text("Hello", chunk_size=0)


def test_split_text_rejects_negative_overlap():
    with pytest.raises(ValueError):
        split_text("Hello", chunk_size=5, overlap=-1)


def test_split_text_rejects_overlap_equal_to_chunk_size():
    with pytest.raises(ValueError):
        split_text("Hello", chunk_size=5, overlap=5)

def test_split_text_never_exceeds_chunk_size():
    text = "A" * 1000

    chunks = split_text(text, chunk_size=100, overlap=20)

    assert all(len(chunk) <= 100 for chunk in chunks)


def test_split_text_covers_the_end_of_the_text():
    text = "ABCDEFGHIJKLMNO"

    chunks = split_text(text, chunk_size=6, overlap=2)

    assert chunks[-1].endswith("O")