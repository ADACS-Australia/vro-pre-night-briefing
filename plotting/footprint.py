from concurrent.futures import ThreadPoolExecutor

import bokeh.layouts
import bokeh.transform
import healpy as hp
import numpy as np
from astropy.time import Time
from rubin_sim.scheduler.modelObservatory import Model_observatory

from plotting.settings import scheduler, NIGHT
from plotting.spheremap import Planisphere

worker = ThreadPoolExecutor()


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


def make_footprint():
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

        footprint = get_footprint()

        mjds = {
            "night start": conditions.sun_n12_setting,
            "night middle": (conditions.sun_n12_setting + conditions.sun_n12_rising) / 2,
            "night end": conditions.sun_n12_rising,
        }
        planispheres = []
        for time_name, mjd in mjds.items():
            observatory.mjd = mjd
            these_conditions = observatory.return_conditions()
            this_planisphere = skymap(footprint, these_conditions)
            this_planisphere.figure.title = f'{Time(mjd, format="mjd").iso} ({time_name})'
            planispheres.append(this_planisphere.figure)

        return planispheres
    except Exception as e:
        print(e)


def skymap(footprint, conditions, map_class=Planisphere):
    ps = map_class(mjd=conditions.mjd)
    cmap = bokeh.transform.linear_cmap("value", "Reds256", 5, 0)
    nside = hp.npix2nside(footprint.shape[0])
    ps.add_healpix(footprint, nside=nside, cmap=cmap)
    ps.decorate()
    ps.add_horizon()
    ps.add_horizon(zd=70, line_kwargs={"color": "red", "line_width": 2})
    ps.add_marker(
        ra=np.degrees(conditions.sunRA),
        decl=np.degrees(conditions.sunDec),
        name="Sun",
        glyph_size=15,
        circle_kwargs={"color": "yellow", "fill_alpha": 1},
    )
    ps.add_marker(
        ra=np.degrees(conditions.moonRA),
        decl=np.degrees(conditions.moonDec),
        name="Moon",
        glyph_size=15,
        circle_kwargs={"color": "lightgray", "fill_alpha": 0.8},
    )
    return ps


def generate_footprint_plot():
    result = worker.submit(make_footprint)
    return bokeh.layouts.row(result.result())
