# import the modules we need
"""Functions for analysis and reading the tidal data"""
import argparse
import datetime
import glob
import os

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import pytz
from scipy import stats
import uptide

def read_tidal_data(filename):
    """Code to read a file, text date/time into real datetimes, make sea level into number"""
    data = pd.read_csv(
        filename,
        skiprows=11,
        sep=r"\s+",
        header=None,
        engine="python")
    data.columns = ["Cycle", "Date", "Time", "Sea Level", "Residual"]
    data["datetime"] = pd.to_datetime(
       data["Date"].astype(str) + " " + data["Time"].astype(str),
       format="%Y/%m/%d %H:%M:%S",
       errors="coerce")
    for col in ["Sea Level", "Residual"]:
        data[col]=data[col].astype(str).str.replace(r"[A-Za-z]$","", regex=True)
        data[col]=pd.to_numeric(data[col], errors="coerce").replace(-99.0, np.nan)

    data = data.dropna(subset=["datetime"]).set_index("datetime").sort_index()
    data.index = data.index.floor("h")
    return data

def extract_single_year_remove_mean(year, data):
    """Return one year of data with mean sea level removed"""
    year=int(year)
    full_index=pd.date_range(
        start=f"{year}-01-01 00:00:00",
        end=f"{year}-12-31 23:00:00",
        freq="h")
    year_data=data[data.index.year == year].copy()
    year_data=year_data.reindex(full_index)
    year_data["Sea Level"]=year_data["Sea Level"] - year_data["Sea Level"].mean()
    return year_data


def extract_section_remove_mean(start, end, data):
    """Returning selected section of data with mean sea level removed"""
    start=pd.to_datetime(start, format = "%Y%m%d")
    end=pd.to_datetime(end, format = "%Y%m%d") + pd.Timedelta(hours=23)
    section=data.loc[start:end].copy()
    full_index=pd.date_range(start = start, end = end, freq = "h")
    section=section.reindex(full_index)
    section["Sea Level"] = section["Sea Level"] - section["Sea Level"].mean()
    return section


def join_data(data1, data2):
    """joining two yearly tidal dateframes and return them in order"""
    data=pd.concat([data2, data1])
    data=data.sort_index()
    return data

def sea_level_rise(data):
    """estimating rate of sea level rise using linear regression"""
    clean = data.dropna(subset=["Sea Level"]).copy()
    monthly = clean["Sea Level"].resample("ME").mean().dropna()

    x = mdates.date2num(monthly.index.to_pydatetime())
    y = monthly.to_numpy(dtype=float)

    result = stats.linregress(x, y)
    slope = result.slope 
    p_value = result.pvalue
    return slope, p_value

def tidal_analysis(data, constituents, start_datetime):
    """Calculating tidal constituent amplitude"""
    clean = data.dropna(subset=["Sea Level"]).copy()
    if clean.empty:
        raise ValueError("No valid sea level data available")

    tide = uptide.Tides(constituents)
    tide.set_initial_time(start_datetime)

    start_naive = start_datetime.replace(tzinfo=None)
    t = np.array(
        [(dt.to_pydatetime() - start_naive).total_seconds() for dt in clean.index],
        dtype=float,
    )
    eta = clean["Sea Level"].to_numpy(dtype=float)
    amp, pha = uptide.harmonic_analysis(tide, eta, t)
    return amp, pha

def analyse_station(data):
    """Return tidal amplitudes and sea-level trend."""
    slope, p_value = sea_level_rise(data)
    analysis_data = data.copy()
    analysis_data["Sea Level"] = (
        analysis_data["Sea Level"] - analysis_data["Sea Level"].mean())
    clean = analysis_data.dropna(subset=["Sea Level"]).copy()
    first_time = clean.index[0]

    tz = pytz.timezone("utc")
    start_datetime = datetime.datetime(
        first_time.year,
        first_time.month,
        first_time.day,
        first_time.hour,
        first_time.minute,
        first_time.second,
        tzinfo=tz,)
    amp, pha = tidal_analysis(analysis_data, ["M2", "S2"], start_datetime)
    return slope, p_value, amp, pha

def load_station_data(dirname):
    """Load and join all valid tidal files in a directory."""
    file_list = sorted(glob.glob(os.path.join(dirname, "*.txt")))
    datasets = []

    for filename in file_list:
        try:
            datasets.append(read_tidal_data(filename))
        except pd.errors.EmptyDataError:
            continue

    if not datasets:
        raise FileNotFoundError(f"No valid txt files found in {dirname}")

    data = datasets[0]
    for next_data in datasets[1:]:
        data = join_data(data, next_data)

    return data, len(datasets)

def main(args_list=None):
    """Running the full tidal analysis from a directory of yearly files."""
    parser = argparse.ArgumentParser(
                     prog="UK Tidal analysis",
                     description="Calculate tidal constiuents and RSL from tide gauge data",
                     )

    parser.add_argument("directory",help="the directory containing txt files with data")
    parser.add_argument('-v', '--verbose',
                    action='store_true',
                    default=False,
                    help="Print progress")
    args = parser.parse_args(args_list)
    dirname = args.directory
    verbose = args.verbose
    data, nfiles=load_station_data(dirname)

    slope, p_value, amp, _ = analyse_station(data)

    output_lines = [
        f"Files read: {nfiles}",
        f"M2 amplitude: {amp[0]:.3f}",
        f"S2 amplitude: {amp[1]:.3f}",
        f"Sea-level rise per year: {slope:.8f}",
        f"p-value: {p_value:.3f}",
    ]

    if verbose:
        for line in output_lines:
            print(line)
    else:
        output_file = os.path.join(dirname, "tidal_analysis_output.txt")
        with open(output_file, "w", encoding="utf-8") as handle:
            for line in output_lines:
                handle.write(line + "\n")

if __name__ == '__main__':
    main()
