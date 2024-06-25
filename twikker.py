import tkinter as tk
import asyncio
from pyppeteer import launch
import time
import csv
from datetime import datetime, timedelta


async def scrape_and_save_table_data(start_date_str, end_date_str, output_text):
    start_time = time.time()
    executable_path = '/usr/bin/google-chrome'

    browser = await launch(headless=False, executablePath=executable_path, defaultViewport=None,
                           args=['--start-maximized'])
    page = await browser.newPage()

    try:
        output_text.insert(tk.END, "Launching browser...\n")
        output_text.update()

        await page.goto("https://www.abc.ca.gov/licensing/licensing-reports/new-applications/",
                        waitUntil='domcontentloaded')

        start_date = datetime.strptime(start_date_str, '%B %d, %Y')
        end_date = datetime.strptime(end_date_str, '%B %d, %Y')

        # Initialize an empty list to accumulate all table data
        all_table_data = []

        while start_date <= end_date:
            formatted_date = start_date.strftime('%B %d, %Y')

            output_text.insert(tk.END, f"Pulling  data for {formatted_date}...\n")
            output_text.update()

            await page.waitForSelector('#daily-report-datepicker')
            await page.click('#daily-report-datepicker')

            await page.waitForSelector('.ui-datepicker-calendar')

            viewport_height = await page.evaluate('window.innerHeight')
            await page.evaluate(f'window.scrollBy(0, {int(viewport_height * 0.3)})')

            await page.type('#daily-report-datepicker', formatted_date)

            await page.waitForSelector('#daily-report-submit')
            await page.click('#daily-report-submit')

            await asyncio.sleep(5)

            await page.evaluate(f'window.scrollBy(0, {int(viewport_height * 0.6)})')

            await asyncio.sleep(5)

            table_exists = await page.querySelector('#license_report')
            if table_exists:
                if start_date == datetime.strptime(start_date_str, '%B %d, %Y'):
                    headers = await page.evaluate('''() => {
                        const table = document.querySelector('#license_report');
                        const headerRow = table.querySelector('thead tr');
                        return Array.from(headerRow.querySelectorAll('th')).map(header => header.innerText.trim());
                    }''')

                    all_table_data.append(headers)

                page_number = 1
                while True:
                    next_button = await page.querySelector('#license_report_next')
                    if not next_button:
                        break

                    is_disabled = await page.evaluate('(nextButton) => nextButton.classList.contains("disabled")',
                                                      next_button)
                    if is_disabled:
                        break

                    await page.waitForSelector('#license_report tbody tr')
                    await asyncio.sleep(5)

                    table_data = await page.evaluate('''() => {
                        const table = document.querySelector('#license_report');
                        const rows = Array.from(table.querySelectorAll('tbody tr'));
                        return rows.map(row => {
                            const columns = Array.from(row.querySelectorAll('td, th'));
                            return columns.map(column => column.innerText.trim());
                        });
                    }''')

                    all_table_data.extend(table_data)

                    output_text.insert(tk.END, f"Table data from page {page_number} for {formatted_date} appended.\n")
                    output_text.update()

                    page_number += 1

                    await next_button.click()
                    await asyncio.sleep(5)

            else:
                output_text.insert(tk.END, f"Table with id 'license_report' not found for date: {formatted_date}\n")
                output_text.update()

            start_date += timedelta(days=1)

        csv_file_name = f'table_data_{start_date_str}_{end_date_str}.csv'
        with open(csv_file_name, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(all_table_data)

        output_text.insert(tk.END, f"All table data from {start_date_str} to {end_date_str} saved to '{csv_file_name}' successfully.\n")
        output_text.update()

    finally:
        await browser.close()
        end_time = time.time()
        total_time = end_time - start_time
        output_text.insert(tk.END, f"Total execution time: {total_time:.2f} seconds\n")
        output_text.update()


async def start_scraping_async():
    start_date_str = start_date_entry.get()
    end_date_str = end_date_entry.get()

    output_text.delete(1.0, tk.END)  # Clear previous output

    if not start_date_str or not end_date_str:
        output_text.insert(tk.END, "Please enter both start and end dates.\n")
    else:
        await scrape_and_save_table_data(start_date_str, end_date_str, output_text)


def start_scraping():
    asyncio.run(start_scraping_async())


# Create the main tkinter window
root = tk.Tk()
root.title("Daily License Report")

# Create labels and entry widgets
start_date_label = tk.Label(root, text="Start Date (e.g., June 22, 2024):")
start_date_label.pack()
start_date_entry = tk.Entry(root, width=40)
start_date_entry.pack()

end_date_label = tk.Label(root, text="End Date (e.g., June 23, 2024):")
end_date_label.pack()
end_date_entry = tk.Entry(root, width=40)
end_date_entry.pack()

start_button = tk.Button(root, text="Generate Report", command=start_scraping)
start_button.pack()

output_text = tk.Text(root, height=20, width=80)
output_text.pack()

root.mainloop()
