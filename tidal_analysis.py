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
        sep = r'\s+',
        header = None,
        engine = "python")
    
    data.columns = ["Cycle", "Date", "Time", "Sea Level", "Residual"]
    data["Sea Level"] = data["Sea Level"].replace({"M": np.nan, "N": np.nan, "T": np.nan})
    data["Residual"] = data["Residual"].replace({"M": np.nan, "N": np.nan, "T": np.nan})

    data["datetime"] = pd.to_datetime(data["Date"] + " " + data["Time"], errors="coerce")

    data["Sea Level"] = pd.to_numeric(data["Sea Level"], errors="coerce")
    data["Residual"] = pd.to_numeric(data["Residual"], errors="coerce")

    data = data[["datetime", "Sea Level", "Residual"]].copy()
    data = data.dropna(subset=["datetime"])
    data = data.set_index("datetime")
    return data
    
    
def extract_single_year_remove_mean(year, data):
    """Returning one year of data with mean seal level removed"""
    year_data = data[data.index.year == int(year)].copy()

    year_data["Sea Level"] = year_data["Sea Level"] - year_data["Sea Level"].mean()
    return year_data




def extract_section_remove_mean(start, end, data):

    return year_data


def join_data(data1, data2):

    return 

def sea_level_rise(data):

    return

def tidal_analysis(data, constituents, start_datetime):

    return

def get_longest_contiguous_data(data):

    return 


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
