"""Implements functions to handle geographical data."""
import shapely
from energy_forecast import ROOT_DIR
from energy_forecast.constants import departement_names, region_names
import geojson
from pathlib import Path
from tqdm.auto import tqdm
from shapely.geometry import Polygon, MultiPolygon, Point
import shapely.plotting
import numpy as np
import xarray as xr
import logging

logger = logging.getLogger(__name__)

#: Path to the file containing the coordinates of France.
LONLAT_FRANCE_FILENAME = ROOT_DIR / "data" / "geo" / "lonlat_france.npz"

def extract_list_poly(geojson_filename:str|Path, list_features_to_keep:list, verbose:bool=False):
    """Return a dictionary of polygons extracted from a geojson file.
    
    The dictionary keys are the index of the feature in the list of features to keep.

    Parameters
    ----------
    geojson_filename : str | Path
        The path to the geojson file.
    list_features_to_keep : list[str]
        The list of features to keep.
    verbose : bool, optional
        if True, more information is displaid, by default False

    Returns
    -------
    dict[int, Polygon]
        The dictionary of polygons.
    """
    polys = geojson.load(open(geojson_filename))
    
    polys_kept = {}
    if verbose:
        for feature in polys["features"]:
            print(feature["properties"]["nom"])

    
    for feature in tqdm(polys["features"]):
        name = feature["properties"]["nom"]
        if name not in list_features_to_keep:
            continue
        index = list_features_to_keep.index(name)
        if feature["geometry"]["type"] == "Polygon":
            polys_kept[index] = Polygon(feature["geometry"]["coordinates"][0])
        elif feature["geometry"]["type"] == "MultiPolygon":
            # keeping the largest polygon
            tmp_list = [Polygon(geo[0]) for geo in feature["geometry"]["coordinates"]]
            largest = max(tmp_list, key=lambda x: x.area)
            polys_kept[index] = Polygon(largest)
    
    if verbose:
        all_polys = [poly for poly in polys_kept.values()]
        maxi_multi_poly = MultiPolygon(all_polys)   
        for poly in maxi_multi_poly.geoms:
            shapely.plotting.plot_polygon(poly)
    return polys_kept


def generate_mask(type):
    """Produce a mask of France with the regions or the departements.

    Parameters
    ----------
    type : str
        Either "regions" or "departements".

    Returns
    -------
    xr.DataArray
        The mask of France.

    Raises
    ------
    ValueError
        If the type is not "regions" or "departements".
    """
    if type == "regions":
        geojson_filename = ROOT_DIR / "data" / "geo" / "regions.geojson"
        names = region_names
    elif type == "departements":
        geojson_filename = ROOT_DIR / "data" / "geo" / "departements.geojson"
        names = departement_names
    else:
        raise ValueError("type should be either 'regions' or 'departements'")
    
    polygones = extract_list_poly(geojson_filename, names)
    
    data_coords = np.load(LONLAT_FRANCE_FILENAME)
    long = xr.DataArray(data_coords['lon'], dims='longitude', coords={'longitude': data_coords['lon']})
    lat = xr.DataArray(data_coords['lat'], dims='latitude', coords={'latitude': data_coords['lat']})
    
    mask = xr.apply_ufunc(
        which_region,
        long,
        lat,
        kwargs={"polygons_regions": polygones},
        vectorize=True,
        dask="parallelized",
    )
    return mask

def get_mask(type):
    """Get the mask of France with the regions or the departements.
    
    The mask is saved in a file in the data/geo folder and is loaded if it exists.

    Parameters
    ----------
    type : str
        Either "regions" or "departements".

    Returns
    -------
    xr.DataArray
        The mask of France.

    Raises
    ------
    ValueError
        If the type is not "regions" or "departements".
    """
    if type not in ["regions", "departements"]:
        raise ValueError("type should be either 'regions' or 'departements'")
    file_to_save = ROOT_DIR / "data" / "geo" / f"mask_france_{type}.nc"
    if not file_to_save.exists():
        mask = generate_mask(type)
        mask.to_netcdf(file_to_save)
    else:
        mask = xr.open_dataarray(file_to_save)
    return mask

def get_mask_regions():
    """Get the mask of France with the regions.
    
    A wrapper around get_mask("regions").

    Returns
    -------
    xr.DataArray
        The mask of France with the regions.
    """
    return get_mask("regions")

def get_mask_departements():
    """Get the mask of France with the departements.

    A wrapper around get_mask("departements").
    
    Returns
    -------
    xr.DataArray
        The mask of France with the departements.
    """
    return get_mask("departements")

def which_region(lon, lat, polygons_regions: dict[int, Polygon]):
    """Return the index of the region in which the point is located.
    
    Parameters
    ----------
    lon : float
        The longitude of the point.
    lat : float
        The latitude of the point.
    polygons_regions : dict[int, Polygon]
        The dictionary of polygons representing the regions.
    
    Returns
    -------
    int
        The index of the region in which the point is located.
    """
    for index, poly in polygons_regions.items():
        if poly.contains(Point(lon, lat)):
            return index
    else:
        return np.nan
