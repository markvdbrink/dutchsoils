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
    Represents a single Dutch soil profile.

    Parameters
    ----------
    index : int, optional
        Soil profile index. Provide either this, `code`, or `bofekcluster`.
    code : int, optional
        Soil profile code. Provide either this, `index`, or `bofekcluster`.
    bofekcluster : int, optional
        BOFEK2020 cluster number. The dominant soil profile within this cluster will be used.
    soilprofile_index : int, optional [Deprecated]
        .. deprecated:: 0.1.5
            This attribute is deprecated and will be removed in a later version.
            Please use `index` instead.
    bofek_cluster : int, optional [Deprecated]
        .. deprecated:: 0.1.5
            This attribute is deprecated and will be removed in a later version.
            Please use `bofekcluster` instead.

    Notes
    -----
    Only one of `index`, `code`, or `bofekcluster` should be provided.
    Deprecated attributes are for backward compatibility and will be removed in a future version.
    """

    index: int | None = None
    code: int | None = None
    name: str = field(init=False)
    bofekcluster: int | None = None
    bofekcluster_name: str = field(init=False)
    bofekcluster_dominant: bool = field(init=False)
    # Deprecated attributes
    soilprofile_index: int | None = None
    bofek_cluster: int | None = None

    def __post_init__(self):
        """
        Validates input and sets attributes based on provided parameters.
        """
        self._check_input()
        self._set_attributes()

    def _check_input(self):
        """
        Validates initialization parameters and raises ValueError if invalid.

        - Issues DeprecationWarnings for deprecated attributes.
        - Ensures only one of `index`, `code`, or `bofekcluster` is provided.
        - Checks if provided values exist in the data.
        """

        # Deprecation warning
        if self.bofek_cluster:
            warn(
                "The use of `bofek_cluster` is deprecated and will be removed in a later version. Please use `bofekcluster` or the designated `from_bofekcluster` function.",
                FutureWarning,
                stacklevel=4,
            )
            self.bofekcluster = self.bofek_cluster

        # Deprecation warning
        if self.soilprofile_index:
            warn(
                "The use of `soilprofile_index` is deprecated and will be removed in a later version. Please use `index` or the designated `from_index` function.",
                FutureWarning,
                stacklevel=4,
            )
            self.index = self.soilprofile_index

        # Get data bofek clusters and soil profiles
        bofekclusters = self._get_data_csv("BofekClusters")
        soilprofiles = self._get_data_csv("SoilProfiles")

        # Check input parameters
        # Check if input is given
        nr_inputs = (
            (self.index is not None)
            + (self.bofekcluster is not None)
            + (self.code is not None)
        )
        if nr_inputs == 0:
            m = "Provide a soilprofile index or code or a bofek cluster number."
        # Check if only one input is given
        elif nr_inputs > 1:
            m = "Provide only one input: soilprofile index, code or a bofek cluster number, not multiple."
        # Check if given soilproile index is valid
        elif (
            self.index is not None
            and self.index not in bofekclusters["normalsoilprofile_id"].values
        ):
            m = f"Given soilprofile index '{self.index}' does not exist."
        # Check if given soilprofile code is valid
        elif self.code is not None and self.code not in soilprofiles["soilunit"].values:
            m = f"Given soilprofile code '{self.code}' does not exist."
        # Check if given bofek cluster number is valid
        elif (
            self.bofekcluster is not None
            and self.bofekcluster not in bofekclusters["cluster"].values
        ):
            m = f"Given bofek cluster number '{self.bofekcluster}' does not exist."
        else:
            return

        # Raise ValueError if one of the above conditions is not met
        raise ValueError(m)

    def _set_attributes(self):
        """
        Sets derived attributes (name, cluster info) based on input parameters.

        - Finds and assigns soil profile index, code, name, cluster, and dominance.
        - Raises ValueError if lookup fails.
        """
        # Get data
        bofekclusters = self._get_data_csv(csvfile="BofekClusters")
        soilprofiles = self._get_data_csv(csvfile="SoilProfiles")

        # Find soilprofile index if soilprofile code is given
        # TODO: there can be multiple indices for a single code, given different forms of land use (901, 902)
        if self.code is not None:
            self.index = (
                soilprofiles.loc[
                    soilprofiles["soilunit"] == self.code, "normalsoilprofile_id"
                ]
                .values[0]
                .item()
            )  # Convert datatype np.in64 to int

        # Find dominant soilprofile_index if bofek_cluster is given
        if self.bofekcluster is not None:
            row = bofekclusters[
                (bofekclusters["cluster"] == self.bofekcluster)
                & (bofekclusters["dominant"] == 1)
            ]
            self.index = row["normalsoilprofile_id"].iloc[0].item()
        # Find bofek_cluster if soilprofile_index is given
        else:
            # Find bofek_cluster
            row = bofekclusters[bofekclusters["normalsoilprofile_id"] == self.index]

            # Store bofek cluster
            self.bofekcluster = row["cluster"].iloc[0].item()

        # Store bofek cluster dominance
        self.bofekcluster_dominant = row["dominant"].iloc[0].astype(bool)

        # Store code and name of soilprofile
        self.code = soilprofiles.loc[
            soilprofiles["normalsoilprofile_id"] == self.index, "soilunit"
        ].values[0]
        self.name = soilprofiles.loc[
            soilprofiles["normalsoilprofile_id"] == self.index, "othersoilname"
        ].values[0]

        # Store name bofek cluster
        bofeknames = self._get_data_csv(csvfile="BofekClustersNames")
        self.bofekcluster_name = bofeknames.loc[
            bofeknames["cluster"] == self.bofekcluster, "name"
        ].values[0]

    def _get_data_csv(
        self,
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

        # Filter profile
        if filter_profile:
            mask = data["normalsoilprofile_id"] == self.index
            data = data.loc[mask].reset_index(drop=True)

        return data

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
        return isinstance(obj, Iterable) and not isinstance(obj, str)

    @classmethod
    def _from_userinput(
        cls,
        input,
        input_type: str,
    ):
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
            # Initiate SoilProfile for every cluster element
            result = []
            for ii in input:
                try:
                    result.append(cls(**{input_type: ii}))
                except ValueError:
                    # If input is invalid, give a warning and store a None
                    warn(
                        message=f"Given {input_type} '{ii}' is invalid, 'None' returned.",
                        stacklevel=3,
                    )
                    result.append(None)
        # Else return a SoilProfile instance
        else:
            result = cls(**{input_type: input})

        return result

    @classmethod
    def from_bofekcluster(
        cls,
        cluster: int | Iterable,
    ) -> "SoilProfile" | list["SoilProfile"]:
        """
        Create SoilProfile(s) from a BOFEK cluster number.

        You can provide either a single bofek cluster number to get a single SoilProfile or an iterable of cluster numbers to obtain multiple SoilProfiles in a list.

        Parameters
        ----------
        cluster : int or iterable of int
            BOFEK cluster number(s). If an iterable of int is given, a list of SoilProfiles will be returned.

        Returns
        -------
        SoilProfile or list of SoilProfile
        """
        return cls._from_userinput(input=cluster, input_type="bofekcluster")

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
    def from_code(
        cls,
        code: str | Iterable,
    ):
        """
        Create SoilProfile(s) from a soil profile code.

        You can provide either a single soil profile code to get a single SoilProfile or an iterable of codes to obtain multiple SoilProfiles in a list.

        Parameters
        ----------
        code : str or iterable of str
            Soil profile code(s). If an iterable of str is given, a list of SoilProfiles will be returned.

        Returns
        -------
        SoilProfile or list of SoilProfile
        """
        return cls._from_userinput(input=code, input_type="code")

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
        df = cls._get_data_csv(self=None, csvfile="SoilProfiles_MapAreaID")

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
                f"Value '{which}' for which-parameter is invalid. Please use 'profile' or 'bofekcluster'."
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
                Median value of the content of mineral particles with a grain size smaller than 50 µm.
            loamcontent10p
                The 10th percentile for the variation in the content of mineral particles with a grain size smaller than 50 µm.
            loamcontent90p
                The 90th percentile for the variation in the content of mineral particles with a grain size smaller than 50 µm.
            lutitecontent
                Median value of the content of mineral particles with a grain size smaller than 2 µm.
            lutitecontent10p
                The 10th percentile for the variation in the content of mineral particles with a grain size smaller than 2 µm.
            lutitecontent90p
                The 90th percentile for the variation in the content of mineral particles with a grain size smaller than 2 µm.
            sandmedian
                Median value of the sand fraction (µm).
            sandmedian10p
                The 10th percentile for the variation in sand median (µm).
            sandmedian90p
                The 10th percentile for the variation in sand median (µm).
            siltcontent
                Median value of the content of mineral particles with a grain size between 50 µm and 2 mm.
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
        dataall = self._get_data_csv("SoilHorizons", filter_profile=True)

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

    def plot(self, merge_layers: bool = False) -> None:
        """
        Plots the soil profile using the DutchSoils visualization.

        Parameters
        ----------
        merge_layers : bool, optional
            If True, adjacent layers with identical properties are merged before plotting.
            If False (default), all layers are plotted as-is.

        Returns
        -------
        matplotlib.pyplot.Figure

        Notes
        -----
        The actual plotting is delegated to the `plot_soilprofile` function.
        """

        plot_soilprofile(self, merge_layers=merge_layers)

    def _get_allprofiles(self) -> DataFrame:
        """
        [Deprecated] Returns a DataFrame with all soil profiles.

        .. deprecated:: 0.1.5
            This function is deprecated and will be removed in a later version.
            Please use _get_data_csv instead.

        Returns
        -------
        pandas.DataFrame
        """

        # Deprecation warning
        warn(
            "This function is deprecated and will be removed in a later version. Please use _get_data_csv instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        path = Path(__file__).parent / "data/soilprofiles_BodemkaartBofek.csv"
        all_profiles = read_csv(path, skiprows=12)

        return all_profiles

    def get_data(self) -> DataFrame:
        """
        [Deprecated] Returns a DataFrame with data per soil layer.

        .. deprecated:: 0.1.5
            This function is deprecated and will be removed in a later version.
            Please use get_data_horizons or the attributes of the soilprofile instead.

        Returns
        -------
        pandas.DataFrame
        """

        # Deprecation warning
        warn(
            "This function is deprecated and will be removed in a later version. Please use get_data_horizons or the attributes of the soilprofile instead.",
            FutureWarning,
            stacklevel=2,
        )

        # Get data all profiles
        allprofiles = self._get_allprofiles()

        # Make mask depending on given input
        if self.index is not None:
            mask = allprofiles["soil_id"] == self.index
        elif self.bofekcluster is not None:
            # If bofek cluster is given, return only the dominant profile
            mask = (allprofiles["bofek_cluster"] == self.bofekcluster) & (
                allprofiles["bofek_dominant"]
            )

        # Get data
        data = allprofiles.loc[mask].reset_index(drop=True)

        return data
