# DutchSoils - get Dutch soil data

[![PyPI - Version](https://img.shields.io/pypi/v/dutchsoils)](https://pypi.org/project/dutchsoils/)
[![PyPi - Supported Python Versions](https://img.shields.io/pypi/pyversions/dutchsoils)](https://pypi.org/project/dutchsoils/)
[![Code size](https://img.shields.io/github/languages/code-size/markvdbrink/dutchsoils)](https://pypi.org/project/dutchsoils/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

DutchSoils is a Python package to get soil data from the Dutch Soil Map, Staring series and BOFEK clustering.

It contains code to get soil physical, textural, chemical data from the [Dutch Soil Map](https://www.wur.nl/nl/show/bodemkaart-van-nederland.htm) and combine that with the [BOFEK soil clustering](https://www.wur.nl/nl/show/Bodemfysische-Eenhedenkaart-BOFEK2020.htm) and the hydraulic parameters from the [Staring series](https://research.wur.nl/en/publications/waterretentie-en-doorlatendheidskarakteristieken-van-boven-en-ond-5).

> [!Note]
> The data and soil profiles in this package are not actual measurements but are **derived** from field measurements. It is assumed that the soil profile and associated data are typical for the soil at a certain location.

> [!Note]
> The method `from_location()` uses the API of [soilphysics.wur.nl](https://soilphysics.wur.nl) to get the soil profile at a location. This website uses the outdated soil map from 1999. Please check https://bodemdata.nl/documentatie if your location is within an area which was updated in the last 25 years. If so, please do not use this method.

## Get started

The easiest way to install the package is through `pip`:

```shell
pip install dutchsoils
```

Getting a soil profile with geographical coordinates and plotting its most common parameters:

```
import dutchsoils as ds
sp = ds.SoilProfile.from_location(x=171827, y=445436, crs="EPSG:28992")
sp.plot()
```

Other examples are given in the [documentation](https://dutchsoils.readthedocs.io/en/latest/).

## Questions, issues & contributions

Feel free to get in touch:

- Questions can be posted in the [Q&A discussion section](https://github.com/markvdbrink/dutchsoils/discussions/categories/q-a).
- Bugs and feature requests can be reported in the [issue section](https://github.com/markvdbrink/dutchsoils/issues).
- Contributions are welcome! Please have a look at the [contributing page](https://dutchsoils.readthedocs.io/en/latest/contribute.html).

## Many thanks to
- The developers of [Wageningen Environmental Research](https://soilphysics.wur.nl) for publishing and maintaining the Dutch soil map and providing an API to get the soil profile at a certain location.
- The people behind [pyOpenSci](https://www.pyopensci.org/python-package-guide/index.html), who provided an elaborate step-by-step tutorial on how to publish a Python package.
- The developers of (among others) [pyswap](https://github.com/zawadzkim/pySWAP), [pedon](https://github.com/martinvonk/pedon), and [Artesia Water](https://github.com/ArtesiaWater), whose Python packages were a source of inspiration.

## Sources

- Wageningen Environmental Research (2024). Bodemkaart van Nederland V2024-01. https://www.broloket.nl/ondergrondmodellen; downloaded on 07-08-2025.
- Heinen, M., Brouwer, F., Teuling, K., & Walvoort, D. (2021). BOFEK2020 - Bodemfysische schematisatie van Nederland: Update bodemfysische eenhedenkaart. Wageningen Environmental Research. https://doi.org/10.18174/541544
- Heinen, M., Bakker, G., & Wösten, J. H. M. (2020). Waterretentie- en doorlatendheidskarakteristieken van boven- en ondergronden in Nederland: De Staringreeks : Update 2018 [page 17]. Wageningen Environmental Research. https://doi.org/10.18174/512761
