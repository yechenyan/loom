# Python API

Use `import loom` when Python code needs a local path to a raw file managed by a
Loom workspace.

## Get One Raw File

```python
import loom

path = loom.get(
    "energy/demo_germany_energy_data/open_power_system_data/generation_capacity/germany_2015_net_capacity.csv"
)
print(path)
```

`loom.get(...)` expects `workspace/path/to/file`. It returns a local `Path`.

Resolution order:

1. Return the existing cached file when it is healthy.
2. Populate the cache from a matching local scan source when possible.
3. Pull that exact raw file from the configured Loom server.

If the file cannot be found, `loom.get(...)` raises `FileNotFoundError`.

## Workspace Root

By default, Loom treats the current working directory as the workspace root. Pass
`workspace_root` when your Python process runs from another directory:

```python
import loom

path = loom.get(
    "energy/path/to/file.csv",
    workspace_root="/path/to/project",
)
```

## Server URL

Pass `server_url` to override the configured default for this call:

```python
import loom

path = loom.get(
    "energy/path/to/file.csv",
    server_url="https://example.com",
)
```

## Pull Raw Data

Use `loom.pull(...)` to pull raw files through Python:

```python
import loom

results = loom.pull("energy")
```

Omit the workspace to pull raw files for remote workspaces:

```python
results = loom.pull()
```

For normal analysis, prefer `loom.get(...)` because it fetches only the exact raw
file needed.
