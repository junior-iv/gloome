from os import path as ospath
from sys import path as syspath

# Path to the project root
root_path = ospath.abspath(ospath.dirname(ospath.dirname(__file__)))
if root_path not in syspath:
    syspath.insert(0, root_path)

# Path to the script folder
app_path = ospath.abspath(ospath.dirname(__file__))
if app_path not in syspath:
    syspath.insert(0, app_path)

from app.mail import *

mail = MailSenderSMTPLib(name='execution reports runs')
date = datetime.date.today() - datetime.timedelta(days=1)
start_datetime = datetime.datetime(date.year, date.month, date.day, 0, 0, 0, 0).timestamp()
end_datetime = datetime.datetime(date.year, date.month, date.day, 23, 59, 59, 999999).timestamp()
mail.send_log_files_list(start_date=start_datetime, end_date=end_datetime)
