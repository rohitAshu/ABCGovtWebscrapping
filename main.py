import asyncio
from pyppeteer import launch
import time
import csv
from datetime import datetime, timedelta


async def scrape_and_save_table_data(start_date_str, end_date_str):
    start_time = time.time()
    executable_path = '/usr/bin/google-chrome'

    browser = await launch(headless=True, executablePath=executable_path, defaultViewport=None,
                           args=['--start-maximized'])
    page = await browser.newPage()

    try:
        await page.goto("https://www.abc.ca.gov/licensing/licensing-reports/new-applications/",
                        waitUntil='domcontentloaded')

        start_date = datetime.strptime(start_date_str, '%B %d, %Y')
        end_date = datetime.strptime(end_date_str, '%B %d, %Y')

        # Initialize an empty list to accumulate all table data
        all_table_data = []

        while start_date <= end_date:
            formatted_date = start_date.strftime('%B %d, %Y')

            await page.waitForSelector('#daily-report-datepicker')
            await page.click('#daily-report-datepicker')
            print(f"Input box clicked successfully for {formatted_date}")

            # Wait for the date picker to fully load
            await page.waitForSelector('.ui-datepicker-calendar')

            # Calculate the scroll height for 30% of the viewport height
            viewport_height = await page.evaluate('window.innerHeight')
            scroll_distance = int(viewport_height * 0.3)

            # Scroll down by 30% of the viewport height
            await page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            print("Scrolled down by 30%")

            # Type the formatted date into the input field
            await page.type('#daily-report-datepicker', formatted_date)
            print(f"Typed '{formatted_date}' into the input box")

            # Click on the submit button
            await page.waitForSelector('#daily-report-submit')
            await page.click('#daily-report-submit')
            print("Clicked on Submit button")

            await asyncio.sleep(5)  # Wait for a few seconds after clicking submit

            # Scroll down by another 60% of the viewport height (adjust as needed)
            await page.evaluate(f'window.scrollBy(0, {int(viewport_height * 0.6)})')
            print("Scrolled down by additional 60%")

            await asyncio.sleep(5)  # Wait for a few seconds to observe the scroll action

            # Check if the table with id 'license_report' exists
            table_exists = await page.querySelector('#license_report')
            if table_exists:
                # Initialize CSV headers once (for the first date only)
                if start_date == datetime.strptime(start_date_str, '%B %d, %Y'):
                    headers = await page.evaluate('''() => {
                        const table = document.querySelector('#license_report');
                        const headerRow = table.querySelector('thead tr');
                        return Array.from(headerRow.querySelectorAll('th')).map(header => header.innerText.trim());
                    }''')

                    all_table_data.append(headers)  # Add headers to the accumulated data

                # Process pagination to click on "Next" button until disabled
                page_number = 1
                while True:
                    next_button = await page.querySelector('#license_report_next')
                    if not next_button:
                        break  # Exit loop if "Next" button not found

                    is_disabled = await page.evaluate('(nextButton) => nextButton.classList.contains("disabled")',
                                                      next_button)
                    if is_disabled:
                        break  # Exit loop if "Next" button is disabled

                    # Wait for the table to load on the next page
                    await page.waitForSelector('#license_report tbody tr')
                    await asyncio.sleep(5)  # Adjust as needed

                    # Extract table data from the next page
                    table_data = await page.evaluate('''() => {
                        const table = document.querySelector('#license_report');
                        const rows = Array.from(table.querySelectorAll('tbody tr'));
                        return rows.map(row => {
                            const columns = Array.from(row.querySelectorAll('td, th'));
                            return columns.map(column => column.innerText.trim()); // Trim whitespace
                        });
                    }''')

                    all_table_data.extend(table_data)  # Extend the accumulated data with current page data

                    print(f"Table data from page {page_number} for {formatted_date} appended to accumulated data.")

                    page_number += 1  # Increment page number

                    # Click on "Next" button for pagination
                    await next_button.click()
                    print(f"Clicked on Next button for page {page_number}")

                    await asyncio.sleep(5)  # Wait for a few seconds after clicking "Next"

            else:
                print(f"Table with id 'license_report' not found for date: {formatted_date}")

            start_date += timedelta(days=1)  # Move to the next date

        # Write all accumulated data to a single CSV file
        csv_file_name = f'table_data_{start_date_str}_{end_date_str}.csv'
        with open(csv_file_name, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerows(all_table_data)

        print(f"All table data from {start_date_str} to {end_date_str} saved to '{csv_file_name}' successfully.")

    finally:
        await browser.close()
        end_time = time.time()
        total_time = end_time - start_time
        print(f"Total execution time: {total_time:.2f} seconds")


if __name__ == "__main__":
    start_date = 'June 22, 2024'
    end_date = 'June 23, 2024'
    asyncio.run(scrape_and_save_table_data(start_date, end_date))
    print("Script execution completed!")
