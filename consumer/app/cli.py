"""
CLI commands for the Order Consumer service.
"""
import asyncio
import json

import click
import yaml


@click.group()
def cli():
    """Order Consumer Service CLI."""
    pass


@cli.command()
def run():
    """Run the order consumer service."""
    from .main import app
    asyncio.run(app.run())


@cli.command()
@click.option("--yaml", "output_yaml", is_flag=True, help="Output as YAML instead of JSON")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
def asyncapi(output_yaml: bool, output: str | None):
    """Generate AsyncAPI specification."""
    from .main import app

    # Get the schema and convert to plain dict via JSON round-trip
    # This ensures no Python objects leak into the YAML output
    schema = app.schema.to_specification()
    schema_dict = json.loads(json.dumps(schema, default=str))

    if output_yaml:
        content = yaml.safe_dump(schema_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)
    else:
        content = json.dumps(schema_dict, indent=2)

    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Wrote AsyncAPI spec to {output}")
    else:
        click.echo(content)


if __name__ == "__main__":
    cli()
