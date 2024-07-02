"""
Imports:
- csv: Provides functionality to read from and write to CSV files.
- os: Provides operating system functionalities like directory
creation and path manipulation.
- platform: Provides access to information about the operating system.
- shutil: Provides high-level file operations such as copying and removal.
- tkinter (as tk): Provides a GUI toolkit for Python applications.
- CTkMessagebox: Custom module or class for displaying tkinter message
boxes with custom styling.
"""

import csv
import os
import platform
import shutil
import threading
import tkinter as tk
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import json
from CTkMessagebox import CTkMessagebox


def print_the_output_statement(output, message):
    """
    Print a message to both a tkinter Text widget and to standard output (console).
    Args:
        output (tk.Text): The tkinter Text widget where the message should be displayed.
        message (str): The message to be printed and inserted into the Text widget.

    Returns:
        None
    Notes:
        - Inserts the message followed by a newline into the tkinter Text widget.
        - Updates the widget to display the inserted message immediately.
        - Prints the message to the standard output (console).
    """
    output.insert(tk.END, f"{message} \n", "bold")
    output.update_idletasks()  # Update the widget immediately
    print(message)


def save_data_to_file(json_data, save_folder):
    try:
        os.makedirs(save_folder, exist_ok=True)
        file_name = f"{save_folder}/combined_table_data.xlsx"

        # Parse JSON data
        data = json.loads(json_data)

        # Create a new Workbook
        wb = Workbook()
        ws = wb.active

        # Add headers from JSON keys
        headers = list(data[0].keys())
        ws.append(headers)

        # Add data rows
        for item in data:
            ws.append([item[key] for key in headers])

        # Save workbook to file
        wb.save(file_name)

        return file_name

    except Exception as e:
        # Handle exceptions
        print(f"Error saving data: {str(e)}")
        return None


def find_chrome_executable():
    """
    Finds the path to the Google Chrome executable based on
    the current operating system.
    Returns:
        str or None: Path to the Chrome executable if found,
        or None if not found.
    Raises:
        None
    Notes:
        - On Windows, it checks common installation paths under Program Files
        and Program Files (x86).
        - On Linux, it checks for 'google-chrome' and 'google-chrome-stable'
         in the system PATH.
    """
    system = platform.system()
    print(f"system : {system}")
    if system == "Windows":
        chrome_paths = [
            os.path.join(
                os.environ["ProgramFiles"],
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ["ProgramFiles(x86)"],
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                return path
    elif system == "Linux":
        chrome_path = shutil.which("google-chrome")
        if chrome_path is None:
            chrome_path = shutil.which("google-chrome-stable")
        return chrome_path
    return None


def print_current_thread():
    current_thread = threading.current_thread()
    print("---------- Current Thread:", current_thread.name)


def convert_array_to_json(keys, data):
    json_data = []
    for item in data:
        # Create a dictionary mapping combined_headers to item values
        item_dict = {keys[i]: item[i] for i in range(len(keys))}
        # Append the dictionary to json_data
        json_data.append(item_dict)
    json_output = json.dumps(json_data, indent=4)
    return json_output


def generate_json_data(main_json):
    data1 = json.loads(main_json)
    parsed_data = []
    for entry in data1:
        address = entry["Primary Owner and Premises Addr."]
        lines = address.splitlines()
        dba = lines[0].strip()  # Assuming the first line is DBA
        dba = " ".join(dba.split())
        applicant = (
            lines[0].split("                            ")[-1].strip()
        )  # Assuming the first line contains both the DBA and the Applicant
        street = lines[1].strip()  # Assuming the second line is Street
        city_state_zip = lines[
            2
        ].strip()  # Assuming the third line is City, State ZipCode

        # Split City, State, ZipCode
        city_state_zip_parts = city_state_zip.split(", ")
        city = city_state_zip_parts[0].strip()
        state_zip = city_state_zip_parts[1].strip()
        # Separate State and ZipCode
        state = state_zip.split()[0].strip()
        zipcode = state_zip.split()[1].strip()
        # Print or use the parsed data as needed
        parsed_entry = {
            "DBA": dba,
            "Applicant": applicant,
            "Street": street,
            "City": city,
            "State": state,
            "ZipCode": zipcode,
        }
        parsed_data.append(parsed_entry)
    json_data2 = json.dumps(parsed_data, indent=4)
    return json_data2


def merge_json(json_data1, json_data2):
    # Parse JSON data
    data1 = json.loads(json_data1)
    data2 = json.loads(json_data2)
    merged_data = []
    for i in range(len(data1)):
        merged_entry = data1[i].copy()  # Copy the original entry from data1
        premises_info = data2[i]  # Get premises address info from data2
        # Append premises address info directly after the last field in each entry of data1
        for key, value in premises_info.items():
            merged_entry[key] = value
        merged_data.append(merged_entry)
    merged_json = json.dumps(merged_data, indent=4)
    return merged_json
