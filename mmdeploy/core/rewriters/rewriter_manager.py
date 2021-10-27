from typing import Dict

import torch.nn as nn

from mmdeploy.utils.constants import Backend
from .function_rewriter import FunctionRewriter
from .module_rewriter import ModuleRewriter
from .symbolic_rewriter import SymbolicRewriter


class RewriterManager:
    """The rewrite manager that manages some rewriters."""

    def __init__(self):
        self.module_rewriter = ModuleRewriter()
        self.function_rewrite = FunctionRewriter()
        self.symbolic_rewriter = SymbolicRewriter()

    def add_backend(self, backend: str):
        """Add backend to all rewriters.

        Args:
            backend (str): The backend to support.
        """
        self.module_rewriter.add_backend(backend)
        self.function_rewrite.add_backend(backend)
        self.symbolic_rewriter.add_backend(backend)


REWRITER_MANAGER = RewriterManager()
REWRITER_MANAGER.add_backend(Backend.ONNXRUNTIME.value)
REWRITER_MANAGER.add_backend(Backend.TENSORRT.value)
REWRITER_MANAGER.add_backend(Backend.NCNN.value)
REWRITER_MANAGER.add_backend(Backend.PPL.value)
REWRITER_MANAGER.add_backend(Backend.PYTORCH.value)
REWRITER_MANAGER.add_backend(Backend.OPENVINO.value)

MODULE_REWRITER = REWRITER_MANAGER.module_rewriter
FUNCTION_REWRITER = REWRITER_MANAGER.function_rewrite
SYMBOLIC_REWRITER = REWRITER_MANAGER.symbolic_rewriter


def patch_model(model: nn.Module,
                cfg: Dict,
                backend: str = Backend.DEFAULT.value,
                recursive: bool = True,
                **kwargs) -> nn.Module:
    """Patch the model, replace the modules that can be rewritten.

    Args:
        model (torch.nn.Module): The model to patch.
        cfg (Dict): Config dictionary of deployment.
        backend (str): The inference engine name.
        recursive (bool): The flag to enable recursive patching.

    Returns:
        nn.Module: THe patched model.

    Examples:
        >>> from mmdeploy.core import patch_model
        >>> patched_model = patch_model(model, cfg=deploy_cfg, backend=backend)
    """
    return MODULE_REWRITER.patch_model(model, cfg, backend, recursive,
                                       **kwargs)


class RewriterContext:
    """The rewrite context.

    The context is used to manage the rewrite functions and the backend.

    Args:
        cfg (Dict): Config dictionary of deployment.
        backend (str): The inference engine name.
        rewrite_manager (RewriterManager): An RewriteManager that consists of
            several rewriters

    Examples:
        >>> from mmdeploy.core import RewriterContext
        >>> with RewriterContext(cfg, backend='onnxruntime'):
        >>>     # the rewrite has been activated inside the context
        >>>     torch.onnx.export(model, inputs, onnx_file)
    """

    def __init__(self,
                 cfg: Dict = dict(),
                 backend: str = Backend.DEFAULT.value,
                 rewrite_manager: RewriterManager = REWRITER_MANAGER,
                 **kwargs):
        self._cfg = cfg
        self._backend = backend
        self._kwargs = kwargs
        self._rewrite_manager = rewrite_manager

    def enter(self):
        """Call the enter() of rewriters."""
        self._rewrite_manager.function_rewrite.enter(self._cfg, self._backend,
                                                     **self._kwargs)
        self._rewrite_manager.symbolic_rewriter.enter(self._cfg, self._backend,
                                                      **self._kwargs)

    def exit(self):
        """Call the exit() of rewriters."""
        self._rewrite_manager.function_rewrite.exit()
        self._rewrite_manager.symbolic_rewriter.exit()

    def __enter__(self):
        """Call enter()"""
        self.enter()

    def __exit__(self, type, val, tb):
        """Call exit()"""
        self.exit()
