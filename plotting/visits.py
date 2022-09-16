import sqlite3
from concurrent.futures import ThreadPoolExecutor

import bokeh.layouts
import bokeh.models
import bokeh.palettes
import bokeh.plotting
import bokeh.transform
import healpy as hp
import numpy as np
import pandas as pd
from rubin_sim.scheduler.modelObservatory import Model_observatory

from plotting.settings import BAND_COLOURS, NIGHT, scheduler, BASELINE_SIM_DB_FNAME
from plotting.spheremap import Planisphere, ArmillarySphere

worker = ThreadPoolExecutor()


def skymaps(visits, footprint, conditions):
    band_sizes = {'u': 15, 'g': 13, 'r': 11, 'i': 9, 'z': 7, 'y': 5}

    psphere = Planisphere(mjd=conditions.mjd)

    asphere = ArmillarySphere(mjd=conditions.mjd)
    cmap = bokeh.transform.linear_cmap("value", "Greys256", 8, 0)
    nside = hp.npix2nside(footprint.shape[0])
    healpix_ds, cmap, glyph = asphere.add_healpix(footprint, nside=nside, cmap=cmap)
    psphere.add_healpix(healpix_ds, nside=nside, cmap=cmap)
    for band in 'ugrizy':
        band_visits = visits.query(f"filter == '{band}'")
        visit_ds = asphere.add_marker(
            ra=band_visits.fieldRA,
            decl=band_visits.fieldDec,
            glyph_size=band_sizes[band],
            name=band_visits.index.values,
            min_mjd=band_visits.observationStartMJD.values,
            circle_kwargs={"fill_alpha": "in_mjd_window", "fill_color": BAND_COLOURS[band], 'line_alpha': 0},
        )
        psphere.add_marker(data_source=visit_ds,
                           glyph_size=band_sizes[band],
                           name=band_visits.index.values,
                           min_mjd=band_visits.observationStartMJD.values,
                           circle_kwargs={"fill_alpha": "in_mjd_window", "fill_color": BAND_COLOURS[band],
                                          'line_alpha': 0},
                           )
    asphere.decorate()
    psphere.decorate()
    horizon_ds = asphere.add_horizon()
    psphere.add_horizon(data_source=horizon_ds)
    horizon70_ds = asphere.add_horizon(zd=70, line_kwargs={"color": "red", "line_width": 2})
    psphere.add_horizon(data_source=horizon70_ds, line_kwargs={"color": "red", "line_width": 2})
    sun_ds = asphere.add_marker(
        ra=np.degrees(conditions.sunRA),
        decl=np.degrees(conditions.sunDec),
        name="Sun",
        glyph_size=15,
        circle_kwargs={"color": "yellow", "fill_alpha": 1},
    )
    psphere.add_marker(data_source=sun_ds,
                       name="Sun",
                       glyph_size=15,
                       circle_kwargs={"color": "yellow", "fill_alpha": 1},
                       )

    moon_ds = asphere.add_marker(
        ra=np.degrees(conditions.moonRA),
        decl=np.degrees(conditions.moonDec),
        name="Moon",
        glyph_size=15,
        circle_kwargs={"color": "orange", "fill_alpha": 0.8},
    )
    psphere.add_marker(
        data_source=moon_ds,
        name="Moon",
        glyph_size=15,
        circle_kwargs={"color": "orange", "fill_alpha": 0.8},
    )

    asphere.sliders["mjd"].start = conditions.sun_n12_setting
    asphere.sliders["mjd"].end = conditions.sun_n12_rising

    return [asphere.figure, psphere.figure]


def get_footprint():
    """Extract the footprint from a survey."""
    # This is a hack, good enough for example code, not for production.

    # Look through the scheduler to find a blob survey that has a footprint basis function
    for survey_tier in scheduler.survey_lists:
        for survey in survey_tier:
            if survey.__class__.__name__ in ("Blob_survey", "Greedy_survey"):
                for basis_function in survey.basis_functions:
                    if basis_function.__class__.__name__.startswith("Footprint"):
                        footprint = np.sum(basis_function.footprint.footprints, axis=0)
                        break

    footprint[footprint == 0] = np.nan
    return footprint


def make_visit():
    try:
        # Set the site of the observatory:
        observatory = Model_observatory(mjd_start=NIGHT.mjd - 1)

        # Initialaze the time to the start of the night. Start by getting a conditions object for some time in the night
        # in question, which will have the sunset time:
        observatory.mjd = NIGHT.mjd
        conditions = observatory.return_conditions()

        # Now that we have a conditions object in the night we want, get the sunset time from it to get the specific time
        # for the start of observing:
        start_mjd = conditions.sun_n12_setting

        # Now, create a conditions object for this specific time we want, and update the scheduler for that time:
        observatory.mjd = start_mjd
        conditions = observatory.return_conditions()
        scheduler.update_conditions(conditions)

        with sqlite3.connect(BASELINE_SIM_DB_FNAME) as sim_connection:
            visits = pd.read_sql_query(
                "SELECT * FROM observations", sim_connection, index_col="observationId"
            )

        footprint = get_footprint()

        observatory.mjd = (conditions.sun_n12_setting + conditions.sun_n12_rising) / 2
        night_middle_conditions = observatory.return_conditions()
        return skymaps(visits, footprint, night_middle_conditions)
    except Exception as e:
        print(e)


def generate_visit_plot():
    result = worker.submit(make_visit)
    return bokeh.layouts.row(result.result())
