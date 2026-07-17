# Career Studio V2 Core TDD Report

**Branch:** `career-studio-v2-core`  
**Worktree:** `/home/gopal/Professional_Grade_RAG/.worktrees/career-studio-v2`  
**Plan commit:** `cdcb3dd docs: plan career studio v2 core`

## Baseline

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/platform -q
```

Observed:

```text
....................                                                     [100%]
20 passed in 0.44s
```

## TDD Cycles

### Cycle 1 RED — immutable claims and typed requirements

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_claims_requirements.py -q
```

Observed expected failure:

```text
E   ModuleNotFoundError: No module named 'app.studios'
1 error in 0.39s
```

The test suite could not collect because the new Career Studio domain package had not been implemented.

### Cycle 1 GREEN — immutable claims and typed requirements

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_claims_requirements.py -q
```

Observed:

```text
...........                                                              [100%]
11 passed in 0.64s
```

### Cycle 2 RED — bounded scoring and one-to-one matching

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_matching.py -q
```

Observed expected failure:

```text
E   ImportError: cannot import name 'CoverageBand' from 'app.studios.career.domain'
1 error in 0.99s
```

The test suite could not collect because score, match, and calibrated coverage contracts had not been implemented.

### Cycle 2 GREEN — bounded scoring and one-to-one matching

Command:

```bash
/home/gopal/.local/bin/uv run --isolated --with pytest --with pydantic==2.11.5 --with scipy python -m pytest tests/studios/career/test_matching.py -q -rA
```

Observed:

```text
............                                                             [100%]
12 passed in 29.38s
```

The passing cases include bounded component validation, preserved score breakdowns, no claim double-counting, deterministic tie behavior across input order, weighted coverage ranges, truthful unmatched requirements, inferred-evidence rejection, and edge integrity checks.
