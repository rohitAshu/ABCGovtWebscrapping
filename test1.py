import asyncio
from pyppeteer import launch
import time
import os
import pandas as pd
import shutil
from datetime import datetime, timedelta

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
    # the path where you want to save the downloaded files
    download_path = os.path.abspath(os.path.dirname(__file__))  # Current directory of the script
    target_folder = os.path.join(download_path, 'downloaded_files')
    
    start_time = time.time()
    executable_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'  # Update this path    
    browser = await launch(headless=False, executablePath=executable_path, defaultViewport=None)
    page = await browser.newPage()

    # Set the download behavior
    cdp = await page.target.createCDPSession()
    await cdp.send('Page.setDownloadBehavior', {
        'behavior': 'allow',
        'downloadPath': download_path
    })
    
    try:
        await page.goto("https://www.abc.ca.gov/licensing/licensing-reports/new-applications/", waitUntil='domcontentloaded')

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

            # Scroll down 90% of the page after submitting the date
            await asyncio.sleep(5)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.9)')

            # Click the button with the specified XPath
            await page.waitForXPath('//*[@id="license_report_wrapper"]/div[4]/div/button[1]')
            button = await page.xpath('//*[@id="license_report_wrapper"]/div[4]/div/button[1]')
            print("\n\n")
            print(formatted_date)
            print("\n\n")
            if button:
                await button[0].click()

            current_date += timedelta(days=1)
            await asyncio.sleep(5)

            # Move the downloaded file to the desired location with a unique name
            downloaded_files = os.listdir(download_path)
            for file_name in downloaded_files:
                if file_name.endswith('.csv'):  # Adjust the extension as needed
                    new_name = f"downloaded_file_{formatted_date}.csv"
                    await asyncio.sleep(5)
                    shutil.move(os.path.join(download_path, file_name), os.path.join(target_folder, new_name))
                    await asyncio.sleep(5)

    finally:
        await browser.close()
        dfs = []
        current_directory = os.getcwd()
        # Directory where your CSV files are located (assuming they are in a subdirectory)
        directory = os.path.join(current_directory, 'downloaded_files')
        
        # Loop through all CSV files in the directory
        for filename in os.listdir(directory):
            if filename.endswith(".csv"):
                file_path = os.path.join(directory, filename)
                df = pd.read_csv(file_path)
                dfs.append(df)

        # Concatenate all DataFrames into one
        merged_df = pd.concat(dfs, ignore_index=True)

        # Path to the output CSV file
        output_csv = os.path.join(current_directory, 'downloaded_files', 'merged_file.csv')

        # Write merged DataFrame to CSV
        merged_df.to_csv(output_csv, index=False)

        print(f"Merged data saved to {output_csv}")
        
        end_time = time.time()
        total_time = end_time - start_time
        print(f"Total execution time: {total_time:.2f} seconds")

if __name__ == "__main__":
    start_date = 'June 13, 2024'
    end_date = 'June 14, 2024'
    asyncio.run(scrape_and_save_table_data(start_date, end_date))
    print("Script execution completed!")
