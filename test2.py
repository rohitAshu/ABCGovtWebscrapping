import os
import platform
import asyncio
from pyppeteer import launch
from screeninfo import get_monitors

def find_chrome_path():
    system = platform.system()
    if system == "Windows":
        chrome_paths = [
            os.path.join(
                os.environ["ProgramFiles"],
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ["ProgramFiles(x86)"],
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                return path
    elif system == "Linux":
        import shutil
        chrome_path = shutil.which("google-chrome")
        if chrome_path is None:
            chrome_path = shutil.which("google-chrome-stable")
        return chrome_path
    return None

async def main():
    chrome_path = find_chrome_path()
    if chrome_path:
        # Get the screen resolution
        monitor = get_monitors()[0]
        width = monitor.width
        height = monitor.height

        browser = await launch(executablePath=chrome_path, headless=HEADLESS, args=[f'--window-size={width},{height}'])
        page = await browser.newPage()
        
        # Set the viewport size
        await page.setViewport({'width': width, 'height': height})

        # Navigate to the login page
        await page.goto('https://abcbiz.abc.ca.gov/login')
        await page.waitFor(6000)

        username_xpath = '//*[@id="username"]'
        await page.waitForXPath(username_xpath)
        username_element = await page.xpath(username_xpath)
        await username_element[0].type('mike@calabc.com')
        await page.waitFor(3000)

        password_xpath = '//*[@id="password"]'
        await page.waitForXPath(password_xpath)
        password_element = await page.xpath(password_xpath)
        await password_element[0].type('19MichaelBrewer68!')
        await page.waitFor(3000)

        login_button_xpath = '//*[@id="root"]/div/div[3]/div/div/div[2]/div[1]/form/div[1]/button/span[1]'
        await page.waitForXPath(login_button_xpath)
        login_button_element = await page.xpath(login_button_xpath)
        await login_button_element[0].click()
        print("click the login button......!")

        await page.waitForNavigation()
        await asyncio.sleep(10)

        target_button_xpath = '//*[@id="root"]/div/div[3]/div/div[2]/div[1]/h1/div[2]/div/button/span/span'
        await page.waitForXPath(target_button_xpath)
        target_button_element = await page.xpath(target_button_xpath)
        await target_button_element[0].click()
        await asyncio.sleep(5)

        target_element_xpath = '//*[@id="long-menu"]/div[2]/ul/li'
        await page.waitForXPath(target_element_xpath)
        target_element = await page.xpath(target_element_xpath)
        await target_element[0].click()
        await asyncio.sleep(15)

        # Scroll the page down after clicking
        await page.evaluate('window.scrollBy(0, window.innerHeight)')

        await page.waitFor(9000)

        # Close the browser
        await browser.close()
    else:
        print("Chrome browser not found. Please install Chrome.")

if __name__ == "__main__":
    HEADLESS = False
    asyncio.get_event_loop().run_until_complete(main())
