"""Tests the :obj:`trolldb.config.config` module."""

import pytest
from pydantic import ValidationError

from trolldb.config.config import id_must_be_valid


@pytest.mark.parametrize("id_string", [
    1, 1.0, {}, None, [], ()
])
def test_id_must_be_valid_bad_types(id_string):
    """Tests that we fail to generate a valid ObjectId with wrong input types."""
    with pytest.raises(ValidationError):
        id_must_be_valid(id_string)


def test_id_must_be_valid_bad_values():
    """Tests that we fail to generate a valid ObjectId with wrong input values."""
    number_of_chars = list(range(1, 24)) + list(range(25, 30))
    for i in number_of_chars:
        id_string = "0" * i
        with pytest.raises(ValueError, match=id_string):
            id_must_be_valid(id_string)


@pytest.mark.parametrize("id_string", [
    "0" * 24, "f" * 24, "6255bbd29606404848162477"
])
def test_id_must_be_valid_success(id_string):
    """Tests that we succeed to generate a valid ObjectId with valid input values and type."""
    assert str(id_must_be_valid(id_string)) == id_string
