import logging
import pyodbc
import xml.etree.ElementTree as ET
import socket

logger = logging.getLogger("DataBase Connection")

try:
    xmltree = ET.parse('./config.xml')
    xmlroot = xmltree.getroot()
    host = xmlroot.find('host').text
    database = xmlroot.find('database').text
    username = xmlroot.find('username').text
    password = xmlroot.find('password').text
    driver = xmlroot.find('ODBC_Driver').text
except:
    logger.error("Cannot read config file ")

def c_cursor():

    try:
        ip_addr = socket.gethostbyname(host)
        logger.debug(f"ip_add: {ip_addr}")
    except:
        ip_addr = host
        logger.deg(f"ip_add: {ip_addr}")


    try:
        connection_string = f'DRIVER={driver};SERVER={ip_addr};DATABASE={database};UID={username};PWD={password}'
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        return cursor

    except:
        return False


def execute_query(query, operation_type,values=None):
    cursor = c_cursor()
    try:
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)

        if operation_type.lower() == 'select':
            # Fetch and print the results
            rows = cursor.fetchall()
            for row in rows:
                return(row)

        elif operation_type.lower() in ['insert', 'update', 'delete']:
            # Commit for operations that modify the database
            cursor.commit()
            if operation_type.lower() == 'insert':
                logger.debug("Record inserted successfully.")
            elif operation_type.lower() == 'update':
                logger.debug("Record updated successfully.")
            elif operation_type.lower() == 'delete':
                logger.debug("Record deleted successfully.")

        else:
            logger.debug("Invalid operation type. Supported types: select, insert, update, delete.")

    except Exception as e:
        cursor.rollback()
        logger.error(f"Error: {str(e)}")

    finally:
        cursor.close()



"""query = "insert into [dbo].[personInfo] values ('حسين', 'ميرزائي زاده سرريگاني', 'عباس', '1370/04/23', '3410146962', '3410146962')"
execute_query(query, "insert")
"""