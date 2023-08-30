import click


@click.command()
@click.option(
    "-n",
    "--name",
    prompt=True,
)
@click.option(
    "-f",
    "--formal",
    is_flag=True,
    help="Increase the formality of the greeting",
)
def main(name, formal):  # pragma: no cover
    """Greet a person or entity by NAME

    NAME is the name of the person or entity you wish to greet."""
    print(make_greeting(name, formal))
    click.pause()


def make_greeting(name, formality):
    return (
        f"Greetings and felicitations, {name}!"
        if formality
        else f"Hello, {name}!"
    )


if __name__ == "__main__":  # pragma: no cover
    # Ignored missing parameter lint, since the click library passes the
    # arguments in from the command line for us
    main()  # pylint:disable=no-value-for-parameter
