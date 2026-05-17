"""Component index generation for the index-sync tool."""

from __future__ import annotations

from pathlib import Path

from index_writer import generate_lookup_indexes


def generate_component_indexes(index_dir: Path, tasks: list) -> None:
    """Generate by-component lookup indexes under `index_dir`."""
    components = sorted(
        {
            component
            for task in tasks
            for component in [task.primary_component, *task.related_components]
            if component and component != "unknown"
        }
    )
    generate_lookup_indexes(
        index_dir,
        tasks,
        "by-component",
        "component",
        components,
        lambda task, value: (
            task.primary_component == value or value in task.related_components
        ),
    )
