import warnings
from pathlib import Path

import pytest
from numpy import array
from pandas import DataFrame, read_csv
from pandas.testing import assert_frame_equal

from dutchsoils import SoilProfile


def test_from_bofekcluster():
    # Test with correct input
    SoilProfile.from_bofekcluster(3012)
    SoilProfile.from_bofekcluster([3012, 1008])

    # Test with incorrect input: wrong bofek
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_bofekcluster(999999)
    assert "Given bofek cluster number '999999' does not exist." in str(exc_info.value)

    # Test with incorrect input: second element is wrong
    with warnings.catch_warnings(record=True) as w:
        result = SoilProfile.from_bofekcluster([3012, 999999])
    assert len(w) == 1
    assert "Given bofekcluster '999999' is invalid, 'None' returned." in str(
        w[0].message
    )
    assert result[1] is None


def test_from_index():
    # Test with correct input
    SoilProfile.from_index(90110280)
    SoilProfile.from_index([90110280, 3030])

    # Test with incorrect input: wrong index
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_index(999999)
    assert "Given soilprofile index '999999' does not exist." in str(exc_info.value)

    # Test with incorrect input: second element is wrong
    with warnings.catch_warnings(record=True) as w:
        result = SoilProfile.from_index([3030, 999999])
    assert len(w) == 1
    assert "Given index '999999' is invalid, 'None' returned." in str(w[0].message)
    assert result[1] is None


def test_from_code():
    # Test with correct input
    SoilProfile.from_code("Zn21")
    SoilProfile.from_code(["Zn21", "bEZ23"])

    # Test with incorrect input: wrong index
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_code("test")
    assert "Given soilprofile code 'test' does not exist." in str(exc_info.value)

    # Test with incorrect input: second element is wrong
    with warnings.catch_warnings(record=True) as w:
        result = SoilProfile.from_code(["Zn21", "test"])
    assert len(w) == 1
    assert "Given code 'test' is invalid, 'None' returned." in str(w[0].message)
    assert result[1] is None


def test_from_location():
    # Test with correct input: single location
    sp = SoilProfile.from_location(
        x=200234,
        y=507675,
    )
    assert sp.index == 1230

    # Test with correct input: single location, other CRS
    sp = SoilProfile.from_location(
        x=51.350794,
        y=3.574202,
        crs="EPSG:4326",
    )
    assert sp.index == 90115320

    # Test with location without soil profile: x=0,y=0
    with warnings.catch_warnings(record=True) as w:
        sp = SoilProfile.from_location(x=0, y=0)
    assert len(w) == 1
    assert "No soil information available for this location: x = 0, y = 0." in str(
        w[0].message
    )
    assert issubclass(w[0].category, UserWarning)
    assert sp is None

    # Test with location without soil profile: buildup area
    with warnings.catch_warnings(record=True) as w:
        sp = SoilProfile.from_location(x=185848.5, y=320060.5)
    assert len(w) == 1
    assert (
        "No soil information available for this location: x = 185848.5, y = 320060.5."
        in str(w[0].message)
    )
    assert issubclass(w[0].category, UserWarning)
    assert sp is None

    # Test with location without soil profile: digged area
    with warnings.catch_warnings(record=True) as w:
        sp = SoilProfile.from_location(x=183758.4, y=319317.1)
    assert len(w) == 1
    assert (
        "No soil information available for this location: x = 183758.4, y = 319317.1."
        in str(w[0].message)
    )
    assert issubclass(w[0].category, UserWarning)
    assert sp is None

    # Test with correct input: multiple locations
    # Zuid-Limburg, Texel, Zeeland
    x_test = [187859, 114373, 28193.4]
    y_test = [321963, 567756, 375309.9]

    sps = SoilProfile.from_location(
        x=x_test,
        y=y_test,
    )
    assert [sp.index for sp in sps] == [5030, 90110186, 90115320]

    # Test with one of the locations not having a soil profile
    with warnings.catch_warnings(record=True) as w:
        sp = SoilProfile.from_location(
            x=x_test + [0],
            y=y_test + [0],
        )
    assert len(w) == 1
    assert "No soil information available for this location: x = 0, y = 0." in str(
        w[0].message
    )
    assert issubclass(w[0].category, UserWarning)
    assert sp[-1] is None

    # Test with other forms of iterables
    # np array
    sps = SoilProfile.from_location(
        x=array(x_test),
        y=array(y_test),
    )
    assert [sp.index for sp in sps] == [5030, 90110186, 90115320]

    # pd dataframe
    df = DataFrame(index=x_test, data=y_test, columns=["y_test"])
    sps = SoilProfile.from_location(
        x=df.index,
        y=df["y_test"],
    )
    assert [sp.index for sp in sps] == [5030, 90110186, 90115320]

    # Test with incorrect input: X is list, Y not
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_location(
            x=x_test,
            y=321963,
        )
    assert "X is iterable while Y is not." in str(exc_info.value)

    # Test with incorrect input: Y is list, X not
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_location(
            x=187859,
            y=y_test,
        )
    assert "Y is iterable while X is not." in str(exc_info.value)

    # Test with incorrect input: X and Y do not have the same length
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_location(
            x=x_test[1:],
            y=y_test,
        )
    assert (
        "List of X and Y coordinates do not have the same length (x: 2, y: 3)."
        in str(exc_info.value)
    )

    # Test with incorrect input: X-coordinate in list is a string
    xx = x_test + ["test"]
    yy = y_test + [y_test[-1]]
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_location(
            x=xx,
            y=yy,
        )
    assert "The 3th element of the X-coordinates is neither a float or int." in str(
        exc_info.value
    )

    # Test with incorrect input: Y-coordinate in list is a string
    xx = x_test + [x_test[-1]]
    yy = y_test + ["test"]
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_location(
            x=xx,
            y=yy,
        )
    assert "The 3th element of the Y-coordinates is neither a float or int." in str(
        exc_info.value
    )

    # Test with incorrect input: X-coordinate is a string
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_location(
            x="test",
            y=y_test[0],
        )
    assert "The X-coordinate 'test' is neither a float or int." in str(exc_info.value)

    # Test with incorrect input: Y-coordinate is a string
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_location(
            x=x_test[0],
            y="test",
        )
    assert "The Y-coordinate 'test' is neither a float or int." in str(exc_info.value)

    # Test with non-existing CRS
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_location(x=x_test[0], y=y_test[0], crs="test")
    assert "Unsupported CRS namespace" in str(exc_info.value)


def test_initialisation_soilprofile():
    # CORRECT INPUT
    # soil id
    SoilProfile(index=90110280)

    # soil code
    SoilProfile(code="Zn21")

    # bofek cluster
    SoilProfile(bofekcluster=3002)

    # WRONG INPUT
    # Test with incorrect input: no input
    with pytest.raises(ValueError) as exc_info:
        SoilProfile()
    assert "Provide a soilprofile index or code or a bofek cluster number." in str(
        exc_info.value
    )

    # Test with incorrect input: too much input
    with pytest.raises(ValueError) as exc_info:
        SoilProfile(bofekcluster=1001, index=1001)
    assert (
        "Provide only one input: soilprofile index, code or a bofek cluster number, not multiple."
        in str(exc_info.value)
    )

    # Test with incorrect input: wrong soil id
    with pytest.raises(ValueError) as exc_info:
        SoilProfile(index=999999)
    assert "Given soilprofile index '999999' does not exist." in str(exc_info.value)

    # Test with incorrect input: wrong soil code
    with pytest.raises(ValueError) as exc_info:
        SoilProfile(code="test")
    assert "Given soilprofile code 'test' does not exist." in str(exc_info.value)

    # Test with incorrect input: wrong bofek
    with pytest.raises(ValueError) as exc_info:
        SoilProfile(bofekcluster=999999)
    assert "Given bofek cluster number '999999' does not exist." in str(exc_info.value)


def test_get_area():
    # Get soilprofile
    sp = SoilProfile(bofekcluster=3015)

    # Get area from profile
    area = sp.get_area()
    assert area == 186782.5653

    # Get area from bofekcluster
    area = sp.get_area(which="bofekcluster")
    assert area == 335205.67601799994


def test_get_data_horizons():
    # Get soilprofile
    sp = SoilProfile(bofekcluster=1008)

    # Test which=all
    # Data to test
    data_test = sp.get_data_horizons()
    # Reference data
    path = Path(__file__).parent / "data/soilprofile90110280_horizondata_all.csv"
    data_ref = read_csv(path)
    # Test
    assert_frame_equal(
        data_test,
        data_ref,
        check_dtype=False,
    )

    # Test which=hydraulic
    # Data to test
    data_test = sp.get_data_horizons(which="hydraulic")
    # Reference data
    path = Path(__file__).parent / "data/soilprofile90110280_horizondata_hydraulic.csv"
    data_ref = read_csv(path)
    # Test
    assert_frame_equal(
        data_test,
        data_ref,
        check_dtype=False,
    )

    # Test which=physical
    # Data to test
    data_test = sp.get_data_horizons(which="physical")
    # Reference data
    path = Path(__file__).parent / "data/soilprofile90110280_horizondata_physical.csv"
    data_ref = read_csv(path)
    # Test
    assert_frame_equal(
        data_test,
        data_ref,
        check_dtype=False,
    )

    # Test which=chemical
    # Data to test
    data_test = sp.get_data_horizons(which="chemical")
    # Reference data
    path = Path(__file__).parent / "data/soilprofile90110280_horizondata_chemical.csv"
    data_ref = read_csv(path)
    # Test
    assert_frame_equal(
        data_test,
        data_ref,
        check_dtype=False,
    )

    # Test which=wrong
    with pytest.raises(ValueError) as exc_info:
        sp.get_data_horizons(which="wrong")
    assert (
        "Unvalid value for 'which': wrong. Choose between 'all', 'hydraulic', 'physical', 'chemical'."
        in str(exc_info.value)
    )


def test_swapsoilprofile():
    # Get soil profile
    sp = SoilProfile(bofekcluster=1001)

    # Test for discretisation that aligns well with soil physical layering
    # Get correct dataframes
    path = Path(__file__).parent / "data/bofek1001_sp1.csv"
    sp_ref1 = read_csv(path)

    # Get output to test
    sp_test1 = DataFrame(
        sp.get_swapinput_profile(
            discretisation_depths=[50, 30, 60, 60, 100],
            discretisation_compheights=[1, 2, 5, 10, 20],
        )
    )

    # Test if frames are equal
    assert_frame_equal(
        sp_ref1,
        sp_test1,
        check_dtype=False,
    )

    # Test for discretisation that aligns not with soil physical layering
    # Get correct dataframes
    path = Path(__file__).parent / "data/bofek1001_sp2.csv"
    sp_ref2 = read_csv(path)

    # Get output to test
    sp_test2 = DataFrame(
        sp.get_swapinput_profile(
            discretisation_depths=[10, 20, 80, 90, 100],
            discretisation_compheights=[1, 2, 5, 10, 20],
        )
    )

    # Test if frames are equal
    assert_frame_equal(
        sp_ref2,
        sp_test2,
        check_dtype=False,
    )


def test_swaphydraulicparams():
    # Get correct dataframe
    path = Path(__file__).parent / "data/bofek1001_hf.csv"
    hf_ref = read_csv(path)

    # Get soil profile
    sp = SoilProfile(bofekcluster=1001)

    # Get output to test
    hf_test = DataFrame(sp.get_swapinput_hydraulicparams())

    # Test if frames are equal
    assert_frame_equal(
        hf_ref,
        hf_test,
        check_dtype=False,
    )


def test_swapfractions():
    # Get correct dataframe
    path = Path(__file__).parent / "data/bofek1001_frac.csv"
    frac_ref = read_csv(path)

    # Get soil profile
    sp = SoilProfile(bofekcluster=1001)

    # Get output to test
    frac_test = DataFrame(sp.get_swapinput_fractions())

    # Test if frames are equal
    assert_frame_equal(
        frac_ref,
        frac_test,
        check_dtype=False,
    )


def test_swapcofani():
    # Get correct result
    cof_ref = [1.0, 1.0, 1.0, 1.0]

    # Get soil profile
    sp = SoilProfile(bofekcluster=1001)

    # Get output to test
    cof_test = sp.get_swapinput_cofani()

    # Test if frames are equal
    assert cof_ref == cof_test


def test_plot():
    SoilProfile(bofekcluster=3015).plot()
    SoilProfile(index=1050).plot()
