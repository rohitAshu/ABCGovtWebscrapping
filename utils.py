import csv
import json
import os
import platform
import shutil
import tkinter as tk


def print_the_output_statement(output, message):
    """
    Inserts a message into a Tkinter Text widget and prints the message to the console.
    Args:
        output (tk.Text): The Tkinter Text widget where the message will be inserted.
        message (str): The message to be inserted and printed.

    """
    # Insert the message into the Text widget at the end with the 'bold' tag for styling
    output.insert(tk.END, f"{message} \n", "bold")
    # Update the widget to reflect the changes immediately
    output.update_idletasks()

    # Print the message to the console
    print(message)


def find_chrome_executable():
    """
    Finds the path to the Google Chrome executable on the system.

    Returns:
        str: The path to the Chrome executable if found, otherwise None.
    """
    # Get the current operating system
    system = platform.system()
    print(f"system : {system}")

    # Handle Windows systems
    if system == "Windows":
        # Possible paths for Chrome on Windows
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
        # Check if Chrome exists at any of these paths
        for path in chrome_paths:
            if os.path.exists(path):
                return path

    # Handle Linux systems
    elif system == "Linux":
        # Try to find Chrome using `shutil.which`
        chrome_path = shutil.which("google-chrome")
        if chrome_path is None:
            # Fallback to a stable version if the default one isn't found
            chrome_path = shutil.which("google-chrome-stable")
        return chrome_path

    # Return None if Chrome is not found
    return None


async def page_load(page, date, pageurl):
    """
    Loads a web page asynchronously using Puppeteer and checks the response status.

    Parameters:
    - page: Puppeteer page object.
    - date (str): Date parameter to include in the URL query.
    - pageurl (str): Base URL for the web page.

    Returns:
    - bool: True if page loaded successfully, False otherwise.
    """
    pageurl = f"{pageurl}/?RPTTYPE=2&RPTDATE={date}"
    print(f"Opening page from URL: {pageurl}")
    # Navigate to the page and wait for DOM content to be loaded
    response = await page.goto(pageurl, waitUntil="domcontentloaded")

    # Check response status
    if response.status == 404:
        print(f"Page not found: {pageurl}")
        return False
    elif response.status == 403:
        print("403 Forbidden")
        return False
    else:
        return True


def get_default_download_path():
    """
    Retrieves the default download path based on the current operating system.

    Returns:
    - str: Default download path for the current operating system.

    Raises:
    - NotImplementedError: If the current platform is not recognized (not Linux, Windows, or macOS).
    """
    system = platform.system()

    if system == "Linux":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    elif system == "Windows":
        return os.path.join(os.environ["USERPROFILE"], "Downloads")
    elif system == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")


def delete_file(file_path):
    """
    Deletes a file if it exists at the specified path.

    Parameters:
    - file_path (str): Path to the file to be deleted.

    Returns:
    - None
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        else:
            print(f"File does not exist: {file_path}")
    except Exception as e:
        print(f"Error deleting file: {e}")


def csv_to_json(csv_file, currendate, json_file):
    """
    Convert CSV data to JSON format.

    Parameters:
    - csv_file (str): Path to the CSV file.

    Returns:
    - str: JSON formatted string.
    """
    json_data = []
    with open(csv_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row["Report Date"] = currendate.strftime("%B %d, %Y")
            json_data.append(row)
    with open(json_file, "w") as f:
        json.dump(json_data, f, indent=4)

    return json.dumps(json_data, indent=4)


def generate_json_data(main_json):
    """
    Generate structured JSON data from a main JSON dataset.

    Parameters:
    - main_json (str): JSON formatted string representing the main dataset.

    Returns:
    - str: JSON formatted string representing the parsed and structured data.

    Notes:
    - Parses the main JSON data to extract and structure information such as DBA, Applicant, Street,
      City, State, and ZipCode.
    - Assumes the input JSON data contains entries with a field 'Primary Owner and Premises Addr.'.
    """
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


def convert_csv_to_json_and_add_report_date(
    meincsvfile, filename, tempfolder, currendate
):
    """
    Convert a CSV file to JSON format, add a 'Report Date' field, and save both CSV and JSON files.

    Parameters:
    - meincsvfile (str): Path to the input CSV file.
    - filename (str): Base name for the output CSV and JSON files.
    - tempfolder (str): Path to the temporary folder where files will be saved.
    - current_date (datetime.datetime): Current date used for adding 'Report Date'.

    Returns:
    - tuple: A tuple containing:
        - bool: True if conversion and saving were successful, False otherwise.
        - str: Path to the directory where the generated files are saved.

    Notes:
    - The function creates a new CSV file with added 'Report Date' column.
    - The function also generates a corresponding JSON file with the converted data.
    """
    try:
        if not os.path.exists(meincsvfile):
            print(f"Error: File '{meincsvfile}' not found.")
            return False
        print("meincsvfile", meincsvfile)
        download_date = currendate.strftime("%d_%m_%Y")
        new_filename = f"{tempfolder}/{filename}_generate_report_{download_date}.csv"
        print("new_filename", new_filename)
        tempjson = f"{tempfolder}/{filename}_generate_report_{download_date}.json"
        print("tempjson", tempjson)
        current_directory = os.getcwd()
        print("current_directory", current_directory)
        # Determine the destination path
        destination_file = os.path.join(current_directory, new_filename)
        print("destination_file", destination_file)
        report_directory = os.path.dirname(destination_file)
        print("report_directory", report_directory)
        if not os.path.exists(report_directory):
            os.makedirs(report_directory)
            print(f"Created directory: {report_directory}")
        json_data = csv_to_json(meincsvfile, currendate, tempjson)
        json_data2 = generate_json_data(json_data)
        mergejson = merge_json(json_data, json_data2)
        with open(tempjson, "r") as f:
            data = json.load(f)
        if data:
            # Extract headers from the first dictionary
            headers = data[0].keys()
            # Write CSV file
            with open(new_filename, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
        delete_file(tempjson) if os.path.exists(tempjson) else ""
        return True, report_directory
    except PermissionError:
        print(f"Error: Permission denied moving '{meincsvfile}'.")


def list_files_in_directory(directory_path):
    """
    List all files in a directory.

    Parameters:
    - directory_path (str): Path to the directory.

    Returns:
    - list: List of file paths in the directory.

    Notes:
    - If the directory is not found, an empty list is returned.
    - If permission is denied to access the directory, an empty list is returned.
    """
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


def merge_csv_files(file_paths, save_folder, file_name, file_type, main_folder):
    """
    merge multiple CSV files into one CSV file, sorted by 'Report Date' in ascending order.

    Parameters:
    - file_paths (list): List of paths to CSV files to merge.
    - save_folder (str): Folder path where the merged CSV file will be saved.
    - file_name (str): Name of the merged CSV file.
    - file_type (str): File extension ('csv', 'xlsx', etc.).
    - main_folder (str): Main folder where intermediate files might be stored.
    returns:
    - str: Path to the merged CSV file.
    raises:
    - FileNotFoundError: If one of the input CSV files is not found.
    - PermissionError: If permission is denied accessing or writing to output files.
    """
    os.makedirs(save_folder, exist_ok=True)
    output_file = os.path.join(save_folder, f"{file_name}.{file_type}")
    combined_data = []
    header_written = False
    try:
        for file_path in file_paths:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"File not found: '{file_path}'")

            with open(file_path, "r", newline="", encoding="utf-8-sig") as infile:
                reader = csv.reader(infile)
                headers = next(reader)  # Read headers from the first file
                if not header_written:
                    combined_data.append(headers)  # Append headers only once
                    header_written = True
                for row in reader:
                    combined_data.append(row)  # Append rows from each file

        # Find the index of 'Report Date' column
        report_date_index = headers.index("Report Date")

        # Sort combined_data by 'Report Date' column (skip sorting headers)
        combined_data.sort(
            key=lambda x: (
                x[report_date_index] if x[report_date_index].isdigit() else float("inf")
            )
        )

        with open(output_file, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.writer(outfile)
            writer.writerows(combined_data)

        print(f"Merged {len(file_paths)} CSV files into '{output_file}'")
    except FileNotFoundError as e:
        print(f"Error: One of the files '{file_paths}' not found.")
        print(e)
    except PermissionError as e:
        print(f"Error: Permission denied accessing or writing to output files.")
        print(e)

    # Assuming delete_directory is a function that deletes the main_folder
    delete_directory(rf"{main_folder}")
    return output_file


def delete_directory(directory_path):
    """
    Delete a directory and all its contents.

    Parameters:
        directory_path (str): Path to the directory to delete.

    Returns:
        None

    Raises:
        OSError: If an error occurs while attempting to delete the directory.

    Notes:
        This function recursively deletes all files and subdirectories within the specified directory.
        If the directory does not exist, no action is taken.
    """
    try:
        shutil.rmtree(directory_path)  # Recursively delete the directory
        print(f"Deleted directory and contents: {directory_path}")
    except OSError as e:
        print(
            f"Error: {directory_path} - {e.strerror}"
        )  # Print error message if deletion fails


def Read_Csv(file_path):
    """
    Read data from a CSV file and return it as a list of lists.

    Parameters:
    - file_path (str): Path to the CSV file to be read.

    Returns:
    - list: A list containing each row of the CSV file as a list of strings.
            Each inner list represents a row of data from the CSV file.

    Raises:
    - FileNotFoundError: If the specified file_path does not exist.
    - IOError: If an error occurs while reading the file.
    """
    csv_data = []
    with open(file_path, "r", newline="") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=";")
        for row in csvreader:
            csv_data.append(row)
    return csv_data
