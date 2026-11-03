from pytest_conda_solvers import data


def test_load_data_file():
    index = data.load_data_file("channel-1_non-noarch.json")
    # 1149 in conda upstream records, + scipy-0.11.0-np17py33_x0, from track-features tests
    assert len(index) == 1150
    random_entry_key = "numpy-1.7.0rc1-py33_p0.tar.bz2"
    random_entry_value = {
        "build": "py33_p0",
        "build_number": 0,
        "depends": [
            "mkl 10.3",
            "nose",
            "python 3.3*",
        ],
        "features": "mkl",
        "md5": "4976525dda67fb55578b8763dd2c04b1",
        "name": "numpy",
        "pub_date": "2013-01-29",
        "requires": [
            "mkl 10.3",
            "nose 1.2.1",
            "python 3.3",
        ],
        "version": "1.7.0rc1",
    }
    assert index[random_entry_key] == random_entry_value


def test_exported_channels_expose_features_as_track_features():
    raw = data.get_channel_repodata("channel-1", "linux-64", "repodata.json")
    exported = data.get_channel_repodata(
        "channel-1", "linux-64", "repodata.json", features_as_track_features=True
    )
    raw_packages, exported_packages = raw["packages"], exported["packages"]
    assert set(exported_packages) == set(raw_packages)
    mkl_numpy = "numpy-1.7.0rc1-py33_p0.tar.bz2"
    assert raw_packages[mkl_numpy]["features"] == "mkl"
    assert "features" not in exported_packages[mkl_numpy]
    assert exported_packages[mkl_numpy]["track_features"] == "mkl"
    with_features = {fn for fn, meta in raw_packages.items() if "features" in meta}
    assert mkl_numpy in with_features
    for fn in with_features:
        assert "features" not in exported_packages[fn]
        assert exported_packages[fn]["track_features"] == raw_packages[fn]["features"]
        assert {
            key: value
            for key, value in exported_packages[fn].items()
            if key != "track_features"
        } == {
            key: value for key, value in raw_packages[fn].items() if key != "features"
        }
    untouched = set(raw_packages) - with_features
    assert any("track_features" in raw_packages[fn] for fn in untouched)
    for fn in untouched:
        assert exported_packages[fn] == raw_packages[fn]


def test_simple_environment_channels_keep_features():
    assert "channel-10" not in data.EXPORTED_CHANNELS
    raw = data.get_channel_repodata("channel-10", "linux-64", "repodata.json")
    exported = data.get_channel_repodata(
        "channel-10", "linux-64", "repodata.json", features_as_track_features=True
    )
    assert any("features" in meta for meta in raw["packages"].values())
    assert exported["packages"] == raw["packages"]
