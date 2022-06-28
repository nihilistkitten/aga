# Command-Line Interface

The command-line interface allows checking (via test cases with provided
`aga_output`) the validity of golden solutions, as well as generating the
autograder file from a problem.

## Problem Discovery

`aga` looks for a python object with the same name as the problem you pass it in
any python file in the directory where aga is invoked. If multiple such objects
are found, an error will be raised. A more nuanced (type-sensitive,
directory-recursive) discovery algotirhm is on the roadmap, but has not yet been
implemented.

```{eval-rst} .. click:: aga.cli:click_object :prog: aga :nested: full ```
