import requests
import json
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger("Estelam")

try:
    xmltree = ET.parse('./config.xml')
    xmlroot = xmltree.getroot()
    url_estelam = xmlroot.find('url_estelam').text
    code_estelam = xmlroot.find('code_estelam').text
    pass_estelam = xmlroot.find('pass_estelam').text
    logger.debug("reading config file.")
except:
    logger.error("Cannot read config file ")
def getestelam(nationalCode):
    logger.debug(f"NationalID: {nationalCode}")
    nationalCode = str(nationalCode)
    logger.info(nationalCode)
    url = url_estelam
    headers = {
        "Content-Type": "application/json",
        "Cookie": "cookiesession1=678B288D2551DACBE64A24FF2C5A5A41"
    }

    data = {
        "credential": {
            "code": code_estelam,
            "password": pass_estelam
        },
        "parameters": [
            {
                "parameterName": "nationalCode",
                "parameterValue": nationalCode
            }
        ],
        "service": "cloudSrv-inq"
    }

    # Make a POST request
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        response_dict = json.loads(response.text)
        response_text = response_dict.get('responseText', '')
        response_text_list = json.loads(response_text) if response_text else []

        response_text_list = sorted(response_text_list , key=lambda x: x['studentUniInfo']['studyLevelId'])
        for entry in response_text_list:
            entry['studentInfo']['totalAverage'] = round(entry['studentInfo']['totalAverage'],2)
        last_person_info=None
        study_info = []
        student_info = []
        for i in response_text_list:
            if "personInfo" in i:
                last_person_info = i["personInfo"]
            if "studentUniInfo" in i:
                study_info.append(i["studentUniInfo"])
            if "studentInfo" in i:
                student_info.append(i["studentInfo"])


        return (response.status_code,last_person_info,study_info,student_info)

    else:
        return (response.status_code,response.reason)



