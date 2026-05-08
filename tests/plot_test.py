if __name__ == "__main__":
    import matplotlib.pyplot as plt

    import dutchsoils as ds

    # sp = ds.SoilProfile.from_bofekcluster(1001)
    # sp = ds.SoilProfile.from_bofekcluster(2001)
    # sp = ds.SoilProfile.from_bofekcluster(3001)
    # sp = ds.SoilProfile.from_bofekcluster(4001)
    sp = ds.SoilProfile.from_bofekcluster(5001)
    # sp = ds.SoilProfile.from_bofekcluster(1008)
    fig = sp.plot(which="all")
    # fig = sp.plot(which="chemical")
    # fig = sp.plot(which="hydraulic")
    # fig = sp.plot(which="physical")
    plt.show()
