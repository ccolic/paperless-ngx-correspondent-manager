"""
Paperless-ngx Correspondent Manager

This module provides the main PaperlessCorrespondentManager class for interacting with paperless-ngx.
"""

import json
import sys
from difflib import SequenceMatcher
from urllib.parse import urljoin

import requests
import yaml

# Global configuration
DEFAULT_SIMILARITY_THRESHOLD = 0.9


class PaperlessCorrespondentManager:
    """Main class for managing paperless-ngx correspondents."""

    def __init__(self, base_url: str, token: str):
        """
        Initialize the Paperless-ngx client.

        Args:
            base_url: Base URL of the paperless-ngx instance
            token: API token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token {token}",
                "Accept": "application/json; version=9",
                "Content-Type": "application/json",
            }
        )

    def get_correspondents(self) -> list[dict]:
        """
        Retrieve all correspondents from the paperless-ngx instance.

        Returns:
            List of correspondent dictionaries
        """
        url = urljoin(self.base_url, "/api/correspondents/")
        all_correspondents = []

        try:
            while url:
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()

                all_correspondents.extend(data.get("results", []))
                url = data.get("next")

                print(f"Retrieved {len(data.get('results', []))} correspondents...")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching correspondents: {e}")
            sys.exit(1)

        return all_correspondents

    def list_correspondents(self, output_format: str = "table") -> None:
        """Print all correspondents in a formatted way.

        Args:
            output_format: Output format ('table', 'json', 'yaml')
        """
        correspondents = self.get_correspondents()

        if output_format.lower() == "json":
            # AIDEV-NOTE: JSON output for machine-readable format
            print(json.dumps(correspondents, indent=2))
        elif output_format.lower() == "yaml":
            # AIDEV-NOTE: YAML output for human-readable structured format
            print(yaml.dump(correspondents, default_flow_style=False, indent=2))
        else:
            # Default table format
            print(f"\\nFound {len(correspondents)} correspondents:")
            print("-" * 80)

            for correspondent in correspondents:
                print(f"ID: {correspondent['id']:>4} | Name: {correspondent['name']}")
                if correspondent.get("last_correspondence"):
                    print(
                        f"     | Last correspondence: {correspondent['last_correspondence']}"
                    )
                if correspondent.get("document_count", 0) > 0:
                    print(f"     | Documents: {correspondent['document_count']}")
                print()

    def find_exact_duplicates(self) -> list[list[dict]]:
        """
        Find correspondents with identical names.

        Returns:
            List of duplicate groups (each group is a list of correspondents)
        """
        correspondents = self.get_correspondents()
        name_groups = {}

        # Group correspondents by name (case-insensitive)
        for correspondent in correspondents:
            name_lower = correspondent["name"].lower().strip()
            if name_lower not in name_groups:
                name_groups[name_lower] = []
            name_groups[name_lower].append(correspondent)

        # Find groups with more than one correspondent
        duplicates = [group for group in name_groups.values() if len(group) > 1]

        return duplicates

    def calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two correspondent names.

        Args:
            name1: First correspondent name
            name2: Second correspondent name

        Returns:
            Similarity score between 0 and 1
        """
        # Normalize names
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, name1, name2).ratio()

    def find_similar_correspondents_pairs(
        self, threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> list[tuple[dict, dict, float]]:
        """
        Find correspondents with similar names (returns pairs).

        Args:
            threshold: Similarity threshold (0-1)

        Returns:
            List of tuples (correspondent1, correspondent2, similarity_score)
        """
        correspondents = self.get_correspondents()
        similar_pairs = []

        for i, corr1 in enumerate(correspondents):
            for _j, corr2 in enumerate(correspondents[i + 1 :], i + 1):
                similarity = self.calculate_similarity(corr1["name"], corr2["name"])
                if similarity >= threshold:
                    similar_pairs.append((corr1, corr2, similarity))

        # Sort by similarity score (descending)
        similar_pairs.sort(key=lambda x: x[2], reverse=True)

        return similar_pairs

    def find_similar_correspondents(
        self, threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> list[list[dict]]:
        """
        Find correspondents with similar names grouped together.

        Args:
            threshold: Similarity threshold (0-1)

        Returns:
            List of groups, where each group is a list of similar correspondents
        """
        correspondents = self.get_correspondents()

        # Create a graph of similar correspondents
        similar_graph = {}
        for i, corr1 in enumerate(correspondents):
            similar_graph[corr1["id"]] = []
            for j, corr2 in enumerate(correspondents):
                if i != j:
                    similarity = self.calculate_similarity(corr1["name"], corr2["name"])
                    if similarity >= threshold:
                        similar_graph[corr1["id"]].append(corr2["id"])

        # Group similar correspondents using graph traversal
        visited = set()
        groups = []

        for correspondent in correspondents:
            if correspondent["id"] not in visited:
                # Start a new group
                group = []
                stack = [correspondent["id"]]

                while stack:
                    current_id = stack.pop()
                    if current_id not in visited:
                        visited.add(current_id)
                        # Find the correspondent object
                        current_corr = next(
                            c for c in correspondents if c["id"] == current_id
                        )
                        group.append(current_corr)

                        # Add similar correspondents to the stack
                        for similar_id in similar_graph[current_id]:
                            if similar_id not in visited:
                                stack.append(similar_id)

                # Only add groups with more than one correspondent
                if len(group) > 1:
                    # Sort group by name for consistent ordering
                    group.sort(key=lambda x: x["name"].lower())
                    groups.append(group)

        return groups

    def print_duplicates(self) -> None:
        """Print exact duplicate correspondents."""
        duplicates = self.find_exact_duplicates()

        if not duplicates:
            print("No exact duplicate correspondents found.")
            return

        print(f"\\nFound {len(duplicates)} groups of exact duplicates:")
        print("=" * 80)

        for i, group in enumerate(duplicates, 1):
            print(f"\\nDuplicate Group {i}:")
            print(f"Name: '{group[0]['name']}'")
            print("-" * 40)

            for correspondent in group:
                print(
                    f"  ID: {correspondent['id']:>4} | Documents: {correspondent.get('document_count', 0):>3}"
                )
                if correspondent.get("last_correspondence"):
                    print(
                        f"       | Last correspondence: {correspondent['last_correspondence']}"
                    )

    def print_similar_correspondents(
        self, threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> None:
        """Print similar correspondents grouped together."""
        similar_groups = self.find_similar_correspondents(threshold)

        if not similar_groups:
            print(f"No similar correspondents found with threshold {threshold}.")
            return

        print(
            f"\\nFound {len(similar_groups)} groups of similar correspondents (threshold: {threshold}):"
        )
        print("=" * 80)

        for i, group in enumerate(similar_groups, 1):
            print(f"\\nSimilar Group {i}:")
            print("-" * 50)

            # Calculate and show similarity scores within the group
            similarities = []
            for j, corr1 in enumerate(group):
                for _k, corr2 in enumerate(group[j + 1 :], j + 1):
                    similarity = self.calculate_similarity(corr1["name"], corr2["name"])
                    similarities.append(similarity)

            avg_similarity = (
                sum(similarities) / len(similarities) if similarities else 0
            )
            print(f"Average similarity in group: {avg_similarity:.3f}")
            print()

            for j, correspondent in enumerate(group, 1):
                print(
                    f"  {j}. ID: {correspondent['id']:>4} | Name: '{correspondent['name']}' | Docs: {correspondent.get('document_count', 0)}"
                )
                if correspondent.get("last_correspondence"):
                    print(
                        f"     | Last correspondence: {correspondent['last_correspondence']}"
                    )
            print()

    def print_similar_correspondents_pairs(
        self, threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> None:
        """Print similar correspondents as pairs (old behavior)."""
        similar_pairs = self.find_similar_correspondents_pairs(threshold)

        if not similar_pairs:
            print(f"No similar correspondents found with threshold {threshold}.")
            return

        print(
            f"\\nFound {len(similar_pairs)} pairs of similar correspondents (threshold: {threshold}):"
        )
        print("=" * 80)

        for i, (corr1, corr2, similarity) in enumerate(similar_pairs, 1):
            print(f"\\nSimilar Pair {i} (Similarity: {similarity:.3f}):")
            print(
                f"  1. ID: {corr1['id']:>4} | Name: '{corr1['name']}' | Docs: {corr1.get('document_count', 0)}"
            )
            print(
                f"  2. ID: {corr2['id']:>4} | Name: '{corr2['name']}' | Docs: {corr2.get('document_count', 0)}"
            )

    def get_correspondent_documents(self, correspondent_id: int) -> list[dict]:
        """
        Get all documents for a specific correspondent.

        Args:
            correspondent_id: ID of the correspondent

        Returns:
            List of document dictionaries
        """
        url = urljoin(
            self.base_url, f"/api/documents/?correspondent__id__in={correspondent_id}"
        )
        documents = []

        try:
            while url:
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()

                documents.extend(data.get("results", []))
                url = data.get("next")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching documents for correspondent {correspondent_id}: {e}")

        return documents

    def merge_correspondents(self, source_id: int, target_id: int) -> bool:
        """
        Merge two correspondents by updating all documents from source to target.

        Args:
            source_id: ID of the correspondent to merge from
            target_id: ID of the correspondent to merge to

        Returns:
            True if successful, False otherwise
        """
        # Get all documents for the source correspondent
        documents = self.get_correspondent_documents(source_id)

        if not documents:
            print(f"No documents found for correspondent {source_id}")
            return True

        # Update all documents using the improved bulk reassignment method
        document_ids = [doc["id"] for doc in documents]

        print(
            f"Merging {len(document_ids)} documents from correspondent {source_id} to {target_id}..."
        )
        return self.bulk_reassign_documents(document_ids, target_id)

    def merge_correspondent_group(
        self, group: list[dict], target_id: int = None
    ) -> bool:
        """
        Merge a group of similar correspondents into one.

        Args:
            group: List of correspondent dictionaries to merge
            target_id: ID of the target correspondent (if None, uses the one with most documents)

        Returns:
            True if successful, False otherwise
        """
        if len(group) < 2:
            print("Group must have at least 2 correspondents to merge.")
            return False

        # If no target specified, use the correspondent with the most documents
        if target_id is None:
            target_correspondent = max(group, key=lambda x: x.get("document_count", 0))
            target_id = target_correspondent["id"]
            print(
                f"Using correspondent '{target_correspondent['name']}' (ID: {target_id}) as merge target (has {target_correspondent.get('document_count', 0)} documents)"
            )
        else:
            target_correspondent = next(
                (c for c in group if c["id"] == target_id), None
            )
            if not target_correspondent:
                print(f"Target ID {target_id} not found in the group.")
                return False

        # Merge all other correspondents into the target
        success = True
        merged_sources = []

        for correspondent in group:
            if correspondent["id"] != target_id:
                print(
                    f"Merging '{correspondent['name']}' (ID: {correspondent['id']}) into '{target_correspondent['name']}' (ID: {target_id})..."
                )
                if self.merge_correspondents(correspondent["id"], target_id):
                    merged_sources.append(correspondent["id"])
                else:
                    success = False

        if success and merged_sources:
            print(
                f"\\nSuccessfully merged {len(merged_sources)} correspondents into '{target_correspondent['name']}'"
            )

            # Ask if user wants to delete the merged correspondents
            response = input(
                f"Delete the {len(merged_sources)} merged correspondents? (y/N): "
            )
            if response.lower() == "y":
                for source_id in merged_sources:
                    self.delete_correspondent(source_id)

        return success

    def delete_correspondent(self, correspondent_id: int) -> bool:
        """
        Delete a correspondent.

        Args:
            correspondent_id: ID of the correspondent to delete

        Returns:
            True if successful, False otherwise
        """
        url = urljoin(self.base_url, f"/api/correspondents/{correspondent_id}/")

        try:
            response = self.session.delete(url)
            response.raise_for_status()
            print(f"Successfully deleted correspondent {correspondent_id}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error deleting correspondent {correspondent_id}: {e}")
            return False

    def find_empty_correspondents(self) -> list[dict]:
        """
        Find correspondents that have no documents associated with them.

        Returns:
            List of correspondent dictionaries with no documents
        """
        correspondents = self.get_correspondents()
        empty_correspondents = []

        for correspondent in correspondents:
            if correspondent.get("document_count", 0) == 0:
                empty_correspondents.append(correspondent)

        return empty_correspondents

    def print_empty_correspondents(self) -> None:
        """Print correspondents that have no documents."""
        empty_correspondents = self.find_empty_correspondents()

        if not empty_correspondents:
            print(
                "No empty correspondents found (all correspondents have at least one document)."
            )
            return

        print(f"\\nFound {len(empty_correspondents)} correspondents with no documents:")
        print("=" * 80)

        for i, correspondent in enumerate(empty_correspondents, 1):
            print(
                f"{i:>3}. ID: {correspondent['id']:>4} | Name: '{correspondent['name']}'"
            )
            if correspondent.get("last_correspondence"):
                print(
                    f"     | Last correspondence: {correspondent['last_correspondence']}"
                )
        print()

    def delete_empty_correspondents(self, confirm_each: bool = True) -> int:
        """
        Delete all correspondents that have no documents.

        Args:
            confirm_each: If True, ask for confirmation for each deletion

        Returns:
            Number of correspondents successfully deleted
        """
        empty_correspondents = self.find_empty_correspondents()

        if not empty_correspondents:
            print("No empty correspondents found to delete.")
            return 0

        print(f"Found {len(empty_correspondents)} correspondents with no documents:")
        self.print_empty_correspondents()

        if not confirm_each:
            response = input(
                f"Delete all {len(empty_correspondents)} empty correspondents? (y/N): "
            )
            if response.lower() != "y":
                print("Deletion cancelled.")
                return 0

        deleted_count = 0
        for correspondent in empty_correspondents:
            should_delete = True

            if confirm_each:
                response = input(
                    f"Delete '{correspondent['name']}' (ID: {correspondent['id']})? (y/N/q): "
                )
                if response.lower() == "q":
                    break
                elif response.lower() != "y":
                    should_delete = False

            if should_delete:
                if self.delete_correspondent(correspondent["id"]):
                    deleted_count += 1

        print(
            f"\\nDeleted {deleted_count} out of {len(empty_correspondents)} empty correspondents."
        )
        return deleted_count

    def auto_merge_similar_correspondents(self, threshold: float) -> int:
        """
        Interactively merge groups of similar correspondents above a threshold.
        For each group, user selects which correspondent to keep as the target.

        Args:
            threshold: Similarity threshold for finding and merging correspondents

        Returns:
            Number of groups successfully merged
        """
        similar_groups = self.find_similar_correspondents(threshold)

        if not similar_groups:
            print(
                f"No similar correspondents found with threshold {threshold} to merge."
            )
            return 0

        print(
            f"\\nFound {len(similar_groups)} groups of similar correspondents (threshold: {threshold}):"
        )
        print("=" * 80)

        merged_count = 0
        for i, group in enumerate(similar_groups, 1):
            print(f"\\n--- Group {i} of {len(similar_groups)} ---")
            print("Similar correspondents found:")

            # Display all correspondents in the group with indices
            for j, correspondent in enumerate(group, 1):
                print(
                    f"  {j}. ID: {correspondent['id']:>4} | Name: '{correspondent['name']}' | Docs: {correspondent.get('document_count', 0)}"
                )
                if correspondent.get("last_correspondence"):
                    print(
                        f"     | Last correspondence: {correspondent['last_correspondence']}"
                    )

            # Ask user to choose which correspondent to keep
            while True:
                try:
                    choice = (
                        input(
                            f"\\nWhich correspondent should be kept as the target? (1-{len(group)}, 's' to skip, 'q' to quit): "
                        )
                        .strip()
                        .lower()
                    )

                    if choice == "q":
                        print("Merge operation cancelled by user.")
                        return merged_count
                    elif choice == "s":
                        print("Skipping this group.")
                        break

                    choice_num = int(choice)
                    if 1 <= choice_num <= len(group):
                        target_correspondent = group[choice_num - 1]
                        target_id = target_correspondent["id"]

                        print(
                            f"\\nSelected '{target_correspondent['name']}' (ID: {target_id}) as the target."
                        )
                        print("Will merge these correspondents into the target:")

                        sources_to_merge = [c for c in group if c["id"] != target_id]
                        for correspondent in sources_to_merge:
                            print(
                                f"  - '{correspondent['name']}' (ID: {correspondent['id']}) - {correspondent.get('document_count', 0)} docs"
                            )

                        # Confirm this specific merge
                        confirm = input(
                            f"\\nProceed with merging {len(sources_to_merge)} correspondents into '{target_correspondent['name']}'? (y/N): "
                        )
                        if confirm.lower() == "y":
                            print(f"\\n--- Merging Group {i} ---")
                            if self.merge_correspondent_group(group, target_id):
                                merged_count += 1
                                print(f"Successfully merged group {i}")
                            else:
                                print(f"Failed to merge group {i}")
                        else:
                            print("Skipping this group.")
                        break
                    else:
                        print(
                            f"Please enter a number between 1 and {len(group)}, 's' to skip, or 'q' to quit."
                        )
                except ValueError:
                    print(
                        f"Please enter a number between 1 and {len(group)}, 's' to skip, or 'q' to quit."
                    )

        print("\\n=== Merge Summary ===")
        print(
            f"Successfully merged {merged_count} out of {len(similar_groups)} groups."
        )
        return merged_count

    def diagnose_correspondent(self, correspondent_id: int) -> dict:
        """
        Get detailed information about a correspondent and its documents.

        Args:
            correspondent_id: ID of the correspondent to diagnose

        Returns:
            Dictionary with correspondent details and document information
        """
        # Get correspondent info
        try:
            url = urljoin(self.base_url, f"/api/correspondents/{correspondent_id}/")
            response = self.session.get(url)
            response.raise_for_status()
            correspondent = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching correspondent {correspondent_id}: {e}")
            return {}

        # Get documents for this correspondent
        documents = self.get_correspondent_documents(correspondent_id)

        # Get document details including titles and dates
        detailed_documents = []
        for doc in documents[:10]:  # Limit to first 10 for performance
            try:
                doc_url = urljoin(self.base_url, f"/api/documents/{doc['id']}/")
                doc_response = self.session.get(doc_url)
                doc_response.raise_for_status()
                detailed_documents.append(doc_response.json())
            except Exception as e:
                print(f"Error fetching document {doc['id']}: {e}")
                detailed_documents.append(doc)

        return {
            "correspondent": correspondent,
            "document_count": len(documents),
            "documents": documents,
            "detailed_documents": detailed_documents,
        }

    def print_correspondent_diagnosis(self, correspondent_id: int) -> None:
        """Print detailed diagnostic information for a correspondent."""
        diagnosis = self.diagnose_correspondent(correspondent_id)

        if not diagnosis:
            return

        corr = diagnosis["correspondent"]
        print("\\n=== Correspondent Diagnosis ===")
        print(f"ID: {corr['id']}")
        print(f"Name: '{corr['name']}'")
        print(f"Document Count: {diagnosis['document_count']}")
        print(f"API Document Count: {corr.get('document_count', 'N/A')}")

        if corr.get("last_correspondence"):
            print(f"Last Correspondence: {corr['last_correspondence']}")

        print("\\n--- Recent Documents (showing first 10) ---")
        for i, doc in enumerate(diagnosis["detailed_documents"][:10], 1):
            print(f"{i:>2}. ID: {doc['id']:>5} | Title: {doc.get('title', 'N/A')}")
            print(f"     | Created: {doc.get('created', 'N/A')}")
            if doc.get("archive_serial_number"):
                print(f"     | ASN: {doc['archive_serial_number']}")

        if diagnosis["document_count"] > 10:
            print(f"... and {diagnosis['document_count'] - 10} more documents")

    def bulk_reassign_documents(
        self,
        document_ids: list[int],
        target_correspondent_id: int,
        batch_size: int = 50,
    ) -> bool:
        """
        Reassign documents to a correspondent in smaller batches to avoid timeouts.

        Args:
            document_ids: List of document IDs to reassign
            target_correspondent_id: ID of the target correspondent
            batch_size: Number of documents to process in each batch

        Returns:
            True if all batches successful, False otherwise
        """
        if not document_ids:
            print("No documents to reassign.")
            return True

        print(
            f"Reassigning {len(document_ids)} documents in batches of {batch_size}..."
        )

        success = True
        for i in range(0, len(document_ids), batch_size):
            batch = document_ids[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(document_ids) + batch_size - 1) // batch_size

            print(
                f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)..."
            )

            bulk_edit_url = urljoin(self.base_url, "/api/documents/bulk_edit/")
            payload = {
                "documents": batch,
                "method": "set_correspondent",
                "parameters": {"correspondent": target_correspondent_id},
            }

            try:
                response = self.session.post(bulk_edit_url, json=payload, timeout=60)
                response.raise_for_status()
                print(f"  ✓ Batch {batch_num} completed successfully")
            except requests.exceptions.Timeout:
                print(f"  ✗ Batch {batch_num} timed out - trying smaller batches")
                # Try with smaller batch size
                if batch_size > 10:
                    smaller_batch_success = self.bulk_reassign_documents(
                        batch, target_correspondent_id, batch_size // 2
                    )
                    if not smaller_batch_success:
                        success = False
                else:
                    success = False
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Batch {batch_num} failed: {e}")
                success = False

        return success

    def find_documents_by_date_range(
        self, start_date: str = None, end_date: str = None
    ) -> list[dict]:
        """
        Find documents within a date range to help identify incorrectly assigned documents.

        Args:
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)

        Returns:
            List of document dictionaries matching the criteria
        """
        url = urljoin(self.base_url, "/api/documents/")
        params = {}

        if start_date:
            params["created__date__gte"] = start_date
        if end_date:
            params["created__date__lte"] = end_date

        documents = []

        try:
            while url:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                documents.extend(data.get("results", []))
                url = data.get("next")
                params = {}  # Only use params on first request

                if len(documents) >= 100:  # Limit to prevent overwhelming output
                    break

        except requests.exceptions.RequestException as e:
            print(f"Error fetching documents: {e}")

        return documents

    def restore_documents_to_correspondent(
        self, document_ids: list[int], target_correspondent_id: int
    ) -> bool:
        """
        Restore specific documents to a correspondent with better error handling.

        Args:
            document_ids: List of document IDs to restore
            target_correspondent_id: ID of the correspondent to restore to

        Returns:
            True if successful, False otherwise
        """
        if not document_ids:
            print("No documents to restore.")
            return True

        print(
            f"Restoring {len(document_ids)} documents to correspondent {target_correspondent_id}..."
        )

        # Use smaller batches to avoid timeouts
        return self.bulk_reassign_documents(
            document_ids, target_correspondent_id, batch_size=25
        )
