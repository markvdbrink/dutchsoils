import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pedon as pe

# Set default colors for each soil type
COLORS_SOILS = {
    # Zand: brown
    "B01": "#e6c8a5",
    "B02": "#d6b095",
    "B03": "#c69885",
    "B04": "#b68075",
    "B05": "#f6e0b5",
    "B06": "#a66865",
    # Zavel: blue
    "B07": "#b3e6ff",
    "B08": "#99ddff",
    "B09": "#80d4ff",
    # Klei: purple
    "B10": "#d9b3ff",
    "B11": "#cc99ff",
    "B12": "#bf80ff",
    # Leem: red
    "B13": "#ffb3b3",
    "B14": "#ff8080",
    # Moerig: green
    "B15": "#b3ffb3",
    "B16": "#99ff99",
    "B17": "#80ff80",
    "B18": "#66ff66",
    # Zand: brown
    "O01": "#e6c8a5",
    "O02": "#d6b095",
    "O03": "#c69885",
    "O04": "#b68075",
    "O05": "#f6e0b5",
    "O06": "#460005",
    "O07": "#e6ccff",
    # Zavel: blue
    "O08": "#b3e6ff",
    "O09": "#99ddff",
    "O10": "#80d4ff",
    # Klei: purple
    "O11": "#d9b3ff",
    "O12": "#cc99ff",
    "O13": "#bf80ff",
    # Leem: red
    "O14": "#ffb3b3",
    "O15": "#ff8080",
    # Veen: green
    "O16": "#1aff1a",
    "O17": "#00e600",
    "O18": "#00cc00",
}


def soilprofile(
    soilprofile,
    which: str,
) -> plt.Figure:
    """
    Plot a comprehensive visualization of a soil profile, including profile layers, hydraulic properties, texture fractions, and organic matter content.
    This function generates a multi-panel matplotlib figure summarizing key properties of a given soil profile. The visualization includes:
        - A bar plot of soil layers with Staring class labels.
        - Soil water retention and hydraulic conductivity curves for each unique layer.
        - Stacked bar plots of particle size fractions (clay, silt, sand) per layer.
        - Bar plots of organic matter content per layer.

    Parameters
    ----------
    soilprofile : SoilProfile
        An object representing the soil profile, expected to provide a `get_data()` method returning a DataFrame with required soil properties.
    which : str, optional
        Which data to plot (default: "all"). Options:
            * "all": Combination of hydraulic, physical, and chemical data.
            * "hydraulic": Staring series data.
            * "physical": Mass fractions, density.
            * "chemical": Organic matter, calcite, iron oxide, acidity.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The matplotlib Figure object containing the generated plots.

    Example
    -------
    >>> fig = soilprofile(my_soilprofile, merge_layers=True)
    >>> fig.show()
    """

    # Get data of soil horizons
    data = soilprofile.get_data_horizons(which="all")
    data = data.set_index("layernumber")

    # Define figure dimensions for each data dype
    ncols = {
        "all": 6,
        "hydraulic": 2,
        "chemical": 3,
        "physical": 3,
    }

    width_ratios = {
        "all": [1.1, 1, 1, 1, 1, 1.75],
        "hydraulic": [1.2, 1.75],
        "chemical": [1.2, 1, 1],
        "physical": [1.2, 1, 1],
    }

    # Plot figure
    fig = plt.figure(
        figsize=(sum(width_ratios[which]) * 2, 5),
        layout="constrained",
    )
    # Make a gridspec for the different subplots
    gs = mpl.gridspec.GridSpec(
        nrows=2,
        ncols=ncols[which],
        width_ratios=width_ratios[which],
        figure=fig,
    )

    # Set fontsizes
    context = {
        "figure.dpi": 100,
        "figure.titlesize": 10,
        "axes.titlesize": 8,
        "axes.labelsize": 9,
        "axes.grid": True,
        "axes.axisbelow": True,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 9,
        "legend.title_fontsize": 9,
        "font.size": 8,
        "font.family": "DejaVu Sans",
    }

    with mpl.rc_context(context):
        # Plot different data types
        ax_sp = fig.add_subplot(gs[:, 0])
        plot_profile(ax_sp, data)

        if which == "all" or which == "hydraulic":
            ax_swrc = (
                fig.add_subplot(gs[0, 5])
                if which == "all"
                else fig.add_subplot(gs[0, 1])
            )
            ax_shcc = (
                fig.add_subplot(gs[1, 5], sharex=ax_swrc)
                if which == "all"
                else fig.add_subplot(gs[1, 1], sharex=ax_swrc)
            )
            plot_hydraulic_data(ax_swrc=ax_swrc, ax_shcc=ax_shcc, data=data)

        if which == "all" or which == "chemical":
            ax_cont = fig.add_subplot(gs[:, 1])
            ax_ac = fig.add_subplot(gs[:, 2])
            plot_chemical_data(ax_cont=ax_cont, ax_ac=ax_ac, data=data)

        if which == "all" or which == "physical":
            ax_bd = (
                fig.add_subplot(gs[:, 3])
                if which == "all"
                else fig.add_subplot(gs[:, 1])
            )
            ax_tex = (
                fig.add_subplot(gs[:, 4])
                if which == "all"
                else fig.add_subplot(gs[:, 2])
            )
            plot_physical_data(ax_bd=ax_bd, ax_tex=ax_tex, data=data)

        # Set title of plot for input soil or bofek cluster soil
        title = (
            "Soil profile "
            + str(soilprofile.code)
            + " ("
            + str(soilprofile.index)
            + "): "
            + str(soilprofile.name)
            + "\nBofek cluster "
            + str(soilprofile.bofekcluster)
            + ": "
            + str(soilprofile.bofekcluster_name)
        )
        if soilprofile.bofekcluster_dominant:
            title += " (dominant)"
        else:
            title += " (not dominant)"
        fig.suptitle(title)

    return fig


def plot_profile(ax_sp, data):
    hatches = {
        "B": "/",
        "O": ".",
    }

    # Plot soil profile as bars
    for layer in data.index:
        # Get bottom level and height of layer
        zbot, height = get_z(data, layer)

        # Plot profile as bar plot
        ax_sp.bar(
            x=0,
            height=height,
            bottom=zbot,
            width=2.0,
            color=COLORS_SOILS[data.loc[layer, "staringseriesblock"]],
            hatch=hatches[data.loc[layer, "staringseriesblock"][0]],
            hatch_linewidth=1.0,
            edgecolor="darkgray",
        )

        # Plot FAO horizon description and Staring class number and name for each layer
        string = (
            f"Horizon {layer + 1}: "
            + data.loc[layer, "faohorizonnotation"]
            + "\n"
            + data.loc[layer, "staringseriesblock"]
            + ": "
            + data.loc[layer, "staringblocklabel"]
        )
        ax_sp.text(
            x=0,
            y=zbot + height / 2,
            s=string,
            ha="center",
            va="center",
        )

    # Layout
    ax_sp.set_ylim(-120, 0)
    ax_sp.set_yticks(np.arange(-120, 10, 10))
    ax_sp.set_ylabel("Depth [cm]")
    ax_sp.set_xlim(-1, 1)
    ax_sp.set_xticks([0], [None])
    ax_sp.set_axisbelow(True)
    ax_sp.grid(color="lightgrey")
    ax_sp.set_title("Soil profile")


def plot_hydraulic_data(ax_swrc, ax_shcc, data):
    linestyles = ["-", "--", ":", "-."]

    for count, block in enumerate(data["staringseriesblock"].unique()):
        # Define range of pressure heads
        h = np.logspace(-3, 10, 1000) * -1

        # If multiple horizons with the same block, use the first one
        row = data[data["staringseriesblock"] == block].head(1)

        # Define pedon soilmodel
        shf = pe.Genuchten(
            theta_r=row["wcres"].item(),
            theta_s=row["wcsat"].item(),
            alpha=row["vgmalpha"].item(),
            n=row["vgmnpar"].item(),
            k_s=row["ksatfit"].item(),
            l=row["vgmlambda"].item(),
        )

        # Plot soil water retention curve
        ax_swrc.plot(
            h,
            shf.theta(h=-h),  # requires positive pressure heads
            label=block,
            color=COLORS_SOILS[block],
            linestyle=linestyles[count % 4],
        )

        # Plot soil hydraulic conductivity
        ax_shcc.plot(
            h,
            shf.k(h=-h),  # requires positive pressure heads
            label=block,
            color=COLORS_SOILS[block],
            linestyle=linestyles[count % 4],
        )

    # Layout soil water retention curve
    ax_swrc.legend()
    ax_swrc.set_xscale("symlog")
    ax_swrc.set_xlim(-1e-1, -1e6)
    ax_swrc.set_xticks(np.logspace(-1, 6, 8) * -1, [None] * 8)
    ax_swrc.set_ylabel("Water content\n[$cm^3/cm^{3}$]")
    ax_swrc.set_title("Soil Water Retention & Conductivity Curve")
    ax_swrc.set_axisbelow(True)
    ax_swrc.grid(color="lightgrey")

    # Layout soil hydraulic conductivity curve
    ax_shcc.legend()
    ax_shcc.set_xscale("symlog")
    ax_shcc.set_xlim(-1e-1, -1e6)
    ax_shcc.set_xlabel("Pressure head [cm]")
    ax_shcc.set_xticks(np.logspace(-1, 6, 8) * -1)
    ax_shcc.set_yscale("log")
    ax_shcc.set_ylim(1e-10, 1e3)
    ax_shcc.set_ylabel("Hydraulic conductivity\n[$cm/d$]")
    ax_shcc.set_axisbelow(True)
    ax_shcc.grid(color="lightgrey")


def plot_chemical_data(ax_cont, ax_ac, data):
    for layer in data.index:
        # Get bottom level and height of layer
        zbot, height = get_z(data=data, layer=layer)

        # PLOT CONTENTS

        # Plot median organic matter content
        ax_cont.plot(
            [data.loc[layer, "organicmattercontent"].item()] * 2,
            [zbot, zbot + height],
            color="saddlebrown",
            label="OM median" if layer == 1 else None,
        )

        # Plot 10th and 90th percentile organic matter content
        ax_cont.fill_between(
            x=data.loc[layer, ["organicmattercontent10p", "organicmattercontent90p"]]
            .astype(float)
            .values,
            y1=zbot,
            y2=zbot + height,
            color="saddlebrown",
            alpha=0.5,
            edgecolor="None",
            label="OM 10-90p" if layer == 1 else None,
        )

        # Plot iron and calcite content
        ax_cont.plot(
            [data.loc[layer, "calciccontent"].item()] * 2,
            [zbot, zbot + height],
            color="orange",
            label="Calcite" if layer == 1 else None,
        )
        ax_cont.plot(
            [data.loc[layer, "fedith"].item()] * 2,
            [zbot, zbot + height],
            color="deepskyblue",
            label="Fe$_{2}$O$_{3}$" if layer == 1 else None,
        )

        # PLOT ACIDITY

        # Plot median organic matter content
        ax_ac.plot(
            [data.loc[layer, "acidity"].item()] * 2,
            [zbot, zbot + height],
            color="cyan",
            label="pH median" if layer == 1 else None,
        )

        # Plot 10th and 90th percentile organic matter content
        ax_ac.fill_between(
            x=data.loc[layer, ["acidity10p", "acidity90p"]].astype(float).values,
            y1=zbot,
            y2=zbot + height,
            color="cyan",
            alpha=0.2,
            edgecolor="None",
            label="pH 10-90p" if layer == 1 else None,
        )

    # Layout contents plot
    ax_cont.set_title("Compounds")
    ax_cont.set_xlabel("Content [mass-%]")
    ax_cont.legend()
    ax_cont.set_ylim(-120, 0)
    ax_cont.set_yticks(np.arange(-120, 10, 10), [None] * 13)
    ax_cont.set_axisbelow(True)
    ax_cont.grid(color="lightgrey")

    # Layout contents plot
    ax_ac.set_title("Acidity")
    ax_ac.set_xlabel("pH")
    ax_ac.legend()
    ax_ac.set_ylim(-120, 0)
    ax_ac.set_yticks(np.arange(-120, 10, 10), [None] * 13)
    ax_ac.set_axisbelow(True)
    ax_ac.grid(color="lightgrey")


def plot_physical_data(ax_bd, ax_tex, data):
    for layer in data.index:
        # Get bottom and height of horizon
        zbot, height = get_z(data=data, layer=layer)

        # SUBPLOT BULK DENSITY
        ax_bd.plot(
            [data.loc[layer, "density"].item()] * 2,
            [zbot, zbot + height],
            color="k",
        )

        # SUBPLOT SOIL TEXTURE
        pclay = data.loc[layer, "lutitecontent"].item()
        psilt = data.loc[layer, "siltcontent"].item()
        psand = 100 - pclay - psilt
        left = 0

        for fraction, label, color in zip(
            [pclay, psilt, psand],
            ["<2µm", ">2µm\n<50µm", ">50µm"],
            ["#f6e0b5", "#80d4ff", "#cc99ff"],
        ):
            # Plot fractions
            ax_tex.fill_between(
                x=[left, left + fraction],
                y1=zbot,
                y2=zbot + height,
                color=color,
                edgecolor="None",
                label=label if layer == 1 else None,
                alpha=0.75,
            )
            left += fraction

    # Layout bulk density
    ax_bd.set_title("Bulk density")
    ax_bd.set_xlabel("Bulk density [g/cm$^{3}$]")
    ax_bd.set_ylim(-120, 0)
    ax_bd.set_yticks(np.arange(-120, 10, 10), [None] * 13)
    ax_bd.set_axisbelow(True)
    ax_bd.grid(color="lightgrey")

    # Layout texture
    ax_tex.set_title("Texture")
    ax_tex.set_xlabel("Particle size fraction [%]")
    ax_tex.legend()
    ax_tex.set_xlim(0, 100)
    ax_tex.set_xticks(np.arange(0, 110, 20))
    ax_tex.set_ylim(-120, 0)
    ax_tex.set_yticks(np.arange(-120, 10, 10), [None] * 13)
    ax_tex.set_axisbelow(True)
    ax_tex.grid(color="lightgrey")


def get_z(data, layer):
    # Get depth and height of layer
    zbot = data.loc[layer, "zbottom"].item() * -100  # cm depth
    height = data.loc[layer, "ztop"].item() * -100 - zbot  # cm height
    return zbot, height
