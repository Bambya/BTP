import requests
import pymongo
import re
import os.path
import traceback
from cfg_flipkart1 import config
from logger import logger
from bs4 import BeautifulSoup as bsoup
from time import sleep

def get_printers():

    # Initializing MongoDB database and collection
    myclient = pymongo.MongoClient(config['mongo_uri'])
    mydb = myclient["BTP"]
    mycol = mydb["PrintersFlipkart"]

    # drop collection values if already exists
    mycol.drop()

    # Get request to obtain html text from website
    try:
        logger.debug("Making HTTP GET request: " + config['website_url'])
        r = requests.get(config['website_url'])
        res = r.text
        logger.debug("Got HTML source, content length = " + str(len(res)))
    except:
        logger.exception("Failed to get HTML source from " + config['website_url'])
        traceback.print_exc()

    soup = bsoup(res, 'html.parser')

    # Optional - if you want to download the html to your disk
    '''with open(os.path.join(config["save_location"], "xyz.html"), 'w', encoding="utf-8") as f:
        f.write(res)'''

    # Get all the printer links and store them in a list
    a_tag = soup.find_all('a',class_="s1Q9rs")
    link_list = []
    for a in a_tag:
        link = a.get("href")
        link_list.append(link)

    print(len(link_list))

    count = 1

    # Make get request for every printer and store the data in Mongodb collection
    for printer_link in link_list:
        try:
            logger.debug("Making HTTP GET request for: " + "Printer " + str(count))
            r = requests.get(config['website_url'] + printer_link)
            res = r.text
            logger.debug("Got HTML source for: " + "Printer " + str(count))
        except:
            logger.exception("Failed to get HTML source from " + "Printer " + str(count))
            traceback.print_exc()

        dict = {"Printer Name": None, "Price": None, "Print Speed": None, "Auto Calibration Present": None, "Printing Technology": None,
                "Print Bed Type": None, "SD Card Support": None, "Build Volume": None, "Power Consumption": None, "Nozzle Diameter": None,
                "Filament Diameter": None, "Height": None, "Width": None, "Weight": None, "Warranty Summary": None, "Source": "Flipkart"}

        soup = bsoup(res, 'html.parser')
        tbody = soup.find_all('tbody')
        price = soup.find("div", class_="_30jeq3 _16Jk6d")
        name = soup.find("span", class_="B_NuCI")

        if price:
            dict["Price"] = price.get_text()
        if name:
            dict["Printer Name"] = name.get_text()

        # Printer parameters are given in the form of a table
        for t in tbody:
            tr = t.find_all('tr')
            for r in tr:
                td = r.find_all('td')
                if len(td) == 2:
                    parameter = td[0].get_text()               # td[0] contains parameter name
                    value = td[1].get_text()                   # td[1] contains the value of the parameter
                    if parameter in dict:
                        dict[parameter] = value

        mycol.insert_one(dict)

        count += 1


if __name__ == "__main__":

    logger.debug('Starting process')

    logger.debug('Getting links in database')

    get_printers()

    logger.debug('Process complete')
