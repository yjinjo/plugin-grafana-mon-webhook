import logging
import hashlib
import re
from typing import Union
from datetime import datetime
from dateutil import parser

from spaceone.core import utils
from plugin.manager.event_manager import ParseManager
from plugin.error import *

_LOGGER = logging.getLogger("spaceone")


class StandardManager(ParseManager):
    webhook_type = "STANDARD"

    def parse(self, raw_data: dict) -> dict:
        """

        :param raw_data: dict
        :return EventsResponse: {
            "results": EventResponse
        }
        """
        results = []
        _LOGGER.debug(f"[StandardManager] data => {raw_data}")
        event_dict = {
            "event_key": self.generate_event_key(raw_data),
            "event_type": self.get_event_type(raw_data.get("status", "")),
            "severity": self.get_severity(raw_data.get("status", "")),
            "title": self.remove_alert_code_from_title(raw_data.get("title")),
            "rule": raw_data.get("groupKey", ""),
            "image_url": self._get_value_from_alerts(raw_data, "panelURL"),
            "resource": {},
            "description": raw_data.get("message", ""),
            "occurred_at": self._convert_to_iso8601(self._get_value_from_alerts(raw_data, "startsAt")),
            "additional_info": self.get_additional_info(raw_data)
        }
        results.append(event_dict)
        _LOGGER.debug(f"[ContactPointParseManager] parse Event : {event_dict}")

        return {
            "results": results
        }

    def generate_event_key(self, raw_data: dict) -> str:
        group_key = raw_data.get("groupKey")

        if group_key is None:
            raise ERROR_REQUIRED_FIELDS(field="group_key")
        hash_object = hashlib.md5(group_key.encode())
        hashed_event_key = hash_object.hexdigest()

        return hashed_event_key

    def get_event_type(self, event_status: str) -> str:
        """
        firing : ALERT
        resolved : RECOVERY
        :param event_status:
        :return:
        """
        return "RECOVERY" if event_status == "resolved" else "ALERT"

    def get_severity(self, event_status: str) -> str:
        """
        firing : ERROR
        resolved : INFO
        :param event_status:
        :return:
        """
        severity_flag = "NONE"

        if event_status == "resolved":
            severity_flag = "INFO"
        elif event_status == "firing":
            severity_flag = "ERROR"

        return severity_flag

    def get_additional_info(self, raw_data: dict) -> dict:
        additional_info = {}
        if "orgId" in raw_data:
            additional_info.update({"org_id": str(raw_data.get("orgId", ""))})

        if "groupKey" in raw_data:
            additional_info.update({"group_key": str(raw_data.get("groupKey", ""))})

        if "alerts" in raw_data:
            alerts_dict = raw_data.get("alerts")
            alerts_str = self.change_eval_dict_to_str(alerts_dict)
            additional_info.update({"alerts": alerts_str})

        return additional_info

    def remove_alert_code_from_title(self, title: str) -> str:
        try:
            title = re.sub("\[[FIRING|RESOLVED]+\:+[0-9]+\] ", "", title)

        except Exception as e:
            ERROR_CONVERT_TITLE()

        return title

    def change_eval_dict_to_str(self, eval_matches: dict) -> str:
        try:
            eval_matches = utils.dump_json(eval_matches)
            return eval_matches

        except Exception as e:
            raise ERROR_CONVERT_DATA_TYPE(field=e)

    def _get_value_from_alerts(self, raw_data: dict, key: str) -> Union[dict, datetime, str]:
        if self._get_alerts_cnt(raw_data) > 0:
            return raw_data.get("alerts")[0].get(key)
        else:
            if key == "startsAt":
                return datetime.now()
            return ""

    @staticmethod
    def _get_alerts_cnt(raw_data: dict) -> int:
        return len(raw_data.get("alerts", ""))

    @staticmethod
    def _convert_to_iso8601(raw_time: str) -> Union[str, None]:
        return utils.datetime_to_iso8601(parser.parse(raw_time))
