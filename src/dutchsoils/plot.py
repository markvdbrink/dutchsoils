import warnings

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

# Set default colors for each soil group
COLORS_SOILGROUPS = {
    ">50µm": "#f6e0b5",  # yellow
    ">2µm\n<50µm": "#80d4ff",  # light blue
    "<2µm": "#cc99ff",  # purple
}


def soilprofile(
    soilprofile,
    merge_layers=False,
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
    merge_layers : bool, optional
        [Deprecated] If True, visually merges consecutive layers with identical Staring class names in the profile plot (default: False).
        This parameter is deprecated because it is wrong to merge layers on the Staringclass alone because other properties are different.
        At the moment, the parameter does nothing and will be removed in version 1.0.0.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The matplotlib Figure object containing the generated plots.

    Example
    -------
    >>> fig = soilprofile(my_soilprofile, merge_layers=True)
    >>> fig.show()
    """

    if merge_layers:
        warnings.warn(
            "The use of merge_layers is deprecated and will be removed in version 1.0.0.",
            DeprecationWarning,
            stacklevel=2,
        )

    # Get data
    data = soilprofile.get_data_horizons(which="all")
    data = data.set_index("layernumber")

    # Plot figure
    fig = plt.figure(
        figsize=(10, 5),
        layout="constrained",
    )

    # Use a gridspec, derive axes
    gs = mpl.gridspec.GridSpec(nrows=2, ncols=3, width_ratios=[1.2, 2, 2], figure=fig)
    ax1 = fig.add_subplot(gs[:, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 1])
    ax4 = fig.add_subplot(gs[0, 2])
    ax5 = fig.add_subplot(gs[1, 2])

    # Counter to account for duplicate staring series blocks
    staring_count = 0

    # Linestyles
    linestyles = ["-", "--", ":", "-."]
    hatches = {
        "B": "/",
        "O": ".",
    }
    height = None

    # Plot soil profile as bars
    for count, layer in zip(range(1, len(data) + 1), data.index):
        # SUBPLOT 1: Soil profile

        # Get depth and height of layer
        zbot = data.loc[layer, "zbottom"] * -100  # cm depth
        height = data.loc[layer, "ztop"] * -100 - zbot  # cm height

        # Plot profile as bar plot
        ax1.bar(
            x=0,
            height=height,
            bottom=zbot,
            width=2.0,
            color=COLORS_SOILS[data.loc[layer, "staringseriesblock"]],
            hatch=hatches[data.loc[layer, "staringseriesblock"][0]],
            hatch_linewidth=1.0,
            edgecolor="darkgray",
        )

        # Plot Staring class number and description for each layer
        string = (
            f"Horizon {count}\n"
            + data.loc[layer, "staringseriesblock"]
            + ": "
            + data.loc[layer, "staringblocklabel"]
        )
        ax1.text(
            x=0,
            y=zbot + height / 2,
            s=string,
            ha="center",
            va="center",
            fontsize=8,
        )

        # Because of duplicates: plot if staring block is not plotted yet
        blocks_plotted = [line.get_label() for line in ax2.get_lines()]
        if data.loc[layer, "staringseriesblock"] not in blocks_plotted:
            # Define range of pressure heads
            h = np.logspace(-3, 10, 1000) * -1

            # Define pedon soilmodel
            shf = pe.Genuchten(
                theta_r=data.loc[layer, "wcres"],
                theta_s=data.loc[layer, "wcsat"],
                alpha=data.loc[layer, "vgmalpha"],
                n=data.loc[layer, "vgmnpar"],
                k_s=data.loc[layer, "ksatfit"],
                l=data.loc[layer, "vgmlambda"],
            )

            # SUBPLOT 2: Soil water retention curve
            ax2.plot(
                h,
                shf.theta(h=-h),  # requires positive pressure heads
                label=data.loc[layer, "staringseriesblock"],
                color=COLORS_SOILS[data.loc[layer, "staringseriesblock"]],
                linestyle=linestyles[staring_count],
            )

            # SUBPLOT 3: Soil hydraulic conductivity
            ax3.plot(
                h,
                shf.k(h=-h),  # requires positive pressure heads
                label=data.loc[layer, "staringseriesblock"],
                color=COLORS_SOILS[data.loc[layer, "staringseriesblock"]],
                linestyle=linestyles[staring_count],
            )

            # Increase staring blocks counter
            staring_count += 1

        # SUBPLOT 4: Soil texture
        pclay = data.loc[layer, "lutitecontent"]
        psilt = data.loc[layer, "siltcontent"]
        psand = 100 - pclay - psilt
        bot = 0
        for soilgroup, fraction in zip(
            ["<2µm", ">2µm\n<50µm", ">50µm"], [pclay, psilt, psand]
        ):
            # Plot fractions
            ax4.bar(
                x=count,
                height=fraction,
                bottom=bot,
                width=0.8,
                color=COLORS_SOILGROUPS[soilgroup],
                edgecolor="dimgrey",
            )
            # Plot label
            ax4.text(
                x=count,
                y=bot + fraction / 2,
                s=soilgroup,
                ha="center",
                va="center",
                fontsize=7,
                color="dimgrey",
            )
            bot += fraction

        # SUBPLOT 5: Soil organic matter
        ax5.bar(
            x=count,
            height=data.loc[layer, "organicmattercontent"],
            width=0.8,
            color="saddlebrown",
            edgecolor="dimgrey",
        )

    # Layout subplot 1
    ax1.set_ylim(-120, 0)
    ax1.set_yticks(np.arange(-120, 10, 10))
    ax1.set_ylabel("Depth [cm]")
    ax1.set_xlim(-1, 1)
    ax1.set_xticks([0], [None])
    ax1.set_axisbelow(True)
    ax1.grid(color="lightgrey")
    ax1.set_title("Soil profile", fontsize=8)

    # Layout subplot 2
    ax2.legend()
    ax2.set_xscale("symlog")
    ax2.set_xlim(-1e-1, -1e6)
    ax2.set_xticks(np.logspace(-1, 6, 8) * -1, [None] * 8)
    ax2.set_ylabel("Water content\n[$cm^3/cm^{3}$]")
    ax2.set_title("Soil Water Retention & Conductivity Curve", fontsize=8)
    ax2.set_axisbelow(True)
    ax2.grid(color="lightgrey")

    # Layout subplot 3
    ax3.legend()
    ax3.set_xscale("symlog")
    ax3.set_xlim(-1e-1, -1e6)
    ax3.set_xlabel("Pressure head [cm]")
    ax3.set_yscale("log")
    ax3.set_ylim(1e-10, 1e3)
    ax3.set_ylabel("Hydraulic conductivity\n[$cm/d$]")
    ax3.set_axisbelow(True)
    ax3.grid(color="lightgrey")

    # Layout subplot 4
    ax4.set_ylim(0, 100)
    ax4.set_ylabel("Particle size fraction [%]")
    ax4.set_yticks(np.arange(0, 110, 10))
    ax4.set_title("Soil Texture & Organic Matter Content", fontsize=8)
    ax4.set_xticks(
        range(1, count + 1),
        [None] * count,
    )
    ax4.set_axisbelow(True)
    ax4.grid(color="lightgrey")

    # Layout subplot 5
    ax5.set_ylabel("Organic matter content [%]")
    # ax5.set_title("Soil organic matter", fontsize=8)
    ax5.set_xlabel("Soil horizon")
    ax5.set_xticks(
        range(1, count + 1),
    )
    ax5.set_axisbelow(True)
    ax5.grid(color="lightgrey")

    # Get title of plot for input soil or bofek cluster soil
    title = (
        "Soil profile "
        + str(soilprofile.index)
        + ": "
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
