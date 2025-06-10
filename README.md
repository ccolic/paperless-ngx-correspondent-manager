# Paperless-ngx Correspondent Manager

A Python CLI tool to manage correspondents in your paperless-ngx instance, with functionality to find and merge duplicate/similar correspondents.

## Features

- List all correspondents with their document counts
- Multiple output formats for correspondent listing (table, JSON, YAML)
- Find exact duplicate correspondents (same name)
- Find similar correspondents using fuzzy string matching
- Group similar correspondents together (instead of just pairs)
- Find correspondents with no documents
- Merge correspondents by moving all documents from one to another
- Merge entire groups of correspondents in one operation
- Automatically merge all similar correspondents above a threshold
- Delete individual correspondents
- Delete all empty correspondents (with or without individual confirmation)
- Delete correspondents after merging
- Diagnose correspondent issues
- Restore documents to correspondents
- Find recently created documents

## Installation

### From PyPI (recommended)

```bash
pip install paperless-ngx-correspondent-manager
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/ccolic/paperless_ngx_correspondent_manager.git
cd paperless_ngx_correspondent_manager
```

2. Install in development mode:
```bash
pip install -e .
```

## Configuration

Set your API credentials as environment variables (recommended):
```bash
export PAPERLESS_URL="https://your-paperless-instance.com"
export PAPERLESS_TOKEN="your_actual_api_token_here"
```

## Usage

The CLI uses Click framework with subcommands. Use `--help` with any command to see detailed usage.

### Basic Commands

#### List all correspondents:
```bash
paperless-ngx-correspondent-manager list
```

#### List correspondents in different output formats:
```bash
# Default table format
paperless-ngx-correspondent-manager list --format table

# JSON format (machine-readable)
paperless-ngx-correspondent-manager list --format json

# YAML format (human-readable structured)
paperless-ngx-correspondent-manager list --format yaml
```

#### Find exact duplicates:
```bash
paperless-ngx-correspondent-manager find-duplicates
```

#### Find similar correspondents (grouped):
```bash
paperless-ngx-correspondent-manager find-similar
```

#### Find similar correspondents (as pairs):
```bash
paperless-ngx-correspondent-manager find-similar-pairs
```

#### Find correspondents with no documents:
```bash
paperless-ngx-correspondent-manager find-empty
```

### Advanced Operations

#### Merge correspondents:
Move all documents from correspondent ID 456 to correspondent ID 123:
```bash
paperless-ngx-correspondent-manager merge 123 456
```

#### Merge multiple correspondents at once:
```bash
paperless-ngx-correspondent-manager merge-group 123 456 789
```

#### Delete a correspondent:
```bash
paperless-ngx-correspondent-manager delete 123
```

#### Delete all empty correspondents (with confirmation for each):
```bash
paperless-ngx-correspondent-manager delete-empty
```

#### Delete all empty correspondents (batch mode, no individual confirmation):
```bash
paperless-ngx-correspondent-manager delete-empty-batch
```

#### Automatically merge similar correspondents above threshold:
```bash
paperless-ngx-correspondent-manager merge-threshold 0.9
```

#### Diagnose a correspondent:
```bash
paperless-ngx-correspondent-manager diagnose 123
```

#### Restore documents to a correspondent:
```bash
paperless-ngx-correspondent-manager restore-docs 1001 1002 1003 --to-correspondent 123
```

#### Find recently created documents:
```bash
paperless-ngx-correspondent-manager find-recent-docs --days 7
```

### Using with Explicit Credentials

If you prefer not to use environment variables:

```bash
paperless-ngx-correspondent-manager --url "https://your-paperless-instance.com" --token "your_token" list
```

## Configuration

The script supports configuration via environment variables:

- `PAPERLESS_URL`: Your paperless-ngx instance URL
- `PAPERLESS_TOKEN`: Your API token

You can also pass these as command-line options:
```bash
paperless-ngx-correspondent-manager --url "https://your-paperless-instance.com" --token "your_token" COMMAND
```

## API Token

To get your API token:

1. Log into your paperless-ngx web interface
2. Click on your username in the top right
3. Select "My Profile"
4. Click the circular arrow button to generate/regenerate your API token
5. Copy the token for use with this script

## Similarity Matching

The similarity matching uses Python's `difflib.SequenceMatcher` with a default threshold of 0.9:

- `1.0` = Exact match only
- `0.9` = Very similar (recommended for finding typos)
- `0.8` = Moderately similar
- `0.7` = More loosely similar
- `0.6` or lower = May produce many false positives

## Safety Features

- The script will prompt for confirmation before deleting correspondents
- Merge operations move documents first, then optionally delete the source correspondent
- All operations use the official paperless-ngx REST API
- Built-in validation for correspondent IDs

## Example Workflow

1. First, list all correspondents to get an overview:
```bash
paperless-ngx-correspondent-manager list
```

2. Find exact duplicates:
```bash
paperless-ngx-correspondent-manager find-duplicates
```

3. Find similar correspondents:
```bash
paperless-ngx-correspondent-manager find-similar
```

4. Find correspondents with no documents:
```bash
paperless-ngx-correspondent-manager find-empty
```

5. Merge duplicates (replace IDs with actual ones from step 2/3):
```bash
paperless-ngx-correspondent-manager merge 123 456
```

6. Or automatically merge all similar correspondents above 90% similarity:
```bash
paperless-ngx-correspondent-manager merge-threshold 0.9
```

7. Clean up empty correspondents:
```bash
paperless-ngx-correspondent-manager delete-empty
```

## Troubleshooting

- **401 Unauthorized**: Check your API token
- **Connection errors**: Verify the base URL is correct and accessible
- **No correspondents found**: Ensure you have correspondents in your paperless-ngx instance

## API Compatibility

This script uses paperless-ngx REST API version 9 and should work with paperless-ngx 1.3.0 and later versions.
