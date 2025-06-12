from dataclasses import dataclass
from pathlib import Path

from numpy import array, ones, diff, concatenate, searchsorted
from pandas import (
    DataFrame,
    read_csv,
)

from .plot import soilprofile as plot_soilprofile


@dataclass
class SoilProfile:
    """Class of a single soil profile.

    Attributes:
        soilprofile_index:
            Soil profile index.
        bofek_cluster:
            Bofek cluster number. The dominant soil profile within this cluster will be used.
    """

    soilprofile_index: int | None = None
    bofek_cluster: int | None = None

    def __post_init__(self):
        """
        Checks if given input parameters are valid.
        """

        # Get data all profiles
        allprofiles = self._get_allprofiles()

        # Check input parameters
        check_none = self.soilprofile_index is None and self.bofek_cluster is None
        check_idxsp = self.soilprofile_index not in allprofiles["soil_id"].values
        check_clbfk = self.bofek_cluster not in allprofiles["bofek_cluster"].values
        if check_none or (check_idxsp and check_clbfk):
            m = (
                f"No data available for soilprofile index {self.soilprofile_index}"
                f" or bofek cluster {self.bofek_cluster}."
            )
            raise ValueError(m)

    def _get_allprofiles(self) -> DataFrame:
        """
        Returns a dataframe with all soil profiles.
        """

        path = Path(__file__).parent / "data/soilprofiles_BodemkaartBofek.csv"
        all_profiles = read_csv(path, skiprows=12)

        return all_profiles

    def get_data(self) -> DataFrame:
        """
        Return pandas dataframe with the data per soil layer.
        Only the soilprofile index will be used if both
        the soilprofile index and bofek cluster are given.

        Returns
        -------
        pandas.DataFrame
        """

        # Get data all profiles
        allprofiles = self._get_allprofiles()

        # Make mask depending on given input
        if self.soilprofile_index is not None:
            mask = allprofiles["soil_id"] == self.soilprofile_index
        elif self.bofek_cluster is not None:
            # If bofek cluster is given, return only the dominant profile
            mask = (allprofiles["bofek_cluster"] == self.bofek_cluster) & (
                allprofiles["bofek_dominant"]
            )

        # Get data
        data = allprofiles.loc[mask].reset_index(drop=True)

        return data

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
        data = self.get_data()

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
        soillay_zb = (array(data["layer_zbot"]) * 100).astype(
            int
        )  # convert from m to cm

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
        data = self.get_data()

        # Define a dictionary
        result = {}

        # Add given information or data from the database
        result.update(
            {
                "ORES": data["layer_wcres"],
                "OSAT": data["layer_wcsat"],
                "ALFA": data["layer_VGalfa"],
                "NPAR": data["layer_VGnpar"],
                "KSATFIT": data["layer_ksatfit"],
                "LEXP": data["layer_VGlexp"],
                "H_ENPR": h_enpr
                if h_enpr is not None
                else [0.0] * len(data["layer_wcres"]),
                "KSATEXM": ksatexm if ksatexm is not None else data["layer_ksatfit"],
                "BDENS": data["layer_bdens"] * 1000,  # Convert from g / cm3 to mg / cm3
            }
        )

        return result

    def get_swapinput_fractions(self) -> dict:
        """
        Returns a dictionary with input for the SOILTEXTURES table in pySWAP.
        """
        # Get data
        data = self.get_data()

        # Define result dictionary
        result = {}

        # Define PSAND as the remainder after subtracting PSILT and PCLAY
        psand = -data["layer_psilt"].values - data["layer_pclay"].values + 100
        result.update({"PSAND": psand})

        # Add other information from the database
        result.update(
            {
                "PSILT": data["layer_psilt"],
                "PCLAY": data["layer_pclay"],
                "ORGMAT": data["layer_porgmat"],
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
        data = self.get_data()

        return [1.0] * len(data.index)
