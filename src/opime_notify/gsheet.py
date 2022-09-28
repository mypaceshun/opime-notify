from pathlib import Path

import gspread
from gspread.exceptions import WorksheetNotFound
from gspread.utils import rowcol_to_a1
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
            if len(all_values) == 0:
                return []
            if key not in all_values[0]:
                return []
        for value_dict in all_values:
            if len(value_dict["date"]) == 0:
                continue
            schedule = NotifySchedule(**value_dict)
            schedule_list.append(schedule)

        return schedule_list

    def fetch_curr_article(self, sheet_name: str) -> list[dict]:
        headers = ["id", "title", "date"]
        try:
            wsheet = self.sheet.worksheet(sheet_name)
        except WorksheetNotFound:
            wsheet = self.init_wsheet(sheet_name, headers)
        all_values = wsheet.get_all_records()
        return all_values

    def fetch_curr_tag(self, sheet_name: str) -> list[dict]:
        """
        for ShopSession
        """
        headers = ["id", "title", "date", "code", "name", "name_kana"]
        try:
            wsheet = self.sheet.worksheet(sheet_name)
        except WorksheetNotFound:
            wsheet = self.init_wsheet(sheet_name, headers)
        all_values = wsheet.get_all_records()
        return all_values

    def init_wsheet(
        self, sheet_name: str, headers: list[str], rows: int = 100, cols: int = 20
    ):
        wsheet = self.sheet.add_worksheet(title=sheet_name, rows=rows, cols=cols)
        end_col = len(headers)
        end_range = rowcol_to_a1(1, end_col)
        range_str = f"A1:{end_range}"
        wsheet.update(range_str, [headers], value_input_option="USER_ENTERED")
        return wsheet

    def fetch_headers(self, sheet_name: str = "", wsheet=None) -> list[str]:
        if sheet_name == "":
            sheet_name = self.sheet_name
        if wsheet is None:
            wsheet = self.sheet.worksheet(sheet_name)
        header = wsheet.row_values(1)
        return header

    def write_all_schedule(self, schedule_list: list[NotifySchedule]) -> None:
        wsheet = self.sheet.worksheet(self.sheet_name)
        header = self.fetch_headers(wsheet=wsheet)
        nodup_schedule_list = list(set(schedule_list))
        sorted_schedule_list = sorted(nodup_schedule_list)
        for index, schedule in enumerate(sorted_schedule_list):
            self.write_schedule(wsheet, schedule, index, header)

    def write_schedule(
        self, wsheet, schedule: NotifySchedule, index: int, header: list[str]
    ) -> None:
        # index 0 is row 2
        row_value = []
        for key in header:
            if key == "id":
                row_value.append("=ROW()-1")
                continue
            value = schedule.get_value(key)
            if value is None:
                value = ""
            if key == "status" and value == "":
                value = "BEFORE"
            row_value.append(value)
        end_col = len(header)
        row = index + 2
        end_range = rowcol_to_a1(row, end_col)
        range_str = f"A{row}:{end_range}"
        wsheet.update(range_str, [row_value], value_input_option="USER_ENTERED")

    def write_table(self, table: list[list[str]], sheet_name: str = "") -> None:
        if sheet_name == "":
            sheet_name = self.sheet_name
        if len(table) == 0:
            return None
        row_len = len(table) + 1
        col_len = len(table[0])
        end_range_str = rowcol_to_a1(row_len, col_len)
        range_str = f"A2:{end_range_str}"
        wsheet = self.sheet.worksheet(sheet_name)
        wsheet.update(range_str, table, value_input_option="USER_ENTERED")

    def clear_schedule(self, sheet_name: str = ""):
        if sheet_name == "":
            sheet_name = self.sheet_name
        wsheet = self.sheet.worksheet(sheet_name)
        header = self.fetch_headers(wsheet=wsheet)
        end_col = len(header)
        end_range = rowcol_to_a1(100, end_col)
        range_str = f"A2:{end_range}"
        wsheet.batch_clear([range_str])
