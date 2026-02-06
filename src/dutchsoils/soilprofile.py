from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from warnings import warn
from xml.etree import ElementTree

from numpy import array, concatenate, diff, ones, searchsorted
from pandas import (
    DataFrame,
    read_csv,
)
from requests import get as requests_get
from requests.exceptions import JSONDecodeError

from .plot import soilprofile as plot_soilprofile


@dataclass
class SoilProfile:
    """
    Represents a single Dutch soil profile, providing access to soil properties, horizons, and cluster information
    based on various identifiers (index, code, or BOFEK2020 cluster). This class supports profile lookup by index,
    code, cluster, or geographic location, and provides methods for retrieving soil horizon data, area statistics,
    and input dictionaries for pySWAP modeling. Data is loaded from CSV files located in the package's data directory.

    Attributes
    ----------
    index : int or None
        Soil profile index.
    code : int or None
        Soil profile code.
    name : str
        Name of the soil profile.
    bofekcluster : int or None
        BOFEK2020 cluster number.
    bofekcluster_name : str
        Name of the BOFEK cluster.
    bofekcluster_dominant : bool or None
        Whether the profile is dominant in its cluster.

    Examples
    --------
    >>> sp = SoilProfile(index=101)
    >>> sp.get_data_horizons()
    >>> sp.get_area(which="profile")
    >>> sp.plot()
    """

    index: int | None = None
    code: int | None = None
    name: str = field(init=False)
    bofekcluster: int | None = None
    bofekcluster_name: str = field(init=False)
    bofekcluster_dominant: bool | None = None

    def __post_init__(self):
        """
        Validates input and sets attributes based on provided parameters.
        """
        # Check nr of inputs
        nr_inputs = sum(
            x is not None for x in (self.index, self.bofekcluster, self.code)
        )
        if nr_inputs != 1:
            raise ValueError(
                "Provide exactly one input: soilprofile index, code, or bofek cluster number."
            )

        # Get data
        bofekclusters = self._get_data_csv(csvfile="BofekClusters")
        soilprofiles = self._get_data_csv(csvfile="SoilProfiles")

        # If index is given as input
        if self.index is not None:
            self._init_from_index(
                soilprofiles=soilprofiles, bofekclusters=bofekclusters
            )
        # If soil unit code is given as input
        elif self.code is not None:
            self._init_from_code(bofekclusters=bofekclusters)
        # If bofekcluster is given as input (else conditions since nr of inputs is checked)
        else:
            self._init_from_bofekcluster(
                soilprofiles=soilprofiles, bofekclusters=bofekclusters
            )

        self._set_names(soilprofiles=soilprofiles)

    def _init_from_index(self, soilprofiles, bofekclusters):
        """Set attributes SoilProfile based on provided soil profile index.

        Parameters
        ----------
        soilprofiles: pandas.DataFrame
            DataFrame from data/SoilProfiles.csv
        bofekclusters: pandas.DataFrame
            DataFrame from data/BofekClusters.csv
        """
        # Check input
        self._validate_input("index", self.index)

        # Set soil code & bofek
        self._set_bofekcluster(bofekclusters=bofekclusters)
        self._set_code(soilprofiles=soilprofiles)

    def _init_from_code(self, bofekclusters):
        """Set attributes SoilProfile based on provided soil profile code.

        Parameters
        ----------
        bofekclusters: pandas.DataFrame
            DataFrame from data/BofekClusters.csv
        """

        # Check input
        self._validate_input("code", self.code)

        # Check nr indices
        indices = self._get_indices(code=self.code)

        # If only 1 index: find attributes
        if len(indices) == 1:
            # Set soil index & bofek
            self.index = indices[0]
            self._set_bofekcluster(bofekclusters=bofekclusters)

        # If multiple indices: raise error
        else:
            msg = (
                f"Given soil unit code {self.code} corresponds to multiple soils with indices "
                + f"{', '.join([str(ind) for ind in indices])}.\n"
                + "Specify the index to get one of them or use the method from_code() to get all."
            )
            raise ValueError(msg)

    def _init_from_bofekcluster(self, soilprofiles, bofekclusters):
        """Set attributes SoilProfile based on provided BOFEK cluster.

        Parameters
        ----------
        soilprofiles: pandas.DataFrame
            DataFrame from data/SoilProfiles.csv
        bofekclusters: pandas.DataFrame
            DataFrame from data/BofekClusters.csv
        """

        # Check input
        self._validate_input("bofekcluster", self.bofekcluster)

        # Check if cluster dominance is given
        if self.bofekcluster_dominant is None:
            msg = "Please specify the attribute bofekcluster_dominant."
            raise ValueError(msg)
        # If bofekcluster dominance True: find attributes
        elif self.bofekcluster_dominant:
            # Set soil index & code
            mask = (bofekclusters["cluster"].values == self.bofekcluster) & (
                bofekclusters["dominant"].values == 1
            )
            self.index = bofekclusters.loc[mask, "normalsoilprofile_id"].item()
            self._set_code(soilprofiles=soilprofiles)
        # If not: raise error
        else:
            msg = "To get all soilprofiles corresponding to this BOFEK cluster, use the method from_bofekcluster()."
            raise ValueError(msg)

    def _set_code(self, soilprofiles):
        """Sets attribute code based on provided soil profile index.

        Parameters
        ----------
        soilprofiles: pandas.DataFrame
            DataFrame from data/SoilProfiles.csv
        """

        # Set soil unit code
        self.code = soilprofiles.loc[
            soilprofiles["normalsoilprofile_id"] == self.index, "soilunit"
        ].values[0]

    def _set_bofekcluster(self, bofekclusters):
        """Set attributes bofekcluster, bofekcluster_dominant based on provided soil profile index.

        Parameters
        ----------
        bofekclusters: pandas.DataFrame
            DataFrame from data/BofekClusters.csv
        """

        # Set bofek cluster & dominance
        row = bofekclusters[bofekclusters["normalsoilprofile_id"] == self.index]
        self.bofekcluster = row["cluster"].iloc[0].item()
        self.bofekcluster_dominant = row["dominant"].iloc[0].astype(bool)

    def _set_names(self, soilprofiles):
        """Set attributes name and bofekcluster_name based on provided soil profile index.

        Parameters
        ----------
        soilprofiles: pandas.DataFrame
            DataFrame from data/SoilProfiles.csv
        """

        # Set name soil
        self.name = soilprofiles.loc[
            soilprofiles["normalsoilprofile_id"] == self.index, "othersoilname"
        ].values[0]

        # Set name bofek cluster
        bofeknames = self._get_data_csv(csvfile="BofekClustersNames")
        self.bofekcluster_name = bofeknames.loc[
            bofeknames["cluster"] == self.bofekcluster, "name"
        ].values[0]

    @staticmethod
    def _get_data_csv(
        csvfile: str,
        filter_profile: bool = False,
    ) -> DataFrame:
        """
        Loads a CSV file from the data directory as a pandas DataFrame.

        Parameters
        ----------
        csvfile : str
            Name of the CSV file (without extension).
        filter_profile : bool, optional
            If True, filters the DataFrame for the current profile index.

        Returns
        -------
        pandas.DataFrame
        """
        # Read data
        path = Path(__file__).parent / "data" / (csvfile + ".csv")
        data = read_csv(path, skiprows=10)

        return data

    @staticmethod
    def _validate_input(input_type, value):
        """
        Validates if given input for bofekcluster, code, or index exists in database.
        """

        if input_type == "bofekcluster":
            valid = (
                value in SoilProfile._get_data_csv("BofekClusters")["cluster"].values
            )
            msg = f"Given bofek cluster number '{value}' does not exist."
        elif input_type == "index":
            valid = (
                value
                in SoilProfile._get_data_csv("BofekClusters")[
                    "normalsoilprofile_id"
                ].values
            )
            msg = f"Given soilprofile index '{value}' does not exist."
        elif input_type == "code":
            valid = (
                value in SoilProfile._get_data_csv("SoilProfiles")["soilunit"].values
            )
            msg = f"Given soilprofile code '{value}' does not exist."
        else:
            valid = False
            msg = "Unknown input type."

        if not valid:
            raise ValueError(msg)
        else:
            return

    @staticmethod
    def _get_indices(
        cluster: int | Iterable | None = None,
        code: str | Iterable | None = None,
    ):
        """
        Retrieves indices of soil profiles based on cluster or soil unit code.

        Parameters
        ----------
        cluster : int or Iterable
            Cluster identifier(s) to filter the mapping. If provided, indices are selected based on cluster.
        code : str or Iterable
            Soil unit code(s) to filter the mapping. Used if `cluster` is None.

        Returns
        -------
        numpy.ndarray
            Array of indices corresponding to the selected cluster(s) or soil unit code(s).
        """

        # Check if given input exists for both bofekcluster and soil unit code
        variable = "bofekcluster" if cluster is not None else "code"
        input = cluster if cluster is not None else code
        values = (
            input if SoilProfile._is_iterable(input) else [input]
        )  # Make iterable if not already
        for val in values:
            SoilProfile._validate_input(variable, val)

        # Set data csv file and column name for given input
        name_csv = "BofekClusters" if cluster is not None else "SoilProfiles"
        data = SoilProfile._get_data_csv(name_csv)
        col = "cluster" if cluster is not None else "soilunit"

        # Get indices belonging to this variable
        indices_all = []
        for val in values:
            indices = list(data.loc[data[col] == val, "normalsoilprofile_id"])
            indices_all += indices

        return indices_all

    @staticmethod
    def _is_iterable(obj):
        """
        Checks if object is iterable and not a string.

        Parameters
        ----------
        obj : any
            Object to check.

        Returns
        -------
        bool
        """
        return isinstance(obj, Iterable) and not isinstance(obj, str) and len(obj) > 0

    @classmethod
    def _from_userinput(cls, input, input_type: str, **kwargs):
        """
        Creates one or more SoilProfile instances from user input.

        Parameters
        ----------
        input : int, str, or iterable
            Input value(s) for profile selection.
        input_type : str
            Type of input ('index', 'code', or 'bofekcluster').

        Returns
        -------
        SoilProfile or list of SoilProfile
        """

        # Return a list of Soilprofiles if input is an iterable
        if cls._is_iterable(input):
            return [cls(**{input_type: ii}, **kwargs) for ii in input]
        # Else return a SoilProfile instance
        else:
            return cls(**{input_type: input}, **kwargs)

    @classmethod
    def from_index(
        cls,
        index: int | Iterable,
    ) -> "SoilProfile" | list["SoilProfile"]:
        """
        Create SoilProfile(s) from a soil profile index.

        You can provide either a single soil profile index to get a single SoilProfile or an iterable of indices to obtain multiple SoilProfiles in a list.

        Parameters
        ----------
        index : int or iterable of int
            Soil profile index(es). If an iterable of int is given, a list of SoilProfiles will be returned.

        Returns
        -------
        SoilProfile or list of SoilProfile
        """
        return cls._from_userinput(input=index, input_type="index")

    @classmethod
    def from_bofekcluster(
        cls,
        cluster: int | Iterable,
        dominant: bool = True,
    ) -> "SoilProfile" | list["SoilProfile"]:
        """
        Create SoilProfile(s) from a BOFEK cluster number.

        You can provide either a single BOFEK cluster number or an iterable of cluster numbers.
        Either only the dominant soil profile (default) or all profiles belonging to a cluster can be returned.

        Parameters
        ----------
        cluster : int or iterable of int
            BOFEK cluster number(s). If an iterable of int is given, a list of SoilProfiles will be returned.
        dominant: bool
            Whether to return the dominant (default) or all soil profiles belonging to a BOFEK cluster.

        Returns
        -------
        SoilProfile or list of SoilProfile
        """

        if dominant:
            # Only one SoilProfile per cluster will be returned, checks are done in __post_init
            return cls._from_userinput(
                input=cluster, input_type="bofekcluster", bofekcluster_dominant=True
            )
        else:
            # Multiple SoilProfiles per cluster will be returned using from_index
            # Get indices of all soilprofiles belonging to this BOFEK cluster
            indices = cls._get_indices(cluster=cluster)

            return cls._from_userinput(input=indices, input_type="index")

    @classmethod
    def from_code(
        cls,
        code: str | Iterable,
    ):
        """
        Create SoilProfile(s) from a soil profile code.

        You can provide either a single soil profile code or an iterable of codes.
        When multiple soil profiles have the same soil code, all of these are returned.

        Parameters
        ----------
        code : str or iterable of str
            Soil profile code(s). If an iterable of str is given, a list of SoilProfiles will be returned.

        Returns
        -------
        SoilProfile or list of SoilProfile
        """
        # Check if multiple soil profiles have the same soil code
        indices = cls._get_indices(code=code)
        # Make sure a SoilProfile object is returned if only one index corresponds with soil unit code
        indices = indices[0] if len(indices) == 1 else indices

        return cls._from_userinput(indices, "index")

    @classmethod
    def from_location(
        cls,
        x: float | list | None,
        y: float | list | None,
        crs: str = "EPSG:28992",
    ) -> "SoilProfile" | list["SoilProfile"]:
        """
        Create SoilProfile(s) from geographic coordinates using the WMS of PDOK (https://www.pdok.nl/ogc-webservices/-/article/bro-bodemkaart-sgm-).

        You can provide either a single pair of coordinates (x, y), or two iterables of coordinates (x and y) of equal length to obtain multiple SoilProfiles.

        Parameters
        ----------
        x : float or list of float
            X coordinate(s) (longitude or easting). If a list or array is given, it must have the same length as `y`.
        y : float or list of float
            Y coordinate(s) (latitude or northing). If a list or array is given, it must have the same length as `x`.
        crs : str, optional
            Coordinate reference system, choose from: `["EPSG:28992", "EPSG:25831", "EPSG:25832", "EPSG:3034", "EPSG:3035",
            "EPSG:3857", "EPSG:4258", "EPSG:4326", "CRS:84"]` (default: "EPSG:28992" (Amersfoort / RD New)).

        Returns
        -------
        SoilProfile or list of SoilProfile

        """

        # Check if x and y have the same length and right data type
        cls._check_input_location(x, y)

        # Convert to list if scalar
        is_scalar = not (cls._is_iterable(x) and cls._is_iterable(y))
        xl = [x] if is_scalar else x
        yl = [y] if is_scalar else y

        # Request soil profile codes from PDOK WMS
        result = []
        for xx, yy in zip(xl, yl):
            # Request code using coordinates
            mapid = cls._request_mapid(xx, yy, crs)

            # Initialise SoilProfile if code is not None
            if mapid is not None:
                sp = cls._from_mapid(mapid)
                result.append(sp)
            else:
                # Give warning and return None
                warn(
                    f"No soil information available for this location: x = {xx}, y = {yy}.",
                    stacklevel=2,
                )
                result.append(None)

        return result[0] if is_scalar else result

    @classmethod
    def _check_input_location(cls, x, y):
        """
        Validates location input for profile lookup.

        Parameters
        ----------
        x : float or iterable
            X coordinate(s).
        y : float or iterable
            Y coordinate(s).

        Raises
        ------
        ValueError
            If input is invalid.
        """

        # Check if x and y are both iterables or both scalars
        if cls._is_iterable(x):
            if not cls._is_iterable(y):
                raise ValueError("X is iterable while Y is not.")
            if len(x) != len(y):
                raise ValueError(
                    f"List of X and Y coordinates do not have the same length (x: {len(x)}, y: {len(y)})."
                )
            for i, xx in enumerate(x):
                if not isinstance(xx, (float, int)):
                    raise ValueError(
                        f"The {i}th element of the X-coordinates is neither a float or int."
                    )
            for j, yy in enumerate(y):
                if not isinstance(yy, (float, int)):
                    raise ValueError(
                        f"The {j}th element of the Y-coordinates is neither a float or int."
                    )
        else:
            if cls._is_iterable(y):
                raise ValueError("Y is iterable while X is not.")
            if not isinstance(x, (float, int)):
                raise ValueError(f"The X-coordinate '{x}' is neither a float or int.")
            if not isinstance(y, (float, int)):
                raise ValueError(f"The Y-coordinate '{y}' is neither a float or int.")

        return

    @classmethod
    def _request_mapid(cls, xx, yy, crs):
        """
        Requests mapid of feature at given location from PDOK WMS 1.3.0 API for given coordinates.

        Parameters
        ----------
        xx : float
            X-coordinate.
        yy : float
            Y-coordinate.
        crs : str
            Coordinate reference system in format "EPSG:xxx".

        Returns
        -------
        str or None
            Map id of feature of the Dutch Soil Map, or None if not available.
        """

        # Send request for soil data to PDOK WMS
        # The bounding box extents from the requested location 1 meter north and east
        # The image consists of 2x2 pixels
        # The pixel value of the lower left pixel is returned
        r = requests_get(
            url="https://service.pdok.nl/bzk/bro-bodemkaart/wms/v1_0",
            params={
                "request": "getFeatureInfo",
                "service": "WMS",
                "version": "1.3.0",
                "info_format": "json",
                "layers": "soilarea",
                "query_layers": "soilarea",
                "crs": crs,
                "bbox": f"{xx},{yy},{xx + 1e-5},{yy + 1e-5}",
                "width": 2,
                "height": 2,
                "i": 0,
                "j": 2,
            },
        )
        # Raise error for a HTTP error
        # This is not inside a try-except loop because the error should be displayed to the user
        r.raise_for_status()

        # Get soil profile mapid
        # Valid request
        try:
            data = r.json()["features"]

            # Check if a soil profile is available for this location
            if len(data) == 0:
                # Return None if not available
                return
            else:
                # Return mapid if available
                return data[0]["properties"]["maparea_id"]

        # Invalid request
        except JSONDecodeError:
            # Parse XML file using namespace
            root = ElementTree.fromstring(r.text)
            ns = {"ogc": "http://www.opengis.net/ogc"}
            exception = root.find("ogc:ServiceException", ns)

            if "Unsupported CRS namespace" in exception.text:
                m = f"Unsupported CRS: {crs}. Please use format 'EPSG:XXX'."
                raise ValueError(m)
            else:
                raise ValueError(exception.text)

    @classmethod
    def _from_mapid(cls, mapid):
        """
        Create a SoilProfile instance from a given map area ID.
        This class method retrieves the corresponding soil profile index for the provided map area ID (`mapid`)
        by referencing a CSV file that maps area IDs to soil profile indices. It then constructs and returns
        a SoilProfile object using the retrieved index.

        Parameters
        ----------
        mapid : str
            The full map area ID from which the soil profile should be created.

        Returns
        -------
        SoilProfile
            An instance of the SoilProfile class corresponding to the provided map area ID.
        """
        # Load dataframe relating mapid to soilprofile index
        df = cls._get_data_csv(csvfile="SoilProfiles_MapAreaID")

        # Strip mapid from redudant information
        mapid_short = int(mapid[-5:])

        # Get soilprofile index from mapid_short
        index = (
            df.loc[df["maparea_id"] == mapid_short, "normalsoilprofile_id"]
            .values[0]
            .item()
        )

        # Make SoilProfile object
        return cls.from_index(index=index)

    def get_area(self, which: str = "profile") -> float:
        """
        Returns the total area (ha) in the Netherlands of this profile or the total BOFEK2020 cluster it belongs to.

        Parameters
        ----------
        which : str, optional
            Which area to return. Options:
                * "profile": Area of this profile.
                * "bofekcluster": Total area of the BOFEK cluster.

        Returns
        -------
        float

        Raises
        ------
        ValueError
            If 'which' is not a valid option.
        """

        # Get data
        data = self._get_data_csv("BofekClusters")
        # Return area of this profile
        if which == "profile":
            return data.loc[data["normalsoilprofile_id"] == self.index, "area"].iloc[0]
        # Return total area of the bofek cluster
        elif which == "bofekcluster":
            return data.loc[data["cluster"] == self.bofekcluster, "area"].sum()
        # Return ValueError
        else:
            raise ValueError(
                f"Value '{which}' for variable 'which' is invalid. Please use 'profile' or 'bofekcluster'."
            )

    def get_data_horizons(
        self,
        which: str = "all",
    ) -> DataFrame:
        """
        Returns a DataFrame with soil horizon data for this profile.

        Parameters
        ----------
        which : str, optional
            Which data to return (default: "all"). Options:
                * "all": Combination of hydraulic, physical, and chemical data.
                * "hydraulic": Staring series data.
                * "physical": Mass fractions, sand median, density.
                * "chemical": Organic matter, calcite, iron oxide, acidity.

        Returns
        -------
        pandas.Dataframe
            Data for each soil horizon. The columns are (for further explanation see https://docs.geostandaarden.nl/bro/vv-im-SGM-20220328/):

            layernumber
                Horizon number, counting from top.
            faohorizonnotation
                Horizon type according to FAO classification (see https://www.fao.org/4/a0541e/a0541e.pdf, chapter 5)
            ztop
                Depth of top of the horizon (cm below surface).
            zbottom
                Depth of bottom of the horizon (cm below surface).
            staringseriesblock
                Name of staring series block.
            organicmattercontent
                Median organic matter content (mass-%).
            organicmattercontent10p
                The 10th percentile of the variation in organic matter content (mass-%).
            organicmattercontent90p
                The 90th percentile of the variation in organic matter content (mass-%).
            acidity
                Median acidity (pH).
            acidity10p
                The 10th percentile for the variation in acidity (pH).
            acidity90p
                The 90th percentile for the variation in acidity (pH).
            cnratio
                Ratio between carbon and nitrogen in the organic matter.
            peattype
                Type of peat.
            calciccontent
                Median calcite (CaCO3) content (mass-%).
            fedith
                Median Fe2O3 content (mass-%).
            loamcontent
                Median value of the content of mineral particles with a grain size smaller than 50 µm (mass-%).
            loamcontent10p
                The 10th percentile for the variation in the content of mineral particles with a grain size smaller than 50 µm (mass-%).
            loamcontent90p
                The 90th percentile for the variation in the content of mineral particles with a grain size smaller than 50 µm (mass-%).
            lutitecontent
                Median value of the content of mineral particles with a grain size smaller than 2 µm (mass-%).
            lutitecontent10p
                The 10th percentile for the variation in the content of mineral particles with a grain size smaller than 2 µm (mass-%).
            lutitecontent90p
                The 90th percentile for the variation in the content of mineral particles with a grain size smaller than 2 µm (mass-%).
            sandmedian
                Median value of the sand fraction (µm).
            sandmedian10p
                The 10th percentile for the variation in sand median (µm).
            sandmedian90p
                The 10th percentile for the variation in sand median (µm).
            siltcontent
                Median value of the content of mineral particles with a grain size between 50 µm and 2 mm (mass-%).
            density
                Median value for density (g cm^-3).
            wcres
                Residual water content (cm^3 cm^-3).
            wcsat
                Saturated water content (cm^3 cm^-3)
            vgmalpha
                Van Genuchten-Mualem shape parameter (cm^-1).
            vgmnpar
                Van Genuchten-Mualem shape parameter (-).
            vgmlambda
                Van Genuchten-Mualem shape parameter (-).
            ksatfit
                Fitted hydraulic conductivity at saturation (cm d^-1)
        """
        # Get data horizons
        dataall = self._get_data_csv("SoilHorizons")

        # Filter profile
        mask = dataall["normalsoilprofile_id"] == self.index
        dataall = dataall.loc[mask].reset_index(drop=True)

        # Keep relevant columns
        column_names = [
            "normalsoilprofile_id",
            "layernumber",
            "faohorizonnotation",
            "ztop",
            "zbottom",
            "staringseriesblock",
            "organicmattercontent",
            "organicmattercontent10p",
            "organicmattercontent90p",
            "acidity",
            "acidity10p",
            "acidity90p",
            "cnratio",
            "peattype",
            "calciccontent",
            "fedith",
            "loamcontent",
            "loamcontent10p",
            "loamcontent90p",
            "lutitecontent",
            "lutitecontent10p",
            "lutitecontent90p",
            "sandmedian",
            "sandmedian10p",
            "sandmedian90p",
            "siltcontent",
            "density",
        ]

        # If only hydraulic data should be returned, keep only horizon depth parameters
        if which == "hydraulic":
            columns = column_names[1:6]
        # If only chemical data should be returned, keep only chemical parameters
        elif which == "chemical":
            columns = column_names[1:5] + column_names[6:16]
        # If only chemical data should be returned, keep only chemical parameters
        elif which == "physical":
            columns = column_names[1:5] + column_names[16:]
        # Keep all columns except the soilprofile_index
        elif which == "all":
            columns = column_names[1:]
        else:
            raise ValueError(
                f"Unvalid value for 'which': {which}. Choose between 'all', 'hydraulic', 'physical', 'chemical'."
            )

        # Filter columns
        datafil = dataall[columns]

        # Add hydraulic data if necessary
        if which == "hydraulic" or which == "all":
            # Merge with Staringreeks data
            # Get Staringreeks data
            staring = self._get_data_csv("Staringreeks2018")
            # Join on Staringreeks block
            datafil = datafil.merge(staring, on="staringseriesblock")

            # Merge with Staringreeks names
            # Get Staringreeks names
            staringnames = self._get_data_csv("StaringreeksNamen2018")
            # Join on Staringreeks block
            datafil = datafil.merge(staringnames, on="staringseriesblock")

            # Change Staringreeks block name: 1 -> B, 2 -> O
            datafil = datafil.astype({"staringseriesblock": str})
            datafil.loc[:, "staringseriesblock"] = [
                {"1": "B", "2": "O"}.get(str(name)[0]) + str(name)[-2:]
                for name in datafil["staringseriesblock"]
            ]

        return datafil

    def get_swapinput_profile(
        self,
        discretisation_depths: list,
        discretisation_compheights: list,
    ):
        """
        Returns a dictionary for the SOILPROFILE table in pySWAP.

        Parameters
        ----------
        discretisation_depths : list of int
            List of discretisation depths (cm). For example "[30, 70]" will result in two layers with a depth of 30 and 70 cm, respectively. The result is a soil profile of 100 cm depth.
        discretisation_compheights : list of int
            List of compartment heights (cm) for each depth. For example, "[1, 2]" will result in two layers with cell sizes of 1 and 2 cm, respectively.

        Returns
        -------
        dict
            Discretisation information for pySWAP.
        """

        # Get data
        data = self.get_data_horizons()

        # Check if the depth of each discretisation layer is a natural product of its compartment height
        check = array(
            [
                depth % hcomp
                for depth, hcomp in zip(
                    discretisation_depths, discretisation_compheights
                )
            ]
        )
        if any(check != 0):
            idx = check.nonzero()[0]
            m = (
                f"The given compartment depths {array(discretisation_depths)[idx]}"
                f" are not a natural product of the given compartment heights "
                f"{array(discretisation_compheights)[idx]}."
            )
            raise ValueError(m)

        # Define the height for each compartment
        comps_h = concatenate(
            [
                ones(int(hsublay / hcomp)) * hcomp
                for hsublay, hcomp in zip(
                    discretisation_depths, discretisation_compheights
                )
            ]
        )

        # Define the bottom z for each compartment
        comps_zb = comps_h.cumsum().astype(int)

        # Get bottom of the soil physical layers
        soillay_zb = (array(data["zbottom"]) * 100).astype(int)  # convert from m to cm

        # Intersect with the bottom of the soil physical layers
        comps_zb = array(sorted(set(soillay_zb).union(set(comps_zb))))

        # Remove values deeper than given depth (sum of discretisation keys)
        comps_zb = comps_zb[comps_zb <= sum(discretisation_depths)]

        # Redefine height compartments
        comps_h = concatenate([[comps_zb[0]], diff(comps_zb)])

        # Define corresponding soil layer for each sublayer
        comps_soillay = searchsorted(soillay_zb, comps_zb, side="left") + 1
        # Deeper sublayers than the BOFEK profile get same properties as the deepest soil physical layer
        comps_soillay[comps_soillay > len(soillay_zb)] = len(soillay_zb)

        # Convert to dataframe
        result = DataFrame(
            {
                "ISOILLAY": comps_soillay,
                "HCOMP": comps_h,
                "HSUBLAY": comps_h,
            }
        )

        # Group layers if they have the same soil physical layer and compartment height
        result = result.groupby(["ISOILLAY", "HCOMP"], as_index=False).sum()

        # Calculate remaining parameters
        result["ISUBLAY"] = result.index.values + 1
        result["NCOMP"] = (result["HSUBLAY"].values / result["HCOMP"].values).astype(
            int
        )

        # Rearrange columns
        result = result[["ISUBLAY", "ISOILLAY", "HSUBLAY", "HCOMP", "NCOMP"]]

        # Convert to dictionary
        result = result.to_dict("list")

        return result

    def get_swapinput_hydraulicparams(
        self,
        ksatexm: list | None = None,
        h_enpr: list | None = None,
    ) -> dict:
        """
        Returns a dictionary for the SOILHYDRFUNC table in pySWAP.

        Parameters
        ----------
        ksatexm : list, optional
            Measured saturated hydraulic conductivities (cm/d).
        h_enpr : list, optional
            Measured air entry pressure head (cm).

        Returns
        -------
        dict
            Hydraulic parameters for pySWAP.
        """

        # Get data
        data = self.get_data_horizons(which="all")

        # Define a dictionary
        result = {}

        # Add given information or data from the database
        result.update(
            {
                "ORES": data["wcres"].values,
                "OSAT": data["wcsat"].values,
                "ALFA": data["vgmalpha"].values,
                "NPAR": data["vgmnpar"].values,
                "KSATFIT": data["ksatfit"].values,
                "LEXP": data["vgmlambda"].values,
                "H_ENPR": h_enpr if h_enpr is not None else [0.0] * len(data["wcres"]),
                "KSATEXM": ksatexm if ksatexm is not None else data["ksatfit"].values,
                "BDENS": data["density"].values * 1000,  # Convert from g/cm3 to kg/m3
            }
        )

        return result

    def get_swapinput_fractions(self) -> dict:
        """
        Returns a dictionary for the SOILTEXTURES table in pySWAP.

        Returns
        -------
        dict
            Texture fractions and organic matter for pySWAP.
        """

        # Get data
        data = self.get_data_horizons(which="all")

        # Define result dictionary
        result = {}

        # Define PSAND as the remainder after subtracting PSILT and PCLAY
        psand = -data["siltcontent"].values - data["lutitecontent"].values + 100
        result.update({"PSAND": psand})

        # Add other information from the database
        result.update(
            {
                "PSILT": data["siltcontent"].values,
                "PCLAY": data["lutitecontent"].values,
                "ORGMAT": data["organicmattercontent"].values,
            }
        )

        # Convert from percentage to fraction
        result.update({var: values * 0.01 for var, values in result.items()})

        return result

    def get_swapinput_cofani(self) -> list:
        """
        Returns a list of 1.0 for each soil physical layer (for pySWAP).

        Returns
        -------
        list of float
        """

        # Get data
        data = self.get_data_horizons()

        return [1.0] * len(data.index)

    def plot(self) -> None:
        """
        Plots the soil profile using the DutchSoils visualization.

        Returns
        -------
        matplotlib.pyplot.Figure

        Notes
        -----
        The actual plotting is delegated to the `plot_soilprofile` function.
        """

        plot_soilprofile(self)
