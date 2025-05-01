# Import packages
import os
import zipfile

import pandas as pd
import geopandas as gpd

# Set the directories of the raw and processed data
DIR_RAW = os.path.join("data", "raw")
DIR_PROC = os.path.join("data", "processed")


def unpack_zip_bofek():
    # Import the py7zr package
    # This package is used to unpack the 7z files
    import py7zr

    # Unpack the zip file containing the BOFEK 2020 scripts
    loc_src = os.path.join(DIR_RAW, "BOFEK2020_v1.0_scripts.zip")
    loc_dest = os.path.join(DIR_RAW, "bofek_scripts")
    with zipfile.ZipFile(loc_src, 'r') as zip_ref:
        zip_ref.extractall(loc_dest)

    # Unpack the zip file containing the BOFEK 2020 map again
    loc_src = os.path.join(DIR_RAW, "BOFEK2020_GIS.zip")
    loc_dest = os.path.join(DIR_RAW, "bofek_gis")
    with zipfile.ZipFile(loc_src, 'r') as zip_ref:
        zip_ref.extractall(loc_dest)
    # It requires double unpacking
    loc_src = os.path.join(DIR_RAW, "bofek_gis", "BOFEK2020_GIS.7z")
    loc_dest = os.path.join(DIR_RAW, "bofek_gis")
    with py7zr.SevenZipFile(loc_src, mode='r') as z:
        z.extractall(loc_dest)


def read_dutchsoilmap():
    """
    Read the Dutch soil map data from a geopackage file and process it.
    The function reads the following layers from the geopackage:
    - normalsoilprofiles: Contains the names of the soil units and their corresponding inspire IDs.
    - normalsoilprofiles_landuse: Contains the land use information for each soil profile.
    - soil_units: Contains the classification of the soil units.
    - soilhorizon: Contains the soil horizon information, including various properties of the soil layers.
    The function processes the data by setting appropriate indices and selecting relevant columns.
    The function returns four DataFrames:
    - names: Contains the soil unit names and their corresponding inspire IDs.
    - landuse: Contains the land use information for each soil profile.
    - classification: Contains the classification of the soil units.
    - soilprofiles: Contains the soil horizon information, including various properties of the soil layers.
    """
    # Read geopackage
    loc = os.path.join(DIR_RAW, "BRO_DownloadBodemkaart.gpkg")

    # Read name layer
    names = gpd.read_file(loc, layer="normalsoilprofiles")
    names.index = [int(row.split(".")[-1]) for row in names["inspireid"]]
    names = names.loc[:, ["soilunit", "othersoilname"]]

    # Read landuse layer
    landuse = gpd.read_file(loc, layer="normalsoilprofiles_landuse")
    landuse = landuse.set_index("normalsoilprofile_id")

    # Read classification layer
    classification = gpd.read_file(loc, layer="soil_units")
    classification = classification.set_index("code")
    classification = classification.loc[:, ["mainsoilclassification"]]

    # Read soil profiles layer
    soilprofiles = gpd.read_file(loc, layer="soilhorizon")
    columns_keep = [
        "normalsoilprofile_id",
        "layernumber",
        "faohorizonnotation",
        "lowervalue",
        "uppervalue",
        "staringseriesblock",
        "organicmattercontent",
        "lutitecontent",
        "siltcontent",
        "density",
    ]
    soilprofiles = soilprofiles.loc[:, columns_keep]

    return names, landuse, classification, soilprofiles


def read_staring():
    """
    This function reads the Staring series data from the scripts used for the BOFEK 2020 clustering 
    and the names of the Staring classes from the separate CSV file.
    The function processes the data by selecting relevant columns and setting appropriate indices.
    The function returns two DataFrames: one for the Staring series data and one for the Staring class names."""
    
    # Read Staringreeks data
    loc = os.path.join(DIR_RAW, "bofek_scripts", "1_CalcAllPars", "Data", "StaringReeksPARS_2018.csv")
    staring = pd.read_csv(loc)

    # Omit i and R2 column
    staring = staring.loc[:, staring.columns[1:-1].values]  
    
    # Get staringclassblock as index
    # replace B and O with 1 and 2 and cast string to int
    staring.index = [int({"B": "1", "O": "2"}[row[0]] +  row[-2:]) for row in staring["Name"]]

    # Load Staringreeks names
    loc = os.path.join(DIR_RAW, "Staringreeks_namen.csv")
    staring_names = pd.read_csv(loc)
    staring_names = staring_names.set_index("id")
    
    return staring, staring_names


def read_bofek():
    """
    This function reads the BOFEK cluster numbers and names from the CSV files.
    The cluster numbers are read from the all_results_formatted_95.csv file, and the cluster names
    are read from the Clusterhoofden.xlsx file. The function processes the data by selecting relevant columns
    and setting appropriate indices.
    The function returns two DataFrames: one for the cluster numbers and one for the cluster names.
    """
    # Read BOFEK cluster numbers
    loc = os.path.join(DIR_RAW, "bofek_scripts", "3_Clustering", "Output", "")
    bofek = pd.read_csv(loc + "all_results_formatted_95.csv")

    # Only keep relevant columns
    bofek = bofek.loc[:, ["iProfile", "clust1", "dominant", "Areaal"]]
    bofek = bofek.set_index("iProfile")

    # Read BOFEK cluster names
    loc = os.path.join(DIR_RAW, "bofek_gis", "GIS", "BOFEK2020_bestanden", "tabellen", "Clusterhoofden.xlsx")
    bofek_names = pd.read_excel(loc)

    # Only keep names of BOFEK cluster
    bofek_names = bofek_names.loc[:, ["clust1", "Omschrijving cluster"]]
    # Drop empty rows
    bofek_names = bofek_names.dropna()
    # Cast BOFEK cluster to int
    bofek_names["clust1"] = [int(row) for row in bofek_names.loc[:, "clust1"]]
    bofek_names = bofek_names.set_index("clust1")

    return bofek, bofek_names


def merge_data(soilprofiles, names, landuse, classification, staring, staring_names, bofek, bofek_names):
    # Main dataframe is soilprofiles

    # Merge soilprofile names
    merged = soilprofiles.join(
        names,
        on="normalsoilprofile_id"
    )

    # Merge landuses
    merged = merged.join(
        landuse,
        on="normalsoilprofile_id"
    )

    # Merge classification
    merged = merged.join(
        classification,
        on="soilunit"
    )

    # Merge staringclass
    merged = merged.join(
        staring,
        on="staringseriesblock"
    )

    # Merge staringclass names
    merged = merged.join(
        staring_names,
        on="Name"
    )

    # Merge with bofek cluster numbers
    merged = merged.join(
        bofek,
        on="normalsoilprofile_id"
    )

    # Merge with bofek cluster names
    merged = merged.join(
        bofek_names,
        on="clust1"
    )
    
    return merged


def format_data(merged):
    """
    This function formats the merged data by reordering columns and renaming them.
    The function returns the formatted DataFrame.
    """
    # Reorder columns
    formatted = merged[[
        "normalsoilprofile_id",
        "soilunit",
        "othersoilname",
        "mainsoilclassification",
        "landuse",
        "clust1",
        "dominant",
        "Omschrijving cluster",
        "Areaal",
        "layernumber",
        "faohorizonnotation",
        "lowervalue",
        "uppervalue",
        "staringseriesblock",
        "Name",
        "description",
        "label",
        "organicmattercontent",
        "lutitecontent",
        "siltcontent",
        "density",
        "WCr",
        "WCs",
        "Alpha",
        "Npar",
        "Lambda",
        "Ksfit",
    ]]

    # Rename columns
    formatted = formatted.rename(
        columns={
            "normalsoilprofile_id": "soil_id",
            "othersoilname": "soil_name",
            "mainsoilclassification": "soil_classification",
            "landuse": "soil_landuse",
            "clust1": "bofek_cluster",
            "dominant": "bofek_dominant",
            "Omschrijving cluster": "bofek_name",
            "Areaal": "bofek_area",
            "layernumber": "layer_number",
            "faohorizonnotation": "layer_faohorizon",
            "lowervalue": "layer_ztop",
            "uppervalue": "layer_zbot",
            "staringseriesblock": "layer_staringclass",
            "Name": "layer_staringclassname",
            "description": "layer_staringdescription",
            "label": "layer_staringlabel",
            "organicmattercontent": "layer_percentileorgmat",
            "lutitecontent": "layer_percentileclay",
            "siltcontent": "layer_percentilesilt",
            "density": "layer_bulkdensity",
            "Name": "layer_staringclassname",
            "WCr": "layer_wcres",
            "WCs": "layer_wcsat",
            "Alpha": "layer_VGalfa",
            "Npar": "layer_VGnpar",
            "Lambda": "layer_VGlexp",
            "Ksfit": "layer_ksatfit",
        }
    )

    return formatted

def write_data(formatted):
    """
    This function writes the formatted data to a CSV file in the processed data directory.
    The function does not return anything.
    """
    # Write data
    formatted.to_csv(
        os.path.join(DIR_PROC, "soilprofiles_BodemkaartBofek.csv"),
        index=False
    )


if __name__ == "__main__":
    # Unpack the bofek zip file
    unpack_zip_bofek()
    
    # Read data
    names, landuse, classification, soilprofiles = read_dutchsoilmap()
    staring, staring_names = read_staring()
    bofek, bofek_names = read_bofek()

    # Merge data
    merged = merge_data(soilprofiles, names, landuse, classification, staring, staring_names, bofek, bofek_names)

    # Format data
    formatted = format_data(merged)

    # Write data
    write_data(formatted)
    print("Data processing complete. The data has been written to the processed data directory.")
