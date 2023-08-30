import pytest

import structured_api

make_greeting_params = [
    ("World", False, "Hello, World!"),
    ("World", True, "Greetings and felicitations, World!"),
    ("Blu", False, "Hello, Blu!"),
]


@pytest.mark.parametrize("name, formality, expected", make_greeting_params)
def test_make_greeting(name, formality, expected):
    result = structured_api.make_greeting(name, formality)
    assert expected == result
