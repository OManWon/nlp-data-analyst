
import io
import contextlib
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class SafeExecResult:
    """코드 실행 결과를 담는 데이터 클래스"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    local_ns: Dict[str, Any] = field(default_factory=dict)

def safe_execute(code: str, global_ns: dict | None = None, local_ns: dict | None = None) -> SafeExecResult:
    """
    신뢰할 수 없는 코드를 격리된 환경에서 안전하게 실행하고 결과를 반환합니다.
    실행 후의 local namespace를 결과에 포함하여 반환합니다.
    """
    if local_ns is None:
        local_ns = {}
    if global_ns is None:
        global_ns = {}

    stdout_io = io.StringIO()
    stderr_io = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout_io), contextlib.redirect_stderr(stderr_io):
            exec(code, global_ns, local_ns)

        return SafeExecResult(
            success=True,
            stdout=stdout_io.getvalue(),
            stderr=stderr_io.getvalue(),
            local_ns=local_ns,
        )
    except Exception:
        return SafeExecResult(
            success=False,
            stdout=stdout_io.getvalue(),
            stderr=stderr_io.getvalue(),
            error=traceback.format_exc(),
            local_ns=local_ns,
        )
