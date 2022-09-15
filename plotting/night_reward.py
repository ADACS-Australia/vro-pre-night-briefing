import warnings
from concurrent.futures import ProcessPoolExecutor

import bokeh
import bokeh.palettes
import bokeh.plotting
from astropy.time import Time
from rubin_sim.scheduler.modelObservatory import Model_observatory

from plotting.settings import scheduler, NIGHT
import numpy as np
import pandas as pd


worker_pool = ProcessPoolExecutor(1)


def reward_bfs_df(scheduler, conditions):
    reward_df = scheduler.make_reward_df(conditions)
    summary_df = reward_df.reset_index()

    def make_tier_name(row):
        tier_name = f"tier {row.list_index}"
        return tier_name

    summary_df["tier"] = summary_df.apply(make_tier_name, axis=1)

    def get_survey_name(row):
        survey_name = scheduler.survey_lists[row.list_index][
            row.survey_index
        ].survey_name
        return survey_name

    summary_df["survey_name"] = summary_df.apply(get_survey_name, axis=1)

    def make_survey_row(survey_bfs):
        infeasible_bf = ", ".join(
            survey_bfs.loc[~survey_bfs.feasible.astype(bool)].basis_function.to_list()
        )
        infeasible = ~np.all(survey_bfs.feasible.astype(bool))
        list_index = survey_bfs.list_index.iloc[0]
        survey_index = survey_bfs.survey_index.iloc[0]
        direct_reward = scheduler.survey_lists[list_index][
            survey_index
        ].calc_reward_function(conditions)
        reward = survey_bfs.accum_reward.iloc[-1]
        assert reward == np.nanmax(direct_reward)
        survey_row = pd.Series(
            {
                "reward": reward,
                "infeasible": infeasible,
                "infeasible_bfs": infeasible_bf,
            }
        )
        return survey_row

    survey_df = summary_df.groupby(["tier", "survey_name"]).apply(make_survey_row)
    return survey_df


def _process_night_reward_df(freq):
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

    sample_times = pd.date_range(
        Time(conditions.sun_n12_setting, format="mjd", scale="utc").datetime,
        Time(conditions.sun_n12_rising, format="mjd", scale="utc").datetime,
        freq=freq,
    )

    reward_df_time_list = []
    for pd_time in sample_times:
        ap_time = Time(pd_time)
        observatory.mjd = ap_time.mjd
        conditions = observatory.return_conditions()
        this_time_reward_df = reward_bfs_df(scheduler, conditions)
        this_time_reward_df["mjd"] = ap_time.mjd
        this_time_reward_df["time"] = pd_time
        reward_df_time_list.append(this_time_reward_df)

    return pd.concat(reward_df_time_list).reset_index()


def _make_night_reward_plot(freq="10T"):
    proc = worker_pool.submit(_process_night_reward_df, freq)
    night_reward_df = proc.result()

    night_reward_ds = dict()
    for survey_name, reward_df in night_reward_df.groupby("survey_name"):
        survey_reward_ds = bokeh.models.ColumnDataSource(reward_df.sort_values("time"))
        night_reward_ds[survey_name] = survey_reward_ds

    survey_colors = dict(
        zip(night_reward_ds.keys(), bokeh.palettes.Category20[len(night_reward_ds)])
    )

    # tier_dash_pattern = {"tier 0": "solid", "tier 1": "dashed", "tier 2": "dotdash", "tier 3": "dotted"}
    tier_dash_pattern = {
        "tier 0": "solid",
        "tier 1": "solid",
        "tier 2": "dashed",
        "tier 3": "dotdash",
        "tier 4": "dotted",
    }
    survey_dash_pattern = dict()
    for survey_name in night_reward_ds:
        survey_tier = night_reward_df.query(
            f'survey_name == "{survey_name}"'
        ).tier.iloc[0]
        survey_dash_pattern[survey_name] = tier_dash_pattern[survey_tier]

    night_rewards_fig = bokeh.plotting.figure(
        height=500,
        width=800,
        x_axis_label="time",
        y_axis_label="reward",
        x_axis_type="datetime",
    )
    night_rewards_fig.add_layout(bokeh.models.Legend(), "right")
    for survey_name, reward_ds in night_reward_ds.items():
        night_rewards_fig.line(
            "time",
            "reward",
            line_color=survey_colors[survey_name],
            line_dash=survey_dash_pattern[survey_name],
            line_width=3,
            legend_label=survey_name,
            source=reward_ds,
        )

    return night_rewards_fig


def generate_night_rewards_plot():
    # Plotting the rewards for scheduled surveys
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=RuntimeWarning, lineno=552)
        warnings.filterwarnings('ignore', category=FutureWarning, lineno=465)
        return _make_night_reward_plot(
            freq="10T"
        )
