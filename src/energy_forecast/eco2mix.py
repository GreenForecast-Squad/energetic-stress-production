"""Access the RTE eco2mix via ODRE API to get real-time data on the French electricity grid.

Needed mostly for the regional data, as the national data is available on the RTE API.
"""
import logging

import numpy as np
import pandas as pd
import requests

api_url = "https://odre.opendatasoft.com/api/explore/v2.1/"
datasets_url = api_url + "catalog/datasets/{dataset}/{action}/"
short_requests = "records"
long_requests = "exports/json"

eco2mix_national_tr_ds = "eco2mix-national-tr"  # Real time national data, see https://odre.opendatasoft.com/explore/dataset/eco2mix-national-tr
eco2mix_regional_tr_ds = "eco2mix-regional-tr"  # Real time regional data, see https://odre.opendatasoft.com/explore/dataset/eco2mix-regional-tr

time_f = 'date_heure'

energy_sources_l = [
    'fioul',
    'charbon',
    'gaz',
    'nucleaire',
    'eolien',
    'solaire',
    'hydraulique',
    'pompage',
    'bioenergies',
    'ech_physiques',
    'stockage_batterie',
    'destockage_batterie',
]

detailed_energy_sources_l = [
    'ech_comm_angleterre',
    'ech_comm_espagne',
    'ech_comm_italie',
    'ech_comm_suisse',
    'ech_comm_allemagne_belgique',
    'fioul_tac',
    'fioul_cogen',
    'fioul_autres',
    'gaz_tac',
    'gaz_cogen',
    'gaz_ccg',
    'gaz_autres',
    'hydraulique_fil_eau_eclusee',
    'hydraulique_lacs',
    'hydraulique_step_turbinage',
    'bioenergies_dechets',
    'bioenergies_biomasse',
    'bioenergies_biogaz',
]

consumptions_l = [
    'consommation', 'prevision_j1', 'prevision_j'
]

all_energy_sources_l = energy_sources_l + detailed_energy_sources_l

non_numeric_columns_l = [
    'date',
    'heure',
    'perimetre',
    'nature',
    'libelle_region',
    'code_insee_region',
]


log = logging.getLogger(__name__)


def map_inclusive(inclusive):
    """Map the inclusive parameter to the corresponding conditions in the API.

    Parameters
    ----------
    inclusive : {'left', 'right', 'both', None}
        The type of inclusivity to use for the start and end of the interval.

    Returns
    -------
    dict :
        A dictionary with the keys 'start' and 'end' mapping to the conditions
        to use for the start and end of the interval, respectively.
    """
    starts = {
        'left': '>=',
        'right': '>',
        'both': '>=',
        None: '>',
    }
    ends = {
        'left': '<',
        'right': '<=',
        'both': '<=',
        None: '<',
    }
    return {'start': starts[inclusive],
            'end': ends[inclusive]}

def harmonize_bounds(start, end, timezone):
    """Make sure that the start and end bounds are tz-aware timestamps or None.

    Parameters
    ----------
    start : datetime-like, optional
        The start of the interval to request. If None, nothing is done.
    end : datetime-like, optional
        The end of the interval to request. If None, nothing is done.
    timezone : str
        The timezone to use for the timestamps if not provided.

    Returns
    -------
    tuple :
        A tuple with the start and end bounds as tz-aware timestamps or None.

    """
    if start is not None:
        try:
            start = pd.Timestamp(start, tz=timezone)
        except ValueError: # start already has a timezone
            pass
    if end is not None:
        try:
            end = pd.Timestamp(end, tz=timezone)
        except ValueError:
            pass
    return start, end

def prepare_request_parameters(
        start=None,
        end=None,
        limit=None,
        timezone="Europe/Paris",
        inclusive='left',
        unsafe=False,
        dataset=eco2mix_national_tr_ds,
        ):
    """Prepare the parameters for a request to the eco2mix API.

    Parameters
    ----------
    start : datetime-like, optional
        The start of the interval to request. If None, no lower bound is set.
    end : datetime-like, optional
        The end of the interval to request. If None, no upper bound is set.
    limit : int, optional
        The maximum number of rows to request. If None, no limit is set.
        A limit is always set if start and end are both None and unsafe is False.
    timezone : str, optional
        The timezone to use for the results returned by the API.
        The default is 'Europe/Paris'.
    inclusive : {'left', 'right', 'both', None}, optional
        The type of inclusivity to use for the start and end bounds of the interval.
    unsafe : bool, optional
        If True, do not set a limit if start and end are both None. Else,
        arbitrarily set a limit of 10000.
    dataset : str, optional
        The name of the dataset to request. The default is eco2mix national
        real-time data.


    .. note::

        The documentation of the eco2mix API can be found on the
        `opendatasoft website <https://odre.opendatasoft.com/api/explore/v2.1/console>`_.


    Returns
    -------
    dict :
        A dictionary with the parameters to use for the request.
        The parameters specify to

    """
    ops = map_inclusive(inclusive)
    parameters = {
        'dataset': dataset,
        'timezone' : timezone,
        'order_by': time_f,
    }
    if start is not None:
        parameters['where'] = f"{time_f} {ops['start']} date'{start.isoformat()}'"
    if end is not None:
        where = parameters.get('where', '')
        if where:
            where += " AND "
        parameters['where'] = f"{where}{time_f} {ops['end']} date'{end.isoformat()}'"
    if limit is not None:
        parameters['limit'] = limit
    else:
        if start is None and end is None and not unsafe:
            parameters['limit'] = 10000
    return parameters

def format_result(result_dict, timezone="Europe/Paris"):
    """Format the result of a request to the eco2mix API into a DataFrame.

    Parameters
    ----------
    result_dict : dict
        The result of a request to the eco2mix API as json dict.

    Returns
    -------
    DataFrame :
        A DataFrame with the result of the request.
        The index of the DataFrame is the timstamp of the data.
        The columns representing energy are formated as floats, while the `date`
        and `heure` columns are dropped as they are redundant with the index.

    """
    result = pd.DataFrame.from_records(result_dict)
    if result.empty:
        result.index.name = time_f
        return result
    result.loc[:, time_f] = pd.to_datetime(result[time_f], utc=True).dt.tz_convert(timezone)
    result.drop(columns=['date', 'heure'], inplace=True)
    result.set_index(time_f, inplace=True)
    result.replace('ND', np.nan, inplace=True)
    result.replace('-', np.nan, inplace=True)
    # both lines are needed as different datasets have diffferent representations of missing data -_-
    result = result.astype({col: float for col in result.columns if
                            col not in non_numeric_columns_l})
    return result

def get_data(
        start=None,
        end=None,
        inclusive='left',
        timezone="Europe/Paris",
        dataset=eco2mix_national_tr_ds,
        limit=None,
        unsafe=False,
        ):
    """Request data from the eco2mix API using an http GET request.

    Parameters
    ----------
    start : datetime-like, optional
        The start of the interval to request. If None, no lower bound is set.
    end : datetime-like, optional
        The end of the interval to request. If None, no upper bound is set.
    inclusive : {'left', 'right', 'both', None}, optional
        The type of inclusivity to use for the start and end bounds of the interval.
        'left' means that the start is included and the end is not, and so on.
    timezone : str, optional
        The timezone to use for the results returned by the API.
        The default is 'Europe/Paris'.
    dataset : str, optional
        The name of the dataset to request. The default is eco2mix national
        real-time data.
    limit : int, optional
        The maximum number of rows to request. If None, no limit is set in case
        `unsafe` is set to `True`.
    unsafe : bool, optional
        If True, do not set a limit if start and end are both None. Else,
        arbitrarily set a limit of 10000.

    Returns
    -------
    DataFrame :
        A DataFrame with the result of the request.
        The index of the DataFrame is the timstamp of the data.
        The columns representing physical quantities are formated as floats.
        CO2 emissions are in (gCO2eq/kWh) while energy production and consumption
        are given as powers in (MW).

    """
    start, end = harmonize_bounds(start, end, timezone)
    parameters = prepare_request_parameters(
        start=start,
        end=end,
        limit=limit,
        timezone=timezone,
        inclusive=inclusive,
        unsafe=unsafe,
        dataset=dataset,)
    log.debug("Requesting data from the eco2mix API with parameters: %s", parameters)
    api_url = datasets_url.format(dataset=dataset, action=long_requests)
    log.debug("Use api_url: %s", api_url)
    response = requests.get(api_url,
                            params=parameters)
    response.raise_for_status()
    return format_result(response.json(), timezone=timezone)

def split_exchanges(data):
    """Return a copy where the `ech_physiques` column is split into imports and exports.

    Parameters
    ----------
    data : DataFrame
        The DataFrame to split.
    """
    data = data.copy()
    data['imports'] = data['ech_physiques'].clip(lower=0)
    data['exports'] = data['ech_physiques'].clip(upper=0)
    data.drop(columns=['ech_physiques'], inplace=True)
    return data
