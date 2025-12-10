from __future__ import annotations

from typing import Dict


class CICDWorkflow:
    """
    Declarative model of CI/CD steps (lint, test, build, deploy).
    """

    def __init__(self) -> None:
        self.steps = ["lint", "test", "package", "deploy"]

    def plan(self) -> Dict[str, str]:
        return {"workflow": "github_actions", "steps": ",".join(self.steps)}
