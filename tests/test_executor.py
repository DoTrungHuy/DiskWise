from pathlib import Path

import pytest

from diskwise.executor.service import FeatureDisabledError, FileExecutor


@pytest.mark.parametrize("operation", ["move", "rename", "delete"])
def test_real_file_operations_are_disabled(operation):
    executor = FileExecutor()

    with pytest.raises(FeatureDisabledError):
        if operation == "move":
            executor.move(Path("source"), Path("destination"))
        elif operation == "rename":
            executor.rename(Path("source"), "new-name")
        else:
            executor.delete(Path("target"))

