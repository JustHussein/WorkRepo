import logging
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger("send")


try:

    logger.debug("start creating connection.")
    xmltree = ET.parse('./config.xml')
    xmlroot = xmltree.getroot()
    logger.debug("read config file")

    smsuser = xmlroot.find('smsuser').text
    smspass = xmlroot.find('smspass').text
    number = xmlroot.find('number').text
    smstype = xmlroot.find('smstype').text
except:
    logger.error("can not read file")


def send_message(rows):
    if smstype == 'RASA':
        base_url='http://s081/sms'
        logger.debug(smstype)

        for row in rows:
            logger.info(
                f"[try phone: {row[0]}, message: {row[1]}]"
            )
            phone = row[0]
            message = row[1].encode().decode(
                'unicode-escape').encode('latin1').decode('utf-8')
            params = {
                'phone': phone,
                'msg': message
            }

            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                logger.info(f"{phone}-SMS sent successfully.")

            else:
                logger.info(
                    f"Failed to send SMS. Status code: {response.status_code}")
                logger.info("Response content:", response.text)

    if smstype == 'AFE':
        base_url='http://www.AFE.ir/Url/SendSMS.aspx'
        logger.debug(smstype)

        for row in rows:
            logger.info(
                f"[try phone: {row[0]}, message: {row[1]}]"
            )
            phone = row[0]
            message = row[1].encode().decode('unicode-escape').encode('latin1').decode('utf-8')
            params = {
                'Username': smsuser,
                'Password': smspass,
                'Number': number,
                'Mobile': phone,
                'SMS': message
            }

            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                logger.info(f"{phone}-SMS sent successfully.")

            else:
                logger.info(
                    f"Failed to send SMS. Status code: {response.status_code}")
                logger.info("Response content:", response.text)

