"""Tests for the gradescope main file."""

import json
from os.path import dirname
from os.path import join as pathjoin
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from aga.core import Problem
from aga.gradescope.main import gradescope_main


def get_gs_json(
    problem: Problem[Any], source: str, mocker: MockerFixture, tmp_path: Path
) -> Any:
    """Get the gradescope JSON output for the given problem and submission source."""
    mocked_load_problem = mocker.patch("aga.gradescope.main.load_problem")
    mocked_load_problem.return_value = problem

    output = pathjoin(tmp_path, "results.json")
    gradescope_main(submission_dir=dirname(source), output_file=output)

    with open(output, encoding="UTF-8") as file:
        return json.load(file)


@pytest.fixture(name="gs_json_square")
def fixture_gs_json_square(
    square: Problem[int], source_square: str, mocker: MockerFixture, tmp_path: Path
) -> Any:
    """Generate the JSON output from the square problem."""
    return get_gs_json(square, source_square, mocker, tmp_path)


def test_json_test_name_square(gs_json_square: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct test names."""
    assert set(map(lambda x: x["name"], gs_json_square["tests"])) == {
        "Test 4",
        "Test 2",
        "Test -2",
    }


def test_json_test_score_square(gs_json_square: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct score."""
    assert gs_json_square["score"] == 3


def test_json_test_visibility_square(gs_json_square: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct visibility."""
    assert set(map(lambda t: t["visibility"], gs_json_square["tests"])) == {
        "visible",
        "hidden",
    }


@pytest.fixture(name="gs_json_square_incorrect")
def fixture_gs_json_square_incorrect(
    square: Problem[int],
    source_square_incorrect: str,
    mocker: MockerFixture,
    tmp_path: Path,
) -> Any:
    """Generate the JSON output from the square problem with an incorrect submission."""
    return get_gs_json(square, source_square_incorrect, mocker, tmp_path)


def test_json_test_score_square_incorrect(gs_json_square_incorrect: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct score."""
    assert gs_json_square_incorrect["score"] == 0


def test_json_test_output_square_incorrect(gs_json_square_incorrect: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct output."""
    assert any(
        map(
            lambda t: "Checked with 2. Expected 4. Got 0 instead." in t["output"],
            gs_json_square_incorrect["tests"],
        )
    )


@pytest.fixture(name="gs_json_square_error")
def fixture_gs_json_square_error(
    square: Problem[int],
    source_square_error: str,
    mocker: MockerFixture,
    tmp_path: Path,
) -> Any:
    """Generate the JSON output from the square problem with an erroring submission."""
    return get_gs_json(square, source_square_error, mocker, tmp_path)


def test_json_test_score_square_error(gs_json_square_error: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct score."""
    assert gs_json_square_error["score"] == 0


def test_json_test_output_square_error(gs_json_square_error: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct output."""
    assert all(
        map(
            lambda t: "NameError" in t["output"],
            gs_json_square_error["tests"],
        )
    )


@pytest.fixture(name="gs_json_square_custom_name")
def fixture_gs_json_square_custom_name(
    square_custom_name: Problem[int],
    source_square: str,
    mocker: MockerFixture,
    tmp_path: Path,
) -> Any:
    """Generate the JSON output from the square problem with an erroring submission."""
    return get_gs_json(square_custom_name, source_square, mocker, tmp_path)


def test_json_test_name_square_custom_name(gs_json_square_custom_name: Any) -> None:
    """Test that the JSON file produced by gradescope has the correct test names."""
    assert set(map(lambda x: x["name"], gs_json_square_custom_name["tests"])) == {
        "Test positive two",
        "Test minus two",
        "This is a deliberately silly name!",
    }
