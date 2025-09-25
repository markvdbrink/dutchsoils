# DutchSoils - get Dutch soil data

[![PyPI - Version](https://img.shields.io/pypi/v/dutchsoils)](https://pypi.org/project/dutchsoils/)
[![PyPi - Supported Python Versions](https://img.shields.io/pypi/pyversions/dutchsoils)](https://pypi.org/project/dutchsoils/)
[![Code size](https://img.shields.io/github/languages/code-size/markvdbrink/dutchsoils)](https://pypi.org/project/dutchsoils/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/pypi/l/dutchsoils)](https://pypi.org/project/pedon/)

DutchSoils is a Python package to get soil data from the Dutch Soil Map, Staring series and BOFEK clustering.

It contains code to get soil physical, textural, chemical data from the [Dutch Soil Map](https://www.wur.nl/nl/show/bodemkaart-van-nederland.htm) and combine that with the [BOFEK soil clustering](https://www.wur.nl/nl/show/Bodemfysische-Eenhedenkaart-BOFEK2020.htm) and the hydraulic parameters from the [Staring series](https://research.wur.nl/en/publications/waterretentie-en-doorlatendheidskarakteristieken-van-boven-en-ond-5).

> [!Note]
> The data and soil profiles in this package are not actual measurements but are **derived** from field measurements. It is assumed that the soil profile and associated data are typical for the soil at a certain location.

## Installation

The easiest way to install the package is through `pip`:

```shell
pip install dutchsoils
```

## Get started

Getting a soil profile with geographical coordinates, getting the data of its horizons and plotting the common parameters:

```
import dutchsoils as ds
sp = ds.SoilProfile.from_location(x=171827, y=445436, crs="EPSG:28992")
sp.get_data_horizons()
sp.plot()
```

An example with other available options is given in `docs/examples`.

## Feedback

Feedback is always welcome!

Questions, issues, feature requests and bugs can be reported in the [issue section](https://github.com/markvdbrink/dutchsoils/issues).

## Many thanks to
- The people behind [pyOpenSci](https://www.pyopensci.org/python-package-guide/index.html), who provided an elaborate step-by-step tutorial on how to publish a Python package.
- The developers of (among others) [pyswap](https://github.com/zawadzkim/pySWAP), [pedon](https://github.com/martinvonk/pedon), and [Artesia Water](https://github.com/ArtesiaWater), whose Python packages were a source of inspiration.

## Sources

- Wageningen Environmental Research (2024). Bodemkaart van Nederland V2024-01. https://www.broloket.nl/ondergrondmodellen; downloaded on 07-08-2025.
- Heinen, M., Brouwer, F., Teuling, K., & Walvoort, D. (2021). BOFEK2020 - Bodemfysische schematisatie van Nederland: Update bodemfysische eenhedenkaart. Wageningen Environmental Research. https://doi.org/10.18174/541544
- Heinen, M., Bakker, G., & Wösten, J. H. M. (2020). Waterretentie- en doorlatendheidskarakteristieken van boven- en ondergronden in Nederland: De Staringreeks : Update 2018 [page 17]. Wageningen Environmental Research. https://doi.org/10.18174/512761
