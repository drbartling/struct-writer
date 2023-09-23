import pytest
from pydantic.dataclasses import dataclass

from struct_writer.templating import Template

template_substitute_params = [
    (
        "I have ${bag_count} bags of coffee",
        {"bag_count": 42},
        "I have 42 bags of coffee",
    ),
    (
        "I have ${bag_count} bags of coffee",
        {"bag_count": "42"},
        "I have 42 bags of coffee",
    ),
    (
        "I have 0x${bag_count:02X} bags of coffee",
        {"bag_count": 42},
        "I have 0x2A bags of coffee",
    ),
    (
        "I have ${bag_count} bags of coffee for $$${cost} each",
        {"bag_count": 42, "cost": 12},
        "I have 42 bags of coffee for $12 each",
    ),
]


@pytest.mark.parametrize(
    "template_str, params, expected", template_substitute_params
)
def test_template_substitute(template_str, params, expected):
    t = Template(template_str)

    result = t.render(params)
    assert expected == result

    result = t.safe_render(params)
    assert expected == result


def test_template_matches_string_template_interface():
    # Except all variables must be wraped in curly braces
    t = Template("${who} likes ${what}")
    result = t.render(who="tim", what="kung pao")
    assert "tim likes kung pao" == result

    d = {"who": "tim"}
    result = Template("Give ${who} $$200").render(d)
    assert "Give tim $200" == result

    with pytest.raises(AttributeError):
        result = t.render(d)

    result = t.safe_render(d)
    assert "tim likes ${what}" == result


def test_template_allows_periods_and_flattens_dictionaries():
    t = Template("Hello Mr. ${name.last}, ${name.first}")
    d = {"name": {"first": "Charles", "last": "Dickens"}}
    result = t.render(d)
    expected = "Hello Mr. Dickens, Charles"
    assert expected == result


def test_we_also_flatten_key_word_args():
    t = Template("Hello Mr. ${name.last}, ${name.first}")
    result = t.render(name={"first": "Charles", "last": "Dickens"})
    expected = "Hello Mr. Dickens, Charles"
    assert expected == result


def test_we_merge_dict_with_kwargs():
    t = Template("Hello Mr. ${name.last}, ${name.first}")
    d = {"name": {"first": "Charles"}}
    result = t.render(d, name={"last": "Dickens"})
    expected = "Hello Mr. Dickens, Charles"
    assert expected == result


def test_we_can_access_object_attributes():
    @dataclass
    class Person:
        name: str = "Bob"

    p = Person()
    t = Template("Hello, ${person.name}")
    result = t.render(person=p)
    expected = "Hello, Bob"
    assert expected == result


def test_we_can_recursevily_resolve_templates():
    templates = {
        "full_name": "${person.name.first} ${person.name.last}",
        "last_first": "${person.name.last}, ${person.name.first}",
    }
    person = {
        "name": {
            "first": "Charles",
            "last": "Dickens",
        },
        "title": "Mr.",
    }
    t = Template("Hello, ${person.title} ${templates.last_first}")
    result = t.render(person=person, templates=templates)
    expected = "Hello, Mr. Dickens, Charles"
    assert expected == result
