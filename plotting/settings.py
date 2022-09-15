import gzip
import pickle

from astropy.time import Time


# Configuration
# This section is for parameters that users may want to change or configure.
SCHEDULER_FNAME = "/home/lewis/Projects/vro/prenight_samples/baseline22_start.pickle.gz"
BASELINE_SIM_DB_FNAME = "/home/lewis/rubin_sim_data/sim_baseline/baseline_v2.1_10yrs.db"

NIGHT = Time("2023-10-04", scale="utc")
TIMEZONE = "Chile/Continental"
SIMULATE_NIGHT = False

BAND_COLOURS = dict(u='#56b4e9', g='#008060', r='#ff4000', i='#850000', z='#6600cc', y='#000000')


# Load the instance of the scheduler we will be using to schedule the night:
def load_scheduler(fname=SCHEDULER_FNAME):
    opener = gzip.open if fname.endswith(".gz") else open
    with opener(fname, "rb") as pickle_io:
        scheduler, conditions = pickle.load(pickle_io)

    scheduler.update_conditions(conditions)
    return scheduler


scheduler = load_scheduler()
