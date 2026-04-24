from __future__ import annotations

import os
import shutil


AGENT_BACKEND_ENV = "JUBEN_AGENT_BACKEND"

_BACKENDS = {
    "claude": {
        "label": "Claude",
        "executable": "claude",
        "command_prefix": ["claude", "-p", "--dangerously-skip-permissions"],
    },
    "codex": {
        "label": "Codex",
        "executable": "codex.cmd",
        "command_prefix": ["codex.cmd", "exec", "--dangerously-bypass-approvals-and-sandbox"],
    },
}
_AUTO_BACKEND_ORDER = ("claude", "codex")


class AgentBackendError(RuntimeError):
    pass


def _normalize_backend_name(raw: str | None) -> str | None:
    if raw is None:
        return None
    normalized = raw.strip().lower()
    if not normalized or normalized == "auto":
        return None
    return normalized


def resolve_agent_backend(backend_name: str | None = None) -> dict[str, object]:
    requested = _normalize_backend_name(backend_name)
    if requested is None:
        requested = _normalize_backend_name(os.environ.get(AGENT_BACKEND_ENV))

    if requested is not None:
        backend = _BACKENDS.get(requested)
        if backend is None:
            supported = ", ".join(["auto", *_BACKENDS.keys()])
            raise AgentBackendError(
                f"unsupported agent backend '{requested}'; expected one of: {supported}"
            )
        if shutil.which(str(backend["executable"])) is None:
            raise AgentBackendError(
                f"configured agent backend '{requested}' is not installed or not on PATH"
            )
        return backend

    for candidate in _AUTO_BACKEND_ORDER:
        backend = _BACKENDS[candidate]
        if shutil.which(str(backend["executable"])) is not None:
            return backend

    tried = ", ".join(_AUTO_BACKEND_ORDER)
    raise AgentBackendError(
        f"no supported agent backend found on PATH (tried: {tried}). "
        f"Install one of them or set {AGENT_BACKEND_ENV} explicitly."
    )


def build_agent_command(prompt: str, backend_name: str | None = None) -> tuple[str, list[str]]:
    backend = resolve_agent_backend(backend_name)
    label = str(backend["label"])
    command = [*backend["command_prefix"], prompt]
    return label, command
