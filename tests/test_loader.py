"""Tests for the `loader` module."""

from os.path import join as pathjoin
from pathlib import Path

import pytest
from dill import dump  # type: ignore

from aga.core import Problem
from aga.loader import (
    NoMatchingSymbol,
    SubmissionSyntaxError,
    TooManyMatchingSymbols,
    load_problem,
    load_symbol_from_dir,
    load_symbol_from_path,
)


def car_tester(Car: type) -> None:  # pylint: disable=invalid-name
    """Test an imported Car class."""
    car = Car()
    car.drive(50)
    assert car.distance() == 50


def test_load_symbol_from_path_square(source_square: str) -> None:
    """Test that load_symbol_from_path loads a function."""

    square = load_symbol_from_path(source_square, "square")
    assert square(5) == 25


def test_load_symbol_from_path_car(source_car: str) -> None:
    """Test that load_symbol_from_path loads a class."""
    Car = load_symbol_from_path(source_car, "Car")  # pylint: disable=invalid-name
    car_tester(Car)


def test_load_symbol_from_path_invalid_source_errors(source_invalid: str) -> None:
    """Test that load_symbol_from_path errors on invalid source."""

    with pytest.raises(SubmissionSyntaxError):
        load_symbol_from_path(source_invalid, "foo")


def test_load_symbol_from_path_no_file_errors(tmp_path: Path) -> None:
    """Test that load_symbol_from_path errors on nonexistent files."""
    with pytest.raises(FileNotFoundError):
        load_symbol_from_path(str(tmp_path.joinpath("src.py")), "foo")


def test_load_symbol_from_path_no_symbol_errors(source_square: str) -> None:
    """Test that load_symbol_from_path errors on nonexistent symbols."""
    with pytest.raises(NoMatchingSymbol):
        load_symbol_from_path(source_square, "foo")


def test_load_symbol_from_dir_function(source_dir: str) -> None:
    """Test that load_symbol_from_dir loads a function."""
    square = load_symbol_from_dir(source_dir, "square")
    assert square(5) == 25


def test_load_symbol_from_dir_class(source_dir: str) -> None:
    """Test that load_symbol_from_dir loads a class."""
    Car = load_symbol_from_dir(source_dir, "Car")  # pylint: disable=invalid-name
    car_tester(Car)


def test_load_symbol_from_dir_nonexistent_symbol_errors(source_dir: str) -> None:
    """Test that load_symbol_from_dir errors on nonexistent symbols."""
    with pytest.raises(NoMatchingSymbol):
        load_symbol_from_dir(source_dir, "foo")


def test_load_symbol_from_dir_multiple_symble_errors(source_dir: str) -> None:
    """Test that load_symbol_from_dir errors on nonexistent symbols."""
    with pytest.raises(TooManyMatchingSymbols):
        load_symbol_from_dir(source_dir, "duplicate")


def test_load_problem(tmp_path: str, square: Problem[int]) -> None:
    """Test that load_problem loads square correctly."""

    path = pathjoin(tmp_path, "problem.pckl")
    with open(path, "wb") as file:
        dump(square, file)

    square_loaded: Problem[int] = load_problem(tmp_path, "problem.pckl")
    square_loaded.check()  # pylint: disable=no-member
