# Publishing `vivado-mcp-native` to PyPI

The repository publishes through GitHub Actions Trusted Publishing. No long-lived PyPI API token is stored in GitHub.

## One-time PyPI configuration

Sign in to PyPI and add a pending GitHub Actions publisher with these exact values:

```text
PyPI project name: vivado-mcp-native
Owner: Arthurzxy
Repository: vivado_mcp_native
Workflow filename: publish-pypi.yml
Environment: pypi
```

The publisher configuration must match `.github/workflows/publish-pypi.yml` exactly.

A pending publisher does not reserve the project name until the first successful upload.

## GitHub environment

Create a repository environment named:

```text
pypi
```

Recommended path:

```text
Settings → Environments → New environment → pypi
```

Optionally require manual approval for this environment.

## First publication

After the pending publisher and GitHub environment are configured:

1. Confirm `pyproject.toml` contains the intended version.
2. Open **Actions → Publish to PyPI**.
3. Select the `master` branch.
4. Click **Run workflow**.
5. Confirm the package page appears as `vivado-mcp-native` on PyPI.

The same workflow also runs automatically when a GitHub Release is published.

## Later releases

1. Update the version in both `pyproject.toml` and `vivado_mcp.__version__` in `__init__.py`.
2. Merge the change from `dev` into `master`.
3. Create and publish a GitHub Release using the matching tag, for example `v0.2.1`.
4. The release workflow builds the wheel and source distribution, validates them with Twine, and publishes them through OIDC.

PyPI does not allow replacing an already uploaded file for the same project version. Increment the version for every new release.
