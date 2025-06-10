#!/usr/bin/env python3
"""
CLI interface for Paperless-ngx Correspondent Manager
"""

import sys
from datetime import datetime, timedelta
from urllib.parse import urljoin

import click

from .manager import PaperlessCorrespondentManager


@click.group(invoke_without_command=True)
@click.option(
    "--url",
    required=True,
    help="Paperless-ngx base URL",
    envvar="PAPERLESS_URL",
)
@click.option(
    "--token",
    required=True,
    help="API token",
    envvar="PAPERLESS_TOKEN",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, url, token, verbose):
    """Manage paperless-ngx correspondents.

    This tool helps you manage correspondents in your paperless-ngx instance by finding
    duplicates, merging them, and cleaning up empty correspondents.

    Set PAPERLESS_URL and PAPERLESS_TOKEN environment variables to avoid
    passing --url and --token every time.

    Examples:\n
        paperless-ngx-correspondent-manager list\n
        paperless-ngx-correspondent-manager find-duplicates\n
        paperless-ngx-correspondent-manager merge 123 456
    """
    ctx.ensure_object(dict)
    ctx.obj["manager"] = PaperlessCorrespondentManager(url, token)
    ctx.obj["verbose"] = verbose

    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
@click.pass_context
def list(ctx, format):
    """List all correspondents."""
    manager = ctx.obj["manager"]
    manager.list_correspondents(format)


@cli.command("find-duplicates")
@click.pass_context
def find_duplicates(ctx):
    """Find exact duplicate correspondents."""
    manager = ctx.obj["manager"]
    duplicates = manager.find_exact_duplicates()

    if duplicates:
        click.echo(f"\nFound {len(duplicates)} groups of exact duplicates:")
        click.echo("=" * 60)

        for i, group in enumerate(duplicates, 1):
            click.echo(f"\nGroup {i}:")
            for correspondent in group:
                click.echo(
                    f"  ID: {correspondent['id']:>4} | Name: {correspondent['name']}"
                )
                if correspondent.get("document_count", 0) > 0:
                    click.echo(f"       | Documents: {correspondent['document_count']}")
    else:
        click.echo("\nNo exact duplicates found.")


@cli.command("find-similar")
@click.pass_context
def find_similar(ctx):
    """Find similar correspondents (grouped)."""
    manager = ctx.obj["manager"]
    similar_groups = manager.find_similar_correspondents()

    if similar_groups:
        click.echo(f"\nFound {len(similar_groups)} groups of similar correspondents:")
        click.echo("=" * 70)

        for i, group in enumerate(similar_groups, 1):
            click.echo(f"\nSimilar Group {i}:")
            for correspondent in group:
                click.echo(
                    f"  ID: {correspondent['id']:>4} | Name: {correspondent['name']}"
                )
                if correspondent.get("document_count", 0) > 0:
                    click.echo(f"       | Documents: {correspondent['document_count']}")
    else:
        click.echo("\nNo similar correspondents found.")


@cli.command("find-similar-pairs")
@click.pass_context
def find_similar_pairs(ctx):
    """Find similar correspondents (as pairs)."""
    manager = ctx.obj["manager"]
    similar_pairs = manager.find_similar_correspondents_pairs()

    if similar_pairs:
        click.echo(f"\nFound {len(similar_pairs)} pairs of similar correspondents:")
        click.echo("=" * 80)

        for i, (corr1, corr2, similarity) in enumerate(similar_pairs, 1):
            click.echo(f"\nPair {i} (Similarity: {similarity:.2f}):")
            click.echo(f"  ID: {corr1['id']:>4} | Name: {corr1['name']}")
            if corr1.get("document_count", 0) > 0:
                click.echo(f"       | Documents: {corr1['document_count']}")
            click.echo(f"  ID: {corr2['id']:>4} | Name: {corr2['name']}")
            if corr2.get("document_count", 0) > 0:
                click.echo(f"       | Documents: {corr2['document_count']}")
    else:
        click.echo("\nNo similar correspondent pairs found.")


@cli.command("find-empty")
@click.pass_context
def find_empty(ctx):
    """Find correspondents with no documents."""
    manager = ctx.obj["manager"]
    manager.print_empty_correspondents()


@cli.command()
@click.argument("correspondent_ids", nargs=-1, type=int, required=True)
@click.pass_context
def merge(ctx, correspondent_ids):
    """Merge correspondents (first ID is target).

    CORRESPONDENT_IDS: List of correspondent IDs to merge (at least 2 required)
    """
    if len(correspondent_ids) < 2:
        click.echo("Error: At least 2 correspondent IDs are required for merging")
        sys.exit(1)

    manager = ctx.obj["manager"]
    target_id = correspondent_ids[0]
    source_ids = correspondent_ids[1:]

    # Get correspondent info for confirmation
    correspondents = manager.get_correspondents()
    corr_dict = {c["id"]: c for c in correspondents}

    # Validate IDs
    invalid_ids = [cid for cid in correspondent_ids if cid not in corr_dict]
    if invalid_ids:
        click.echo(f"Error: Invalid correspondent IDs: {invalid_ids}")
        sys.exit(1)

    click.echo(
        f"Target correspondent: {corr_dict[target_id]['name']} (ID: {target_id})"
    )
    click.echo("Source correspondents to merge:")
    for source_id in source_ids:
        click.echo(f"  - {corr_dict[source_id]['name']} (ID: {source_id})")

    if click.confirm("Proceed with merge?"):
        for source_id in source_ids:
            manager.merge_correspondents(target_id, source_id)
    else:
        click.echo("Merge cancelled.")


@cli.command("merge-group")
@click.argument("correspondent_ids", nargs=-1, type=int, required=True)
@click.pass_context
def merge_group(ctx, correspondent_ids):
    """Merge multiple correspondents into first ID.

    CORRESPONDENT_IDS: List of correspondent IDs to merge (at least 2 required)
    """
    if len(correspondent_ids) < 2:
        click.echo("Error: At least 2 correspondent IDs are required for group merging")
        sys.exit(1)

    manager = ctx.obj["manager"]
    correspondents = manager.get_correspondents()
    corr_dict = {c["id"]: c for c in correspondents}

    # Validate IDs
    valid_ids = [cid for cid in correspondent_ids if cid in corr_dict]

    if len(valid_ids) >= 2:
        target_id = correspondent_ids[0]  # First ID is the target
        manager.merge_correspondent_group(valid_ids, target_id)
    else:
        click.echo("Error: Not enough valid correspondent IDs found")


@cli.command("merge-threshold")
@click.argument("threshold", type=float)
@click.pass_context
def merge_threshold(ctx, threshold):
    """Auto-merge similar correspondents above threshold.

    THRESHOLD: Similarity threshold (0-1)
    """
    if threshold < 0 or threshold > 1:
        click.echo("Error: Threshold must be between 0 and 1")
        sys.exit(1)

    manager = ctx.obj["manager"]
    manager.auto_merge_similar_correspondents(threshold)


@cli.command()
@click.argument("correspondent_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this correspondent?")
@click.pass_context
def delete(ctx, correspondent_id):
    """Delete a correspondent by ID.

    CORRESPONDENT_ID: ID of the correspondent to delete
    """
    manager = ctx.obj["manager"]
    manager.delete_correspondent(correspondent_id)


@cli.command("delete-empty")
@click.pass_context
def delete_empty(ctx):
    """Delete empty correspondents (with confirmation for each)."""
    manager = ctx.obj["manager"]
    manager.delete_empty_correspondents(confirm_each=True)


@cli.command("delete-empty-batch")
@click.confirmation_option(
    prompt="Are you sure you want to delete ALL empty correspondents?"
)
@click.pass_context
def delete_empty_batch(ctx):
    """Delete all empty correspondents without individual confirmation."""
    manager = ctx.obj["manager"]
    manager.delete_empty_correspondents(confirm_each=False)


@cli.command()
@click.argument("correspondent_id", type=int)
@click.pass_context
def diagnose(ctx, correspondent_id):
    """Show detailed information about a correspondent.

    CORRESPONDENT_ID: ID of the correspondent to diagnose
    """
    manager = ctx.obj["manager"]
    manager.print_correspondent_diagnosis(correspondent_id)


@cli.command("restore-docs")
@click.argument("document_ids", nargs=-1, type=int, required=True)
@click.option(
    "--to-correspondent",
    type=int,
    required=True,
    help="Target correspondent ID for restore operation",
)
@click.pass_context
def restore_docs(ctx, document_ids, to_correspondent):
    """Restore documents to a correspondent.

    DOCUMENT_IDS: List of document IDs to restore
    """
    manager = ctx.obj["manager"]

    if click.confirm(
        f"Restore {len(document_ids)} documents to correspondent {to_correspondent}?"
    ):
        manager.restore_documents_to_correspondent(document_ids, to_correspondent)
    else:
        click.echo("Restoration cancelled.")


@cli.command("find-recent-docs")
@click.option("--days", default=7, help="Number of days back to search (default: 7)")
@click.pass_context
def find_recent_docs(ctx, days):
    """Find recently created documents."""
    manager = ctx.obj["manager"]

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    click.echo(f"Finding documents created between {start_date} and {end_date}...")
    recent_docs = manager.find_documents_by_date_range(start_date, end_date)

    click.echo(f"\nFound {len(recent_docs)} recent documents:")
    click.echo("-" * 80)

    for doc in recent_docs[:20]:  # Show first 20
        corr_name = "None"
        if doc.get("correspondent"):
            # Try to get correspondent name
            try:
                corr_url = urljoin(
                    manager.base_url,
                    f"/api/correspondents/{doc['correspondent']}/",
                )
                corr_response = manager.session.get(corr_url)
                if corr_response.status_code == 200:
                    corr_name = corr_response.json().get(
                        "name", f"ID:{doc['correspondent']}"
                    )
                else:
                    corr_name = f"ID:{doc['correspondent']}"
            except Exception:
                corr_name = f"ID:{doc['correspondent']}"

        click.echo(f"ID: {doc['id']:>5} | Title: {doc.get('title', 'N/A')[:50]}")
        click.echo(f"      | Correspondent: {corr_name}")
        click.echo(f"      | Created: {doc.get('created', 'N/A')}")
        click.echo()

    if len(recent_docs) > 20:
        click.echo(f"... and {len(recent_docs) - 20} more documents")


def main() -> None:
    """Main CLI entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
