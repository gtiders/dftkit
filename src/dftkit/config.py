from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML


DEFAULT_PROVIDER = "vasp"
CONFIG_DIR = Path.home() / ".config" / "dftkit"
CONFIG_PATH = CONFIG_DIR / "config.yaml"

yaml = YAML(typ="safe")


@dataclass(frozen=True, slots=True)
class AppConfig:
    default_provider: str = DEFAULT_PROVIDER


def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        return AppConfig()

    data = yaml.load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    default_provider = str(data.get("default_provider", DEFAULT_PROVIDER)).strip().lower()
    if not default_provider:
        default_provider = DEFAULT_PROVIDER
    return AppConfig(default_provider=default_provider)


def ensure_config_file() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(
            "default_provider: vasp\n",
            encoding="utf-8",
        )
    return CONFIG_PATH
