# Ask and Fetch

Use Loom questions when an answer depends on project-local, source-backed data:
CSV values, units, assumptions, model parameters, costs, provenance, or dataset
structure.

## Chat Question Forms

Ask explicitly:

```text
loom ask "What German wind and solar data is available?"
/loom-ask "What German wind and solar data is available?"
```

Or use bare `loom <question>`:

```text
loom 德国 2015 年有哪些发电装机容量数据？
```

The agent may also choose the Loom workflow without an explicit `loom` prefix
when a task needs facts from local datasets.

## Expected Agent Workflow

The agent should:

1. Inspect `loom/` cards and summaries first.
2. Use those files to locate the likely dataset and raw path.
3. Fetch only exact raw files with `loomcli get` or `loom.get(...)`.
4. Answer from the fetched local raw file.

The agent should not guess from a summary when the raw values matter.

## Fetch an Exact Raw File

Terminal:

```bash
loomcli get energy/demo_germany_energy_data/open_power_system_data/generation_capacity/germany_2015_net_capacity.csv
```

Python:

```python
import loom

path = loom.get(
    "energy/demo_germany_energy_data/open_power_system_data/generation_capacity/germany_2015_net_capacity.csv"
)
```

Resources use the form `workspace/path/to/file`. The workspace name is the first
path segment. The file path should usually match the raw workspace path exactly.
That path preserves the dataset directory structure that Loom scanned. If the
scan source is itself a dataset root, the file path starts with that dataset
directory name.

## When Not to Use Loom

Do not use Loom for ordinary data-processing code that already has the needed
file paths, general concept explanations, or external live data. Use Loom when
the hard part is finding the right local source-backed dataset fact.
