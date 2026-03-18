from __future__ import annotations

from pathlib import Path

from tests.smokes.steps import system


def helm_env(workdir: Path) -> dict[str, str]:
    cache_home = workdir / ".helm" / "cache"
    config_home = workdir / ".helm" / "config"
    data_home = workdir / ".helm" / "data"
    system.ensure_dir(cache_home)
    system.ensure_dir(config_home)
    system.ensure_dir(data_home)
    return {
        "HELM_NO_PLUGINS": "1",
        "HELM_CACHE_HOME": str(cache_home),
        "HELM_CONFIG_HOME": str(config_home),
        "HELM_DATA_HOME": str(data_home),
    }


def lint(
    chart_dir: Path,
    *,
    workdir: Path,
    values_file: Path | None = None,
    check: bool = True,
) -> system.CommandResult:
    command = ["helm", "lint", str(chart_dir)]
    if values_file is not None:
        command.extend(["-f", str(values_file)])
    return system.run(command, cwd=chart_dir, env=helm_env(workdir), check=check)


def template(
    chart_dir: Path,
    *,
    release_name: str,
    namespace: str,
    output_path: Path,
    workdir: Path,
    values_file: Path | None = None,
) -> Path:
    command = [
        "helm",
        "template",
        release_name,
        str(chart_dir),
        "--namespace",
        namespace,
    ]
    if values_file is not None:
        command.extend(["-f", str(values_file)])

    result = system.run(command, cwd=chart_dir, env=helm_env(workdir), check=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.stdout, encoding="utf-8")
    return output_path

