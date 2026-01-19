"""
CLI commands for the Order Consumer service.
"""
import asyncio

import click


@click.group()
def cli():
    """Order Consumer Service CLI."""
    pass


@cli.command()
def run():
    """Run the order consumer service."""
    from .main import run as run_consumer
    asyncio.run(run_consumer())


if __name__ == "__main__":
    cli()
