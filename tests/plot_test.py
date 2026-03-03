if __name__ == "__main__":
    import matplotlib.pyplot as plt

    import dutchsoils as ds

    sp = ds.SoilProfile.from_bofekcluster(5001)
    # sp = ds.SoilProfile.from_index(1255)
    fig = sp.plot(which="all")
    plt.show()
