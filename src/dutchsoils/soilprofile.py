from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from warnings import warn

from numpy import array, ones, diff, concatenate, searchsorted
from pandas import (
    DataFrame,
    read_csv,
)
from pyproj import Transformer
from pyproj.database import query_crs_info
from requests import get as requests_get

from .plot import soilprofile as plot_soilprofile


@dataclass
class SoilProfile:
    """
    Class representing a single soil profile.

    Parameters
    ----------
    soilprofile_index : int, optional
        Soil profile index. Provide either this or `bofek_cluster`.
    bofek_cluster : int, optional
        BOFEK cluster number. The dominant soil profile within this cluster will be used.

    Attributes
    ----------
    index : int or None
        Input. Soil profile index.
    bofekcluster : int or None
        Input. BOFEK cluster number.
    soilprofile_index : int or None
        Input. Soil profile index.
    bofek_cluster : int or None
        Input. BOFEK cluster number.
    # TODO

    Notes
    -----
    Either `soilprofile_index` or `bofek_cluster` must be provided, but not both.
    """

    index: int | None = None
    name: str = field(init=False)
    bofekcluster: int | None = None
    bofekcluster_name: str = field(init=False)
    bofekcluster_dominant: bool = field(init=False)
    # Deprecated attributes
    soilprofile_index: int | None = None
    bofek_cluster: int | None = None

    def __post_init__(self):
        """
        Check input and store attributes based on input parameters.
        """
        # Check input
        self._check_input()

        # Lookup attributes and assign
        self._set_attributes()

    def _check_input(self):
        """
        Checks if given input parameters are valid.
        """

        # Deprecation warning
        if self.bofek_cluster:
            warn(
                "The use of `bofek_cluster` is deprecated and will be removed in a later version. Please use `bofekcluster`.",
                DeprecationWarning,
                stacklevel=2,
            )
            self.bofekcluster = self.bofek_cluster

        # Deprecation warning
        if self.soilprofile_index:
            warn(
                "The use of `soilprofile_index` is deprecated and will be removed in a later version. Please use `index`.",
                DeprecationWarning,
                stacklevel=2,
            )
            self.index = self.soilprofile_index

        # Get data all profiles
        all_profiles = self._get_data_csv("BofekClusters")

        # Check input parameters
        # Check if input is given
        nr_inputs = (self.index is not None) + (self.bofekcluster is not None)
        if nr_inputs == 0:
            m = "Provide either a soilprofile index or a bofek cluster number."
        # Check if only one input is given
        elif nr_inputs == 2:
            m = "Provide either a soilprofile index or a bofek cluster number, not both."
        # Check if given soilproile index is valid
        elif (
            self.index is not None
            and self.index not in all_profiles["normalsoilprofile_id"].values
        ):
            m = f"Given soilprofile index {self.index} does not exist."
        # Check if given bofek cluster number is valid
        elif (
            self.bofekcluster is not None
            and self.bofekcluster not in all_profiles["cluster"].values
        ):
            m = f"Given bofek cluster number {self.bofekcluster} does not exist."
        else:
            return

        # Raise ValueError if one of the above conditions is not met
        raise ValueError(m)

    def _set_attributes(self):
        """
        Set uninitialised attributes based on input parameters.
        """
        # Get bofek clustering data
        bofekclustering = self._get_data_csv(csvfile="BofekClusters")

        # Find dominant soilprofile_index if bofek_cluster is given
        if self.bofekcluster is not None:
            row = bofekclustering[
                (bofekclustering["cluster"] == self.bofekcluster)
                & (bofekclustering["dominant"] == 1)
            ]
        # Find bofek_cluster if soilprofile_index is given
        else:
            # Find bofek_cluster
            row = bofekclustering[bofekclustering["normalsoilprofile_id"] == self.index]

        # Store index, area, and bofek dominance
        self.index = row.loc[:, "normalsoilprofile_id"].values[0]
        self.bofekcluster = row.loc[:, "cluster"].values[0]
        self.bofekcluster_dominant = row.loc[:, "dominant"].values[0].astype(bool)

        # Store name soilprofile
        soilnames = self._get_data_csv(csvfile="SoilProfiles")
        self.name = soilnames.loc[
            soilnames["normalsoilprofile_id"] == self.index, "name"
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
        Returns a dataframe from the specified csv file.
        """
        # Read data
        path = Path(__file__).parent / "data" / (csvfile + ".csv")
        data = read_csv(path, skiprows=10)

        # Filter profile
        if filter_profile:
            mask = data["normalsoilprofile_id"] == self.index
            data = data.loc[mask].reset_index(drop=True)

        return data

    @classmethod
    def from_bofekcluster(
        cls,
        cluster: int | list | None,
    ) -> "SoilProfile" | list["SoilProfile"]:
        """ """
        # Return a list of Soilprofiles if input is a list
        if isinstance(cluster, list):
            # Initiate SoilProfile for every cluster element
            result = []
            for cc in cluster:
                try:
                    result.append(cls(bofekcluster=cc))
                except ValueError:
                    # If cluster is invalid, give a warning and store a None
                    warn(message=f"Given BOFEK cluster {cc} is invalid.", stacklevel=2)
                    result.append(None)
        # Else return a SoilProfile instance
        else:
            result = cls(bofekcluster=cluster)

        return result

    @classmethod
    def from_index(
        cls,
        index: int | list | None,
    ) -> "SoilProfile" | list["SoilProfile"]:
        """ """
        # Return a list of Soilprofiles if input is a list
        if isinstance(index, list):
            # Initiate SoilProfile for every cluster element
            result = []
            for ii in index:
                # If cluster is invalid, store a None
                try:
                    result.append(cls(index=ii))
                except ValueError:
                    # If index is invalid, give a warning and store a None
                    warn(message=f"Given index {ii} is invalid.", stacklevel=2)
                    result.append(None)
        # Else return a SoilProfile instance
        else:
            result = cls(index=index)

        return result

    @classmethod
    def from_location(
        cls,
        x: float | list | None,
        y: float | list | None,
        crs: str = "EPSG:28992",
    ) -> "SoilProfile" | list["SoilProfile"]:
        """ """

        # Check input
        cls._check_input_location(cls, x, y, crs)

        # In case x and y are iterables
        try:
            result = []
            for xx, yy in zip(x, y):
                # Transform coordinates if necessary
                xxtf, yytf = cls._transform_coordinates(cls, xx, yy)

                # Request index using coordinates
                index = cls._request_index(cls, xxtf, yytf)

                # Initialise SoilProfile
                sp = cls.from_index(index)
                result.append(sp)
        # In case x and y are not iterables
        except TypeError:
            # Transform coordinates if necessary
            xxtf, yytf = cls._transform_coordinates(cls, x, y)

            # Request index using coordinates
            index = cls._request_index(cls, xxtf, yytf)

            # Initialise SoilProfile
            result = cls.from_index(index)

        return result

    @classmethod
    def _check_input_location(cls, x, y, crs):
        # Check if x is iterable
        try:
            for ii, xx in enumerate(x):
                # Check if its elements are floats or integers
                if not isinstance(xx, (float, int)):
                    m = f"The {ii}th element of the X-coordinates ({xx}) is neither a float or int."
                    raise ValueError(m)

            # Check if y is iterable
            try:
                for jj, yy in enumerate(y):
                    # Check if its elements are floats or integers
                    if not isinstance(yy, (float, int)):
                        m = f"The {jj}th element of the Y-coordinates ({yy}) is neither a float or int."
                        raise ValueError(m)

                # Check if x and y have the same length
                if len(x) != len(y):
                    m = f"List of X and Y coordinates do not have the same length (x: {len(x)}, y: {len(y)})."
                    raise ValueError(m)

            # If y is not iterable, check if it is a float or an integer
            except TypeError:
                if not isinstance(y, (float, int)):
                    m = f"The Y-coordinate ({y}) is neither a float or int."
                    raise ValueError(m)

        # If x is not iterable, check if it is a float or an integer
        except TypeError:
            if not isinstance(x, (float, int)):
                m = f"The X-coordinate ({x}) is neither a float or int."
                raise ValueError(m)

        # Check if crs exists
        crs_info_list = query_crs_info(auth_name=None, pj_types=None)
        crs_list = ["EPSG:" + info[1] for info in crs_info_list]
        if crs not in crs_list:
            m = f"CRS {crs} is not valid."
            raise ValueError

        return

    @classmethod
    def _transform_coordinates(cls, xx, yy, crs):
        # Transform coordinates to EPSG 4326 if necessary
        if crs != "EPSG:4326":
            transformer = Transformer.from_crs(
                crs_from=crs,
                crs_to="EPSG:4326",
            )
            xx, yy = transformer.transform(xx, yy)

        return xx, yy

    @classmethod
    def _request_index(cls, xx, yy):
        # Send request for soil data to soilphysics.wur.nl
        r = requests_get(
            url="https://www.soilphysics.wur.nl/soil.php",
            params={"latitude": xx, "longitude": yy},
        )

        # TODO what if no connection

        # TODO what if no data available

        # Extract data in json format
        data = r.json()

        # Get index
        index = data["id"]

        return index

    def get_area(self, which: str = "profile") -> float:
        """
        Returns the total area of this profile or BOFEK2020 cluster in the Netherlands.

        Parameters
        ---------
        which
            Which area to return. Options (default: "profile"):

                * "profile": Return the area of this profile.
                * "bofekcluster": Return the area of the total bofekcluster.

        """
        # Check input

        # Get area

        return

    def get_data_horizons(
        self,
        which: str = "all",
    ) -> DataFrame:
        """
        Get a dataframe

        Parameters
        ----------
        which
            Which data to return (default: "all"). Options:

                * "all": combination of hydraulic, physical and chemical data.
                * "hydraulic": Staring series data.
                * "physical": Mass fractions with a certain diameter (loam, lutite, silt), sand median and density.
                * "chemical": Organic matter, calcite, ironoxide content and acidity.

        Returns
        -------
        pandas.Dataframe

        Explanation of columns (see also https://docs.geostandaarden.nl/bro/vv-im-SGM-20220328/):

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
            m = f"Unvalid value for 'which': {which}. Choose between 'all', 'hydraulic', 'physical', 'chemical'."
            raise ValueError(m)

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
        Returns a dictionary as input for a SOILPROFILE table in pySWAP.

        Parameters
        ----------
        discretisation_depths : list
            List of discretisation depths (cm).
            The depth of the profile is the total sum.
            If larger than 120 cm, the deepest soil physical layer will be extended.
        discretisation_compheights : list
            List of discretisation compartment heights (cm) for each discretisation depth.
            The discretisation depth should be a natural product of the discretisation compartment height.

        Example
        -------
        discretisation_depths = [50, 30, 60, 60, 100]
        discretisation_compheights = [1, 2, 5, 10, 20]
        will return a discretisation of:
            0-50 cm: 50 compartments of 1 cm
            50-80 cm: 15 compartments of 2 cm
            80-140 cm: 12 compartments of 5 cm
            140-200 cm: 6 compartments of 10 cm
            200-300 cm: 5 compartments of 20 cm
        The total depth of the profile is 300 cm.
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

        ksatexm : list
            List of measured saturated hydraulic conductivities (cm/d).
            If not provided, it will be set equal to ksatfit.
        h_enpr : list
            List of measured air entry pressure head (cm).
            If not provided, it will be set equal to 0.0 cm.
        """

        # Get data
        data = self.get_data_horizons(which="all")

        # Define a dictionary
        result = {}

        # Add given information or data from the database
        result.update(
            {
                "ORES": data["wcres"],
                "OSAT": data["wcsat"],
                "ALFA": data["vgmalpha"],
                "NPAR": data["vgmnpar"],
                "KSATFIT": data["ksatfit"],
                "LEXP": data["vgmlambda"],
                "H_ENPR": h_enpr if h_enpr is not None else [0.0] * len(data["wcres"]),
                "KSATEXM": ksatexm if ksatexm is not None else data["ksatfit"],
                "BDENS": data["density"] * 1000,  # Convert from g/cm3 to kg/m3
            }
        )

        return result

    def get_swapinput_fractions(self) -> dict:
        """
        Returns a dictionary with input for the SOILTEXTURES table in pySWAP.
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
                "PSILT": data["siltcontent"],
                "PCLAY": data["lutitecontent"],
                "ORGMAT": data["organicmattercontent"],
            }
        )

        # Convert from percentage to fraction
        result.update({var: values * 0.01 for var, values in result.items()})

        return result

    def get_swapinput_cofani(self) -> list:
        """
        Returns a list containing 1.0 for each soil physical layer.
        """
        # Get data
        data = self.get_data_horizons()

        return [1.0] * len(data.index)

    def plot(self, merge_layers: bool = False) -> None:
        """
        Plots the soil profile using the specified visualization function.

        Parameters
        ----------
        merge_layers : bool, optional
            If True, adjacent soil layers with identical properties will be merged before plotting.
            If False (default), all layers are plotted as-is.

        Returns
        -------
        matplotlib.pyplot.Figure

        Notes
        -----
        This method provides a visual representation of the soil profile, which can help in analyzing
        layer structure and properties. The actual plotting is delegated to the `plot_soilprofile` function.
        """

        plot_soilprofile(self, merge_layers=merge_layers)

    def _get_allprofiles(self) -> DataFrame:
        """
        Returns a dataframe with all soil profiles.
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
        Return pandas dataframe with the data per soil layer.
        Only the soilprofile index will be used if both
        the soilprofile index and bofek cluster are given.

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
            DeprecationWarning,
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
