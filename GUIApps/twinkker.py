import asyncio
import csv
import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
from pyppeteer import launch
from pyppeteer.errors import PageError
from tkcalendar import DateEntry  # Import DateEntry widget from tkcalendar
import os


async def validate_dates(start_date, end_date):
    current_date = datetime.now().date()
    start_date = datetime.strptime(start_date, '%B %d, %Y').date()
    end_date = datetime.strptime(end_date, '%B %d, %Y').date()

    if start_date > current_date and end_date > current_date:
        raise ValueError("Please select a date that is 2 or more days past.")

    if end_date < start_date:
        raise ValueError("End date should be later than or equal to start date.")


async def print_output_text(output, message):
    output.insert(tk.END, message)
    output.update_idletasks()  # Update the widget immediately
    print(message)


async def scrape_and_save_table_data(start_date, end_date, output_text):
    start_time = time.time()
    output_text.insert(tk.END, 'Processing... Please wait for the result.')
    output_text.update_idletasks()  # Update the widget immediately
    executable_path = '/usr/bin/google-chrome'

    browser = await launch(headless=False, executablePath=executable_path, defaultViewport=None)
    page = await browser.newPage()

    try:
        await print_output_text(output_text, "Launching browser...\n")
        page_url = "https://www.abc.ca.gov/licensing/licensing-reports/new-applications/"
        await page.goto(page_url, waitUntil='domcontentloaded')
        await print_output_text(output_text, f"Opening page from URL: {page_url}\n")
    #
        combined_data = []
        combined_headers = []

        current_date = datetime.strptime(start_date, '%B %d, %Y')
        end_date = datetime.strptime(end_date, '%B %d, %Y')

        while current_date <= end_date:
            formatted_date = current_date.strftime('%B_%d_%Y')
            await print_output_text(output_text, f"Scraping data for {formatted_date}... \n")
            await page.waitForSelector('#daily-report-datepicker')
            await page.click('#daily-report-datepicker')

            await page.waitForSelector('.ui-datepicker-calendar')
            viewport_height = await page.evaluate('window.innerHeight')
            scroll_distance = int(viewport_height * 0.3)

            await page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            await page.type('#daily-report-datepicker', current_date.strftime('%B %d, %Y'))
            await print_output_text(output_text, f"Typed '{formatted_date}' into the input box \n")
            await page.waitForSelector('#daily-report-submit')
            await page.click('#daily-report-submit')
            await asyncio.sleep(5)
            scroll_distance = int(viewport_height * 1.1)
            await page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            dropdown_success = False
            try:
                await page.click('select[name="license_report_length"]')
                await page.waitForSelector('select[name="license_report_length"] option')
                await page.select('select[name="license_report_length"]', '100')
                dropdown_success = True

                await asyncio.sleep(5)

            except Exception as e:
                await print_output_text(output_text, f"No data found for {formatted_date}. \n")

                current_date += timedelta(days=1)
                continue

            try:
                headers = await page.evaluate('''() => {
                    const table = document.querySelector('.display.table.table-striped.dataTable.no-footer');
                    const headerRow = table.querySelector('thead tr');
                    return Array.from(headerRow.querySelectorAll('th')).map(header => header.innerText.trim());
                }''')

                if not combined_headers:
                    combined_headers = headers + ["Report Date"]

                while True:
                    table_data = await page.evaluate('''() => {
                        const table = document.querySelector('.display.table.table-striped.dataTable.no-footer');
                        const rows = Array.from(table.querySelectorAll('tbody tr'));
                        return rows.map(row => {
                            const columns = Array.from(row.querySelectorAll('td, th'));
                            return columns.map(column => column.innerText.trim());
                        });
                    }''')

                    for row in table_data:
                        row.append(current_date.strftime('%B %d, %Y'))
                        combined_data.append(row)

                    next_button = await page.querySelector('#license_report_next')
                    if not next_button:
                        await print_output_text(output_text, f"No more data available for {formatted_date}. \n")
                        break  # Exit loop if "Next" button not found

                    is_disabled = await page.evaluate('(nextButton) => nextButton.classList.contains("disabled")',
                                                      next_button)
                    if is_disabled:
                        await print_output_text(output_text, f"No more data available for {formatted_date}. \n")
                        break  # Exit loop if "Next" button is disabled

                    await next_button.click()
                    await print_output_text(output_text, f"Clicked on Next button for next page \n")
                    await page.waitForSelector('#license_report tbody tr', timeout=30000)
                    await asyncio.sleep(5)  # Adjust as needed

                await print_output_text(output_text, f"Table data for {formatted_date} collected successfully \n")

            except PageError as e:
                await print_output_text(output_text, f"No data found for {formatted_date}: {str(e)}\n")

            current_date += timedelta(days=1)

        # Save combined data to CSV
        folder_name = f'data'
        file_name = f'{folder_name}/combined_table_data_{start_date}_{end_date}.csv'
        # Ensure the folder exists
        os.makedirs(folder_name, exist_ok=True)
        if combined_data:
            with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(combined_headers)  # Write headers as the first row
                csvwriter.writerows(combined_data)  # Write data rows
            output_text.insert(tk.END, f"Combined table data saved to '{file_name}' successfully. \n")
            output_text.update_idletasks()  # Update the widget immediately
            await print_output_text(output_text, f"Combined table data saved to '{file_name}' successfully. \n")

    finally:
        await browser.close()
        end_time = time.time()
        total_time = end_time - start_time
        output_text.insert(tk.END, f"Total execution time: {total_time:.2f} seconds \n")
        output_text.update_idletasks()  # Update the widget immediately
        await print_output_text(output_text, f"Total execution time: {total_time:.2f} seconds \n")


async def start_scraping_async(start_date_str, end_date_str, output_text):
    current_date_str = datetime.now().date().strftime('%B %d, %Y')
    current_date = datetime.strptime(current_date_str, '%B %d, %Y').date()
    print('current_date', current_date)

    start_date = datetime.strptime(start_date_str, '%B %d, %Y').date()
    print('start_date', start_date)

    end_date = datetime.strptime(end_date_str, '%B %d, %Y').date()
    print('end_date', end_date)

    if start_date > current_date or end_date > current_date:
        messagebox.showerror("Error", "Please select a date that is 2 or more days past.")
    elif end_date < start_date:
        messagebox.showerror("Error", "End date should be later than or equal to start date.")
    else:
        await scrape_and_save_table_data(start_date_str, end_date_str, output_text)


def run_scraping():
    start_date_str = start_date_entry.get_date().strftime('%B %d, %Y')
    end_date_str = end_date_entry.get_date().strftime('%B %d, %Y')
    asyncio.run(start_scraping_async(start_date_str, end_date_str, output_text))


# GUI setup
root = tk.Tk()
root.title("Daily License Report")

# Centering the window on the screen

# Heading label
heading_label = tk.Label(root, text="Welcome to the ABC Liquor Daily Report App", font=('Helvetica', 18, 'bold'),
                         pady=20)
heading_label.pack()
# Frame for form elements
form_frame = tk.Frame(root)
form_frame.pack(pady=20)
# Start Date Entry using DateEntry widget from tkcalendar
start_date_label = tk.Label(form_frame, text="Start Date:")
start_date_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')
start_date_entry = DateEntry(form_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
start_date_entry.grid(row=0, column=1, padx=10, pady=10)

# End Date Entry using DateEntry widget from tkcalendar
end_date_label = tk.Label(form_frame, text="End Date:")
end_date_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')

end_date_entry = DateEntry(form_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
end_date_entry.grid(row=1, column=1, padx=10, pady=10)
# Button to start scraping
scrape_button = tk.Button(root, text="Generate Report", command=run_scraping)
scrape_button.pack()
# Output Box (Readonly)
output_text = tk.Text(root, height=10, width=60)
output_text.pack(pady=20)
#
# # Start the Tkinter main loop
root.mainloop()
