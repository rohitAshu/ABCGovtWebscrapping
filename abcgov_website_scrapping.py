import asyncio
from pyppeteer import launch
import time
import csv
from datetime import datetime, timedelta
from pyppeteer.errors import PageError

async def validate_dates(start_date, end_date):
    current_date = datetime.now().date()
    start_date = datetime.strptime(start_date, '%B %d, %Y').date()
    end_date = datetime.strptime(end_date, '%B %d, %Y').date()

    if start_date > current_date and end_date > current_date:
        raise ValueError("Please select a date that is 2 or more days past.")

    if end_date < start_date:
        raise ValueError("End date should be later than or equal to start date.")

async def scrape_and_save_table_data(start_date, end_date):
    try:
        await validate_dates(start_date, end_date)
    except ValueError as e:
        print(f"Error: {str(e)}")
        return
    
    start_time = time.time()
    executable_path = '/usr/bin/google-chrome'
    
    browser = await launch(headless=False, executablePath=executable_path, defaultViewport=None)
    page = await browser.newPage()

    try:
        await page.goto("https://www.abc.ca.gov/licensing/licensing-reports/new-applications/", waitUntil='domcontentloaded')

        combined_data = []
        combined_headers = []

        current_date = datetime.strptime(start_date, '%B %d, %Y')
        end_date = datetime.strptime(end_date, '%B %d, %Y')

        while current_date <= end_date:
            formatted_date = current_date.strftime('%B_%d_%Y')

            await page.waitForSelector('#daily-report-datepicker')
            await page.click('#daily-report-datepicker')

            await page.waitForSelector('.ui-datepicker-calendar')
            viewport_height = await page.evaluate('window.innerHeight')
            scroll_distance = int(viewport_height * 0.3)

            await page.evaluate(f'window.scrollBy(0, {scroll_distance})')

            await page.type('#daily-report-datepicker', current_date.strftime('%B %d, %Y'))
            print(f"Typed '{formatted_date}' into the input box")

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
                print(f"No data found for {formatted_date}.")
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
                        print(f"No more data available for {formatted_date}.")
                        break  # Exit loop if "Next" button not found

                    is_disabled = await page.evaluate('(nextButton) => nextButton.classList.contains("disabled")', next_button)
                    if is_disabled:
                        print(f"No more data available for {formatted_date}.")
                        break  # Exit loop if "Next" button is disabled

                    await next_button.click()
                    print(f"Clicked on Next button for next page")
                    await page.waitForSelector('#license_report tbody tr', timeout=30000)
                    await asyncio.sleep(5)  # Adjust as needed

                print(f"Table data for {formatted_date} collected successfully.")

            except PageError as e:
                print(f"No data found for {formatted_date}: {str(e)}")

            current_date += timedelta(days=1)

        # Save combined data to CSV
        file_name = 'combined_table_data.csv'
        if combined_data:
            with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(combined_headers)  # Write headers as the first row
                csvwriter.writerows(combined_data)  # Write data rows

            print(f"Combined table data saved to '{file_name}' successfully.")

    finally:
        await browser.close()
        end_time = time.time()
        total_time = end_time - start_time
        print(f"Total execution time: {total_time:.2f} seconds")

if __name__ == "__main__":
    start_date = 'June 9, 2024'
    end_date = 'June 15, 2024'
    asyncio.run(scrape_and_save_table_data(start_date, end_date))
    print("Script execution completed!")
