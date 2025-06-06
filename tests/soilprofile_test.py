from pathlib import Path

import pytest
from pandas.testing import assert_frame_equal
from pandas import read_csv, DataFrame

from dutchsoils import SoilProfile


def test_getdata_correctinput():
    # soil id
    data_test = SoilProfile(soilprofile_index=90110280).get_data()
    path = Path(__file__).parent / "data/soil_id_90110280.csv"
    data_ref = read_csv(path)
    assert_frame_equal(
        data_test,
        data_ref,
        check_dtype=False,
    )

    # bofek cluster
    data_test = SoilProfile(bofek_cluster=3002).get_data()
    path = Path(__file__).parent / "data/bofek_cluster_3002.csv"
    data_ref = read_csv(path)
    assert_frame_equal(
        data_test,
        data_ref,
        check_dtype=False,
    )


def test_getdata_wronginput():
    # Test with incorrect input: no input
    with pytest.raises(ValueError) as exc_info:
        SoilProfile().get_data()
    assert "No data available" in str(exc_info.value)

    # Test with incorrect input: wrong soil id
    with pytest.raises(ValueError) as exc_info:
        SoilProfile(soilprofile_index=999999).get_data()
    assert "No data available" in str(exc_info.value)

    # Test with incorrect input: wrong bofek
    with pytest.raises(ValueError) as exc_info:
        SoilProfile(bofek_cluster=999999).get_data()
    assert "No data available" in str(exc_info.value)


def test_swapsoilprofile():
    # Get soil profile
    sp = SoilProfile(bofek_cluster=1001)

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
    sp = SoilProfile(bofek_cluster=1001)

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
    sp = SoilProfile(bofek_cluster=1001)

    # Get output to test
    frac_test = DataFrame(sp.get_swapinput_fractions())

    print(frac_ref)
    print("\n")
    print(frac_test)

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
    sp = SoilProfile(bofek_cluster=1001)

    # Get output to test
    cof_test = sp.get_swapinput_cofani()

    # Test if frames are equal
    assert cof_ref == cof_test


def test_plot():
    SoilProfile(bofek_cluster=3015).plot()
    SoilProfile(soilprofile_index=1050).plot()
