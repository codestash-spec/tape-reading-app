from __future__ import annotations


def rollback_plan(version: str) -> str:
    return f"Rollback to {version}: stop services, deploy previous artifact, verify health."
