"""
CLI commands for the Order Producer service.
"""
import asyncio

import click


@click.group()
def cli():
    """Order Producer Service CLI."""
    pass


@cli.command()
def run():
    """Run the order producer service."""
    from .main import app
    asyncio.run(app.run())


@cli.command()
@click.option("--yaml", "output_yaml", is_flag=True, help="Output as YAML instead of JSON")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
def asyncapi(output_yaml: bool, output: str | None):
    """Generate AsyncAPI specification."""
    from .main import app

    if output_yaml:
        content = app.schema.to_yaml()
    else:
        content = app.schema.to_json()

    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Wrote AsyncAPI spec to {output}")
    else:
        click.echo(content)


if __name__ == "__main__":
    cli()

