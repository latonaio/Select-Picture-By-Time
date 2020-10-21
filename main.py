#!/usr/bin/env python3
# coding: utf-8

# Copyright (c) Latona. All rights reserved.

import os
import sys
import pytz

from datetime import datetime as dt
from glob import glob
from re import split
from time import sleep
from aion.microservice import main_decorator, Options
from aion.kanban import Kanban
from aion.logger import lprint, initialize_logger

PREV_SERVICE_NAME = "real-time-video-streaming"
SERVICE_NAME = os.environ.get("SERVICE")
JST = pytz.timezone('Asia/Tokyo')
initialize_logger(SERVICE_NAME)


def get_datetime_from_file_name(fname):
    return JST.localize(dt.strptime(split("[/.]", fname)[-2], "%Y%m%d%H%M%S%f"))


class NewerFileList():
    def __init__(self, expand, dir_path):
        self.expand = expand
        self.dir_path = dir_path
        self.file_list = []

    def set_file_list(self):
        get_date = dt.now(JST)

        self.file_list = sorted(
            glob(os.path.join(self.dir_path, "*." + self.expand)),
            reverse=True)

        if self.file_list:
            return dt.fromtimestamp(os.path.getctime(self.file_list[0]), JST)
        else:
            return get_date

    def get_new_file_list(self, start_datetime, last_datetime=None):
        ret = []
        if not last_datetime:
            last_datetime = dt.now(JST)
        for file_name in self.file_list:
            file_datetime = get_datetime_from_file_name(file_name)
            # if file is already searched, finish search
            if file_datetime < start_datetime:
                break
            # if file is created after last datetime, it's skipped
            elif file_datetime >= last_datetime:
                continue
            ret.append(file_name)
        return ret[::-1]


class SelectPictureByTime():

    def __init__(self, dir_path):
        if not os.path.isdir(dir_path):
            lprint("Error: transcript data is None")
            sys.exit(1)

        self.dir_path = dir_path
        self.before_time = dt.now(JST)
        self.search_jpg = NewerFileList("jpg", dir_path)

    def __call__(self):
        get_datetime = self.search_jpg.set_file_list()
        if self.before_time >= get_datetime:
            return None
        jpg_file_list = self.search_jpg.get_new_file_list(
            self.before_time, get_datetime)
        self.before_time = get_datetime

        return jpg_file_list


@main_decorator(SERVICE_NAME)
def main(opt: Options):
    conn = opt.get_conn()
    num = opt.get_number()
    kanban: Kanban = conn.set_kanban(SERVICE_NAME, num)

    # assume /var/lib/aion/Data/select-picture-by-time_1
    input_file_path = kanban.get_data_path()
    input_file_path = input_file_path.replace(SERVICE_NAME, PREV_SERVICE_NAME)
    select_picture = SelectPictureByTime(input_file_path + "/output")

    while True:
        picture_list = select_picture()

        if picture_list:
            conn.output_kanban(
                result=True,
                process_number=num,
                metadata={"picture_list": picture_list},
            )
            lprint("send picture_list ", picture_list)
        sleep(0.5)


if __name__ == "__main__":
    main()
