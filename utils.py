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

# from openpyxl import Workbook
# from openpyxl.utils.dataframe import dataframe_to_rows
import tkinter as tk
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
    output.update_idletasks()
    print(message)


def save_data_to_file(json_data, save_folder, file_name, file_type):
    try:
        data = json.loads(json_data)

        os.makedirs(save_folder, exist_ok=True)
        file_path = os.path.join(save_folder, f"{file_name}.{file_type}")

        if file_type == "csv":
            with open(file_path, mode="w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(data[0].keys()))
                writer.writeheader()
                writer.writerows(data)
        # elif file_type == 'xlsx':
        #     wb = Workbook()
        #     ws = wb.active
        #     ws.append(list(data[0].keys()))
        #     for item in data:
        #         ws.append(list(item.values()))
        #     wb.save(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return file_path

    except Exception as e:
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


def convert_array_to_json(keys, data):
    json_data = []
    for item in data:
        item_dict = {keys[i]: item[i] for i in range(len(keys))}
        json_data.append(item_dict)
    json_output = json.dumps(json_data, indent=4)
    return json_output


def generate_json_data(main_json):
    data1 = json.loads(main_json)
    parsed_data = []

    for entry in data1:
        address = entry.get(
            "Primary Owner and Premises Addr.", ""
        )  # Safely retrieve address, default to empty string
        lines = address.splitlines()

        dba = lines[0].strip()  # Assuming the first line is DBA
        dba = " ".join(dba.split())

        # Assuming the first line contains both the DBA and the Applicant
        if "                            " in lines[0]:
            dba_applicant_parts = lines[0].split("                            ")
            dba = dba_applicant_parts[0].strip()
            applicant = dba_applicant_parts[-1].strip()
        else:
            applicant = ""

        street = (
            lines[1].strip() if len(lines) > 1 else ""
        )  # Assuming the second line is Street

        city_state_zip = (
            lines[2].strip() if len(lines) > 2 else ""
        )  # Assuming the third line is City, State ZipCode

        # Split City, State, ZipCode
        city_state_zip_parts = city_state_zip.split(", ") if city_state_zip else []

        city = city_state_zip_parts[0].strip() if len(city_state_zip_parts) > 0 else ""
        state_zip = (
            city_state_zip_parts[1].strip() if len(city_state_zip_parts) > 1 else ""
        )

        # Separate State and ZipCode
        state = state_zip.split()[0].strip() if state_zip else ""
        zipcode = state_zip.split()[1].strip() if len(state_zip.split()) > 1 else ""

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
    """
    Merge two JSON data sets into a single JSON array.

    Args:
        json_data1 (str): JSON formatted string representing the first dataset.
        json_data2 (str): JSON formatted string representing the second dataset.

    Returns:
        str: JSON formatted string representing the merged data array.

    Raises:
        ValueError: If the lengths of json_data1 and json_data2 are different.

    Notes:
        - The function assumes that both input JSON strings represent arrays of objects.
        - Each object in json_data1 will have additional fields appended from the corresponding object in json_data2.
        - If json_data1 and json_data2 do not have the same length, a ValueError is raised.
        - The "Primary Owner and Premises Addr." field is excluded from the merged entries.
    """
    # Parse JSON data
    data1 = json.loads(json_data1)
    data2 = json.loads(json_data2)

    if len(data1) != len(data2):
        raise ValueError("Lengths of json_data1 and json_data2 must be the same.")

    merged_data = []
    for i in range(len(data1)):
        merged_entry = {}

        # Copy all fields from data1[i] except "Primary Owner and Premises Addr."
        for key, value in data1[i].items():
            if key != "Primary Owner and Premises Addr.":
                merged_entry[key] = value

        # Append all fields from data2[i]
        for key, value in data2[i].items():
            merged_entry[key] = value

        merged_data.append(merged_entry)

    merged_json = json.dumps(merged_data, indent=4)
    return merged_json
