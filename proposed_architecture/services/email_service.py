"""Email service for sending notifications"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Environment, FileSystemLoader


class EmailTemplate(ABC):
    """Abstract email template"""

    @abstractmethod
    def render(self, context: Dict[str, Any]) -> str:
        """Render email HTML"""
        pass

    @abstractmethod
    def get_subject(self, context: Dict[str, Any]) -> str:
        """Get email subject"""
        pass


class QualityIssuesEmailTemplate(EmailTemplate):
    """Template for quality issues notification"""

    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, context: Dict[str, Any]) -> str:
        template = self.env.get_template('quality_issues.html')
        return template.render(context)

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"Quality Issues Found - {context['use_case_name']}"


class EvaluationSuccessEmailTemplate(EmailTemplate):
    """Template for evaluation success notification"""

    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, context: Dict[str, Any]) -> str:
        template = self.env.get_template('evaluation_success.html')
        return template.render(context)

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"Evaluation Completed - {context['use_case_name']}"


class TemplateGenerationEmailTemplate(EmailTemplate):
    """Template for sending initial config template"""

    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, context: Dict[str, Any]) -> str:
        template = self.env.get_template('template_generation.html')
        return template.render(context)

    def get_subject(self, context: Dict[str, Any]) -> str:
        return f"Configuration Template - {context['use_case_name']}"


class EmailService:
    """Service for sending emails"""

    def __init__(self, smtp_config: Dict[str, Any]):
        """
        Initialize email service

        Args:
            smtp_config: SMTP configuration
                {
                    'host': 'smtp.gmail.com',
                    'port': 587,
                    'username': 'user@example.com',
                    'password': 'password',
                    'from_email': 'noreply@example.com',
                    'template_dir': './email_templates'
                }
        """
        self.smtp_config = smtp_config
        self.template_dir = smtp_config.get('template_dir', './email_templates')

    def send_template_generation_notification(
        self,
        use_case_id: str,
        use_case_name: str,
        team_email: str,
        template_file_path: str
    ):
        """
        Send template generation notification with config template attachment

        Args:
            use_case_id: Use case identifier
            use_case_name: Use case name
            team_email: Team email to send to
            template_file_path: Path to generated template Excel file
        """
        context = {
            'use_case_id': use_case_id,
            'use_case_name': use_case_name,
            'instructions': [
                'Review the suggested field types and comparison strategies',
                'Modify if needed based on your domain knowledge',
                'Prepare your MIIT evaluation dataset',
                'Reply to this email with both files attached'
            ]
        }

        template = TemplateGenerationEmailTemplate(self.template_dir)
        html_body = template.render(context)
        subject = template.get_subject(context)

        self._send_email(
            to=team_email,
            subject=subject,
            html_body=html_body,
            attachments=[template_file_path]
        )

    def send_quality_issues_notification(
        self,
        use_case_id: str,
        use_case_name: str,
        team_email: str,
        issues: List[Dict[str, Any]],
        report_file_path: str
    ):
        """
        Send quality issues notification with Excel report

        Args:
            use_case_id: Use case identifier
            use_case_name: Use case name
            team_email: Team email to send to
            issues: List of quality issues
            report_file_path: Path to generated report Excel file
        """
        # Calculate summary
        errors = sum(1 for i in issues if i['severity'] == 'error')
        warnings = sum(1 for i in issues if i['severity'] == 'warning')

        context = {
            'use_case_id': use_case_id,
            'use_case_name': use_case_name,
            'issues_count': len(issues),
            'error_count': errors,
            'warning_count': warnings,
            'instructions': [
                'Review the attached Excel report for detailed issues',
                'Fix all ERROR severity issues (these block evaluation)',
                'Review WARNING severity issues (recommended to fix)',
                'Reply to this email with corrected files'
            ]
        }

        template = QualityIssuesEmailTemplate(self.template_dir)
        html_body = template.render(context)
        subject = template.get_subject(context)

        self._send_email(
            to=team_email,
            subject=subject,
            html_body=html_body,
            attachments=[report_file_path]
        )

    def send_evaluation_success_notification(
        self,
        use_case_id: str,
        use_case_name: str,
        team_email: str,
        results: Dict[str, Any],
        recipients_cc: Optional[List[str]] = None
    ):
        """
        Send evaluation success notification

        Args:
            use_case_id: Use case identifier
            use_case_name: Use case name
            team_email: Primary team email
            results: Evaluation results
            recipients_cc: Additional CC recipients
        """
        context = {
            'use_case_id': use_case_id,
            'use_case_name': use_case_name,
            'results': results,
            'entity_extraction': results.get('entity_extraction', {}),
            'classification': results.get('classification', {}),
            'agreement_rate': results.get('agreement_rate', 0)
        }

        template = EvaluationSuccessEmailTemplate(self.template_dir)
        html_body = template.render(context)
        subject = template.get_subject(context)

        self._send_email(
            to=team_email,
            subject=subject,
            html_body=html_body,
            cc=recipients_cc
        )

    def _send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        attachments: Optional[List[str]] = None,
        cc: Optional[List[str]] = None
    ):
        """
        Send email via SMTP

        Args:
            to: Recipient email
            subject: Email subject
            html_body: HTML body content
            attachments: List of file paths to attach
            cc: CC recipients
        """
        msg = MIMEMultipart()
        msg['From'] = self.smtp_config['from_email']
        msg['To'] = to
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = ', '.join(cc)

        msg.attach(MIMEText(html_body, 'html'))

        # Attach files
        if attachments:
            for filepath in attachments:
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = filepath.split('/')[-1].split('\\')[-1]
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={filename}'
                    )
                    msg.attach(part)

        # Send
        with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            recipients = [to] + (cc or [])
            server.send_message(msg, to_addrs=recipients)
