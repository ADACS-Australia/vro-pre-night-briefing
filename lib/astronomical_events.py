import pandas as pd
from astropy.coordinates import EarthLocation
from astropy.time import Time
from rubin_sim.scheduler.modelObservatory import Model_observatory

from plotting.settings import TIMEZONE, scheduler, NIGHT


def all_times(mjds, site):
    """Given a series of mjds, return a DataFrame with all interesting time formats."""

    mjds = pd.Series(mjds)
    ap_times = Time(mjds, format="mjd", scale="utc", location=site)
    time_df = pd.DataFrame(
        {
            "mjd": ap_times.mjd,
            "LST": ap_times.sidereal_time("apparent").deg,
            "UTC": pd.to_datetime(ap_times.iso).tz_localize("UTC"),
        },
        index=mjds.index,
    )
    time_df["Civil"] = time_df["UTC"].dt.tz_convert(TIMEZONE)
    return time_df


def generate_astronomical_events():
    observatory = Model_observatory(mjd_start=NIGHT.mjd - 1)
    site = EarthLocation.from_geodetic(
        observatory.site.longitude, observatory.site.latitude, observatory.site.height
    )

    sun_events = ("sun_n12_setting", "sun_n18_setting", "sun_n18_rising", "sun_n12_rising")
    moon_events = ("moonrise", "moonset")
    events = sun_events + moon_events
    mjds = pd.Series(
        [getattr(scheduler.conditions, event) for event in events], index=events
    )

    return all_times(mjds, site)
