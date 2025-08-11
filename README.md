# DutchSoils - get Dutch soil data

![PyPI - Version](https://img.shields.io/pypi/v/dutchsoils)

DutchSoils is a Python package to get soil data from the Dutch Soil Map, Staring series and BOFEK clustering.

It contains code to get soil texture data from the [Dutch Soil Map](https://www.wur.nl/nl/show/bodemkaart-van-nederland.htm) and combine that with the [BOFEK soil clustering](https://www.wur.nl/nl/show/Bodemfysische-Eenhedenkaart-BOFEK2020.htm) and the hydraulic parameters from the [Staring series](https://research.wur.nl/en/publications/waterretentie-en-doorlatendheidskarakteristieken-van-boven-en-ond-5).

> [!Note]
> The data and soil profiles in this package are not actual measurements but are **derived** from field measurements. It is assumed that the soil profile and associated data are typical for the soil at a certain location.

## Installation

The easiest way to install the package is through `pip`:

```shell
pip install dutchsoils
```

## Get started

Getting a soil profile with the soil identification number and plotting the necessary parameters:

```
import dutchsoils as ds
sp = ds.SoilProfile.from_location(x=171827, y=445436)
sp.plot()
```

A brief example with other options is given in `docs/examples`.

## Directions

- Questions, issues, feature requests and bugs can be reported in the [issue section](https://github.com/markvdbrink/dutchsoils/issues).

## Sources

- Heinen, M., Brouwer, F., Teuling, K., & Walvoort, D. (2021). BOFEK2020 - Bodemfysische schematisatie van Nederland: Update bodemfysische eenhedenkaart. Wageningen Environmental Research. https://doi.org/10.18174/541544
- Heinen, M., Bakker, G., & Wösten, J. H. M. (2020). Waterretentie- en doorlatendheidskarakteristieken van boven- en ondergronden in Nederland: De Staringreeks : Update 2018 [page 17]. Wageningen Environmental Research. https://doi.org/10.18174/512761
