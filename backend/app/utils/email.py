import asyncio
import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, Template, TemplateSyntaxError

logger = logging.getLogger(__name__)

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
SMTP_MIN_TLS_VERSION = os.getenv("SMTP_MIN_TLS_VERSION", "TLSv1_2")  # TLSv1_2, TLSv1_3
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Email retry configuration
MAX_EMAIL_RETRIES = 5
EMAIL_RETRY_DELAY = 1  # seconds


def create_secure_ssl_context() -> ssl.SSLContext:
    """Create a secure SSL context with minimum TLS version enforcement."""
    context = ssl.create_default_context()

    # Set minimum TLS version based on configuration
    if SMTP_MIN_TLS_VERSION == "TLSv1_3":
        context.minimum_version = ssl.TLSVersion.TLSv1_3
    elif SMTP_MIN_TLS_VERSION == "TLSv1_2":
        context.minimum_version = ssl.TLSVersion.TLSv1_2
    else:
        # Default to TLS 1.2 for security
        context.minimum_version = ssl.TLSVersion.TLSv1_2

    # Additional security settings
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED

    return context


def mask_email(email: str) -> str:
    """Mask email address for logging to protect PII."""
    if not email or "@" not in email:
        return "***@***.***"

    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    if "." in domain:
        domain_parts = domain.split(".")
        if len(domain_parts) >= 2:
            masked_domain = domain_parts[0][:2] + "*" + "." + domain_parts[-1]
        else:
            masked_domain = "*" * len(domain)
    else:
        masked_domain = "*" * len(domain)

    return f"{masked_local}@{masked_domain}"


# Email templates
PASSWORD_RESET_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #2563eb;
            margin-bottom: 10px;
        }
        .title {
            font-size: 28px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 20px;
        }
        .content {
            margin-bottom: 30px;
        }
        .button {
            display: inline-block;
            background-color: #2563eb;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            margin: 20px 0;
        }
        .button:hover {
            background-color: #1d4ed8;
        }
        .warning {
            background-color: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            color: #92400e;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 14px;
            color: #6b7280;
            text-align: center;
        }
        .expiry {
            color: #dc2626;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">MyApp</div>
            <h1 class="title">Password Reset Request</h1>
        </div>

        <div class="content">
            <p>Hello,</p>

            <p>We received a request to reset your password. If you made this request, click the button below to reset your password:</p>

            <div style="text-align: center;">
                <a href="{{ reset_link }}" class="button">Reset Password</a>
            </div>

            <div class="warning">
                <strong>⚠️ Important:</strong> This link will expire in <span class="expiry">10 minutes</span> for security reasons.
            </div>

            <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>

            <p>For security reasons, this link can only be used once.</p>
        </div>

        <div class="footer">
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #2563eb;">{{ reset_link }}</p>

            <p style="margin-top: 20px;">
                This email was sent from MyApp. If you have any questions, please contact our support team.
            </p>
        </div>
    </div>
</body>
</html>
"""

PASSWORD_RESET_TEXT_TEMPLATE = """
Password Reset Request

Hello,

We received a request to reset your password. If you made this request, visit the link below to reset your password:

{{ reset_link }}

IMPORTANT: This link will expire in 10 minutes for security reasons.

If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.

For security reasons, this link can only be used once.

If you have any questions, please contact our support team.

Best regards,
MyApp Team
"""

# Verification code email templates
VERIFICATION_CODE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Code</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #2563eb;
            margin-bottom: 10px;
        }
        .title {
            font-size: 28px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 20px;
        }
        .content {
            margin-bottom: 30px;
        }
        .code {
            background-color: #f3f4f6;
            border: 2px solid #d1d5db;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
            font-size: 32px;
            font-weight: bold;
            letter-spacing: 8px;
            color: #1f2937;
            font-family: 'Courier New', monospace;
        }
        .warning {
            background-color: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            color: #92400e;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 14px;
            color: #6b7280;
            text-align: center;
        }
        .expiry {
            color: #dc2626;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">MyApp</div>
            <h1 class="title">Your Verification Code</h1>
        </div>

        <div class="content">
            <p>Hello,</p>

            <p>We received a request to {{ purpose }} your account. Please use the verification code below:</p>

            <div class="code">{{ verification_code }}</div>

            <div class="warning">
                <strong>⚠️ Important:</strong> This code will expire in <span class="expiry">10 minutes</span> for security reasons.
            </div>

            <p>If you didn't request this verification, you can safely ignore this email.</p>

            <p>For security reasons, this code can only be used once and has a maximum of 5 attempts.</p>
        </div>

        <div class="footer">
            <p style="margin-top: 20px;">
                This email was sent from MyApp. If you have any questions, please contact our support team.
            </p>
        </div>
    </div>
</body>
</html>
"""

VERIFICATION_CODE_TEXT_TEMPLATE = """
Your Verification Code

Hello,

We received a request to {{ purpose }} your account. Please use the verification code below:

{{ verification_code }}

IMPORTANT: This code will expire in 10 minutes for security reasons.

If you didn't request this verification, you can safely ignore this email.

For security reasons, this code can only be used once and has a maximum of 5 attempts.

If you have any questions, please contact our support team.

Best regards,
MyApp Team
"""


def validate_email_templates() -> bool:
    """
    Validate all email templates at startup to ensure they are syntactically correct
    and contain required template variables.

    Returns:
        bool: True if all templates are valid, False otherwise
    """
    logger.info("Validating email templates...")

    # Define all templates and their required variables
    templates_to_validate = [
        {
            "name": "PASSWORD_RESET_HTML_TEMPLATE",
            "template": PASSWORD_RESET_HTML_TEMPLATE,
            "required_vars": ["reset_link"],
        },
        {
            "name": "PASSWORD_RESET_TEXT_TEMPLATE",
            "template": PASSWORD_RESET_TEXT_TEMPLATE,
            "required_vars": ["reset_link"],
        },
        {
            "name": "VERIFICATION_CODE_HTML_TEMPLATE",
            "template": VERIFICATION_CODE_HTML_TEMPLATE,
            "required_vars": ["verification_code", "purpose"],
        },
        {
            "name": "VERIFICATION_CODE_TEXT_TEMPLATE",
            "template": VERIFICATION_CODE_TEXT_TEMPLATE,
            "required_vars": ["verification_code", "purpose"],
        },
    ]

    # Create Jinja2 environment for validation
    env = Environment()

    validation_errors = []

    for template_info in templates_to_validate:
        template_name = template_info["name"]
        template_content = template_info["template"]
        required_vars = template_info["required_vars"]

        try:
            # Parse template to check syntax
            env.parse(template_content)

            # Check for required variables with more robust pattern matching
            for var in required_vars:
                # Check for various Jinja2 template variable patterns
                variable_patterns = [
                    f"{{{{ {var} }}}}",  # {{ variable }}
                    f"{{{{{var}}}}}",  # {{variable}}
                    f"{{{{ {var}|",  # {{ variable|filter }}
                    f"{{{{{var}|",  # {{variable|filter}}
                    f"{{{{ {var} ",  # {{ variable with spaces }}
                    f"{{{{{var} ",  # {{variable with spaces}}
                ]

                var_found = False
                for pattern in variable_patterns:
                    if pattern in template_content:
                        var_found = True
                        break

                if not var_found:
                    validation_errors.append(f"{template_name}: Missing required variable '{var}'")

            # Comprehensive security validation
            if "{{" in template_content and "}}" in template_content:
                # Check for potentially dangerous template expressions
                dangerous_patterns = [
                    # Flask/Web framework context variables
                    "{{ config",
                    "{{ request",
                    "{{ session",
                    "{{ g.",
                    "{{ self.",
                    "{{ __",
                    "{{ url_for",
                    "{{ current_user",
                    "{{ current_app",
                    # Python built-ins and dangerous functions
                    "{{ eval(",
                    "{{ exec(",
                    "{{ open(",
                    "{{ file(",
                    "{{ input(",
                    "{{ raw_input(",
                    "{{ compile(",
                    "{{ globals(",
                    "{{ locals(",
                    "{{ vars(",
                    "{{ dir(",
                    "{{ getattr(",
                    "{{ setattr(",
                    "{{ delattr(",
                    "{{ hasattr(",
                    "{{ callable(",
                    "{{ isinstance(",
                    "{{ issubclass(",
                    "{{ super(",
                    "{{ type(",
                    "{{ object(",
                    "{{ class(",
                    "{{ import",
                    "{{ from",
                    "{{ def ",
                    "{{ class ",
                    "{{ if ",
                    "{{ for ",
                    "{{ while ",
                    "{{ try ",
                    "{{ except ",
                    "{{ finally ",
                    "{{ with ",
                    "{{ as ",
                    "{{ in ",
                    "{{ is ",
                    "{{ not ",
                    "{{ and ",
                    "{{ or ",
                    "{{ lambda",
                    "{{ yield",
                    "{{ return",
                    "{{ break",
                    "{{ continue",
                    "{{ pass",
                    "{{ raise",
                    "{{ assert",
                    # File system access
                    "{{ os.",
                    "{{ sys.",
                    "{{ subprocess",
                    "{{ shutil",
                    "{{ pathlib",
                    "{{ tempfile",
                    # Network and HTTP
                    "{{ urllib",
                    "{{ requests",
                    "{{ httplib",
                    "{{ socket",
                    "{{ ssl",
                    # Database access
                    "{{ sqlalchemy",
                    "{{ db.",
                    "{{ database",
                    "{{ query(",
                    "{{ execute(",
                    # Security-sensitive modules
                    "{{ pickle",
                    "{{ marshal",
                    "{{ shelve",
                    "{{ dill",
                    "{{ joblib",
                    # Template injection patterns
                    "{{ ''.__class__",
                    "{{ [].__class__",
                    "{{ {}.__class__",
                    "{{ ().__class__",
                    "{{ ''.__bases__",
                    "{{ [].__bases__",
                    "{{ {}.__bases__",
                    "{{ ().__bases__",
                    "{{ ''.__mro__",
                    "{{ [].__mro__",
                    "{{ {}.__mro__",
                    "{{ ().__mro__",
                    "{{ ''.__subclasses__",
                    "{{ [].__subclasses__",
                    "{{ {}.__subclasses__",
                    "{{ ().__subclasses__",
                ]

                # Check for dangerous patterns (case-insensitive)
                template_lower = template_content.lower()
                for pattern in dangerous_patterns:
                    if pattern in template_lower:
                        validation_errors.append(
                            f"{template_name}: Potentially dangerous template expression found: {pattern}"
                        )

                # Check for template inheritance and includes (potential security risk)
                inheritance_patterns = [
                    "{% extends",
                    "{% include",
                    "{% import",
                    "{% from",
                    "{% macro",
                    "{% call",
                    "{% set",
                    "{% if",
                    "{% for",
                    "{% while",
                    "{% with",
                    "{% block",
                    "{% filter",
                    "{% raw",
                    "{% autoescape",
                ]

                for pattern in inheritance_patterns:
                    if pattern in template_lower:
                        validation_errors.append(
                            f"{template_name}: Template control structure found (potential security risk): {pattern}"
                        )

                # Check for excessive nesting or complexity
                open_braces = template_content.count("{{")
                close_braces = template_content.count("}}")
                if open_braces != close_braces:
                    validation_errors.append(
                        f"{template_name}: Unmatched template braces ({{{{: {open_braces}, }}}}: {close_braces})"
                    )

                # Check for suspiciously long template expressions
                import re

                template_expressions = re.findall(r"\{\{[^}]{50,}\}\}", template_content)
                if template_expressions:
                    validation_errors.append(
                        f"{template_name}: Suspiciously long template expressions found: {len(template_expressions)} expressions"
                    )

                # Check for nested template expressions (potential security risk)
                nested_expressions = re.findall(
                    r"\{\{[^}]*\{\{[^}]*\}\}[^}]*\}\}", template_content
                )
                if nested_expressions:
                    validation_errors.append(
                        f"{template_name}: Nested template expressions found (potential security risk): {len(nested_expressions)} expressions"
                    )

            logger.debug(f"✅ {template_name} validation passed")

        except TemplateSyntaxError as e:
            validation_errors.append(f"{template_name}: Template syntax error - {str(e)}")
        except Exception as e:
            validation_errors.append(f"{template_name}: Validation error - {str(e)}")

    if validation_errors:
        logger.error("❌ Email template validation failed:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        return False
    else:
        logger.info("✅ All email templates validated successfully")
        return True


class EmailService:
    """Email service for sending password reset emails and other notifications."""

    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.smtp_use_tls = SMTP_USE_TLS
        self.smtp_use_ssl = SMTP_USE_SSL
        self.frontend_url = FRONTEND_URL
        self.ssl_context = create_secure_ssl_context()

        # Validate email templates at startup
        if not validate_email_templates():
            logger.warning(
                "Email template validation failed - some email functionality may not work correctly"
            )

    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """
        Send password reset email to user with retry logic.

        Args:
            email: User's email address
            reset_token: The reset token (not hashed)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        masked_email = mask_email(email)

        try:
            reset_link = f"{self.frontend_url}/reset-password?token={reset_token}"

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Reset Your Password - MyApp"
            msg["From"] = "noreply@myapp.com"
            msg["To"] = email

            # Create HTML and text versions
            html_template = Template(PASSWORD_RESET_HTML_TEMPLATE)
            text_template = Template(PASSWORD_RESET_TEXT_TEMPLATE)

            html_content = html_template.render(reset_link=reset_link)
            text_content = text_template.render(reset_link=reset_link)

            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")

            msg.attach(part1)
            msg.attach(part2)

            # Send email with retry logic
            success = await self._send_email_with_retry(msg, email)

            if success:
                logger.info(f"Password reset email sent successfully to {masked_email}")
            else:
                logger.error(
                    f"Failed to send password reset email to {masked_email} after {MAX_EMAIL_RETRIES} attempts"
                )

            return success

        except Exception as e:
            logger.error(
                f"Unexpected error sending password reset email to {masked_email}: {type(e).__name__}"
            )
            return False

    async def _send_email_with_retry(self, msg: MIMEMultipart, to_email: str) -> bool:
        """Send email with retry logic."""
        masked_email = mask_email(to_email)

        for attempt in range(MAX_EMAIL_RETRIES):
            try:
                await self._send_email(msg, to_email)
                return True

            except smtplib.SMTPAuthenticationError as e:
                logger.error(
                    f"SMTP authentication failed for {masked_email}: {e.smtp_error.decode() if hasattr(e, 'smtp_error') else str(e)}"
                )
                return False  # Don't retry auth failures

            except smtplib.SMTPRecipientsRefused as e:
                logger.error(
                    f"SMTP recipients refused for {masked_email}: {e.smtp_error.decode() if hasattr(e, 'smtp_error') else str(e)}"
                )
                return False  # Don't retry invalid recipients

            except smtplib.SMTPException as e:
                logger.warning(
                    f"SMTP error sending to {masked_email} (attempt {attempt + 1}/{MAX_EMAIL_RETRIES}): {type(e).__name__}"
                )
                if attempt < MAX_EMAIL_RETRIES - 1:
                    await asyncio.sleep(EMAIL_RETRY_DELAY * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"Final SMTP failure for {masked_email}: {type(e).__name__}")
                    return False

            except Exception as e:
                logger.error(
                    f"Unexpected error sending email to {masked_email} (attempt {attempt + 1}/{MAX_EMAIL_RETRIES}): {type(e).__name__}"
                )
                if attempt < MAX_EMAIL_RETRIES - 1:
                    await asyncio.sleep(EMAIL_RETRY_DELAY * (attempt + 1))
                else:
                    return False

        return False

    async def _send_email(self, msg: MIMEMultipart, to_email: str) -> None:
        """Send email using SMTP with proper context management."""
        # Run SMTP operations in thread pool to avoid blocking
        await asyncio.to_thread(self._send_email_sync, msg, to_email)

    def _send_email_sync(self, msg: MIMEMultipart, to_email: str) -> None:
        """Synchronous SMTP sending with proper context management and secure TLS."""
        try:
            # Choose SMTP class based on SSL configuration
            if self.smtp_use_ssl:
                # For SSL-only connections, use the secure context
                smtp_class = smtplib.SMTP_SSL
                with smtp_class(self.smtp_host, self.smtp_port, context=self.ssl_context) as server:
                    self._configure_and_send(server, msg)
            else:
                # For STARTTLS connections, use regular SMTP with secure context
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    self._configure_and_send(server, msg)

        except smtplib.SMTPException:
            # Re-raise SMTP exceptions as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise smtplib.SMTPException(f"Unexpected error: {type(e).__name__}: {str(e)}") from e

    def _configure_and_send(self, server: smtplib.SMTP, msg: MIMEMultipart) -> None:
        """Configure SMTP server and send email."""
        # Enable debug if needed (only in development)
        if os.getenv("SMTP_DEBUG", "false").lower() == "true":
            server.set_debuglevel(1)

        # Start TLS if required (and not using SSL) with secure context
        if self.smtp_use_tls and not self.smtp_use_ssl:
            server.starttls(context=self.ssl_context)

        # Authenticate if credentials provided
        if self.smtp_username and self.smtp_password:
            server.login(self.smtp_username, self.smtp_password)

        # Send the email
        server.send_message(msg)

    async def send_verification_code_email(
        self, email: str, verification_code: str, purpose: str
    ) -> bool:
        """
        Send verification code email to user with retry logic.

        Args:
            email: User's email address
            verification_code: The verification code (not hashed)
            purpose: Purpose of verification ("signup" or "login")

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        masked_email = mask_email(email)

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Your Verification Code - MyApp"
            msg["From"] = "noreply@myapp.com"
            msg["To"] = email

            # Create HTML and text versions
            html_template = Template(VERIFICATION_CODE_HTML_TEMPLATE)
            text_template = Template(VERIFICATION_CODE_TEXT_TEMPLATE)

            html_content = html_template.render(
                verification_code=verification_code, purpose=purpose
            )
            text_content = text_template.render(
                verification_code=verification_code, purpose=purpose
            )

            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")

            msg.attach(part1)
            msg.attach(part2)

            # Send email with retry logic
            success = await self._send_email_with_retry(msg, email)

            if success:
                logger.info(
                    f"Verification code email sent successfully to {masked_email} for {purpose}"
                )
            else:
                logger.error(
                    f"Failed to send verification code email to {masked_email} after {MAX_EMAIL_RETRIES} attempts"
                )

            return success

        except Exception as e:
            logger.error(
                f"Unexpected error sending verification code email to {masked_email}: {type(e).__name__}"
            )
            return False


# Global email service instance
email_service = EmailService()
