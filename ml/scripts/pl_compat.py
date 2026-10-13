"""Minimal `pytorch_lightning` compatibility shim for Phase-1 PosFormer inference.

Why: PosFormer (2024) pins pytorch-lightning==1.4.9 / Python 3.7, which cannot
install on this machine's Python 3.11. The inference path only needs
`pl.LightningModule` as an `nn.Module` with a `.device` property — no Trainer,
no callbacks, no distributed logic. This shim provides exactly that, and refuses
to pretend to be a full Lightning install (Trainer raises).

Scope: used ONLY by the Phase-1 standalone harness (run_posformer.py). It is NOT
a general replacement for Lightning and must not be used for training.
Material modification: none to PosFormer source itself (third-party code stays
outside the repo, in a scratch dir); only the import is redirected here.
"""

import sys
import types
from typing import Any

import torch
import torch.nn as nn

_stub = types.ModuleType("pytorch_lightning")
_stub.__doc__ = "Minimal Phase-1 inference shim; NOT full pytorch-lightning."


class LightningModule(nn.Module):
    """nn.Module + `.device` (first parameter's device, else CPU)."""

    @property
    def device(self) -> torch.device:
        try:
            return next(self.parameters()).device
        except StopIteration:
            return torch.device("cpu")

    def save_hyperparameters(self, *args: Any, **kwargs: Any) -> None:
        self._saved_hparams = (args, kwargs)


class LightningDataModule:
    pass


def seed_everything(seed: int = 7, *args: Any, **kwargs: Any) -> int:
    torch.manual_seed(seed)
    return seed


class Trainer:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError(
            "Phase-1 shim Trainer cannot train/evaluate. "
            "Use run_posformer.py (plain-torch inference) instead."
        )


class _CallbackStub:
    """Placeholder for pickled Lightning callbacks (never executed)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._args, self._kwargs = args, kwargs


class LearningRateMonitor(_CallbackStub):
    pass


class ModelCheckpoint(_CallbackStub):
    pass


_callbacks = types.ModuleType("pytorch_lightning.callbacks")
_callbacks.LearningRateMonitor = LearningRateMonitor
_callbacks.ModelCheckpoint = ModelCheckpoint
_callbacks.__path__ = []  # package: deeper imports (e.g. .model_checkpoint) go via _PLFinder

_stub.LightningModule = LightningModule
_stub.LightningDataModule = LightningDataModule
_stub.seed_everything = seed_everything
_stub.Trainer = Trainer
_stub.callbacks = _callbacks
_stub.__path__ = []  # mark as package so 'pytorch_lightning.callbacks' imports


class _PickleStub:
    """Generic stand-in for pickled PL-internal objects (callbacks etc.).

    Only its stored state matters (never executed)."""

    def __new__(cls, *args: Any, **kwargs: Any) -> "_PickleStub":
        inst = object.__new__(cls)
        inst._args, inst._kwargs = args, kwargs
        return inst

    def __setstate__(self, state: Any) -> None:
        if isinstance(state, dict):
            self.__dict__.update(state)


class _PLFinder:
    """Meta-path finder: fabricate any pytorch_lightning.* submodule with
    generic stub classes so legacy checkpoints unpickle without real Lightning."""

    PREFIX = "pytorch_lightning."

    def find_module(self, fullname: str, path=None):  # legacy protocol (py3.11 ok)
        if fullname.startswith(self.PREFIX):
            return self
        return None

    def load_module(self, fullname: str):
        if fullname in sys.modules:
            return sys.modules[fullname]
        mod = types.ModuleType(fullname)
        mod.__path__ = []

        def _mod_getattr(name: str, _mod=fullname):
            return type(f"{_mod}.{name}", (_PickleStub,), {})

        mod.__getattr__ = _mod_getattr  # PEP 562
        sys.modules[fullname] = mod
        return mod


def install() -> None:
    """Register the shim in sys.modules (idempotent)."""
    sys.modules.setdefault("pytorch_lightning", _stub)
    sys.modules.setdefault("pytorch_lightning.callbacks", _callbacks)
    if not any(isinstance(f, _PLFinder) for f in sys.meta_path):
        sys.meta_path.append(_PLFinder())
