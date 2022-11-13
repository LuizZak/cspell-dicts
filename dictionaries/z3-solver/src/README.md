# Z3 Solver API names dictionary generator

Running `python clone-and-gen.py` clones the remote [Z3 Solver] repository and generates a new `z3-solver.txt` in the current working directory containing all unique words found in a [Z3 Solver] installation, cloning from the github repo https://github.com/Z3Prover/z3, sorted alphabetically.

The process works by inspecting a compiler-generated C file that `#include`'s public api/z3.h header file and extracting its public declarations.

The tool also manually inspects all public Z3 header files to extract `#define` declarations that where replaced away by the above step.

```
> python clone-and-gen.py
```

# Requirements

## 1. Python and [pycparser](https://github.com/eliben/pycparser)

---

This generator requires Python 3.10.0 and makes use of the [pycparser](https://github.com/eliben/pycparser) library to parse C headers, which is available on [pip](https://pypi.org/project/pip/):

```
> pip install pycparser
```

[Z3 Solver]: https://github.com/Z3Prover/z3
