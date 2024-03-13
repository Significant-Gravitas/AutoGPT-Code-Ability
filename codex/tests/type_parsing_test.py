import pytest

from codex.common.model import extract_field_type, is_type_equal


@pytest.mark.unit
def test_extract_field_type():
    assert extract_field_type("str") == {"str"}
    assert extract_field_type("tuple[str, dict[str, int]]") == {
        "str",
        "int",
        "Tuple",
        "Dict",
    }
    assert extract_field_type("Tuple[Obj1, Dict[Obj2, Obj3 | Obj4], Obj1]") == {
        "Union",
        "Tuple",
        "Dict",
        "Obj1",
        "Obj2",
        "Obj3",
        "Obj4",
    }


@pytest.mark.unit
def test_is_type_equal():
    assert is_type_equal("str", "str") is True
    assert is_type_equal("str", "int") is False
    assert is_type_equal("Optional[dict]", "Optional[Dict]") is True
    assert (
        is_type_equal(
            "tuple[str, dict[str, Union[int, str]]]", "Tuple[str, Dict[str, int | str]]"
        )
        is True
    )
    assert (
        is_type_equal(
            "tuple[str, dict[str, Union[int, str, float]]]",
            "Tuple[str, Dict[str, int | str]]",
        )
        is False
    )
