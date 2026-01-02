#!/usr/bin/env python3
"""
PHANTOM Framework - Unified CLI

Command-line interface for the Phantom framework combining:
- GCP credit management
- Knowledge extraction & RAG
- Cloud integrations
"""
import sys
import os

# Add phantom to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import typer
    from rich import print as rprint
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("❌ Missing dependencies. Please install:")
    print("   pip install typer rich")
    sys.exit(1)

from phantom.core import gcp
from phantom.modules import credit_burner


app = typer.Typer(
    name="phantom",
    help="PHANTOM Framework - Knowledge Extraction & Cloud Credit Management",
    no_args_is_help=True
)
console = Console()


# ============================================================================
# GCP Commands
# ============================================================================

gcp_app = typer.Typer(help="Google Cloud Platform operations")
app.add_typer(gcp_app, name="gcp")


@gcp_app.command("validate")
def gcp_validate():
    """Validate GCP setup (auth, billing, APIs)"""
    status = gcp.validate_setup(verbose=True)
    sys.exit(0 if status.authenticated else 1)


@gcp_app.command("datastores-list")
def gcp_datastores_list():
    """List Vertex AI Data Stores"""
    try:
        manager = gcp.DataStoreManager()
        stores = manager.list()

        if not stores:
            console.print("[yellow]No data stores found[/yellow]")
            console.print("\n💡 Create one with: phantom gcp datastores-create")
            return

        table = Table(title="Vertex AI Data Stores")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")

        for store in stores:
            table.add_row(store.id, store.display_name, store.content_config)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@gcp_app.command("datastores-create")
def gcp_datastores_create(
    data_store_id: str = typer.Argument(..., help="Data store ID"),
    display_name: str = typer.Option("Phantom Data Store", help="Display name")
):
    """Create a new Vertex AI Data Store"""
    try:
        manager = gcp.DataStoreManager()
        console.print(f"🔨 Creating data store '{data_store_id}'...")

        store = manager.create(
            data_store_id=data_store_id,
            display_name=display_name
        )

        console.print(f"[green]✅ Data Store created: {store.id}[/green]")
        console.print(f"\n📝 Use it with:")
        console.print(f"   export DATA_STORE_ID='{store.id}'")

    except FileExistsError:
        console.print(f"[yellow]⚠️  Data store '{data_store_id}' already exists[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@gcp_app.command("search")
def gcp_search(
    query: str = typer.Argument(..., help="Search query"),
    data_store_id: str = typer.Option(None, envvar="DATA_STORE_ID", help="Data store ID"),
    top_k: int = typer.Option(5, help="Number of results")
):
    """Execute a grounded search query"""
    if not data_store_id:
        console.print("[red]❌ DATA_STORE_ID not configured[/red]")
        console.print("\n🔧 FIX:")
        console.print("   1. phantom gcp datastores-list")
        console.print("   2. export DATA_STORE_ID='your-id'")
        sys.exit(1)

    try:
        search = gcp.VertexAISearch(data_store_id=data_store_id)
        console.print(f"🔍 Searching: {query}")
        console.print(f"📦 Data Store: {data_store_id}\n")

        response = search.grounded_search(query, top_k=top_k)

        if response.summary:
            console.print("[bold green]🤖 AI Summary:[/bold green]")
            console.print(response.summary)
            console.print()

        if response.results:
            console.print(f"[bold]🔎 {len(response.results)} Results:[/bold]")
            for i, result in enumerate(response.results, 1):
                console.print(f"\n[cyan]{i}. {result.title}[/cyan]")
                if result.snippet:
                    console.print(f"   {result.snippet[:200]}...")
                if result.link:
                    console.print(f"   🔗 {result.link}")

        console.print(f"\n💰 Cost: ~${response.cost_estimate:.4f}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================================
# Credit Burner Commands
# ============================================================================

credit_app = typer.Typer(help="GCP credit burning operations")
app.add_typer(credit_app, name="credit")


@credit_app.command("loadtest")
def credit_loadtest(
    num_queries: int = typer.Option(100, help="Number of queries to execute"),
    data_store_id: str = typer.Option(None, envvar="DATA_STORE_ID", help="Data store ID"),
    workers: int = typer.Option(10, help="Parallel workers"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Run load test to burn GenAI App Builder credits"""
    if not data_store_id:
        console.print("[red]❌ DATA_STORE_ID not configured[/red]")
        sys.exit(1)

    try:
        credit_burner.run_loadtest(
            num_queries=num_queries,
            data_store_id=data_store_id,
            max_workers=workers,
            auto_confirm=yes
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@credit_app.command("audit")
def credit_audit(
    days: int = typer.Option(7, help="Days to look back")
):
    """Audit credit consumption via BigQuery"""
    try:
        result = credit_burner.audit_credits(days_back=days, verbose=True)
        sys.exit(0 if result["status"] == "success" else 1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@credit_app.command("dialogflow")
def credit_dialogflow(
    num_conversations: int = typer.Option(10, help="Number of conversations"),
    agent_id: str = typer.Option(None, envvar="DIALOGFLOW_AGENT_ID", help="Agent ID"),
    location: str = typer.Option("us-central1", help="Dialogflow location"),
    workers: int = typer.Option(5, help="Parallel workers"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Burn Dialogflow CX credits via conversation sessions"""
    if not agent_id:
        console.print("[red]❌ DIALOGFLOW_AGENT_ID not configured[/red]")
        console.print("\n🔧 FIX:")
        console.print("   1. Create agent: https://dialogflow.cloud.google.com/cx/")
        console.print("   2. export DIALOGFLOW_AGENT_ID='your-agent-id'")
        sys.exit(1)

    try:
        manager = gcp.DialogflowCXManager(location=location, agent_id=agent_id)
        metrics = manager.run_load_test(
            num_conversations=num_conversations,
            max_workers=workers,
            auto_confirm=yes
        )

        console.print(f"\n[green]✅ Complete! Cost: ${metrics.total_cost_usd:.4f}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================================
# RAG Commands
# ============================================================================

rag_app = typer.Typer(help="RAG server operations")
app.add_typer(rag_app, name="rag")


@rag_app.command("serve")
def rag_serve(
    model: str = typer.Option("TheBloke/Mistral-7B-Instruct-v0.2-GPTQ", help="Model name"),
    port: int = typer.Option(8000, help="Server port"),
    db_path: str = typer.Option("./data/vector_db", help="ChromaDB path")
):
    """Start RAG server with local LLM"""
    console.print("[yellow]⚠️  RAG server not yet implemented in unified CLI[/yellow]")
    console.print("Use: cd phantom && nix develop")
    console.print("Then: cerebro-serve")


# ============================================================================
# Info Commands
# ============================================================================

@app.command("info")
def info():
    """Display Phantom framework information"""
    table = Table(title="PHANTOM Framework v2.0")

    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description", style="yellow")

    table.add_row("Core/GCP", "✅ Ready", "Unified Google Cloud Platform integrations")
    table.add_row("Core/Extraction", "✅ Ready", "Code knowledge extraction")
    table.add_row("Core/RAG", "✅ Ready", "RAG server with local LLM")
    table.add_row("Module/CreditBurner", "✅ Ready", "GCP credit consumption")
    table.add_row("Module/Knowledge", "🚧 Planned", "Knowledge base management")
    table.add_row("Module/NixOS", "🚧 Planned", "NixOS service integration")

    console.print(table)

    console.print("\n📚 Documentation:")
    console.print("   PHANTOM_ARCHITECTURE.md - Complete architecture")
    console.print("   README.md - Getting started")

    console.print("\n🔧 Quick Commands:")
    console.print("   phantom gcp validate           - Validate GCP setup")
    console.print("   phantom gcp datastores-list    - List data stores")
    console.print("   phantom gcp search 'query'     - Search with AI")
    console.print("   phantom credit loadtest        - Burn credits")
    console.print("   phantom credit audit           - Audit consumption")


@app.command("version")
def version():
    """Display version information"""
    console.print("[bold cyan]PHANTOM Framework v2.0.0[/bold cyan]")
    console.print("Knowledge Extraction & Cloud Credit Management")
    console.print("\nComponents:")
    console.print("  • Core: GCP, Extraction, RAG")
    console.print("  • Modules: CreditBurner, Knowledge, NixOS")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    app()
