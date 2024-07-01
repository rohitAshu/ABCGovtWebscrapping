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


def save_data_to_file(combined_headers, combined_data, save_folder):
    """
    Save combined headers and data to a CSV file in the specified folder.
    Args:
        combined_headers (list): List of header strings for the CSV file.
        combined_data (list of lists): List of data rows (each row is a list of values).
        save_folder (str): Path to the folder where the CSV file should be saved.
    Returns:
        str: File path of the saved CSV file if successful, None otherwise.
    Raises:
        IOError: If there's an error creating or writing to the CSV file.
    Notes:
        - The function creates the `save_folder` if it doesn't exist.
        - It writes `combined_headers` as the first row and `combined_data` as
        subsequent rows to a CSV file.
        - Uses UTF-8 encoding for writing the CSV file.
    """
    try:
        os.makedirs(save_folder, exist_ok=True)
        file_name = f"{save_folder}/combined_table_data.csv"
        if combined_data:
            with open(file_name, "w", newline="", encoding="utf-8") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(combined_headers)  # Write headers as the first row
                csvwriter.writerows(combined_data)  # Write data rows
            return file_name
    except Exception as e:
        CTkMessagebox(
            title="Error", message=f"Error saving data: {str(e)}", icon="cancel"
        )


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
