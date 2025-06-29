# Setup

The GitOps CLI can be used in multiple ways depending on your needs: via Docker, using Astral’s uvx, or by installing it from source for local development.

## Option 1: Use via Docker (Recommended)

The official GitOps CLI Docker image comes with all dependencies pre-installed and ready-to-use. Pull it with:
```bash
docker pull baloise/gitopscli
```
Start the CLI and the print the help page with:
```bash
docker run --rm -it baloise/gitopscli --help
```

## Option 2: Run as Tool via uvx

Astral's [uvx](https://docs.astral.sh/uv/guides/tools/) allows you to run the CLI without installing it.

```bash
uvx https://github.com/baloise/gitopscli.git --help
```

## Option 3: From Source For Local Development

Use this method if you're contributing to the project or want to develop it on your own.

### Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if it's not yet available.

### Steps

1. Clone the repository:
```bash
git clone https://github.com/baloise/gitopscli.git
cd gitopscli/
```
2. Install dependencies:
```bash
uv sync --locked --all-groups
```

3. Run the CLI:
```bash
uv run gitopscli --help
```
### Updating uv
If you're using an older version of uv, you can update it with:
```bash
uv self upgrade
```
