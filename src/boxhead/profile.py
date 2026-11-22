"""Perfil local: saldo de moeda e melhorias permanentes, guardados em disco (#17).

O que persiste entre partidas vive aqui; tudo o resto (XP, nível, augments, ronda) é da
partida e recomeça sempre. O ficheiro é JSON versionado e a escrita é atómica: um erro a
meio nunca deixa o save a metade.
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

FORMAT_VERSION = 1
PROFILE_FILE = "profile.json"


class ProfileFormatError(ValueError):
    """O conteúdo do ficheiro não é um perfil válido."""


class LoadStatus(Enum):
    NEW = "new"  # não havia ficheiro
    LOADED = "loaded"
    RECOVERED = "recovered"  # ilegível/corrompido: guardado à parte, perfil novo
    INCOMPATIBLE = "incompatible"  # versão mais recente que a suportada: copiado, perfil novo


@dataclass
class Profile:
    balance: int = 0
    upgrades: dict[str, int] = field(default_factory=dict)  # id da melhoria → nível comprado
    preferences: dict[str, Any] = field(default_factory=dict)  # reservado para o futuro

    def credit(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("não se credita moeda negativa")
        self.balance += amount

    def level(self, upgrade_id: str) -> int:
        return self.upgrades.get(upgrade_id, 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": FORMAT_VERSION,
            "balance": self.balance,
            "upgrades": dict(self.upgrades),
            "preferences": dict(self.preferences),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Profile:
        balance = data.get("balance", 0)
        upgrades = data.get("upgrades", {})
        preferences = data.get("preferences", {})
        if not _is_count(balance):
            raise ProfileFormatError(f"saldo inválido: {balance!r}")
        if not isinstance(upgrades, dict) or not all(
            isinstance(k, str) and _is_count(v) for k, v in upgrades.items()
        ):
            raise ProfileFormatError("melhorias inválidas")
        if not isinstance(preferences, dict):
            raise ProfileFormatError("preferências inválidas")
        return cls(balance=balance, upgrades=dict(upgrades), preferences=dict(preferences))


def _is_count(value: object) -> bool:
    """Inteiro não negativo (bool é int em Python, mas não é um saldo)."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


@dataclass(frozen=True)
class LoadResult:
    profile: Profile
    status: LoadStatus
    detail: str = ""  # para mostrar ao jogador quando algo foi recuperado


def default_profile_path() -> Path:
    """`$BOXHEAD_HOME/profile.json` ou `~/.boxhead/profile.json` (igual em Linux e Windows)."""
    home = os.environ.get("BOXHEAD_HOME")
    return (Path(home) if home else Path.home() / ".boxhead") / PROFILE_FILE


Migration = Callable[[dict[str, Any]], dict[str, Any]]


class ProfileStore:
    def __init__(self, path: Path, migrations: Mapping[int, Migration] | None = None) -> None:
        self.path = Path(path)
        self._migrations = dict(migrations or {})  # versão N → função que o leva a N + 1

    # ------------------------------------------------------------------ leitura

    def load(self) -> LoadResult:
        if not self.path.exists():
            return LoadResult(Profile(), LoadStatus.NEW)
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return self._recover("o ficheiro do perfil estava ilegível")
        version = data.get("version") if isinstance(data, dict) else None
        if not isinstance(version, int) or isinstance(version, bool) or version < 0:
            return self._recover("o ficheiro do perfil não tem um formato válido")
        if version > FORMAT_VERSION:
            return self._set_aside_newer(version)
        try:
            profile = Profile.from_dict(self._migrate(data, version))
        except ProfileFormatError as error:
            return self._recover(f"o perfil estava inválido ({error})")
        return LoadResult(profile, LoadStatus.LOADED)

    def _migrate(self, data: dict[str, Any], version: int) -> dict[str, Any]:
        while version < FORMAT_VERSION:
            step = self._migrations.get(version)
            if step is None:
                raise ProfileFormatError(f"sem migração a partir da versão {version}")
            data = step(dict(data))
            version += 1
        return data

    def _recover(self, reason: str) -> LoadResult:
        """Guarda o ficheiro estragado ao lado (nunca o apaga) e começa um perfil novo."""
        backup = self.path.with_name(self.path.name + ".corrupt")
        try:
            os.replace(self.path, backup)
            detail = f"{reason}; guardámos uma cópia em {backup.name} e começámos um perfil novo"
        except OSError:
            detail = f"{reason}; começámos um perfil novo"
        return LoadResult(Profile(), LoadStatus.RECOVERED, detail)

    def _set_aside_newer(self, version: int) -> LoadResult:
        """Um save de uma versão futura nunca é sobrescrito sem cópia."""
        backup = self.path.with_name(f"{self.path.stem}.v{version}.bak")
        shutil.copy2(self.path, backup)
        detail = (
            f"o perfil é de uma versão mais recente ({version}); "
            f"guardámos uma cópia em {backup.name} e começámos um perfil novo"
        )
        return LoadResult(Profile(), LoadStatus.INCOMPATIBLE, detail)

    # ------------------------------------------------------------------ escrita

    def save(self, profile: Profile) -> None:
        """Escrita atómica: escreve num ficheiro temporário e só depois substitui o save."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        payload = json.dumps(profile.to_dict(), indent=2, sort_keys=True)
        try:
            with open(temporary, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
