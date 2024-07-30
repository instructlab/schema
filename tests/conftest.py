# SPDX-License-Identifier: Apache-2.0

# Standard
import logging
import pathlib

# Third Party
import pytest


@pytest.fixture
def caplog(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:  # pylint: disable=redefined-outer-name
    caplog.set_level(logging.INFO, logger="instructlab.schema")
    return caplog


@pytest.fixture(scope="session")
def testdata() -> pathlib.Path:
    abs_path = pathlib.Path(__file__).parent.resolve().joinpath("testdata")
    cwd = pathlib.Path.cwd()
    return abs_path.relative_to(cwd) if abs_path.is_relative_to(cwd) else abs_path
