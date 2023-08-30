import pytest

import hello

make_greeting_params = [
    ("World", False, "Hello, World!"),
    ("World", True, "Greetings and felicitations, World!"),
    ("Blu", False, "Hello, Blu!"),
]


@pytest.mark.parametrize("name, formality, expected", make_greeting_params)
def test_make_greeting(name, formality, expected):
    result = hello.make_greeting(name, formality)
    assert expected == result
