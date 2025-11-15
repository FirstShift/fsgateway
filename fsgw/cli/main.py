"""
CLI main entry point for FSGW SDK.

Provides interactive command-line interface for API exploration.
"""

import asyncio
import json
import os
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from fsgw import __version__
from fsgw.client import FSGWClient

app = typer.Typer(
    name="fsgw",
    help="FirstShift API Gateway SDK - CLI Tool",
    add_completion=False,
)

console = Console()


def get_client() -> FSGWClient:
    """Get configured client from environment variables."""
    gateway_url = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
    tenant_id = int(os.getenv("FSGW_TENANT_ID", "7"))
    username = os.getenv("FSGW_USERNAME", "")
    password = os.getenv("FSGW_PASSWORD", "")

    if not username or not password:
        console.print("[red]Error: FSGW_USERNAME and FSGW_PASSWORD must be set[/red]")
        raise typer.Exit(1)

    return FSGWClient(
        gateway_url=gateway_url,
        tenant_id=tenant_id,
        username=username,
        password=password,
    )


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"fsgw version {__version__}")


@app.command()
def endpoints() -> None:
    """List all available API endpoints."""

    async def _list_endpoints() -> None:
        async with get_client() as client:
            response = await client.list_endpoints()

            if not response.success:
                console.print(f"[red]Error: {response.error}[/red]")
                raise typer.Exit(1)

            data = response.data

            # Create summary table
            table = Table(title="API Endpoints Summary")
            table.add_column("Group", style="cyan")
            table.add_column("Entities", style="green")

            for group in data.groups:
                table.add_row(group.name, str(len(group.entities)))

            console.print(table)
            console.print(f"\n[green]Total Groups:[/green] {data.total_groups}")
            console.print(f"[green]Total Entities:[/green] {data.total_entities}")

            # Show detailed entities
            console.print("\n[bold]Entities by Group:[/bold]\n")
            for group in data.groups:
                console.print(f"[cyan]{group.name}[/cyan]")
                for entity in group.entities:
                    console.print(f"  • {entity.name} - {entity.endpoint}")

    asyncio.run(_list_endpoints())


@app.command()
def metadata(entity: str) -> None:
    """Get metadata for a specific entity."""

    async def _get_metadata() -> None:
        async with get_client() as client:
            response = await client.get_metadata(entity=entity)

            if not response.success:
                console.print(f"[red]Error: {response.error}[/red]")
                raise typer.Exit(1)

            data = response.data

            # Create table
            table = Table(title=f"Metadata for {entity}")
            table.add_column("Field", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Required", style="yellow")
            table.add_column("PK", style="magenta")
            table.add_column("Nullable", style="blue")

            for field in data.fields:
                table.add_row(
                    field.name,
                    field.data_type,
                    "✓" if field.required else "",
                    "✓" if field.is_primary_key else "",
                    "✓" if field.nullable else "",
                )

            console.print(table)

            if data.primary_keys:
                console.print(f"\n[green]Primary Keys:[/green] {', '.join(data.primary_keys)}")

    asyncio.run(_get_metadata())


@app.command()
def query(
    entity: str,
    filter: Optional[list[str]] = typer.Option(
        None,
        "--filter",
        "-f",
        help="Filter as key=value (can be repeated)",
    ),
    sort_by: Optional[str] = typer.Option(None, "--sort-by", "-s", help="Field to sort by"),
    sort_order: str = typer.Option("asc", "--sort-order", "-o", help="Sort order (asc/desc)"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    limit: int = typer.Option(10, "--limit", "-l", help="Records per page"),
    fields: Optional[str] = typer.Option(None, "--fields", help="Comma-separated fields"),
    output: str = typer.Option("table", "--output", help="Output format (table/json/csv)"),
) -> None:
    """Query data from a specific entity."""

    async def _query() -> None:
        # Parse filters
        filters_dict: dict[str, Any] = {}
        if filter:
            for f in filter:
                if "=" in f:
                    key, value = f.split("=", 1)
                    filters_dict[key] = value

        # Parse fields
        fields_list = fields.split(",") if fields else None

        async with get_client() as client:
            response = await client.query(
                entity=entity,
                filters=filters_dict if filters_dict else None,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                limit=limit,
                fields=fields_list,
            )

            if not response.success:
                console.print(f"[red]Error: {response.error}[/red]")
                raise typer.Exit(1)

            data = response.data

            if output == "json":
                console.print(json.dumps(data.model_dump(), indent=2))
            elif output == "csv":
                if data.items:
                    # Print header
                    headers = list(data.items[0].keys())
                    console.print(",".join(headers))
                    # Print rows
                    for item in data.items:
                        console.print(",".join(str(item.get(h, "")) for h in headers))
            else:  # table
                if data.items:
                    table = Table(title=f"Query Results: {entity}")
                    headers = list(data.items[0].keys())
                    for header in headers:
                        table.add_column(header, style="cyan")

                    for item in data.items:
                        table.add_row(*[str(item.get(h, "")) for h in headers])

                    console.print(table)

                console.print(
                    f"\n[green]Page {data.page} of {data.total_pages}[/green] "
                    f"(Total: {data.total} records)"
                )

    asyncio.run(_query())


@app.command()
def interactive() -> None:
    """Start interactive mode (not implemented yet)."""
    console.print("[yellow]Interactive mode coming soon![/yellow]")


if __name__ == "__main__":
    app()
