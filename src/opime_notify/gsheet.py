from pathlib import Path

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from opime_notify.schedule import NotifySchedule


class GsheetSession:
    def __init__(
        self, json_key: Path, sheet_id: str, sheet_name: str = "schedule_list"
    ):
        self.json_key = json_key
        self.sheet_id = sheet_id
        sheet = self.get_spreadsheets_obj()
        self.sheet = sheet
        self.sheet_name = sheet_name

    def get_spreadsheets_obj(self):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        cred = ServiceAccountCredentials.from_json_keyfile_name(self.json_key, scope)
        gc = gspread.authorize(cred)
        worksheet = gc.open_by_key(self.sheet_id)
        return worksheet

    def read_all_schedule(self):
        wsheet = self.sheet.worksheet(self.sheet_name)
        all_values = wsheet.get_all_records()
        schedule_list = []
        require_keys = ["id", "title", "date", "status"]
        for key in require_keys:
            if key not in all_values[0]:
                return []
        for value_dict in all_values:
            if len(value_dict["date"]) == 0:
                continue
            schedule = NotifySchedule(**value_dict)
            schedule_list.append(schedule)

        return schedule_list

    def fetch_headers(self, wsheet) -> list[str]:
        header = wsheet.row_values(1)
        return header

    def write_all_schedule(self, schedule_list: list[NotifySchedule]) -> None:
        wsheet = self.sheet.worksheet(self.sheet_name)
        header = self.fetch_headers(wsheet)
        for index, schedule in enumerate(schedule_list):
            self.write_schedule(wsheet, schedule, index, header)

    def write_schedule(
        self, wsheet, schedule: NotifySchedule, index: int, header: list[str]
    ) -> None:
        # index 0 is row 2
        row_value = []
        for key in header:
            if key == "id":
                # id is dont change
                continue
            value = schedule.get_value(key)
            if value is None:
                value = ""
            row_value.append(value)
        end_col = len(header)
        end_col_str = self._int_to_alphabet(end_col)
        row = index + 2
        range_str = f"B{row}:{end_col_str}{row}"
        wsheet.update(range_str, [row_value], value_input_option="USER_ENTERED")

    def _int_to_alphabet(self, num: int) -> str:
        # num 1 is A(65)
        if num < 1 or 26 < num:
            # out of range
            return "A"
        ascii_num = num + 64
        return chr(ascii_num)

    def clear_schedule(self):
        wsheet = self.sheet.worksheet(self.sheet_name)
        header = self.fetch_headers(wsheet)
        end_col = len(header)
        end_col_str = self._int_to_alphabet(end_col)
        range_str = f"B2:{end_col_str}30"
        wsheet.batch_clear([range_str])
