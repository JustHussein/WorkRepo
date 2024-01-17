import logging
import pyodbc
import xml.etree.ElementTree as ET
import socket



logger = logging.getLogger("connection")


try:

    logger.debug("start creating connection.")
    xmltree = ET.parse('./config.xml')
    xmlroot = xmltree.getroot()
    logger.debug("read config file")

    host = xmlroot.find('host').text
    database = xmlroot.find('database').text
    username = xmlroot.find('username').text
    password = xmlroot.find('password').text
    driver = xmlroot.find('ODBC_Driver').text
    # sql_query = xmlroot.find('query').text
except:
    logger.error("can not read file")


def create_conection():

    try:
        ip_addr = socket.gethostbyname(host)
        logger.info(f"host: {ip_addr}")
    except:
        ip_addr = host
        logger.info(f"host: {ip_addr}")

    try:
        conection_string = pyodbc.connect(
            'DRIVER={'+driver+'};SERVER='+ip_addr+';DATABASE='+database+';UID='+username+';PWD='+password)
        logger.debug("conection establised")

        return conection_string

    except:
        logger.error("conection is not established")
        return False


def excute_query(query):
    con = create_conection()
    try:
        cursor = con.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        con.close()
        logger.debug('query executed')
        return rows
    except:
        logger.error('Query Error')
        return "Error in executing query"
