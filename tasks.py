from contextlib import contextmanager
from pathlib import Path
import re
from time import sleep
from urllib.parse import urlparse, urlunparse, urljoin

from robocorp.tasks import task
from robocorp import browser

from bs4 import BeautifulSoup
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Tables import Tables
from RPA.Archive import Archive


@task
def minimal_task():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        slowmo=100,
    )
    open_robot_order_website()
    close_modal()
    fill_form_with_csv_data()
    archive_receipts()

def open_robot_order_website():
    """Navigates to the given URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def close_modal():
    """Close the alert modal"""
    browser.page().click("button:text('OK')")

def fill_form_with_csv_data():
    orders = get_orders()
    for order in orders:
        order_robot(order)

def archive_receipts():
    lib = Archive()
    lib.archive_folder_with_zip('output/', 'output/orders.zip', include='_receipt.pdf')

def order_robot(row_info: dict):
    """Fills the data in the form and export the order as pdf"""
    attempts = 3
    for i in range(attempts):
        try:
            fill_form(row_info)
            valid_error_in_order()
        except Exception as e:
            print(f'Attempt #{i + 1}: Error {str(e)}')
        else:
            export_order_as_pdf()
            order_another_robot()
            break
    
def fill_form(row_info: dict):
    """Fill the form with the info of the robot to be ordered"""
    page = browser.page()
    page.select_option("#head", str(row_info["Head"]))
    page.click(f'input[type="radio"][value="{str(row_info["Body"])}"]')
    page.fill('input[placeholder="Enter the part number for the legs"]', str(row_info['Legs']))
    page.fill("#address", row_info['Address'])
    page.click("button:text('Order')")


def order_another_robot():
    """After order a robot, click on another robot button and close a modal"""
    page = browser.page()
    page.click("button:text('Order another robot')")
    close_modal()


def export_order_as_pdf():
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()
    order_number = re.findall(r'RSB-ROBO-ORDER-([A-Z0-9]+)', receipt_html)
    order_number = order_number[0]
    pdf = PDF()
    with screenshot_robot(order_number) as path_img:
        content = f"{receipt_html}<br><img src=\"{path_img}\" alt=\"Robot {order_number}\" width=\"150\">"
        pdf.html_to_pdf(content, f"output/{order_number}_receipt.pdf")

@contextmanager
def screenshot_robot(order_number):
    """Take an screenshot of the recent ordered robot"""
    page = browser.page()
    path_screenshot = Path("output/{order_number}_robot.png")
    page.locator("#robot-preview-image").screenshot(path=path_screenshot)
    yield path_screenshot

    if path_screenshot.exists():
        path_screenshot.unlink()

def valid_error_in_order():
    """In case of error processing an order an exception will be raised"""
    page = browser.page()
    alert_locator = page.locator('div.alert.alert-danger')
    if alert_locator.is_visible():
        raise Exception('OrderError')

def get_orders():
    """Downloads csv file from the given URL"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    library = Tables()
    return library.read_table_from_csv("orders.csv")

# URL Resources

# def convert_relative_urls_to_absolute(html, base_url):
#     """Convert all the relative urls to absolute"""
#     soup = BeautifulSoup(html, 'html.parser')
    
#     url_attrs = ['src', 'href', 'data-src']

#     for tag in soup.find_all(True):
#         for attr in url_attrs:
#             if tag.has_attr(attr):
#                 attr_value = tag[attr]
#                 if attr_value and not attr_value.startswith(('http://', 'https://', 'mailto:', 'data:')):
#                     tag[attr] = urljoin(base_url, attr_value)
    
#     return str(soup)


# def get_base_url(full_url):
#     """Get the full url of an absolute url"""
#     parsed_url = urlparse(full_url)
#     return urlunparse((
#         parsed_url.scheme,
#         parsed_url.netloc,
#         '',  # path
#         '',  # params
#         '',  # query
#         ''   # fragment
#     ))
