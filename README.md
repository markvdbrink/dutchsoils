# dutchsoils - download and combine dutch (hydrological) soil data

This repo contains code to download data of the Dutch soil map, BOFEK soil clustering and Staring series and combine these datasets.  

The code in this repo is somewhat 'quick and dirty'. The goal is to develop this code into a small package or contribute it to [nlmod](https://github.com/gwmod/nlmod/tree/dev), but I wanted to make it public already, because it is also referenced in [pyswap](https://github.com/zawadzkim/pySWAP).

## Steps
1. Download this repo as a zip file and either
    - copy it to your personal environment and make sure `pandas`, `geopandas` and `py7zr` are installed OR
    - install a new local environment using [poetry](https://python-poetry.org/) or [uv](https://docs.astral.sh/uv/).
2. Download the Dutch soil map from the [PDOK website](https://service.pdok.nl/bzk/bro-bodemkaart/atom/downloads/BRO_DownloadBodemkaart.gpkg) and put it in `data/raw/`.
3. Download the [BOFEK clustering](https://www.wur.nl/nl/show/bofek-2020-gis-1.htm) and put the zip-file in `data/raw/`.
4. Download the [scripts](https://www.wur.nl/nl/show/bofek2020_v1.0_scripts.zip.htm) used for the BOFEK clustering and put them in `data/raw/`.
5. The names of the Staring soil classes are shipped within this repo and are derived from Heinen et al. (2020).
6. Run `python process.py` in the terminal. The result is a CSV file in `data/processed`.

You can load this file and use pandas to filter a certain profile.  

As an example of what you can do with this database, a plot function is given in `plot.py`. It requires `matplotlib`, `numpy` and `pedon` to be installed. If that's the case, run `python plot.py` in the terminal.

## References
Heinen, M., Bakker, G., & Wösten, J. H. M. (2020). Waterretentie- en doorlatendheidskarakteristieken van boven- en ondergronden in Nederland: De Staringreeks : Update 2018 [page 17]. Wageningen Environmental Research. https://doi.org/10.18174/512761
