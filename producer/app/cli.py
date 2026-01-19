"""
CLI commands for the Order Producer service.
"""
import asyncio
import json

import click
import yaml


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

    # Get the schema as a jsonable dict (FastStream 0.6+)
    schema = app.schema.to_specification()

    if output_yaml:
        content = yaml.dump(schema, default_flow_style=False, sort_keys=False, allow_unicode=True)
    else:
        content = json.dumps(schema, indent=2)

    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Wrote AsyncAPI spec to {output}")
    else:
        click.echo(content)


if __name__ == "__main__":
    cli()
