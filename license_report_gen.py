import asyncio
import os
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog
from tkinter import ttk
from threading import Thread

from CTkMessagebox import CTkMessagebox
from pyppeteer import launch
import pyppeteer
from pyppeteer.errors import TimeoutError as PyppeteerTimeoutError
from tkcalendar import DateEntry

from utils import (
    convert_array_to_json,
    generate_json_data,
    merge_json,
    print_the_output_statement,
    find_chrome_executable,
    save_data_to_file,
)

# Application constants
APP_TITLE = "Daily License Report"
APP_HEADING = "Welcome to the ABC Liquor Daily Report App"
APP_BUTTON_NAME = "Generate Report"
APP_BUTTON_NAME1 = "Close Window"
PAGE_URL = "https://www.abc.ca.gov/licensing/licensing-reports/new-applications/"
HEADLESS = True
MAX_THREAD_COUNT = 10
# FILE constants
FILE_TYPE= 'csv' # csv or xlsx
FILE_NAME = "ABCLicensingReport"


def pyppeteerBrowserInit(loop):
    executable_path = find_chrome_executable()
    print("executable_path", executable_path)
    asyncio.set_event_loop(loop)
    try:
        browser = loop.run_until_complete(
            launch(
                {
                    "headless": HEADLESS,
                    "executablePath": executable_path,
                    "defaultViewport": None,
                }
            )
        )
        return browser
    except Exception as e:
        print(f"Error initializing browser: {e}")
        return None


async def page_load(page, date):
    pageurl = f"{PAGE_URL}/?RPTTYPE=2&RPTDATE={date}"
    print(f"Opening page from URL: {pageurl}")
    response = await page.goto(pageurl, waitUntil="domcontentloaded")
    if response.status == 404:
        print(f"Page not found: {pageurl}")
        return False
    elif response.status == 403:
        print("403 Forbidden")
        return False
    else:
        return True


async def scrape_and_save_table_data(browser, start_date, end_date, output, start_time):
    start_time = time.time()
    output.delete("1.0", tk.END)
    print_the_output_statement(output, "Data Processing Started...")
    print_the_output_statement(output, "Please wait for the Report generation.")
    combined_data = []
    combined_headers = []
    page = await browser.newPage()
    try:
        print(f"Opening page from URL: {PAGE_URL}")
        start_date = datetime.strptime(start_date, "%B %d, %Y")
        end_date = datetime.strptime(end_date, "%B %d, %Y")
        while start_date <= end_date:
            formatted_date = start_date.strftime(
                "%m/%d/%Y"
            ) 
            print(formatted_date)
            load_page = await page_load(page, formatted_date)
            if load_page:
                print(f"opened  successfully")
                await asyncio.sleep(5)  
                viewport_height = await page.evaluate("window.innerHeight")
                print("viewport_height element is found")
                scroll_distance = int(viewport_height * 0.3)
                print(f"scroll_distance is  {scroll_distance}")
                await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                print(f"scroll_distance progress")
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
                else:
                    scroll_distance = int(viewport_height * 1.1)
                    print(f"Scroll Distanced {scroll_distance}")
                    await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                    print("Scrolling....................")
                    await page.waitForSelector('select[name="license_report_length"]')
                    print("license_report_length element is found")
                    await page.select(
                        'select[name="license_report_length"]', "100"
                    ) 
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
                    while True:
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
                            row.append(start_date.strftime("%B %d, %Y"))
                            combined_data.append(row)
                        next_button = await page.querySelector("#license_report_next")
                        print("next_button element is found")
                        if not next_button:
                            print_the_output_statement(
                                output, f"No more data found for {formatted_date}"
                            )
                            break  
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
                        await asyncio.sleep(5) 
                        print("license_report tbody tr element is found")
                    print_the_output_statement(
                        output, f"Data found for {formatted_date}."
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
        print("converting array to json")
        json_data = convert_array_to_json(combined_headers, combined_data)
        print(
            "Regenerating the Second json on the based of the Primary Owner and Premises Addr."
        )
        json_data2 = generate_json_data(json_data)
        print("merging the two json and convert the combined json data ")
        final_json = merge_json(json_data, json_data2)
        if len(combined_data) == 0 and len(combined_headers) == 0:
            CTkMessagebox(
                title="Error",
                message=f"No Report is found on the dated {start_date} & {end_date}",
                icon="cancel",
            )
        else:
            msg = CTkMessagebox(
                title="Info",
                message="Report Successfully Generated.\n Click ok to Download",
                option_1="Cancel",
                option_2="Ok",
            )
            if msg.get() == "Ok":
                save_folder = filedialog.askdirectory(
                    initialdir=os.getcwd(), title="Select Folder to Save Data"
                )
                if save_folder:
                    start_date_str = start_date_entry.get_date().strftime("%B %d, %Y")
                    enend_date_str = end_date_entry.get_date().strftime("%B %d, %Y")
                    FileName = f"{FILE_NAME}_{start_date_str}_{enend_date_str}"
                    file_name = save_data_to_file(final_json, save_folder,FileName, FILE_TYPE)
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
        print_the_output_statement(output, f"Total execution time: {total_time:.2f} seconds")


def run_scraping_thread(loop, browser, start_date_str, end_date_str, output_text, start_time):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        scrape_and_save_table_data(
            browser, start_date_str, end_date_str, output_text, start_time
        )
    )


def generate_daily_report():
    start_time = time.time()
    current_date_str = datetime.now().date().strftime("%B %d, %Y")
    current_date = datetime.strptime(current_date_str, "%B %d, %Y").date()
    print("current_date", current_date)
    start_date_str = start_date_entry.get_date().strftime("%B %d, %Y")
    start_date = datetime.strptime(start_date_str, "%B %d, %Y").date()
    print("start_date", start_date)
    end_date_str = end_date_entry.get_date().strftime("%B %d, %Y")
    end_date = datetime.strptime(end_date_str, "%B %d, %Y").date()
    print("end_date", end_date)
    print("date vaidation Start")
    if (
        start_date > current_date
        or end_date > current_date
        or start_date == current_date
        or end_date == current_date
    ):
        print("Please select a date that is 2 or more days past.")
        CTkMessagebox(
            title="Error",
            message="Please select a date that is 2 or more days past.",
            icon="cancel",
        )
    elif end_date < start_date:
        print("End date should be later than or equal to start date")
        CTkMessagebox(
            title="Error",
            message="End date should be later than or equal to start date",
            icon="cancel",
        )
    else:
        loop = asyncio.new_event_loop()
        print("browser init")
        browser = pyppeteerBrowserInit(loop)
        print("browser init completed")
        scrape_thread = Thread(
            target=run_scraping_thread,
            args=(loop, browser, start_date_str, end_date_str, output_text, start_time),
        )
        scrape_thread.start()


def close_window():
    root.destroy()


root = tk.Tk()
root.title(APP_TITLE)
root.option_add("*Font", "Handfine")

heading_label = tk.Label(root, text=APP_HEADING, font=("Handfine", 18, "bold italic"), pady=20)
heading_label.pack()
style = ttk.Style()
style.configure("Shadow.TFrame", background="light blue", borderwidth=5, relief="ridge")
form_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
form_frame.pack(pady=20)
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
button_frame = tk.Frame(root)
button_frame.pack(pady=20)
scrape_button = tk.Button(
    button_frame,
    text=APP_BUTTON_NAME,
    command= generate_daily_report,
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
    text=APP_BUTTON_NAME1,
    command= close_window,
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
output_frame = tk.Frame(root, bd=2, relief="groove", bg="white", padx=10, pady=10)
output_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
output_text = tk.Text(
    output_frame, height=10, width=100, font=("Arial", 12), bg="#ccf7ff"
)
output_text.pack(fill=tk.BOTH, expand=True)
output_text.tag_configure("bold", font=("Arial", 12, "bold"))
root.mainloop()
print("Script execution completed!")
