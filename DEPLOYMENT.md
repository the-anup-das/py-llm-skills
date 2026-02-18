# Deployment Guide

This guide explains how to release **llm-skills** to PyPI using GitHub Actions and Trusted Publishers (OIDC).

## Prerequisites

1.  **PyPI Account**: Create an account on [pypi.org](https://pypi.org/).
2.  **GitHub Repository**: Ensure this code is pushed to a public GitHub repository.

## 1. Configure Trusted Publishing (Recommended)

Trusted Publishing allows GitHub Actions to publish to PyPI without long-lived API tokens.

1.  Go to **PyPI** > **Your Projects** > **Publishing**.
2.  Select **"Add a new pending publisher"**.
3.  Fill in the details:
    *   **PyPI Project Name**: `llm-skills`
    *   **Owner**: Your Git username (or organization).
    *   **Repository Name**: The name of your repo (e.g., `llm-skills`).
    *   **Workflow Filename**: `publish.yml`
    *   **Environment Name**: Leave blank (or use `pypi`).
4.  Click **Add**.

## 2. Create a Release

To trigger a deployment, simply create a **Release** on GitHub:

1.  Go to your repository on GitHub.
2.  Click **Releases** > **Draft a new release**.
3.  Tag version: `v0.1.0` (Must match `pyproject.toml` version).
4.  Title: `v0.1.0`.
5.  Click **Publish release**.

The `.github/workflows/publish.yml` workflow will automatically run, build the package using `uv`, and upload it to PyPI.

## 3. Manual Deployment (Alternative)

If you prefer to publish manually from your terminal:

```bash
# 1. Build
uv build

# 2. Publish (requires token)
uv publish
```

You will need a PyPI API token configured in your environment or `~/.pypirc`.
