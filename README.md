# Stellar Distance from Gaia Parallax

Compute distances to nearby stars using parallax measurements from the
[Gaia DR3](https://www.cosmos.esa.int/web/gaia/dr3) catalog.

**Input**: Gaia source IDs and parallax (milliarcseconds), fetched via TAP query.
**Output**: Source IDs and computed distances (parsecs).
**Method**: `distance_pc = 1000 / parallax_mas`

## Reproduce

    make

## Verify

    make test

## Requirements

- Python >= 3.10
- Dependencies declared in `pyproject.toml`; install with `pip install -r requirements.txt`
