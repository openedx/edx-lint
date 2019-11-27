"""pytest setup for this directory."""

import os
import shutil

import pytest


@pytest.fixture(autouse=True)
def run_tests_in_temp_dir(tmpdir):
    """Automatically runs all tests in their own temp directory."""

    cur_dir = os.getcwd()
    new_dir = str(tmpdir)
    os.chdir(new_dir)
    yield
    os.chdir(cur_dir)
    shutil.rmtree(new_dir)
