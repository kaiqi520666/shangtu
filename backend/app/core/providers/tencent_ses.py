import asyncio
import json
import logging

from tencentcloud.common import credential
from tencentcloud.ses.v20201002 import models, ses_client

from app.core.config import get_env, require_env


logger = logging.getLogger(__name__)


class TencentSesSendError(RuntimeError):
    pass


def _send_verification_email(email: str, code: str) -> None:
    client = ses_client.SesClient(
        credential.Credential(
            require_env("TENCENT_CLOUD_SECRET_ID"),
            require_env("TENCENT_CLOUD_SECRET_KEY"),
        ),
        get_env("TENCENT_SES_REGION", "ap-hongkong"),
    )
    request = models.SendEmailRequest()
    request.from_json_string(
        json.dumps(
            {
                "FromEmailAddress": require_env("TENCENT_SES_FROM_EMAIL"),
                "Destination": [email],
                "Subject": "商图 AI 注册验证码",
                "Template": {
                    "TemplateID": int(require_env("TENCENT_SES_TEMPLATE_ID")),
                    "TemplateData": json.dumps({"code": code}),
                },
            }
        )
    )
    client.SendEmail(request)


async def send_verification_email(email: str, code: str) -> None:
    try:
        await asyncio.to_thread(_send_verification_email, email, code)
    except Exception as exc:
        logger.exception("Tencent SES verification email failed")
        raise TencentSesSendError("验证码邮件发送失败，请稍后重试") from exc
