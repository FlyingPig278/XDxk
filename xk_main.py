# -*- coding: utf-8 -*-
from login import *
import time


def main():
    with open("conf.json", 'r', encoding="utf-8") as f:
        conf = json.load(f)  # 加载配置
    a, b = login(conf)

    batch = show_msg(a)  # 显示个人信息
    cat = conf["bx_or_xx"]
    lst = get_class(a, conf, batch=batch, category=cat)

    for kch in conf["KCH"]:
        for i in lst["data"]["rows"]:
            if i["KCH"] == kch:
                add(a, i, cookie=b, batch=batch, category=cat)
                break

    for kcm in conf["KCM"]:
        for i in lst["data"]["rows"]:
            if i["KCM"] == kcm:
                add(a, i, cookie=b, batch=batch, category=cat)
                break


def add_1(bx_or_xx, KCM=None, KCH=None, always=1):
    """
    :param bx_or_xx: 必修_or_选修: 0-必修  1-选修
    :param KCM: 课程名，例如 ["通信原理"]
    :param KCH: 课程号，例如 ["TE204004"]
    :param always: 是否连续选课 1-是  0-否
    :return:
    """
    if KCH is None:
        KCH = [""]
    if KCM is None:
        KCM = [""]
    with open("conf.json", 'r', encoding="utf-8") as f:
        conf = json.load(f)  # 加载配置
    a, b = login(conf)

    batch = show_msg(a)  # 显示个人信息
    cat = bx_or_xx
    lst = get_class(a, conf, batch=batch, category=cat)

    for kch in KCH:
        for i in lst["data"]["rows"]:
            if i["KCH"] == kch:
                add(a, i, cookie=b, batch=batch, category=cat, always=always)
                break

    for kcm in KCM:
        for i in lst["data"]["rows"]:
            if i["KCM"] == kcm:
                add(a, i, cookie=b, batch=batch, category=cat, always=always)
                break



if __name__ == '__main__':
    print('{:-^30}'.format(""))
    print('{: ^30}'.format("Welcome"))
    print('{:-^30}'.format(""))
    main()
    # add_1(0, KCM=["习近平新时代中国特色社会主义思想概论", "数字信号处理", "高频电子线路"], KCH=[""], always=1)
    print("Done")
