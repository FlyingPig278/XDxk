# -*- coding: utf-8 -*-
import json
import os
from getpass import getpass
from pathlib import Path

from func import (
    XKError,
    add,
    choose_available_batch,
    dele,
    get_class,
    get_class_rows,
    get_student_and_batches,
    login,
    show_msg,
)


ENV_PATH = Path(__file__).with_name(".env")
DEFAULT_CONFIG = {
    "ocr_captcha": "1",
    "debug": "0",
    "bx_or_xx": 0,
    "bx": [],
    "xx": [],
    "batch_keyword": "",
    "campus": "S",
    "request_timeout": 12,
    "request_interval": 1,
    "max_attempts": 0,
    "data": {"loginname": "", "password": "", "captcha": "", "uuid": ""},
}


def load_config():
    if not ENV_PATH.exists():
        save_config(dict(DEFAULT_CONFIG))
        print(f"未找到配置文件，已创建：{ENV_PATH}")
        return json.loads(json.dumps(DEFAULT_CONFIG))
    values = _load_env_values()
    conf = json.loads(json.dumps(DEFAULT_CONFIG))
    conf["ocr_captcha"] = str(_env_get(values, "XK_OCR_CAPTCHA", "1"))
    conf["debug"] = str(_env_get(values, "XK_DEBUG", "0"))
    conf["batch_keyword"] = str(_env_get(values, "XK_BATCH_KEYWORD", ""))
    conf["campus"] = str(_env_get(values, "XK_CAMPUS", "S"))
    try:
        conf["request_timeout"] = max(float(_env_get(values, "XK_REQUEST_TIMEOUT", 12)), 1)
        conf["request_interval"] = max(float(_env_get(values, "XK_REQUEST_INTERVAL", 1)), 0)
        conf["max_attempts"] = max(int(_env_get(values, "XK_MAX_ATTEMPTS", 0)), 0)
        conf["bx_or_xx"] = int(_env_get(values, "XK_CATEGORY", 0))
    except (TypeError, ValueError) as exc:
        raise XKError(".env 中的超时、间隔、尝试次数或课程类别格式错误") from exc
    if conf["bx_or_xx"] not in (0, 1):
        raise XKError(".env 中的 XK_CATEGORY 只能是 0 或 1")
    conf["bx"] = _parse_required_courses(str(_env_get(values, "XK_REQUIRED_COURSES", "")))
    conf["xx"] = _parse_elective_courses(str(_env_get(values, "XK_ELECTIVE_COURSES", "")))
    conf["data"] = {
        "loginname": str(_env_get(values, "XK_LOGINNAME", "")),
        "password": str(_env_get(values, "XK_PASSWORD", "")),
        "captcha": "",
        "uuid": "",
    }
    return conf


def save_config(conf):
    data = conf.get("data") or {}
    required = ",".join(
        f"{item.get('KCH', '')}:{item.get('KXH', '')}" for item in conf.get("bx", [])
    )
    elective = ",".join(str(item.get("KCH", "")) for item in conf.get("xx", []))
    values = {
        "XK_LOGINNAME": data.get("loginname", ""),
        "XK_PASSWORD": data.get("password", ""),
        "XK_OCR_CAPTCHA": conf.get("ocr_captcha", "1"),
        "XK_DEBUG": conf.get("debug", "0"),
        "XK_BATCH_KEYWORD": conf.get("batch_keyword", ""),
        "XK_CAMPUS": conf.get("campus", "S"),
        "XK_REQUEST_TIMEOUT": conf.get("request_timeout", 12),
        "XK_REQUEST_INTERVAL": conf.get("request_interval", 1),
        "XK_MAX_ATTEMPTS": conf.get("max_attempts", 0),
        "XK_CATEGORY": conf.get("bx_or_xx", 0),
        "XK_REQUIRED_COURSES": required,
        "XK_ELECTIVE_COURSES": elective,
    }
    content = "".join(
        f"{key}={json.dumps(value, ensure_ascii=False)}\n" for key, value in values.items()
    )
    try:
        ENV_PATH.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise XKError(f"配置保存失败：{exc}") from exc


def _decode_env_value(value):
    value = value.strip()
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        if value.startswith(('"', "'")) and len(value) >= 2:
            return value[1:-1]
        return value


def _load_env_values():
    values = {}
    try:
        for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = _decode_env_value(value)
    except OSError as exc:
        raise XKError(f".env 无法读取：{exc}") from exc
    return values


def _env_get(values, key, default):
    if key in os.environ:
        return _decode_env_value(os.environ[key])
    return values.get(key, default)


def _prompt(label, current, *, hidden=False):
    shown = "已设置" if hidden and current else (str(current) if current != "" else "空")
    prompt = f"{label} [{shown}]（回车保留，输入 - 清空）："
    value = getpass(prompt) if hidden else input(prompt)
    if value == "":
        return current
    return "" if value.strip() == "-" else value.strip()


def _parse_required_courses(text):
    courses = []
    for item in text.replace("，", ",").split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.replace("：", ":").split(":", 1)
        if len(parts) != 2 or not all(part.strip() for part in parts):
            raise XKError(f"必修课格式错误：{item}；应为 课程号:课序号")
        courses.append({"KCH": parts[0].strip(), "KXH": parts[1].strip()})
    return courses


def _parse_elective_courses(text):
    return [
        {"KCH": item.strip()}
        for item in text.replace("，", ",").split(",")
        if item.strip()
    ]


def edit_config():
    conf = load_config()
    print("\n配置编辑模式；直接回车保留原值，输入 - 可清空原值。")
    data = conf["data"]
    data["loginname"] = _prompt("学号", data.get("loginname", ""))
    data["password"] = _prompt("密码", data.get("password", ""), hidden=True)
    conf["ocr_captcha"] = _prompt("自动识别验证码（1/0）", conf.get("ocr_captcha", "1"))
    conf["debug"] = _prompt("保存调试响应（1/0）", conf.get("debug", "0"))
    conf["batch_keyword"] = _prompt(
        "批次名称关键词（如 2026级；留空自动选择首个可选批次）",
        conf.get("batch_keyword", ""),
    )
    conf["campus"] = _prompt("校区代码", conf.get("campus", "S"))
    category = _prompt("课程类别（0 必修 / 1 选修）", conf.get("bx_or_xx", 0))
    if str(category) not in ("0", "1"):
        raise XKError("课程类别只能是 0 或 1")
    conf["bx_or_xx"] = int(category)

    required = ", ".join(f"{c.get('KCH', '')}:{c.get('KXH', '')}" for c in conf["bx"])
    elective = ", ".join(str(c.get("KCH", "")) for c in conf["xx"])
    required_input = input(
        f"必修课（课程号:课序号，逗号分隔） [{required or '空'}]（回车保留，- 清空）："
    )
    elective_input = input(
        f"选修课（课程号，逗号分隔） [{elective or '空'}]（回车保留，- 清空）："
    )
    if required_input.strip() == "-":
        conf["bx"] = []
    elif required_input.strip():
        conf["bx"] = _parse_required_courses(required_input)
    if elective_input.strip() == "-":
        conf["xx"] = []
    elif elective_input.strip():
        conf["xx"] = _parse_elective_courses(elective_input)

    timeout = _prompt("网络超时秒数", conf.get("request_timeout", 12))
    interval = _prompt("重复请求间隔秒数", conf.get("request_interval", 1))
    attempts = _prompt("单课最大尝试次数（0 表示不限）", conf.get("max_attempts", 0))
    try:
        conf["request_timeout"] = max(float(timeout), 1)
        conf["request_interval"] = max(float(interval), 0)
        conf["max_attempts"] = max(int(attempts), 0)
    except ValueError as exc:
        raise XKError("超时、间隔或尝试次数不是有效数字") from exc

    save_config(conf)
    print("全部配置已保存到 Git 忽略的 .env。")


def _find_classes(rows, requested, category):
    found = []
    for target in requested:
        target_kch = str(target.get("KCH", ""))
        match = None
        for row in rows:
            if not isinstance(row, dict) or str(row.get("KCH", "")) != target_kch:
                continue
            if category == 1:
                match = row
                break
            tc_list = row.get("tcList")
            if not isinstance(tc_list, list):
                continue
            for teaching_class in tc_list:
                if (
                    isinstance(teaching_class, dict)
                    and str(teaching_class.get("KXH", "")) == str(target.get("KXH", ""))
                ):
                    # 某些版本把课程号/名称只放在父级，补入后便于输出。
                    match = dict(teaching_class)
                    match.setdefault("KCH", row.get("KCH"))
                    match.setdefault("KCM", row.get("KCM"))
                    break
            if match:
                break
        found.append((target, match))
    return found


def perform_action(action="add", category=None, courses=None, always=1):
    conf = load_config()
    category = conf["bx_or_xx"] if category is None else category
    requested = courses if courses is not None else conf["bx" if category == 0 else "xx"]
    if not requested:
        raise XKError("没有配置目标课程，请先进入配置编辑模式")

    login_json, cookies = login(conf)
    batch = show_msg(login_json, conf.get("batch_keyword", ""))
    rows = get_class_rows(get_class(login_json, conf, batch, category))
    for target, class_info in _find_classes(rows, requested, category):
        if class_info is None:
            suffix = f"，课序号 {target.get('KXH')}" if category == 0 else ""
            print(f"未找到课程 {target.get('KCH')}{suffix}；可能是课程不存在或接口字段已变化。")
            continue
        function = add if action == "add" else dele
        function(
            login_json,
            class_info,
            cookies,
            batch,
            always=always,
            category=category,
            conf=conf,
        )


def main():
    perform_action("add")


def add_1(bx_or_xx, kc=None, always=1):
    perform_action("add", category=bx_or_xx, courses=kc or [], always=always)


def del_1(bx_or_xx, kc=None, always=1):
    perform_action("delete", category=bx_or_xx, courses=kc or [], always=always)


def _field_check(item, fields):
    return [field for field in fields if field not in item]


def compatibility_test():
    """只读检测：仅登录并读取批次、必修和选修课程列表。"""
    conf = load_config()
    print("\n开始只读兼容性检测，不会发送选课或退课请求。")
    print("[1/4] 获取验证码并登录……")
    login_json, _ = login(conf)
    print("      成功：登录响应包含 token。")

    print("[2/4] 检查四年前使用的学生与批次定位字段……")
    student, batches = get_student_and_batches(login_json)
    old_fields = _field_check(student, ("XM", "ZYMC", "schoolClass", "electiveBatchList"))
    if old_fields:
        print("      警告：缺少旧字段：" + ", ".join(old_fields))
    else:
        print("      成功：旧学生字段仍存在。")
    old_2020 = [b for b in batches if isinstance(b, dict) and "2020级" in str(b.get("name", ""))]
    print(
        "      旧定位条件“批次名称包含 2020级”："
        + (f"仍能找到 {len(old_2020)} 项。" if old_2020 else "已找不到；正常模式会自动选择当前可选批次。")
    )
    batch_info = choose_available_batch(batches, conf.get("batch_keyword", ""))
    batch = batch_info["code"]
    print(f"      当前检测批次：{batch_info.get('name', batch)}")

    print("[3/4] 检查必修课列表接口和旧字段……")
    required_rows = get_class_rows(get_class(login_json, conf, batch, 0))
    if not required_rows:
        print("      接口可访问，但返回 0 门课，无法抽样验证教学班字段。")
    else:
        row = next((r for r in required_rows if isinstance(r, dict)), {})
        missing = _field_check(row, ("KCH", "KCM", "tcList"))
        tc_list = row.get("tcList") if isinstance(row.get("tcList"), list) else []
        if tc_list and isinstance(tc_list[0], dict):
            missing.extend(f"tcList[].{f}" for f in _field_check(tc_list[0], ("KXH", "JXBID", "secretVal")))
        elif "tcList" not in missing:
            missing.append("tcList[]（列表为空，无法验证内部字段）")
        print("      " + ("警告：缺少 " + ", ".join(missing) if missing else "成功：旧必修课定位字段仍存在。"))

    print("[4/4] 检查选修课列表接口和旧字段……")
    elective_rows = get_class_rows(get_class(login_json, conf, batch, 1))
    if not elective_rows:
        print("      接口可访问，但返回 0 门课，无法抽样验证课程字段。")
    else:
        row = next((r for r in elective_rows if isinstance(r, dict)), {})
        missing = _field_check(row, ("KCH", "KCM", "JXBID", "secretVal"))
        monitor_missing = _field_check(row, ("SFYX", "numberOfSelected", "classCapacity"))
        print("      " + ("警告：缺少选课定位字段 " + ", ".join(missing) if missing else "成功：旧选修课定位字段仍存在。"))
        if monitor_missing:
            print("      余量监控字段有变化或缺失：" + ", ".join(monitor_missing))
        else:
            print("      成功：旧余量监控字段仍存在。")
    print("\n检测完成：以上过程未调用 /clazz/add 或 /clazz/del。")


def run_menu():
    while True:
        print("\n" + "-" * 34)
        print("西电选课工具")
        print("1. 正常选课")
        print("2. 只读兼容性检测（推荐先运行）")
        print("3. 编辑配置")
        print("4. 退课")
        print("0. 退出")
        choice = input("请选择：").strip()
        try:
            if choice == "1":
                main()
            elif choice == "2":
                compatibility_test()
            elif choice == "3":
                edit_config()
            elif choice == "4":
                perform_action("delete")
            elif choice == "0":
                print("已退出。")
                return
            else:
                print("请输入 0～4。")
        except XKError as exc:
            print(f"\n操作未完成：{exc}")
        except KeyboardInterrupt:
            print("\n操作已取消，返回主菜单。")
        except Exception as exc:
            # 最后一层保护：未知的接口改动也不应让整个程序闪退。
            print(f"\n遇到未预料的错误，已返回主菜单：{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    run_menu()
