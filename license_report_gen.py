"""
scrapping_twinkker.py

This script automates web scraping of licensing reports from ABC Liquor website
using Pyppeteer for headless browser automation. It provides a GUI interface
using Tkinter for user interaction to select date ranges and generate daily reports.

Libraries:
- asyncio: For asynchronous operations.
- tkinter: GUI toolkit.
- datetime: Date and time manipulation.
- pyppeteer: Headless browser automation.
- tkcalendar: DateEntry widget for date selection in Tkinter.

Functions:
- scrape_and_save_table_data: Asynchronously scrapes and saves table data from the website.
- start_scraping_generating_daily_report_async: Initiates scraping based on user-selected date range.
- generating_report: Callback function for GUI button to start the scraping process.
- Other utility functions imported from 'utils.py' for printing output and saving data to file.

"""

import asyncio
import os
import time
import tkinter as tk
import concurrent.futures

from datetime import datetime, timedelta
from tkinter import filedialog
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor
import pyppeteer
from CTkMessagebox import CTkMessagebox
from pyppeteer import launch
from pyppeteer.errors import TimeoutError as PyppeteerTimeoutError
from tkcalendar import DateEntry

from utils import (
    print_the_output_statement,
    save_data_to_file,
    find_chrome_executable,
    convert_array_to_json,
    print_current_thread,
    generate_json_data,
    merge_json,
)

# Application constants
APP_TITLE = "Daily License Report"
APP_HEADING = "Welcome to the ABC Liquor Daily Report App"
APP_BUTTON_NAME = "Generate Report"
PAGE_URL = "https://www.abc.ca.gov/licensing/licensing-reports/new-applications/"
HEADLESS = True
MAX_THREAD_COUNT = 10
page_created = False


# Function to scrape and save table data from the specified date range
# Function to scrape and save table data from the specified date range
async def scrape_and_save_table_data(start_date, end_date, output):
    """
    Asynchronously scrapes data from a web page based on a date range, saves it to a CSV file,
    and displays progress and results in a tkinter Text widget.

    Args:
        start_date (str): Start date in "%B %d, %Y" format.
        end_date (str): End date in "%B %d, %Y" format.
        output (tk.Text): tkinter Text widget to display progress and results.

    Notes:
        - Uses asyncio and pyppeteer to launch a headless browser and navigate to PAGE_URL.
        - Iterates through each date in the specified range, retrieves data from the web page,
          and appends it to `combined_data`.
        - Prompts the user to select a folder to save the scraped data in CSV format.
        - Displays messages in `output` regarding progress, errors, and execution time.
        - Uses `CTkMessagebox` to notify the user upon successful completion of the operation.
    """
    start_time = time.time()
    output.delete("1.0", tk.END)
    print_the_output_statement(output, "Data Processing Started...")
    print_the_output_statement(output, "Please wait for the Report generation.")
    executable_path = find_chrome_executable()
    print(executable_path)
    browser = await launch(
        {
            "headless": HEADLESS,
            "executablePath": executable_path,
            "defaultViewport": None,
        }
    )
    scrape_button1.config(state=tk.NORMAL)
    print(browser)
    combined_data = []
    combined_headers = []
    try:
        page = await browser.newPage()
        print_current_thread()
        print("Launching browser..")
        print(f"Opening page from URL: {PAGE_URL}")
        await page.goto(PAGE_URL, waitUntil="domcontentloaded")
        print(f"opened  successfully")
        if "403 Forbidden" in await page.content():
            CTkMessagebox(
                title="Error",
                message="Internal Error Occurred while running application. Please Try Again!!",
                icon="cancel",
            )
        else:
            # Converting date strings to datetime objects
            current_date = datetime.strptime(start_date, "%B %d, %Y")
            end_date = datetime.strptime(end_date, "%B %d, %Y")
            while current_date <= end_date:
                # print(current_date)
                formatted_date = current_date.strftime("%B %d, %Y")
                print(formatted_date)
                print(f"data scrapping on the dated {current_date}")
                await page.waitForSelector("#daily-report-datepicker", timeout=60000)
                print("daily-report-datepicker element is found")
                await page.click("#daily-report-datepicker")
                print("daily-report-datepicker element is clicked")
                viewport_height = await page.evaluate("window.innerHeight")
                print("viewport_height element is found")
                scroll_distance = int(viewport_height * 0.3)
                print(f"scroll_distance is  {scroll_distance}")
                await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                print(f"scroll_distance progress")
                await asyncio.sleep(5)
                await page.type(
                    "#daily-report-datepicker", current_date.strftime("%B %d, %Y")
                )
                # print_the_output_statement(
                #     output, f"Fetching data for the date  {formatted_date}..."
                # )
                print(f"Typed '{formatted_date}' into the input box")
                await page.waitForSelector("#daily-report-submit")
                print("daily-report-submit element is found")
                await page.click("#daily-report-submit")
                print("daily-report-submit element is clicked")
                await asyncio.sleep(10)
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
                # Evaluate the script on the page
                element_exists = await page.evaluate(check_script)
                if element_exists:
                    print_the_output_statement(
                        output,
                        f"There were no new applications taken on the selected report date. {formatted_date}:",
                    )
                else:
                    scroll_distance = int(viewport_height * 1.1)
                    print(f"Scroll Distanced {scroll_distance}")
                    await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                    print("Scrolling....................")
                    await page.waitForSelector('select[name="license_report_length"]')
                    print("license_report_length element is found")
                    await page.select(
                        'select[name="license_report_length"]', "100"
                    )  # Selecting option '50'
                    print("Option selected successfully.")
                    await asyncio.sleep(5)
                    headers = await page.evaluate(
                        """() => {
                        const table = document.querySelector('.display.table.table-striped.dataTable.no-footer');
                        const headerRow = table.querySelector('thead tr');
                        return Array.from(headerRow.querySelectorAll('th')).map(header => header.innerText.trim());
                    }"""
                    )
                    if not combined_headers:
                        combined_headers = headers + ["Report Date"]
                    print("combined_headers", combined_headers)
                    while True:
                        # Extracting table data
                        table_data = await page.evaluate(
                            """() => {
                            const table = document.querySelector('.display.table.table-striped.dataTable.no-footer');
                            const rows = Array.from(table.querySelectorAll('tbody tr'));
                            return rows.map(row => {
                                const columns = Array.from(row.querySelectorAll('td, th'));
                                return columns.map(column => column.innerText.trim());
                            });
                        }"""
                        )
                        for row in table_data:
                            row.append(current_date.strftime("%B %d, %Y"))
                            combined_data.append(row)
                        next_button = await page.querySelector("#license_report_next")
                        print("next_button element is found")
                        if not next_button:
                            print_the_output_statement(
                                output, f"No more data found for {formatted_date}"
                            )
                            break  # Exit loop if "Next" button not found
                        is_disabled = await page.evaluate(
                            '(nextButton) => nextButton.classList.contains("disabled")',
                            next_button,
                        )
                        print("is_disabled element is found")
                        if is_disabled:
                            break
                        await next_button.click()
                        print("next_button is clicked")
                        print(f"Clicked on Next button for next page")
                        await page.waitForSelector(
                            "#license_report tbody tr", timeout=30000
                        )
                        await asyncio.sleep(5)  # Adjust as needed
                        print("license_report tbody tr element is found")
                    print_the_output_statement(
                        output, f"Data found for {formatted_date}."
                    )
                # print("combined_data", combined_data)
                current_date += timedelta(days=1)
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
        print("converting array to json")
        json_data = convert_array_to_json(combined_headers, combined_data)
        print(
            "Regenerating the Second json on the based of the Primary Owner and Premises Addr."
        )
        json_data2 = generate_json_data(json_data)
        print("merging the two json and convert the combined json data ")
        final_json = merge_json(json_data, json_data2)
        # print('final_json', final_json)
        if len(combined_data) == 0 and len(combined_headers) == 0:
            CTkMessagebox(
                title="Error",
                message=f"No Report is found on the dated {start_date} & {end_date}",
                icon="cancel",
            )
        else:
            # print_the_output_statement(output, f"output is {json_data}")
            msg = CTkMessagebox(
                title="Info",
                message="Report Successfully Generated.\n Click ok to Download",
                # icon="info",
                option_1="Cancel",
                option_2="Ok",
            )
            if msg.get() == "Ok":
                save_folder = filedialog.askdirectory(
                    initialdir=os.getcwd(), title="Select Folder to Save Data"
                )
                if save_folder:
                    file_name = save_data_to_file(final_json, save_folder)
                    CTkMessagebox(
                        message=f"Generated Report Successfully on the dated {start_date} & {end_date} and save the file to  {file_name} ",
                        icon="check",
                        option_1="Thanks",
                    )
                else:
                    CTkMessagebox(
                        message=f"Generated Report Successfully on the dated {start_date} & {end_date} but you have cancelled the downlaod ",
                        icon="check",
                        option_1="Thanks",
                    )
        print_the_output_statement(
            output, f"Total execution time: {total_time:.2f} seconds"
        )


def handle_button_click(action):
    """
    Handle button click events based on the action parameter.

    Parameters:
    - action (str): The action to perform. 'start' starts the scraping process,
      'stop' stops the application.

    This function validates the selected date range and triggers the scraping
    process accordingly. It manages button states to ensure the UI remains responsive
    during asynchronous scraping tasks.
    """
    if action == "start":
        current_date_str = datetime.now().date().strftime("%B %d, %Y")
        current_date = datetime.strptime(current_date_str, "%B %d, %Y").date()
        print("current_date", current_date)
        start_date_str = start_date_entry.get_date().strftime("%B %d, %Y")
        start_date = datetime.strptime(start_date_str, "%B %d, %Y").date()
        print("start_date", start_date)
        end_date_str = end_date_entry.get_date().strftime("%B %d, %Y")
        end_date = datetime.strptime(end_date_str, "%B %d, %Y").date()
        print("end_date", end_date)
        print("date validation Initialized")
        if (
            start_date > current_date
            or end_date > current_date
            or start_date == current_date
            or end_date == current_date
        ):
            CTkMessagebox(
                title="Error",
                message="Please select a date that is 2 or more days past.",
                icon="cancel",
            )
        elif end_date < start_date:
            CTkMessagebox(
                title="Error",
                message="End date should be later than or equal to start date",
                icon="cancel",
            )
        else:
            scrape_button.config(state=tk.DISABLED)
            scrape_button1.config(state=tk.NORMAL)
            with ThreadPoolExecutor(max_workers=MAX_THREAD_COUNT) as executor:
                # Schedule the asyncio task in the event loop running in the main thread
                loop = asyncio.get_event_loop()
                asyncio_task = loop.create_task(
                    scrape_and_save_table_data(
                        start_date_str, end_date_str, output_text
                    )
                )
                loop.run_until_complete(asyncio_task)
                # Enable the generate report button after task completion
                scrape_button.config(state=tk.NORMAL)
                scrape_button1.config(state=tk.DISABLED)
    else:
        print("zxcxzcxzc")
        # root.destroy()


# Setting up the Tkinter GUI
if __name__ == "__main__":
    # Initialize Tkinter
    root = tk.Tk()
    root.title(APP_TITLE)

    # Custom Font
    root.option_add("*Font", "Handfine")

    # Heading label with custom font
    heading_label = tk.Label(
        root, text=APP_HEADING, font=("Handfine", 18, "bold italic"), pady=20
    )
    heading_label.pack()
    # Create a style for the shadow box effect
    style = ttk.Style()
    style.configure(
        "Shadow.TFrame", background="light blue", borderwidth=5, relief="ridge"
    )

    # Form frame for date selection
    form_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
    form_frame.pack(pady=20)
    # Modern color scheme
    # Start Date Label and Entry
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

    # End Date Label and Entry
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
    # Generate Report Button
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)
    # Generate Report Button
    scrape_button = tk.Button(
        button_frame,
        text=APP_BUTTON_NAME,
        command=lambda: handle_button_click("start"),
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

    scrape_button1 = tk.Button(
        button_frame,
        text="Cancel Browser",
        command=lambda: handle_button_click("stop"),
        font=("Arial", 12, "bold"),
        fg="white",
        bg="red",
        relief="solid",
        borderwidth=1,
        highlightbackground="blue",
        highlightcolor="blue",
        highlightthickness=2,
    )
    scrape_button1.pack(side=tk.LEFT, padx=10)

    # Create a frame for the tt widget with border and shadow effect
    output_frame = tk.Frame(root, bd=2, relief="groove", bg="white", padx=10, pady=10)
    output_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
    # Create output text widget inside the frame with light gray background
    output_text = tk.Text(
        output_frame, height=10, width=100, font=("Arial", 12), bg="#ccf7ff"
    )
    output_text.pack(fill=tk.BOTH, expand=True)
    # Configure a bold tag for the text widget
    output_text.tag_configure("bold", font=("Arial", 12, "bold"))
    # Start Tkinter event loop
    root.mainloop()
    print("Script execution completed!")
