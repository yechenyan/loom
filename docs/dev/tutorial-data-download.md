# Tutorial Data Download

Loom tutorial raw data must not be bundled inside the `loom-data` PyPI package.
The CLI package should contain code, skills templates, and metadata only.

## Runtime Behavior

`loomcli init` installs tutorial data by downloading a versioned `.tar.gz`
archive into the user's workspace:

```text
raw_data/demo_germany_energy_data/
```

Fast init with `--agent` attempts the download automatically unless
`--no-tutorial` is provided. Interactive init asks before downloading. Download
failure must not fail the workspace initialization because `loom/`, `raw_data/`,
and skills are the core setup.

## Artifact Contract

The archive should contain exactly one dataset directory with `loom.md`.
The expected top-level directory is:

```text
demo_germany_energy_data/
```

The CLI downloads to a temporary directory, verifies SHA256 when configured,
rejects unsafe archive paths or links, extracts, then moves the dataset into
`raw_data/`. Existing tutorial data is kept unless `--force-tutorial` is used.

## Release Process

Keep editable source data in `raw_example/demo_germany_energy_data/`, outside
the Python package tree. For a new tutorial release:

1. Build a deterministic `demo_germany_energy_data.tar.gz`:

   ```bash
   python scripts/build_tutorial_data.py
   ```

2. Commit it to the repository under `tutorial-data/` and push the tag named by
   `TUTORIAL_DATA_VERSION` before publishing the PyPI package that references it.
3. Update `TUTORIAL_DATA_VERSION`, `TUTORIAL_DATA_URL`, and
   `TUTORIAL_DATA_SHA256` in `packages/loom/src/loom/cli_app/tutorial_download.py`.
4. Run the init and tutorial download tests.
5. Update docs if the dataset path, source, or user-facing workflow changes.

The PyPI release script enforces this ordering: before publishing, it rebuilds
the local archive and verifies that the configured remote URL downloads bytes
with the configured SHA256. A missing tag-backed archive or checksum mismatch
blocks the package publish.

Keep the demo archive small. If raw GitHub downloads are slow for users, switch
the default URL to a CDN-backed mirror and keep `--tutorial-url` for internal
mirrors.
