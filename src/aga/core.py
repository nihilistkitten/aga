"""The core library functionality."""

from typing import Any, Callable, Generic, Optional, TypeVar
from unittest import TestCase, TestSuite

Output = TypeVar("Output")


class _AutograderTestCase(TestCase):
    """A `TestCase` which runs a single test of a `Problem`."""

    def __init__(
        self,
        test_input: "_TestInputs",
        golden: Callable[..., Output],
        under_test: Callable[..., Output],
    ) -> None:
        super().__init__()
        self._test_input = test_input
        self._golden = golden
        self._under_test = under_test

    # pylint: disable=invalid-name
    # this name is required by unittest
    def runTest(self):
        """Run the test case."""
        self._test_input.check(self._golden, self._under_test)


class _TestInputs(TestCase):
    """A single set of test inputs for a problem.

    These will be run against the golden solution and the function under test; their
    outputs will be compared, and a unittest failure raised if they differ.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self._args: tuple = args
        self._kwargs: dict = kwargs

    def _eval(self, func: Callable[..., Output]) -> Output:
        """Evaluate func on the arguments."""
        return func(*self._args, **self._kwargs)

    def check(
        self, golden: Callable[..., Output], under_test: Callable[..., Output]
    ) -> None:
        """Assert that `golden` and `under_test` give the same output.

        This method relies on `TestCase.assertEqual`, which will raise a unittest error
        if they differ. This means it can be plugged into any unittest TestCase as a
        helper method.
        """
        self.assertEqual(self._eval(golden), self._eval(under_test))

    def generate_test_case(
        self, golden: Callable[..., Output], under_test: Callable[..., Output]
    ) -> _AutograderTestCase:
        """Generate a TestCase which tests `golden` against `under_test`."""
        return _AutograderTestCase(self, golden, under_test)


class _GoldenTestInputs(_TestInputs, TestCase):
    """A set of test inputs which also contains an expected output.

    This will be treated as a `TestInput` when the autograder is built, but provides
    additional methods to verify a golden solution against the expected output, for
    testing the accuracy of the golden solution against known outputs.
    """

    def __init__(self, output: Output, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._output = output

    def check_one(self, under_test: Callable[..., Output]) -> None:
        """Assert that `under_test`'s output matches the golden output."""
        self.assertEqual(self._eval(under_test), self._output)


class Problem(Generic[Output]):
    """Stores tests for a single problem.

    The problem has a notion of a "golden solution", which is the guaranteed-correct
    implementation that the test cases rely on. It also provides facilities for testing
    that solution, via golden test cases, constructed by passing the `output` argument
    to the `test_case` decorator.
    """

    def __init__(self, golden: Callable[..., Output]) -> None:
        self._golden: Callable[..., Output] = golden
        self._test_cases: list[_TestInputs] = []
        self._golden_test_cases: list[_GoldenTestInputs] = []

    def add_test_case(self, case: _TestInputs) -> None:
        """Add a test case to the problem.

        Student solutions will be checked against the golden solution; i.e., this method
        does _not_ produce a test of the golden solution.
        """
        self._test_cases.append(case)

    def add_golden_test_case(self, case: _GoldenTestInputs) -> None:
        """Add a golden test case to the problem.

        Student solutions will be checked against the golden solution, and both against
        the output pasted to the GoldenTestInputs constructor; i.e., this method _does_
        produce a test of the golden solution.
        """
        self._golden_test_cases.append(case)

    def run_golden_tests(self) -> None:
        """Run all tests of the golden solution."""
        for case in self._golden_test_cases:
            case.check_one(self._golden)

    def generate_test_suite(self, under_test: Callable[..., Output]) -> TestSuite:
        """Generate a `TestSuite` for the student submitted function."""
        suite = TestSuite([])

        for case in self._test_cases:
            suite.addTest(case.generate_test_case(self._golden, under_test))

        for case in self._golden_test_cases:
            suite.addTest(case.generate_test_case(self._golden, under_test))

        return suite


def problem(func: Callable[..., Output]) -> Problem[Output]:
    """Declare a function as the golden solution to a problem.

    This method should decorate a function which is known to produce the correct
    outputs, which we refer to as the "golden solution". A number of decorators are
    available for both pre- and post-processing of the golden solution and the `Problem`
    created by this decorator.
    """
    return Problem(func)


def test_case(
    *args, output: Optional[Any] = None, **kwargs
) -> Callable[[Problem[Output]], Problem[Output]]:
    """Declare a specific test case for some problem.

    If `output` is None, the inputs will be tested against the wrapped function, the
    "golden solution" to the problem. If `output` is specified, the inputs will double
    as a test _of_ the golden solution; to successfully produce the problem grader, the
    golden solution must return output from the given input.

    The autograder assumes all golden solutions are correct. A golden test case,
    declared by setting `output`, will _not_ be tested in the autograder itself;
    instead, it should be used for unit testing the golden solution in the dev
    environment. The `Problem` class provides a `run_golden_tests` method which asserts
    that the golden solution returns the correct output for each test case with a
    provided output.
    """

    def outer(prob: Problem[Output]) -> Problem[Output]:
        if output is not None:
            prob.add_golden_test_case(_GoldenTestInputs(output, *args, *kwargs))
            return prob

        else:
            prob.add_test_case(_TestInputs(*args, **kwargs))
            return prob

    return outer