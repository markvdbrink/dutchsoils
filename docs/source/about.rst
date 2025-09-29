About
=====

DutchSoils aims to make the Dutch soil data more easily accessible for Python users.

This is done by storing the properties of each soil profile, downloaded via `bodemdata.nl <https://bodemdata.nl/basiskaarten>`_ inside this package. Some logic is written around it to access and plot its contents.
Additionally, this data is combined with the `BOFEK soil clustering <https://www.wur.nl/nl/show/Bodemfysische-Eenhedenkaart-BOFEK2020.htm>`_ and the hydraulic parameters from the `Staring series <https://research.wur.nl/en/publications/waterretentie-en-doorlatendheidskarakteristieken-van-boven-en-ond-5>`_
Accessing a soil profile by geographical coordinates is done via the `soilphysics.wur.nl <https://soilphysics.wur.nl>`_ API, which currently uses an outdated soil map.
