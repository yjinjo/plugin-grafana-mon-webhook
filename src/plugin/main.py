import logging
import json
from typing import List, Union

from spaceone.monitoring.plugin.webhook.lib.server import WebhookPluginServer
from plugin.manager.event_manager.base import ParseManager

_LOGGER = logging.getLogger("spaceone")

app = WebhookPluginServer()


@app.route("Webhook.init")
def webhook_init(params: dict) -> dict:
    """init plugin by options
    {
        'options': 'dict'       # Required
    }

    :return:
    :param params: WebhookRequest :
        WebhookResponse: {
            'metadata': 'dict'  # Required
        }
    """
    return {"meatadata": {}}


@app.route("Webhook.verify")
def webhook_verify(params: dict) -> None:
    """verifying plugin

    :param params: WebhookRequest: {
            'options': 'dict'   # Required
        }

    :return:
        None
    """
    pass


@app.route("Event.parse")
def event_parse(params: dict) -> List[dict]:
    """Parsing Event Webhook

    Args:
        params (EventRequest): {
            'options': {        # Required
                'message_root': 'message.detail.xxx'
            },
            'data': 'dict'      # Required
        }

    Returns:
        List[EventResponse]
        {
            'event_key': 'str'          # Required
            'event_type': 'str'         # Required
            'title': 'str'              # Required
            'description': 'str'
            'severity': 'str'           # Required
            'resource': dict
            'rule': 'str'
            'occurred_at': 'datetime'   # Required
            'additional_info': dict     # Required
            'image_url': ''
        }
    """
    options = params["options"]
    data = params["data"]

    # Messages from AWS SNS
    if message_root := options.get("message_root"):
        data = _get_message_root_data(message_root, data)

    # Check if webhook messages are old template
    webhook_type = _get_webhook_type(data)
    parse_mgr = ParseManager.get_parse_manager_by_webhook_type(webhook_type)

    return parse_mgr.parse(data)


def _get_webhook_type(data: dict) -> str:
    if data.get("dashboardId") and data.get("orgId"):
        return "LEGACY"
    elif data.get("orgId"):
        return "STANDARD"
    else:
        return "AWS_SNS"


def _get_message_root_data(message_root: str, raw_data: dict) -> Union[dict, str]:
    msg_dir = message_root.split(".")
    data = raw_data
    for d in msg_dir:
        if _check_is_loadable(data[d]) is False:
            return data

        data = data[d]
        if type(data) is str:
            data = json.loads(data)

    return data


def _check_is_loadable(data: Union[dict, str]) -> bool:
    if type(data) is dict:
        return True
    else:
        return True if data.startswith("{") else False
