# Saved Gaia DR3 uncertainty data

`gaia_uncertainties.csv` was retrieved on 2026-10-28 from the ESA Gaia TAP service using `extension/fetch_uncertainties.py`, for the exact source IDs in the pinned `gaia/raw/gaia_nearby.csv`.
It adds `parallax_error` and GSP-Phot distances with their lower (16%) and upper (84%) percentiles.
Blank GSP-Phot values are retained; no stars are silently removed.

The analysis checks both source IDs and the original parallaxes.
Refreshing this file is an explicit data update, not part of ordinary reproduction.
The source provenance file records its SHA-256 hash.

Source: https://gea.esac.esa.int/tap-server/tap/sync Field definitions: https://gaia.aip.de/metadata/gaiadr3/gaia_source/

This work uses data from the European Space Agency (ESA) mission Gaia, processed by the Gaia Data Processing and Analysis Consortium (DPAC).
