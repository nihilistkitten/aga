"""Compute a problem's value.

1. setting a relative weight for a test case and computing its absolute value relative
to the assignment (so, if one test case had weight 1 and 2 had weight 2, their values
would be 4 and 8 respectively).

2. setting an absolute value for a test case; the sum of all such values would have to
be less than the total value of the submission, and each such value would be subtracted
from the total value before relative problems are assigned values. So, if one test case
had weight 1, another weight 2, and another absolute value 8, the first would have value
4 and the next value 8.

3. grouping problems and assigning their weight relatively (i.e., have some set of
problems called "easy" that are worth one point, "hard" worth two points, or some
similar mechanism)

4. having extra credit assignments that don't count against the total value of the
assignment.

it could be that having some hidden cases succeed is enough to give you 8o%, just not
1oo%

--

Idea:

 * have a notion of a group, which takes all test cases underneath it
 * two layers of weight generation:
    - first groups are weighted against each other, with "ungrouped" treated as another
      group
    -
"""

# # from .core import Output, Problem
# from typing import Optional


# class Weight:
#     """A problem's weight configuration."""

#     relative: int = 1
#     absolute: int = 0
#     extra_credit: bool = False
#     threshold: Optional[int] = None  # if set,
