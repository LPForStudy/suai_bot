from datetime import datetime
import calendar
import locale
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8') 
from pprint import pprint
import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

class gSheet():
    #class variables
    CREDENTIALS_FILE = 'credentials.json'  #  ← имя скачанного файла с закрытым ключом
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets',                                                                               'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    service = discovery.build('sheets', 'v4', http = httpAuth)
    
    spreadsheetId = '1K1zp958fmDLVgroOM5iqtTzvNHzmFijRyd3675PsK-o'

    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheetId).execute() # pylint: disable=no-member
    sheets = sheet_metadata.get('sheets', '')
    #Значения с одного листа
    def getStudents(self, service, spreadsheetId,title,table,students,groups_number):
        ranges = title +'!B3:B'
        table = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=ranges).execute() # pylint: disable=no-member
        students = table.get("values", {})
        return students
    
    #Список названий всех листов в таблице
    def getTitles(self,service,spreadsheetId,title,sheet_id,groups_number):
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheetId).execute() # pylint: disable=no-member
        sheets = sheet_metadata.get('sheets', '')
        for x in range(groups_number):
            title[x] = sheets[x].get("properties", {}).get("title", "Sheet1")
            sheet_id[x] = sheets[x].get("properties", {}).get("sheetId", 0)
