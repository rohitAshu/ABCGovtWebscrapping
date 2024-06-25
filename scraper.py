import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QTextCursor
import asyncio
from pyppeteer import launch
import csv
from datetime import datetime, timedelta


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Web Scraping Application")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.start_date_label = QLabel("Start Date (e.g., June 22, 2024):")
        layout.addWidget(self.start_date_label)
        self.start_date_entry = QLineEdit()
        layout.addWidget(self.start_date_entry)

        self.end_date_label = QLabel("End Date (e.g., June 23, 2024):")
        layout.addWidget(self.end_date_label)
        self.end_date_entry = QLineEdit()
        layout.addWidget(self.end_date_entry)

        self.start_button = QPushButton("Start Scraping")
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

    def show_message(self, message):
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(message + "\n")
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()

    def validate_date_format(self, date_str):
        try:
            datetime.strptime(date_str, '%B %d, %Y')
            return True
        except ValueError:
            return False

    async def scrape_and_save_table_data(self, start_date_str, end_date_str):
        start_time = datetime.now()
        executable_path = '/usr/bin/google-chrome'

        browser = await launch(headless=False, executablePath=executable_path, defaultViewport=None,
                               args=['--start-maximized'])
        page = await browser.newPage()

        try:
            self.show_message("Launching browser...")

            await page.goto("https://www.abc.ca.gov/licensing/licensing-reports/new-applications/",
                            waitUntil='domcontentloaded')

            start_date = datetime.strptime(start_date_str, '%B %d, %Y')
            end_date = datetime.strptime(end_date_str, '%B %d, %Y')

            all_table_data = []

            while start_date <= end_date:
                formatted_date = start_date.strftime('%B %d, %Y')

                self.show_message(f"Scraping data for {formatted_date}...")

                await page.waitForSelector('#daily-report-datepicker')
                await page.click('#daily-report-datepicker')

                await page.waitForSelector('.ui-datepicker-calendar')

                await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 3)')

                await page.type('#daily-report-datepicker', formatted_date)

                await page.waitForSelector('#daily-report-submit')
                await page.click('#daily-report-submit')

                await asyncio.sleep(5)

                await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.6)')

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

                        self.show_message(f"Table data from page {page_number} for {formatted_date} appended.")
                        page_number += 1

                        await next_button.click()
                        await asyncio.sleep(5)

                else:
                    self.show_message(f"Table with id 'license_report' not found for date: {formatted_date}")

                start_date += timedelta(days=1)

            csv_file_name = f'table_data_{start_date_str}_{end_date_str}.csv'
            with open(csv_file_name, 'w', newline='', encoding='utf-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerows(all_table_data)

            self.show_message(f"All table data from {start_date_str} to {end_date_str} saved to '{csv_file_name}' successfully.")

        finally:
            await browser.close()
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            self.show_message(f"Total execution time: {total_time:.2f} seconds")

    def start_scraping(self):
        start_date_str = self.start_date_entry.text().strip()
        end_date_str = self.end_date_entry.text().strip()

        self.output_text.clear()

        if not start_date_str or not end_date_str:
            self.show_message("Please enter both start and end dates.")
            return

        if not self.validate_date_format(start_date_str) or not self.validate_date_format(end_date_str):
            self.show_message("Invalid date format. Please use format like 'June 22, 2024'.")
            return

        asyncio.run(self.scrape_and_save_table_data(start_date_str, end_date_str))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
