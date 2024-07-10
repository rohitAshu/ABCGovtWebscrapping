import asyncio
from pyppeteer import launch

from utils import find_chrome_executable

def pyppeteerBrowserInit(loop, headless, width, height):
    """
    Initializes a Pyppeteer browser instance with the specified parameters.

    Args:
        loop (asyncio.AbstractEventLoop): The event loop to use for asynchronous operations.
        headless (bool): Whether to run the browser in headless mode.
        width (int): The width of the browser window.
        height (int): The height of the browser window.

    Returns:
        browser (pyppeteer.browser.Browser or None): The initialized browser instance, or None if an error occurred.
    """
    # Find the path to the Chrome executable
    executable_path = find_chrome_executable()
    print("executable_path", executable_path)
    print(f"Using random window size: {width}x{height}")

    # Set the provided event loop as the current event loop
    asyncio.set_event_loop(loop)

    try:
        # Launch the browser with the specified arguments
        browser = loop.run_until_complete(
            launch(
                executablePath=executable_path,
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    f'--window-size={width},{height}',
                    '--start-maximized',
                    '--disable-notifications',
                    '--disable-popup-blocking',
                    '--ignore-certificate-errors',
                    '--allow-file-access',
                    '--allow-running-insecure-content',
                    '--disable-web-security',
                    '--user-data-dir=/tmp/pyppeteer',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-background-networking'
                ]
            )
        )
        return browser

    except Exception as e:
        # Print the error and return None if an exception occurs
        print(f"Error initializing browser: {e}")
        return None
