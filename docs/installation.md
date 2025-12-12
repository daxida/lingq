# Installation

This guide will walk you through installing the LingQ CLI tool and configuring it for use.

## Requirements

- Python 3.12 or higher
- pip (Python package manager)
- A LingQ account
- LingQ API key

## Installing the Package

Install the LingQ CLI using pip:

```bash
pip install lingq
```

This will install the `lingq` command and all required dependencies.

### Optional Dependencies

If you need additional functionality for scraping, audio transcription, or development tools:

```bash
# Install with all optional dependencies
pip install lingq[etc]

# Install with test dependencies
pip install lingq[test]

# Install with documentation dependencies
pip install lingq[docs]

# Install everything
pip install lingq[all]
```

## Getting Your API Key

Before using the CLI, you'll need a LingQ API key:

1. Log in to your LingQ account
2. Navigate to [https://www.lingq.com/en/accounts/apikey/](https://www.lingq.com/en/accounts/apikey/)
3. Copy your API key

!!! warning "Keep Your API Key Secure"
    Your API key provides full access to your LingQ account. Never share it publicly or commit it to version control.

## Configuring the CLI

Once you have your API key, configure the CLI:

```bash
lingq setup yourLingqApiKey
```

This command creates a `.env` file in your configuration directory with your API key securely stored.

### Configuration File Location

The configuration file is stored in a platform-specific location:

- **macOS**: `~/Library/Application Support/lingq/.env`
- **Linux**: `~/.config/lingq/.env`
- **Windows**: `%APPDATA%\lingq\.env`

The `.env` file contains:

```
LINGQ_API_KEY=yourLingqApiKey
```

### Updating Your API Key

To update your API key, simply run the setup command again with the new key:

```bash
lingq setup newApiKey
```

## Security Best Practices

!!! tip "API Key Security"
    - Never share your API key with others
    - Don't commit your API key to version control
    - If you suspect your key has been compromised, regenerate it on the LingQ website
    - The `.env` file should have restricted permissions (the tool handles this automatically)

!!! info "Environment Variables"
    You can also set the API key using an environment variable:
    ```bash
    export LINGQ_API_KEY=yourLingqApiKey
    ```
    This is useful for CI/CD environments or temporary testing.

## Verifying Installation

Verify that the installation was successful:

```bash
# Check the CLI is installed
lingq --version

# View available commands
lingq --help

# Test API connection by viewing your collections
lingq show my en
```

If you see your English collections listed (with their course IDs), everything is working correctly!

!!! tip "Finding Course IDs"
    The course ID is shown next to each course name when you run `lingq show my <language_code>`. You can also find it in the LingQ website URL when viewing a course: `https://www.lingq.com/en/learn/en/web/course/129129` (129129 is the course ID).

## Development Installation

If you want to contribute to the project or work with the source code:

```bash
# Clone the repository
git clone https://github.com/daxida/lingq.git
cd lingq

# Install in development mode with all dependencies
pip install -e ".[all]"

# Run tests
pytest

# Format code
ruff format .

# Type check
mypy src/
```

## Troubleshooting

### Command Not Found

If you get a "command not found" error after installation:

1. Ensure pip's script directory is in your PATH
2. Try using `python -m cli` instead of `lingq`
3. Restart your terminal

### API Key Not Found

If you get an API key error:

1. Verify you ran `lingq setup yourApiKey`
2. Check that the `.env` file exists in the config directory
3. Ensure the API key is valid on the LingQ website

### Permission Errors

If you encounter permission errors during installation:

```bash
# Use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install lingq

# Or install for user only
pip install --user lingq
```

## Next Steps

Now that you have the CLI installed and configured:

- [Learn about available commands](user-guide/commands.md)
- [Follow common workflow tutorials](user-guide/workflows.md)
- [Explore the API reference](api-reference/lingqhandler.md)
