import datetime

from app.config import MailSenderSMTPLib


mail = MailSenderSMTPLib(name='execution reports runs')
date = datetime.date.today() - datetime.timedelta(days=1)
start_datetime = datetime.datetime(date.year, date.month, date.day, 0, 0, 0, 0).timestamp()
end_datetime = datetime.datetime(date.year, date.month, date.day, 23, 59, 59, 999999).timestamp()
mail.send_log_files_list(start_date=start_datetime, end_date=end_datetime)
