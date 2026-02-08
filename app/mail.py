import re

from typing import Any, Optional, Dict
from smtplib import SMTP, SMTP_SSL
from ssl import create_default_context
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from gloome.utils import *


class MailSenderSMTPLib:
    name: str
    sender: str
    receiver: str
    smtp_server: str
    smtp_port: int
    password: str
    report_receivers: List[str]
    log_files_dir: Path
    out_dir: Path
    results: Path
    sender_logger: Any

    def __init__(self, **attributes):
        self.sender = ADMIN_EMAIL
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.password = ADMIN_PASSWORD
        self.report_receivers = REPORT_RECEIVERS
        self.log_files_dir = LOGS_DIR
        self.out_dir = OUT_DIR
        self.results = RESULTS_URL
        self.receiver = ''
        self.name = ''

        self.set_attributes(**attributes)
        self.sender_logger = get_job_logger(f'{self.name} {self.sender}', LOGS_DIR)

    def set_attributes(self, **attributes) -> None:
        if attributes:
            for key, value in attributes.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def create_attachments(self, attachment_path: Path, message: MIMEMultipart, use_attachments: bool = False):
        if use_attachments:
            self.add_attachment_to_email(attachment_path, message)
            return ''
        else:
            suffixes = ('txt', 'csv', 'tsv', 'nwk', 'tree', 'dot', 'fasta', 'log', 'png', 'svg', 'jpeg', 'jpg', 'html',
                        'htm', 'json', 'zip', 'rar', '7z', 'gz', 'tgz', 'tar', 'pdf', 'doc', 'dot', 'wiz', 'docx',
                        'xls', 'xlt', 'xla', 'xlsx', 'ppt', 'pps', 'pps', 'pptx', 'ppsx')
            mode = 'view' if attachment_path.suffix[1:] in suffixes else 'download'
            return (f'\n<a href="{WEBSERVER_URL}/get_file?file_path={str(attachment_path).replace("/", "%2F")}'
                    f'&mode={mode}" target="_blank">{attachment_path}</a>')

    def send_email(self, subject: str, attachments: Union[List[Path], Dict[str, List[Path]], str],
                   body: str, use_attachments: bool = False,
                   receiver: Optional[str] = None) -> None:
        message = MIMEMultipart()
        message["From"] = self.sender
        message["To"] = self.receiver if receiver is None else receiver
        message["Subject"] = subject

        if isinstance(attachments, (tuple, list)):
            body += (f'<br>Link:<br>{self.create_link_to_results(f"{self.results}/{self.name}")}'
                     f'<br>Result files:<br>')
            for attachment_path in attachments:
                body += f'<br>{self.create_attachments(attachment_path, message, use_attachments)}'
        elif isinstance(attachments, dict):
            for key, value in attachments.items():
                body += f'<br>{key}:'
                for attachment_path in value:
                    if key == 'successful runs':
                        attachment_path = self.create_link_to_results(attachment_path)
                    else:
                        attachment_path = self.create_attachments(attachment_path, message, use_attachments)
                    body += f'<br>{attachment_path}'
        elif isinstance(attachments, str):
            body += f'<br>{self.create_attachments(Path(attachments), message, use_attachments)}'
        self.sender_logger.info(body)
        message.attach(MIMEText(body, 'html'))

        if self.smtp_port == 587:
            with SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=create_default_context())
                server.login(self.sender, self.password)
                server.send_message(message)
        elif self.smtp_port == 465:
            with SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.send_message(message)
        elif self.smtp_port == 0:
            with SMTP(self.smtp_server) as server:
                server.send_message(message)
        elif self.smtp_port == -1:
            with SMTP_SSL(self.smtp_server) as server:
                server.send_message(message)

    def send_results_email(self, results_files: Path, log_file: Path,
                           excluded: Optional[Union[Tuple[str, ...], List[str], str]] = None,
                           included: Optional[Union[Tuple[str, ...], List[str], str]] = None,
                           is_error: bool = False, use_attachments: bool = False, **kwargs) -> None:
        self.set_attributes(**kwargs)
        status = 'failed!' if is_error else 'completed'
        subject = f'{WEBSERVER_NAME_CAPITAL} job {self.name} by {self.receiver} has {status}'
        body = f'{subject}\n'
        attachments = [log_file]
        for entry in results_files.iterdir():
            self.add_attachment_to_list(entry, attachments, excluded, included)
        self.send_email(subject, attachments, body, use_attachments)

    def send_log_files_list(self, start_date: float, end_date: float,
                            excluded: Optional[Union[Tuple[str, ...], List[str], str]] = None,
                            included: Optional[Union[Tuple[str, ...], List[str], str]] = None,
                            use_attachments: bool = False, **kwargs) -> None:
        self.set_attributes(**kwargs)
        subject = f'{WEBSERVER_NAME_CAPITAL} Daily Jobs Report'
        body = f'{subject}\n'
        attachments = {'successful runs': [], 'failed runs': [], 'incomplete runs': []}
        for entry in self.log_files_dir.iterdir():
            if start_date <= entry.stat().st_ctime < end_date and bool(re.fullmatch(r"\d{14}\.log", entry.name)):
                process_id = entry.stem
                if self.out_dir.joinpath(process_id).joinpath(f'GLOOME_{process_id}.END_FAIL').exists():
                    self.add_attachment_to_list(entry, attachments.get('failed runs'), excluded, included)
                elif self.out_dir.joinpath(process_id).joinpath(f'GLOOME_{process_id}.END_OK').exists():
                    attachments.get('successful runs').append(self.results.joinpath(process_id))
                else:
                    self.add_attachment_to_list(entry, attachments.get('incomplete runs'), excluded, included)
        for receiver in self.report_receivers:
            self.send_email(subject, attachments, body, use_attachments, receiver)

    @staticmethod
    def create_link_to_results(result_path: Union[Path, str]):
        return f'\n<a href="{result_path}" target="_blank">{result_path}</a>'

    @staticmethod
    def add_attachment_to_list(entry: Path, attachments: List[Path],
                               excluded: Optional[Union[Tuple[str, ...], List[str], str]] = None,
                               included: Optional[Union[Tuple[str, ...], List[str], str]] = None) -> None:
        includ = any((included is None, entry.name in included, entry.suffix in included, entry.suffix[1:] in included))
        exclud = all((excluded is not None, any((entry.name in excluded, entry.suffix in excluded, entry.suffix[1:] in
                                                 excluded))))
        if entry.is_file() and not exclud and includ:
            attachments.append(entry)

    @staticmethod
    def add_attachment_to_email(attachment_path: Path, message: MIMEMultipart) -> None:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read().strip())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {attachment_path.name}",
        )
        message.attach(part)
