# import the modules we need
import pandas as pd
import datetime
import os
import numpy as np
import uptide
import pytz
import math
from scipy import stats
import matplotlib.dates as mdates
import argparse


def read_tidal_data(filename):
    """Code to read a file, text date/time into real datetimes, make sea level into number"""
    data = pd.read_csv(
        filename,
        skiprows = 11,
        sep = r"\s+",
        header = None,
        engine = "python")
    
    data.columns = ["Cycle", "Date", "Time", "Sea Level", "Residual"]
    
    data["datetime"] = pd.to_datetime(
       data["Date"] + " " + data["Time"],
       format="%Y/%m/%d %H:%M:%S",
       errors="coerce")
    
    for col in ["Sea Level", "Residual"]:
       data[col] = data[col].astype(str)
       data[col] = data[col].replace(
           to_replace=r".*[MNT]$", 
           value=np.nan, 
           regex=True)
       
       data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data[["datetime", "Date", "Time", "Sea Level", "Residual"]].copy()
    data = data.dropna(subset=["datetime"])
    data = data.set_index("datetime").sort_index()
    data.index = data.index.floor("h")
    return data
    
    
def extract_single_year_remove_mean(year, data):
    
    year = int(year)
    full_index = pd.date_range(
        start=f"{year}-01-01 00:00:00",
        end=f"{year}-12-31 23:00:00",
        freq="h")
    
    year_data = data[data.index.year == year].copy()
    year_data = year_data.reindex(full_index)
    year_data["Sea Level"] = year_data["Sea Level"] - year_data["Sea Level"].mean()
    return year_data


def extract_section_remove_mean(start, end, data):
    """Returning selected section of data with mean sea level removed"""
    start = pd.to_datetime(start, format = "%Y%m%d")
    end = pd.to_datetime(end, format = "%Y%m%d") + pd.Timedelta(hours=23)
    section = data.loc[start:end].copy()
    full_index = pd.date_range(start = start, end = end, freq = "h")
    section = section.reindex(full_index)
    section["Sea Level"] = section["Sea Level"] - section["Sea Level"].mean()
    return section


def join_data(data1, data2):
    """joining two yearly tidal dateframes and return them in order"""
    data = pd.concat([data2, data1])
    data = data.sort_index()
    return data

def sea_level_rise(data):
    """estimating rate of sea level rise using linear regression"""
    clean =data.dropna(subset =["Sea Level"]).copy()
    x = mdates.date2num(clean.index.to_pydatetime())
    y = clean["Sea Level"].to_numpy(dtype = float)
    result = stats.linregress(x, y)
    slope = result.slope * 365.25
    p_value = result.pvalue
    return slope, p_value
 
def tidal_analysis(data, constituents, start_datetime):
    """Calculating tidal constituent amplitude"""
    clean = data.dropna(subset=["Sea Level"]).copy()
    if clean.empty:
        raise ValueError ("No valid sea level data available")
        
    tide = uptide.Tides(constituents)
    tide.set_initial_time(start_datetime)
    
    start_naive = start_datetime.replace(tzinfo = None)
    times = clean.index.to_pydatetime()
    t = np.array([(dt - start_naive).total_seconds() for dt in times], dtype = float)
    eta = clean["Sea Level"].to_numpy(dtype=float)
    
    amp, pha = uptide.harmonic_analysis(tide, eta, t)
    return amp, pha

def get_longest_contiguous_data(data):
    """Return the length of the longest contiguous non-missing section."""
    valid = data["Sea Level"].notna()
    groups = (~valid).cumsum()
    longest = valid.groupby(groups).sum().max()
    return  int(longest)


def main(args_list=None):

    parser = argparse.ArgumentParser(
                     prog="UK Tidal analysis",
                     description="Calculate tidal constiuents and RSL from tide gauge data",
                     )

    parser.add_argument("directory",
                    help="the directory containing txt files with data")
    parser.add_argument('-v', '--verbose',
                    action='store_true',
                    default=False,
                    help="Print progress")

    args = parser.parse_args(args_list)
    dirname = args.directory
    verbose = args.verbose
    
    

    print("Add your code here to do things!")
    

if __name__ == '__main__':
    main()
