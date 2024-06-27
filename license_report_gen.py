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
- start_scraping_genrating_daily_report_async: Initiates scraping based on user-selected date range.
- generating_report: Callback function for GUI button to start the scraping process.
- Other utility functions imported from 'utils.py' for printing output and saving data to file.

"""

import asyncio
import os
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog
from tkinter import ttk
from CTkMessagebox import CTkMessagebox
from pyppeteer import launch
from pyppeteer.errors import PageError, ElementHandleError
from tkcalendar import DateEntry
from utils import print_the_output_statement, save_data_to_file, find_chrome_executable

# Application constants
APP_TITLE = "Daily License Report"
APP_HEADING = "Welcome to the ABC Liquor Daily Report App"
APP_BUTTON_NAME = "Generate Report"
PAGE_URL = "https://www.abc.ca.gov/licensing/licensing-reports/new-applications/"
HEADLESS = False


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
    print_the_output_statement(
        output, "Data Processing Started..."
    )
    print_the_output_statement(
        output, "Please wait for the Report generation."
    )
    executable_path = find_chrome_executable()
    print(executable_path)
    # Launching the browser
    browser = await launch(
        {
            "headless": HEADLESS,
            "executablePath": executable_path,
            "defaultViewport": None,
        }
    )
    page = await browser.newPage()
    try:
        print("Launching browser..")
        await page.goto(PAGE_URL, waitUntil="domcontentloaded")
        print(f"Opening page from URL: {PAGE_URL}")
        combined_data = []
        combined_headers = []

        # Converting date strings to datetime objects
        current_date = datetime.strptime(start_date, "%B %d, %Y")
        end_date = datetime.strptime(end_date, "%B %d, %Y")

        # Loop through each date in the ranger
        while current_date <= end_date:
            formatted_date = current_date.strftime("%B_%d_%Y")
            await page.waitForSelector("#daily-report-datepicker")
            await page.click("#daily-report-datepicker")

            await page.waitForSelector(".ui-datepicker-calendar", timeout=60000)
            viewport_height = await page.evaluate("window.innerHeight")
            scroll_distance = int(viewport_height * 0.3)

            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")

            await page.type(
                "#daily-report-datepicker", current_date.strftime("%B %d, %Y")
            )
            print_the_output_statement(
                output, f"Fetching data for the date  {formatted_date}..."
            )
            print(f"Typed '{formatted_date}' into the input box")
            await page.waitForSelector("#daily-report-submit")
            await page.click("#daily-report-submit")

            await asyncio.sleep(5)

            scroll_distance = int(viewport_height * 1.1)
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")

            try:
                await page.waitForSelector(
                    'select[name="license_report_length"]', timeout=60000
                )
                await page.click('select[name="license_report_length"]')
                await page.waitForSelector(
                    'select[name="license_report_length"] option', timeout=60000
                )
                await page.select('select[name="license_report_length"]', "100")
                await asyncio.sleep(5)
            except ElementHandleError as e:
                print_the_output_statement(
                    output, f"No data found for {formatted_date}: {str(e)}"
                )
                current_date += timedelta(days=1)
                continue

            try:
                # Extracting table headers
                headers = await page.evaluate(
                    """() => {
                    const table = document.querySelector('.display.table.table-striped.dataTable.no-footer');
                    const headerRow = table.querySelector('thead tr');
                    return Array.from(headerRow.querySelectorAll('th')).map(header => header.innerText.trim());
                }"""
                )

                if not combined_headers:
                    combined_headers = headers + ["Report Date"]

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
                    if not next_button:
                        print_the_output_statement(
                            output, f"No more data found for {formatted_date}"
                        )
                        break  # Exit loop if "Next" button not found

                    is_disabled = await page.evaluate(
                        '(nextButton) => nextButton.classList.contains("disabled")',
                        next_button,
                    )
                    if is_disabled:
                        break

                    await next_button.click()
                    print(f"Clicked on Next button for next page")
                    await page.waitForSelector(
                        "#license_report tbody tr", timeout=30000
                    )
                    await asyncio.sleep(5)  # Adjust as needed
                print_the_output_statement(output, f"Data found for {formatted_date}.")
            except (PageError, ElementHandleError) as e:
                print_the_output_statement(
                    output, f"No data found for {formatted_date}: {str(e)}"
                )
            current_date += timedelta(days=1)

        # Asking user to select a folder to save the data
        save_folder = filedialog.askdirectory(
            initialdir=os.getcwd(), title="Select Folder to Save Data"
        )
        if save_folder:
            file_name = save_data_to_file(combined_headers, combined_data, save_folder)
            print_the_output_statement(
                output,
                f"Download the Generated Report on the {save_folder} file is {file_name}",
            )

    finally:
        await browser.close()
        end_time = time.time()
        total_time = end_time - start_time
        print_the_output_statement(
            output, f"Total execution time: {total_time:.2f} seconds"
        )

        CTkMessagebox(
            title="Report Status",  # Set the title of the message box,
            message="Generated Report Successfully",
            icon="check",
            option_1="Thanks"
        )


# Function to validate date inputs and start the scraping process
async def start_scraping_genrating_daily_report_async(
    start_date_str, end_date_str, outputted
):
    """
    Validates the selected start and end dates against the current date
    and initiates asynchronous scraping and data saving if validation passes.

    Args:
        start_date_str (str): Selected start date in "%B %d, %Y" format.
        end_date_str (str): Selected end date in "%B %d, %Y" format.
        outputted (tk.Text): tkinter Text widget to display output or errors.

    Notes:
        - Converts `start_date_str` and `end_date_str` to datetime objects for comparison.
        - Checks if the selected dates are valid based on current date and relative comparisons.
        - Displays error messages using `CTkMessagebox` if date validations fail.
        - Calls `scrape_and_save_table_data` asynchronously if date validations pass.
    """
    current_date_str = datetime.now().date().strftime("%B %d, %Y")
    current_date = datetime.strptime(current_date_str, "%B %d, %Y").date()
    print("current_date", current_date)
    start_date = datetime.strptime(start_date_str, "%B %d, %Y").date()
    print("start_date", start_date)
    end_date = datetime.strptime(end_date_str, "%B %d, %Y").date()
    print("end_date", end_date)
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
        await scrape_and_save_table_data(start_date_str, end_date_str, outputted)


# Function to handle the button click event
def generating_report():
    """
    Initiates an asynchronous task to start scraping and generating a daily report
    using the selected start and end dates from GUI input fields.

    Notes:
        - Requires global variables or accessible objects `start_date_entry`,
          `end_date_entry`, and `output_text` to retrieve dates and display output.
        - Converts the selected dates into formatted strings ("%B %d, %Y").
    """
    start_date_str = start_date_entry.get_date().strftime("%B %d, %Y")
    end_date_str = end_date_entry.get_date().strftime("%B %d, %Y")
    asyncio.run(
        start_scraping_genrating_daily_report_async(
            start_date_str, end_date_str, output_text
        )
    )


# Setting up the Tkinter GUI
if __name__ == "__main__":
    # Initialize Tkinter
    root = tk.Tk()
    root.title(APP_TITLE)

    # # Maximize the window to full-screen (optional)
    # root.attributes("-zoomed", True)  # for Windows/Linux
    # root.attributes('-fullscreen', True)  # for macOS

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
    scrape_button = tk.Button(
        root,
        text=APP_BUTTON_NAME,
        command=generating_report,
        font=("Arial", 12, "bold"),
        fg="white",
        bg="blue",
    )
    scrape_button.pack()

    # Create a frame for the text widget with border and shadow effect
    output_frame = tk.Frame(root, bd=2, relief="groove", bg="white", padx=10, pady=10)
    output_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    # Create output text widget inside the frame with light gray background
    output_text = tk.Text(
        output_frame, height=10, width=100, font=("Arial", 12), bg="light blue"
    )
    output_text.pack(fill=tk.BOTH, expand=True)

    # Configure a bold tag for the text widget
    output_text.tag_configure("bold", font=("Arial", 12, "bold"))

    # Start Tkinter event loop
    root.mainloop()

    print("Script execution completed!")
