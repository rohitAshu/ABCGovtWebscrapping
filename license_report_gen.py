import asyncio
import os
import random
import time
import tkinter as tk
from datetime import datetime, timedelta
from threading import Thread
from tkinter import ttk, filedialog

import pyppeteer
from CTkMessagebox import CTkMessagebox
from pyppeteer import launch
from pyppeteer.errors import TimeoutError as PyppeteerTimeoutError
from screeninfo import get_monitors
from tkcalendar import DateEntry

from utils import (
    convert_csv_to_json_and_add_report_date,
    delete_directory,
    delete_file,
    get_default_download_path,
    list_files_in_directory,
    merge_csv_files,
    page_load,
    print_the_output_statement,
    # find_chrome_executable,
)
from webdriver import pyppeteerBrowserInit


# Application Settings
APP_TITLE = "Daily License Report"  # Title of the application window
APP_HEADING = "Welcome to the ABC Liquor Daily Report App"  # Heading text displayed in the app
APP_BUTTON_NAME = "Generate Report"  # Text on the report generation button
APP_BUTTON_NAME1 = "Close Window"  # Text on the close window button

# Headless Setting 
HEADLESS = True  # Whether to run the app in headless mode (no GUI)
PAGE_URL = "https://www.abc.ca.gov/licensing/licensing-reports/new-applications/"  # URL for licensing reports
# Threading Settings
MAX_THREAD_COUNT = 10  # Maximum number of threads for concurrent processing
# Report Settings
FILE_TYPE = 'csv'  # Type of file to generate ('csv' or 'xlsx')
FILE_NAME = "ABCLicensingReport"  # Base name for generated report files
FILE_TEMP_FOLDER = "temp"  # Temporary folder for storing generated files

# Screen Resolution Settings
width = get_monitors()[0].width  # Width of the primary monitor
height = get_monitors()[0].height  # Height of the primary monitor


async def scrape_and_save_table_data(browser, start_date, end_date, output, start_time):
        output.delete("1.0", tk.END)
        print_the_output_statement(output, "Data Processing Started...")
        print_the_output_statement(output, "Please wait for the Report generation.")
        error_response = ''
        download_path = get_default_download_path()
        print('download_path' , download_path)
        source_file = f"{download_path}/CA-ABC-LicenseReport.csv"
        print('source_file', source_file)
        page = await browser.newPage()
        delete_file(source_file) if os.path.exists(source_file) else ''
        os.makedirs(download_path, exist_ok=True)
        await page._client.send('Page.setDownloadBehavior',
                            {'behavior': 'allow', 'downloadPath': download_path})
        await page.setViewport({'width': width, 'height': height})
        try:
            start_date = datetime.strptime(start_date, "%B %d, %Y")
            end_date = datetime.strptime(end_date, "%B %d, %Y")
            while start_date <= end_date:
             formatted_date = start_date.strftime(
                "%m/%d/%Y"
            )
             print(f'Scrapping the data {formatted_date}')
             load_page = await page_load(page, formatted_date, PAGE_URL)
             if load_page:
                 print(f"opened  successfully")
                 await asyncio.sleep(5)
                 viewport_height = await page.evaluate("window.innerHeight")
                 print("viewport_height element is found")
                 scroll_distance = int(viewport_height * 0.3)
                 print(f"scroll_distance is  {scroll_distance}")
                 await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                 print('short Scrolling......................................')
                 check_script = """
                        () => {
                            const elements = document.querySelectorAll('.et_pb_code_inner');
                            for (let element of elements) {
                                if (element.textContent.trim() === 'There were no new applications taken on the selected report date.') {
                                    return true;
                                }
                            }
                            return false;
                        }
                    """
                 element_exists = await page.evaluate(check_script)
                 if element_exists:
                    print_the_output_statement(
                        output,
                        f"There were no new applications taken on the selected report date. {start_date}:",
                    )
                    error_response = True
                 else:
                   table_exists = await page.evaluate(
                        'document.querySelector("table#license_report tbody tr") !== null')
                   if table_exists:
                       error_response = False
                       scroll_distance = int(viewport_height * 3.9)
                       print(f"Scroll Distanced {scroll_distance}")
                       await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                       print("Long Scrolling....................")
                       await page.waitForXPath('//*[@class="btn btn-default buttons-csv buttons-html5 abclqs-download-btn et_pb_button et_pb_button_0 et_pb_bg_layout_dark"]')
                       download_csv_btn = await page.xpath(
                            '//*[@class="btn btn-default buttons-csv buttons-html5 abclqs-download-btn et_pb_button et_pb_button_0 et_pb_bg_layout_dark"]')
                       print(f'download_csv_btn element is found {download_csv_btn}')
                       
                       await download_csv_btn[0].click()
                       print("Clicked on download_csv_btn Successfully !!")
                       print('Downloading...............')
                       await asyncio.sleep(7)
                       print(f'Downloaded the File to the {source_file}')
                       success, Response = convert_csv_to_json_and_add_report_date(source_file,FILE_NAME,FILE_TEMP_FOLDER,start_date )
                       if success:
                           delete_file(source_file) if os.path.exists(source_file) else ''
                       print_the_output_statement(
                            output, f"Data found for {formatted_date}."
                        )
                   else:
                       error_response = True
                       print_the_output_statement(
                            output,
                            f"There were no new applications taken on the selected report date. {start_date}:",
                        )
                    
             start_date += timedelta(days=1)
        except PyppeteerTimeoutError as timeout_error:
            CTkMessagebox(
                title="Error",
                message="Internal Error Occurred while running application. Please Try Again!!",
                icon="cancel",
            )
        except pyppeteer.errors.NetworkError:
            CTkMessagebox(
                title="Error",
                message="Internal Error Occurred while running application. Please Try Again!!",
                icon="cancel",
            )
        except Exception as e:
            CTkMessagebox(
                title="Error",
                message="Internal Error Occurred while running application. Please Try Again!!",
                icon="cancel",
            )
        finally:
         await browser.close()
         end_time = time.time()
         total_time = end_time - start_time
         if error_response:
             CTkMessagebox(
                title="Error",
                message=f"No Report is found on the dated {start_date} & {end_date}",
                icon="cancel",
            )
         else:
           msg = CTkMessagebox( title="Info", message="Report Successfully Generated.\n Click ok to Download", option_1="Cancel", option_2="Ok")
           if msg.get() == "Ok":
               start_date_str = start_date_entry.get_date().strftime("%Y-%B-%d")
               enend_date_str = end_date_entry.get_date().strftime("%Y-%B-%d")
               FileName = f"{FILE_NAME}_{start_date_str}_{enend_date_str}"
               save_folder = filedialog.askdirectory(
                    initialdir=os.getcwd(), title="Select Folder to Save Data"
                )
               if save_folder:
                # print('FileName', FileName)
                file_paths = list_files_in_directory(Response)
                # print('file_paths', file_paths)
                merge_the_file = merge_csv_files(file_paths, save_folder, FileName, FILE_TYPE)
                print('merge_the_file', merge_the_file)
                directory_to_delete = fr'{Response}'
                delete_directory(directory_to_delete)
                CTkMessagebox(
                        message=f"Generated Report Successfully on the dated {start_date} & {end_date} and save the file to  {merge_the_file} ",
                        icon="check",
                        option_1="Thanks",
                    )
           else:
               CTkMessagebox(
                        message=f"Generated Report Successfully on the dated {start_date} & {end_date} but you have cancelled the downlaod ",
                        icon="check",
                        option_1="Thanks",
                    )
           
        print_the_output_statement(output, f"Total execution time: {total_time:.2f} seconds")
   

def run_scraping_thread(loop, browser, start_date_str, end_date_str, output_text, start_time):
    """
    Runs the scraping thread, setting the event loop and invoking the scraping coroutine.

    Args:
        loop (asyncio.AbstractEventLoop): The event loop for asynchronous operations.
        browser (pyppeteer.browser.Browser): The initialized browser instance.
        start_date_str (str): The start date in string format.
        end_date_str (str): The end date in string format.
        output_text (tk.Text): The Tkinter Text widget to display output.
        start_time (float): The start time of the function for logging.

    Raises:
        None
    """
    # Set the provided event loop as the current event loop
    asyncio.set_event_loop(loop)

    # Run the scraping coroutine until complete
    loop.run_until_complete(
        scrape_and_save_table_data(
            browser, start_date_str, end_date_str, output_text, start_time
        )
    )


def generate_daily_report():
    """
    Generates a daily report based on selected start and end dates.
    Validates the dates and initiates a scraping process if the dates are valid.

    Raises:
        None
    """
    # Record the start time of the function
    start_time = time.time()

    # Get the current date and format it
    current_date_str = datetime.now().date().strftime("%B %d, %Y")
    current_date = datetime.strptime(current_date_str, "%B %d, %Y").date()
    print("current_date", current_date)

    # Get the start date from the date entry widget and format it
    start_date_str = start_date_entry.get_date().strftime("%B %d, %Y")
    start_date = datetime.strptime(start_date_str, "%B %d, %Y").date()
    print("start_date", start_date)

    # Get the end date from the date entry widget and format it
    end_date_str = end_date_entry.get_date().strftime("%B %d, %Y")
    end_date = datetime.strptime(end_date_str, "%B %d, %Y").date()
    print("end_date", end_date)

    print("date validation Start")

    # Validate the selected dates
    if (
        start_date > current_date
        or end_date > current_date
        or start_date == current_date
        or end_date == current_date
    ):
        # Show error if dates are not in the past
        print("Please select a date that is 2 or more days past.")
        CTkMessagebox(
            title="Error",
            message="Please select a date that is 2 or more days past.",
            icon="cancel",
        )
    elif end_date < start_date:
        # Show error if end date is earlier than start date
        print("End date should be later than or equal to start date")
        CTkMessagebox(
            title="Error",
            message="End date should be later than or equal to start date",
            icon="cancel",
        )
    else:
        # Initialize a new event loop
        loop = asyncio.new_event_loop()
        print("browser init")
        
        # Initialize the browser
        browser = pyppeteerBrowserInit(loop, HEADLESS, width, height)
        print("browser init completed")
        
        # Start a new thread for scraping
        scrape_thread = Thread(
            target=run_scraping_thread,
            args=(loop, browser, start_date_str, end_date_str, output_text, start_time),
        )
        scrape_thread.start()


def close_window():
    """
    Function to close the main window.

    This function destroys the root window of the application,
    effectively closing the entire GUI.

    Parameters:
    None

    Returns:
    None
    """
    root.destroy()  # Destroy the root window to close the application

# Initialize the main application window
root = tk.Tk()
root.title(APP_TITLE)
root.option_add("*Font", "Handfine")

# Create and pack the heading label
heading_label = tk.Label(root, text=APP_HEADING, font=("Handfine", 18, "bold italic"), pady=20)
heading_label.pack()

# Configure the style for the form frame
style = ttk.Style()
style.configure("Shadow.TFrame", background="light blue", borderwidth=5, relief="ridge")

# Create and pack the form frame with padding
form_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
form_frame.pack(pady=20)

# Create and place the start date label and entry
start_date_label = tk.Label(form_frame, text="Start Date:")
start_date_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
start_date_entry = DateEntry(
    form_frame,
    width=12,
    background="black",
    foreground="#f0f0f0",
    borderwidth=2,
    date_pattern="yyyy-mm-dd",
)
start_date_entry.grid(row=0, column=1, padx=10, pady=10)

# Create and place the end date label and entry
end_date_label = tk.Label(form_frame, text="End Date:")
end_date_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
end_date_entry = DateEntry(
    form_frame,
    width=12,
    background="darkblue",
    foreground="white",
    borderwidth=2,
    date_pattern="yyyy-mm-dd",
)
end_date_entry.grid(row=1, column=1, padx=10, pady=10)

# Create and pack the button frame
button_frame = tk.Frame(root)
button_frame.pack(pady=20)

# Create and pack the scrape button
scrape_button = tk.Button(
    button_frame,
    text=APP_BUTTON_NAME,
    command=generate_daily_report,
    font=("Arial", 12, "bold"),
    fg="white",
    bg="blue",
    relief="solid",
    borderwidth=1,
    highlightbackground="blue",
    highlightcolor="blue",
    highlightthickness=2,
)
scrape_button.pack(side=tk.LEFT, padx=10)

# Create and pack the close button
scrape_button1 = tk.Button(
    button_frame,
    text=APP_BUTTON_NAME1,
    command=close_window,
    font=("Arial", 12, "bold"),
    fg="white",
    bg="blue",
    relief="solid",
    borderwidth=1,
    highlightbackground="blue",
    highlightcolor="blue",
    highlightthickness=2,
)
scrape_button1.pack(side=tk.LEFT, padx=10)

# Create and pack the output frame
output_frame = tk.Frame(root, bd=2, relief="groove", bg="white", padx=10, pady=10)
output_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

# Create and pack the output text widget
output_text = tk.Text(
    output_frame, height=10, width=100, font=("Arial", 12), bg="#ccf7ff"
)
output_text.pack(fill=tk.BOTH, expand=True)
output_text.tag_configure("bold", font=("Arial", 12, "bold"))

# Start the main application loop
root.mainloop()
print("Script execution completed!")
