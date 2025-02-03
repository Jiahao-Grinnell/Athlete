# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 15:35:47 2025

@author: dengjiahao
"""

import pandas as pd
import os

def extract_unique_values(input_file, column_name, output_file=None):
    """
    Reads a CSV or Excel file, extracts unique values from a specified column,
    and saves these unique values into a new Excel file as a single-column DataFrame.

    Parameters:
        input_file (str): Path to the input CSV or Excel file.
        column_name (str): The name of the column to extract unique values from.
        output_file (str, optional): Path for the output Excel file.
                                     If not provided, defaults to "<column_name>_unique.xlsx".
    """
    # Determine the file extension to decide how to read the file.
    ext = os.path.splitext(input_file)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(input_file)
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(input_file)
    else:
        raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    
    # Check if the specified column exists.
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in the input file.")

    # Extract unique values and sort them.
    unique_values = df[column_name].unique()
    unique_values = sorted(unique_values)  # This returns a list; remove this if you want original order.
    
    # Create a new DataFrame with one column whose header is the same as the provided column name.
    out_df = pd.DataFrame(unique_values, columns=[column_name])
    
    # Determine the output file name if not specified.
    if output_file is None:
        output_file = f"{column_name}_unique.xlsx"
    
    # Save the new DataFrame to an Excel file (without the index).
    out_df.to_excel(output_file, index=False)
    print(f"Unique values from column '{column_name}' have been saved to '{output_file}'.")

if __name__ == "__main__":
    # Prompt the user for the input file name and the column name.
    input_file = 'combined_records.csv'
    column_name = 'Year'
    extract_unique_values(input_file, column_name)
