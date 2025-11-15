"""
CLI main entry point for FSGW SDK.

Provides interactive command-line interface for API exploration.
"""

import asyncio
import json
import os
import sys
from typing import Any, Optional

import httpx
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
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
def entities(
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Filter by scope")
) -> None:
    """List all entities, optionally filtered by scope."""

    async def _list_entities() -> None:
        async with get_client() as client:
            if scope:
                entities_list = await client.list_apis_by_scope(scope)
                title = f"Entities in scope: {scope}"
            else:
                entities_list = await client.list_apis()
                title = "All Entities"

            # Group by scope
            by_scope: dict[str, list] = {}
            for entity in entities_list:
                if entity.api_scope not in by_scope:
                    by_scope[entity.api_scope] = []
                by_scope[entity.api_scope].append(entity)

            # Display summary
            table = Table(title=title)
            table.add_column("Scope", style="cyan")
            table.add_column("Count", style="green")

            for scope_name in sorted(by_scope.keys()):
                table.add_row(scope_name, str(len(by_scope[scope_name])))

            console.print(table)
            console.print(f"\n[green]Total:[/green] {len(entities_list)} entities")

            # Show entities
            if scope:
                console.print(f"\n[bold]{scope} entities:[/bold]\n")
                for entity in sorted(entities_list, key=lambda x: x.api_url):
                    desc = f" - {entity.description}" if entity.description else ""
                    console.print(f"  • [cyan]{entity.api_url}[/cyan]{desc}")

    asyncio.run(_list_entities())


@app.command()
def info(api_url: str) -> None:
    """Get detailed information about a specific entity."""

    async def _get_info() -> None:
        async with get_client() as client:
            try:
                entity = await client.get_api_info(api_url)
                metadata = await client.get_metadata(api_url)
                pk_fields = await client.get_primary_keys(api_url)

                # Entity info panel
                info_text = f"""
                **API URL:** {entity.api_url}
                **Scope:** {entity.api_scope}
                **Name:** {entity.external_api_name}
                **Description:** {entity.description or 'N/A'}
                """
                console.print(Panel(Markdown(info_text), title="Entity Information"))

                # Metadata table
                table = Table(title=f"Fields ({len(metadata)} total)")
                table.add_column("Field", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("PK", style="magenta")
                table.add_column("Nullable", style="yellow")

                for field in metadata:
                    table.add_row(
                        field.field_name,
                        field.type,
                        "✓" if field.is_primary_key else "",
                        "✓" if field.field_can_be_null else "",
                    )

                console.print(table)

                if pk_fields:
                    console.print(f"\n[green]Primary Keys:[/green] {', '.join(pk_fields)}")

            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                raise typer.Exit(1)

    asyncio.run(_get_info())


@app.command()
def search(term: str) -> None:
    """Search entities by name, scope, or description."""

    async def _search() -> None:
        async with get_client() as client:
            entities_list = await client.list_apis()

            term_lower = term.lower()
            results = [
                e
                for e in entities_list
                if (
                    term_lower in e.api_url.lower()
                    or term_lower in e.external_api_name.lower()
                    or (e.description and term_lower in e.description.lower())
                )
            ]

            if not results:
                console.print(f"[yellow]No entities found matching '{term}'[/yellow]")
                return

            console.print(f"\n[green]Found {len(results)} entities matching '{term}':[/green]\n")

            table = Table(title=f"Search Results: '{term}'")
            table.add_column("API URL", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Description", style="white")

            for entity in sorted(results, key=lambda x: x.api_url):
                table.add_row(
                    entity.api_url,
                    entity.external_api_name,
                    (entity.description or "")[:50] + "..." if entity.description and len(entity.description) > 50 else (entity.description or ""),
                )

            console.print(table)

    asyncio.run(_search())


@app.command()
def ask(question: str) -> None:
    """Ask questions about the API using natural language.

    This command uses the documentation server to answer questions about
    available entities, their metadata, and usage patterns.

    Examples:
      fsgw ask "What entities are in the ops scope?"
      fsgw ask "Show me audit trail fields"
      fsgw ask "How do I query the products entity?"
    """

    async def _ask() -> None:
        # Check if we can reach the docs server
        doc_server_url = os.getenv("FSGW_DOC_SERVER_URL", "http://localhost:8000")

        try:
            async with httpx.AsyncClient() as http_client:
                # Try to get health status
                response = await http_client.get(f"{doc_server_url}/health", timeout=5.0)
                if response.status_code != 200:
                    console.print(f"[yellow]Documentation server not available at {doc_server_url}[/yellow]")
                    console.print("[yellow]Start it with: fsgw-server[/yellow]")
                    console.print("[yellow]Attempting direct API query instead...[/yellow]\n")
                    # Fall back to direct search
                    await _fallback_search(question)
                    return

        except (httpx.ConnectError, httpx.TimeoutException):
            console.print(f"[yellow]Documentation server not available at {doc_server_url}[/yellow]")
            console.print("[yellow]Start it with: fsgw-server[/yellow]")
            console.print("[yellow]Attempting direct API query instead...[/yellow]\n")
            # Fall back to direct search
            await _fallback_search(question)
            return

        # Parse question to determine intent
        question_lower = question.lower()

        # Intent: List entities in a scope
        if any(word in question_lower for word in ["entities in", "what entities", "list entities"]):
            for scope in ["ops", "data", "config", "metadata", "globalmeta", "rbac"]:
                if scope in question_lower:
                    console.print(f"[cyan]Finding entities in {scope} scope...[/cyan]\n")
                    async with get_client() as client:
                        entities_list = await client.list_apis_by_scope(scope)
                        console.print(f"[green]Found {len(entities_list)} entities:[/green]\n")
                        for entity in sorted(entities_list, key=lambda x: x.api_url):
                            console.print(f"  • {entity.api_url}")
                    return

        # Intent: Get metadata for an entity
        if any(word in question_lower for word in ["fields", "metadata", "schema", "columns"]):
            # Try to extract entity name
            async with get_client() as client:
                entities_list = await client.list_apis()
                for entity in entities_list:
                    if entity.api_url.lower() in question_lower or entity.external_api_name.lower() in question_lower:
                        console.print(f"[cyan]Getting metadata for {entity.api_url}...[/cyan]\n")
                        metadata = await client.get_metadata(entity.api_url)
                        table = Table(title=f"{entity.api_url} Fields")
                        table.add_column("Field", style="cyan")
                        table.add_column("Type", style="green")
                        table.add_column("PK", style="magenta")

                        for field in metadata:
                            table.add_row(
                                field.field_name,
                                field.type,
                                "✓" if field.is_primary_key else "",
                            )

                        console.print(table)
                        return

        # Intent: How to query
        if any(word in question_lower for word in ["how to query", "how do i query", "query example"]):
            console.print(Panel(Markdown("""
            **Querying Entities:**

            Use the `fsgw query` command:

            ```bash
            # Simple query
            fsgw query ops/auditTrail --limit 10

            # With filters
            fsgw query ops/auditTrail --filter tenantId=7 --limit 10

            # With sorting
            fsgw query ops/auditTrail --sort-by auditId --sort-order desc

            # JSON output
            fsgw query ops/auditTrail --output json
            ```

            **Using the Python SDK:**

            ```python
            from fsgw import FSGWClient, QueryRequest

            async with FSGWClient(...) as client:
                # Simple query
                results = await client.query("ops/auditTrail")

                # With filters
                query = QueryRequest() \\
                    .add_filter("tenantId", "=", 7) \\
                    .limit(10)
                results = await client.query("ops/auditTrail", query)
            ```
            """), title="Query Examples"))
            return

        # Default: search
        console.print(f"[cyan]Searching for: {question}[/cyan]\n")
        await _fallback_search(question)

    async def _fallback_search(term: str) -> None:
        """Fallback to direct search if doc server unavailable."""
        async with get_client() as client:
            entities_list = await client.list_apis()

            term_lower = term.lower()
            results = [
                e
                for e in entities_list
                if (
                    term_lower in e.api_url.lower()
                    or term_lower in e.external_api_name.lower()
                    or (e.description and term_lower in e.description.lower())
                )
            ]

            if results:
                console.print(f"[green]Found {len(results)} related entities:[/green]\n")
                for entity in results[:10]:  # Limit to 10
                    console.print(f"  • [cyan]{entity.api_url}[/cyan] - {entity.external_api_name}")
            else:
                console.print("[yellow]No direct matches found. Try being more specific.[/yellow]")
                console.print("\n[cyan]Available scopes:[/cyan] ops, data, config, metadata, globalmeta, rbac")
                console.print("\n[cyan]Example questions:[/cyan]")
                console.print("  • What entities are in the ops scope?")
                console.print("  • Show me audit trail fields")
                console.print("  • How do I query data?")

    asyncio.run(_ask())


@app.command()
def server(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
) -> None:
    """Start the documentation server."""
    console.print(f"[green]Starting documentation server on http://{host}:{port}[/green]")
    console.print("[cyan]Press Ctrl+C to stop[/cyan]\n")

    from fsgw.server.main import main as server_main
    server_main(host=host, port=port, reload=reload)


@app.command()
def interactive() -> None:
    """Start interactive mode (not implemented yet)."""
    console.print("[yellow]Interactive mode coming soon![/yellow]")


if __name__ == "__main__":
    app()
