from __future__ import annotations

from app.platform.apps.contracts import AppManifest


class RegistryError(ValueError):
    pass


def _version_tuple(version: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in version.split("."))


class AppRegistry:
    def __init__(self, enabled_ids: set[str] | None = None) -> None:
        self._manifests: dict[str, AppManifest] = {}
        self._enabled_ids = frozenset(enabled_ids) if enabled_ids is not None else None
        self._finalized = False

    def register(self, manifest: AppManifest) -> None:
        if self._finalized:
            raise RegistryError("cannot register applications after finalization")
        if manifest.id in self._manifests:
            raise RegistryError(f"duplicate application id: {manifest.id}")
        self._manifests[manifest.id] = manifest

    def finalize(self) -> None:
        if self._enabled_ids is not None:
            unknown = self._enabled_ids - self._manifests.keys()
            if unknown:
                raise RegistryError(f"unknown enabled application ids: {sorted(unknown)}")
        for manifest in self._manifests.values():
            for dependency in manifest.dependencies:
                installed = self._manifests.get(dependency.app_id)
                if installed is None:
                    raise RegistryError(f"{manifest.id} has missing dependency {dependency.app_id}")
                if _version_tuple(installed.version) < _version_tuple(dependency.minimum_version):
                    raise RegistryError(
                        f"{manifest.id} requires {dependency.app_id}>={dependency.minimum_version}; "
                        f"installed {installed.version}"
                    )
        if self._enabled_ids is not None:
            disabled_dependencies = sorted(
                (manifest.id, dependency.app_id)
                for manifest in self._manifests.values()
                if manifest.id in self._enabled_ids
                for dependency in manifest.dependencies
                if dependency.app_id not in self._enabled_ids
            )
            if disabled_dependencies:
                requirements = ", ".join(
                    f"{app_id} requires {dependency_id}"
                    for app_id, dependency_id in disabled_dependencies
                )
                raise RegistryError(
                    f"enabled application dependencies must also be enabled: {requirements}; "
                    "add the required dependency ids to enabled_ids"
                )
        self._finalized = True

    def _require_finalized(self) -> None:
        if not self._finalized:
            raise RegistryError("registry must be finalized before reading")

    def list_enabled(self) -> list[AppManifest]:
        self._require_finalized()
        manifests = self._manifests.values()
        if self._enabled_ids is not None:
            manifests = [manifest for manifest in manifests if manifest.id in self._enabled_ids]
        return sorted(manifests, key=lambda manifest: manifest.id)

    def get(self, app_id: str) -> AppManifest | None:
        self._require_finalized()
        if self._enabled_ids is not None and app_id not in self._enabled_ids:
            return None
        return self._manifests.get(app_id)
