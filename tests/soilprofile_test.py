from pathlib import Path
import warnings

import pytest
from pandas.testing import assert_frame_equal
from pandas import read_csv, DataFrame

from dutchsoils import SoilProfile


def test_from_bofekcluster():
    # Test with correct input
    SoilProfile.from_bofekcluster(3012)
    SoilProfile.from_bofekcluster([3012, 1008])

    # Test with incorrect input: wrong bofek
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_bofekcluster(999999)
    assert "Given bofek cluster number 999999 does not exist." in str(exc_info.value)

    # Test with incorrect input: second element is wrong
    with warnings.catch_warnings(record=True) as w:
        result = SoilProfile.from_bofekcluster([3012, 999999])
    assert len(w) == 1
    assert "Given BOFEK cluster 999999 is invalid." in str(w[0].message)
    assert result[1] is None


def test_from_index():
    # Test with correct input
    SoilProfile.from_index(90110280)
    SoilProfile.from_index([90110280, 3030])

    # Test with incorrect input: wrong index
    with pytest.raises(ValueError) as exc_info:
        SoilProfile.from_index(999999)
    assert "Given soilprofile index 999999 does not exist." in str(exc_info.value)

    # Test with incorrect input: second element is wrong
    with warnings.catch_warnings(record=True) as w:
        result = SoilProfile.from_index([3030, 999999])
    assert len(w) == 1
    assert "Given index 999999 is invalid." in str(w[0].message)
    assert result[1] is None


def test_from_location():
    pass


def test_initialisation_soilprofile_correctinput():
    # soil id
    SoilProfile(index=90110280)

    # bofek cluster
    SoilProfile(bofekcluster=3002)


def test_initialisation_soilprofile_wronginput():
    # Test with incorrect input: no input
    with pytest.raises(ValueError) as exc_info:
        SoilProfile()
    assert "Provide either a soilprofile index or a bofek cluster number." in str(
        exc_info.value
    )

    # Test with incorrect input: too much input
    with pytest.raises(ValueError) as exc_info:
        SoilProfile(bofekcluster=1001, index=1001)
    assert (
        "Provide either a soilprofile index or a bofek cluster number, not both."
        in str(exc_info.value)
    )

    # Test with incorrect input: wrong soil id
    with pytest.raises(ValueError) as exc_info:
        SoilProfile(index=999999)
    assert "Given soilprofile index 999999 does not exist." in str(exc_info.value)

    # Test with incorrect input: wrong bofek
    with pytest.raises(ValueError) as exc_info:
        SoilProfile(bofekcluster=999999)
    assert "Given bofek cluster number 999999 does not exist." in str(exc_info.value)


def test_get_area():
    # Get soilprofile
    sp = SoilProfile(bofekcluster=1008)

    # Get area
    sp.get_area()
    # TODO


def test_getdatahorizons():
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
