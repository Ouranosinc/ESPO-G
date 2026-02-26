# noqa: D100
from __future__ import annotations

import xarray as xr

from xclim.core.units import declare_units, rate2amount
from xclim.core.units import (
    convert_units_to,
    declare_units,
    pint2cfattrs,
    rate2amount,
    str2pint,
    to_agg_units,
)
from xclim.indices import run_length as rl
from xclim.indices.converters import rain_approximation, snowfall_approximation
from xclim.indices.generic import compare, select_resample_op, threshold_count


def multiday_temperature_inside(
    tasmin: xarray.DataArray,
    tasmax: xarray.DataArray,
    thresh_tasmin: Quantified = "0 degC",
    thresh_tasmax: Quantified = "0 degC",
    window: int = 1,
    op: Literal["mean", "sum", "max", "min", "std", "count"] = "mean",
    op_tasmin: Literal["<", "<=", "lt", "le"] = "<=",
    op_tasmax: Literal[">", ">=", "gt", "ge"] = ">",
    freq: str = "YS",
    resample_before_rl: bool = True,
) -> xarray.DataArray:
    r"""
    Statistics of consecutive diurnal temperature swing events.

    A diurnal swing of max and min temperature event is when Tmax > thresh_tasmax and Tmin <= thresh_tasmin. This indice
    finds all days that constitute these events and computes statistics over the length and frequency of these events.

    Parameters
    ----------
    tasmin : xarray.DataArray
        Minimum daily temperature.
    tasmax : xarray.DataArray
        Maximum daily temperature.
    thresh_tasmin : Quantified
        The temperature threshold needed to trigger a freeze event.
    thresh_tasmax : Quantified
        The temperature threshold needed to trigger a thaw event.
    window : int
        The minimal length of spells to be included in the statistics.
    op : {"mean", "sum", "max", "min", "std", "count"}
        The statistical operation to use when reducing the list of spell lengths.
    op_tasmin : {"<", "<=", "lt", "le"}
        Comparison operation for tasmin. Default: "<=".
    op_tasmax : {">", ">=", "gt", "ge"}
        Comparison operation for tasmax. Default: ">".
    freq : str
        Resampling frequency.
    resample_before_rl : bool
        Determines if the resampling should take place before or after the run
        length encoding (or a similar algorithm) is applied to runs.

    Returns
    -------
    xarray.DataArray, [time]
        {freq} {op} length of diurnal temperature cycles exceeding thresholds.

    Notes
    -----
    Let :math:`TX_{i}` be the maximum temperature at day :math:`i` and :math:`TN_{i}` be the daily minimum temperature
    at day :math:`i`. Then freeze thaw spells during a given period are consecutive days where:

    .. math::

       TX_{i} > 0℃ \land TN_{i} <  0℃

    This indice returns a given statistic of the found lengths, optionally dropping those shorter than the `window`
    argument. For example, `window=1` and `op='sum'` returns the same value as :py:func:`daily_freezethaw_cycles`.
    """
    thaw_threshold = convert_units_to(thresh_tasmax, tasmax)
    freeze_threshold = convert_units_to(thresh_tasmin, tasmin)

    freeze = compare(tasmin, op_tasmin, freeze_threshold)
    thaw = compare(tasmax, op_tasmax, thaw_threshold)
    ft = freeze * thaw

    if op == "count":
        out = rl.resample_and_rl(
            ft,
            resample_before_rl,
            rl.windowed_run_events,
            window=window,
            freq=freq,
        )
    else:
        out = rl.resample_and_rl(
            ft,
            resample_before_rl,
            rl.rle_statistics,
            reducer=op,
            window=window,
            freq=freq,
        )

    return to_agg_units(out, tasmin, "count", deffreq="D")