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
import pandas as pd

# from openpyxl import Workbook
# from openpyxl.utils.dataframe import dataframe_to_rows
import tkinter as tk
import json

from CTkMessagebox import CTkMessagebox


def delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        else:
            print(f"File does not exist: {file_path}")
    except Exception as e:
        print(f"Error deleting file: {e}")


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


def get_default_download_path():
    system = platform.system()
    if system == 'Linux':
        # Ubuntu and other Linux distributions
        return os.path.join(os.path.expanduser('~'), 'Downloads')
    elif system == 'Windows':
        # Windows
        return os.path.join(os.environ['USERPROFILE'], 'Downloads')
    elif system == 'Darwin':
        # macOS
        return os.path.join(os.path.expanduser('~'), 'Downloads')
    else:
        # Default fallback (add more specific handling if needed)
        raise NotImplementedError(f"Unsupported platform: {system}")


# Example usage:
try:
    download_path = get_default_download_path()
    print(f"Default download path: {download_path}")
except NotImplementedError as e:
    print(e)


def move_and_rename_file(source_file, file_name, download_date, temp_folder):
    try:
        # Check if the source file exists
        if not os.path.exists(source_file):
            print(f"Error: File '{source_file}' not found.")
            return False
        new_filename = f"{temp_folder}/{file_name}_generate_report_{download_date}.csv"
        print('new_filename', new_filename)
        current_directory = os.getcwd()
        print('current_directory', current_directory)
        # Determine the destination path
        destination_file = os.path.join(current_directory, new_filename)
        print('destination_file', destination_file)
        report_directory = os.path.dirname(destination_file)
        print('report_directory', report_directory)
        if not os.path.exists(report_directory):
            os.makedirs(report_directory)
            print(f"Created directory: {report_directory}")
            # Move and rename the file
        shutil.move(source_file, destination_file)
        print(f"Moved '{source_file}' to '{destination_file}'")
    except PermissionError:
        print(f"Error: Permission denied moving '{source_file}'.")


def list_files_in_directory(directory_path):
    file_paths = []
    try:
        # List all files in the directory
        files = os.listdir(directory_path)
        # Collect each file path in the directory
        for file in files:
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                file_paths.append(file_path)
        return file_paths
    except FileNotFoundError:
        print(f"Directory '{directory_path}' not found.")
        return []
    except PermissionError:
        print(f"Permission denied accessing '{directory_path}'.")
        return []


def merge_csv_files(file_paths, save_folder, file_name, file_type):
    os.makedirs(save_folder, exist_ok=True)
    out_put_file = os.path.join(save_folder, f"{file_name}.{file_type}")
    print(out_put_file)
    combined_data = pd.DataFrame()  # Initialize an empty DataFrame
    try:
        for file_to_delete in file_paths:
            if not os.path.isfile(file_to_delete):
                raise FileNotFoundError(f"File not found: '{file_to_delete}'")
        for file_to_delete in file_paths:
            df = pd.read_csv(file_to_delete, encoding='utf-8-sig')  # Read each CSV file
            # Concatenate data to combined_data DataFrame
            combined_data = pd.concat([combined_data, df], ignore_index=True)
            delete_file(file_to_delete)
        combined_data.to_csv(out_put_file, index=False, encoding='utf-8')
        print(f"Merged {len(file_paths)} CSV files into '{out_put_file}'")
    except FileNotFoundError as e:
        print(f"Error: One of the files '{file_paths}' not found.")
        print(e)
    except PermissionError as e:
        print(f"Error: Permission denied accessing or writing to output files.")
        print(e)
    return out_put_file
