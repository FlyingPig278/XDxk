import base64
import io
import time

try:
    import requests
except ImportError:  # 让启动菜单仍可打开，并给出可读的缺依赖提示
    requests = None


API_BASE = "https://xk.xidian.edu.cn/xsxk"
DEFAULT_TIMEOUT = 12


class XKError(Exception):
    """可预期的选课程序错误。"""


def _require_requests():
    if requests is None:
        raise XKError("缺少 requests 依赖，请先执行 pip install -r requirements.txt")


def _timeout(conf):
    try:
        value = float(conf.get("request_timeout", DEFAULT_TIMEOUT))
        return max(value, 1)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT


def _post_json(path, conf, *, headers=None, params=None, json_body=None, cookies=None):
    """发送 POST 请求，并把常见网络/协议异常转换成 XKError。"""
    _require_requests()
    url = f"{API_BASE}{path}"
    try:
        response = requests.post(
            url,
            headers=headers,
            params=params,
            json=json_body,
            cookies=cookies,
            timeout=_timeout(conf),
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise XKError(f"请求超时（{path}），请检查网络或稍后重试") from exc
    except requests.RequestException as exc:
        raise XKError(f"网络请求失败（{path}）：{exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        preview = response.text[:160].replace("\n", " ")
        raise XKError(
            f"接口 {path} 未返回 JSON，可能已经改版。响应片段：{preview or '<空>'}"
        ) from exc
    if not isinstance(payload, dict):
        raise XKError(f"接口 {path} 返回的数据结构不是对象，可能已经改版")
    return payload, response


def ocr_captcha(image_bytes):
    """识别验证码；OCR 库只在真正使用时加载。"""
    try:
        import ddddocr
    except ImportError as exc:
        raise XKError("缺少 ddddocr，无法自动识别验证码") from exc
    try:
        return ddddocr.DdddOcr(show_ad=False).classification(image_bytes)
    except TypeError:
        # 兼容不支持 show_ad 参数的旧版本。
        return ddddocr.DdddOcr().classification(image_bytes)
    except Exception as exc:
        raise XKError(f"验证码识别失败：{exc}") from exc


def get_captcha(conf):
    payload, response = _post_json("/auth/captcha", conf)
    if conf.get("debug") == "1":
        with open("captcha_pac.json", "wb") as file:
            file.write(response.content)

    print(payload.get("msg", "已获取验证码"))
    data = payload.get("data")
    if not isinstance(data, dict):
        raise XKError("验证码接口缺少 data 字段，接口可能已经改版")
    image_data = data.get("captcha")
    uuid = data.get("uuid")
    if not isinstance(image_data, str) or not uuid:
        raise XKError("验证码接口缺少 captcha 或 uuid 字段，接口可能已经改版")

    encoded = image_data.split(",", 1)[-1]
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise XKError("验证码图片不是有效的 Base64 数据") from exc

    if conf.get("ocr_captcha", "1") == "1":
        code = ocr_captcha(image_bytes)
        print("验证码识别结果：", code)
    else:
        try:
            import matplotlib.pyplot as plt
            import matplotlib.image as mpimg

            image = mpimg.imread(io.BytesIO(image_bytes), format="png")
            plt.imshow(image)
            plt.axis("off")
            plt.show()
        except ImportError as exc:
            raise XKError("缺少 matplotlib，无法显示验证码") from exc
        except Exception as exc:
            raise XKError(f"验证码图片显示失败：{exc}") from exc
        code = input("请输入验证码：").strip()

    if not code:
        raise XKError("验证码为空")
    return code, uuid


def login(conf):
    """登录并返回登录 JSON 和 Cookie；不会调用选课或退课接口。"""
    from getpass import getpass

    form = dict(conf.get("data") or {})
    login_name = str(form.get("loginname") or "").strip()
    password = str(form.get("password") or "")
    if not login_name:
        login_name = input("学号：").strip()
    if not password:
        password = getpass("密码：")
    if not login_name or not password:
        raise XKError("学号或密码为空")

    try:
        from encrypt import AES_encrypt

        encrypted_password = AES_encrypt(password)
    except ImportError as exc:
        raise XKError("缺少 pycryptodome，无法按选课系统要求加密密码") from exc
    except Exception as exc:
        raise XKError(f"密码加密失败：{exc}") from exc

    captcha, uuid = get_captcha(conf)
    form.update(
        {
            "loginname": login_name,
            "password": encrypted_password,
            "captcha": captcha,
            "uuid": uuid,
        }
    )
    headers = {
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/103 Safari/537.36",
    }
    payload, response = _post_json(
        "/auth/login", conf, headers=headers, params=form
    )
    if conf.get("debug") == "1":
        with open("login_pac.json", "wb") as file:
            file.write(response.content)

    token = ((payload.get("data") or {}).get("token")
             if isinstance(payload.get("data"), dict) else None)
    if not token:
        raise XKError(f"登录未成功：{payload.get('msg', '响应中没有 token')}")
    cookies = requests.utils.dict_from_cookiejar(response.cookies)
    return payload, cookies


def get_student_and_batches(login_json):
    data = login_json.get("data")
    if not isinstance(data, dict):
        raise XKError("登录响应缺少 data 字段")
    student = data.get("student")
    if not isinstance(student, dict):
        raise XKError("登录响应缺少 student 字段，接口可能已经改版")
    batches = student.get("electiveBatchList")
    if not isinstance(batches, list):
        raise XKError("登录响应缺少 electiveBatchList，接口可能已经改版")
    return student, batches


def choose_available_batch(batches, preferred_keyword=""):
    available = [
        item for item in batches
        if isinstance(item, dict) and str(item.get("canSelect")) == "1" and item.get("code")
    ]
    keyword = str(preferred_keyword or "").strip()
    if keyword:
        for item in available:
            if keyword in str(item.get("name", "")):
                return item
    if available:
        return available[0]
    raise XKError("没有找到当前可选且包含 code 的选课批次")


def show_msg(login_json, preferred_keyword=""):
    student, batches = get_student_and_batches(login_json)
    print("姓名：", student.get("XM", "<字段缺失>"))
    print("专业：", student.get("ZYMC", "<字段缺失>"))
    print("班级：", student.get("schoolClass", "<字段缺失>"))
    for item in batches:
        if isinstance(item, dict):
            print(
                "选课批次：", item.get("name", "<无名称>"),
                "\t是否可选：", item.get("canSelect", "<字段缺失>"),
            )
    selected = choose_available_batch(batches, preferred_keyword)
    print("使用批次：", selected.get("name", selected["code"]))
    return selected["code"]


def _auth_headers(login_json, batch, content_type=False):
    data = login_json.get("data") or {}
    token = data.get("token") if isinstance(data, dict) else None
    if not token:
        raise XKError("登录令牌不存在或已失效")
    headers = {
        "Connection": "keep-alive",
        "batchId": batch,
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/103 Safari/537.36",
    }
    if content_type:
        headers["Content-Type"] = "application/json;charset=UTF-8"
    return headers


def get_class(login_json, conf, batch, category=0):
    categories = ["FANKC", "XGKC"]
    if category not in (0, 1):
        raise XKError(f"未知课程类别：{category}，只支持 0（必修）或 1（选修）")
    form = {
        "teachingClassType": categories[category],
        "pageNumber": 1,
        "pageSize": 300,
        "orderBy": "",
        "campus": str(conf.get("campus", "S")),
    }
    payload, response = _post_json(
        "/elective/clazz/list",
        conf,
        headers=_auth_headers(login_json, batch, content_type=True),
        json_body=form,
    )
    if conf.get("debug") == "1":
        name = "classlist_required.json" if category == 0 else "classlist_elective.json"
        with open(name, "wb") as file:
            file.write(response.content)
    return payload


def get_class_rows(payload):
    data = payload.get("data")
    if not isinstance(data, dict):
        raise XKError(f"课程列表缺少 data 字段：{payload.get('msg', '接口可能已经改版')}")
    rows = data.get("rows")
    if not isinstance(rows, list):
        raise XKError("课程列表缺少 data.rows 数组，接口可能已经改版")
    return rows


def _action_form(class_dict, category, deleting=False):
    if not isinstance(class_dict, dict):
        raise XKError("教学班数据格式错误")
    missing = [key for key in ("JXBID", "secretVal") if not class_dict.get(key)]
    if missing:
        raise XKError("教学班缺少关键字段：" + ", ".join(missing))
    if category not in (0, 1):
        raise XKError(f"未知课程类别：{category}")
    clazz_type = "TJKC" if deleting and category == 0 else ("FANKC" if category == 0 else "XGKC")
    form = {
        "clazzType": clazz_type,
        "clazzId": class_dict["JXBID"],
        "secretVal": class_dict["secretVal"],
    }
    if not deleting or category == 1:
        form["chooseVolunteer"] = "1"
    return form


def _run_action(login_json, class_dict, cookie, batch, conf, *, category, always, deleting):
    path = "/elective/clazz/del" if deleting else "/elective/clazz/add"
    action_name = "退课" if deleting else "选课"
    form = _action_form(class_dict, category, deleting=deleting)
    headers = _auth_headers(login_json, batch)
    token = headers["Authorization"]
    cookies = dict(cookie or {})
    cookies["Authorization"] = token
    success_words = (
        ("操作成功", "退课成功", "未查询到选课结果")
        if deleting else
        ("操作成功", "选课成功", "该课程已在选课结果中", "所选课程与已选课程冲突")
    )
    try:
        interval = max(float(conf.get("request_interval", 1)), 0)
    except (TypeError, ValueError):
        interval = 1
    try:
        max_attempts = max(int(conf.get("max_attempts", 0)), 0)
    except (TypeError, ValueError):
        max_attempts = 0

    attempt = 0
    consecutive_errors = 0
    while True:
        attempt += 1
        try:
            payload, _ = _post_json(
                path, conf, headers=headers, params=form, cookies=cookies
            )
            consecutive_errors = 0
            message = str(payload.get("msg", "<响应中没有 msg>"))
            print(
                class_dict.get("KCH", "<无课程号>"),
                class_dict.get("KCM", "<无课程名>"),
                action_name,
                message,
            )
            if any(word in message for word in success_words):
                return True
        except XKError as exc:
            consecutive_errors += 1
            print(f"第 {attempt} 次{action_name}请求失败：{exc}")
            if consecutive_errors >= 5:
                print("连续失败 5 次，已停止当前课程操作，避免无休止报错。")
                return False

        if not always or (max_attempts and attempt >= max_attempts):
            return False
        if interval:
            time.sleep(interval)


def add(login_json, class_dict, cookie, batch, always=1, category=0, conf=None):
    return _run_action(
        login_json, class_dict, cookie, batch, conf or {},
        category=category, always=bool(always), deleting=False,
    )


def dele(login_json, class_dict, cookie, batch, always=1, category=0, conf=None):
    return _run_action(
        login_json, class_dict, cookie, batch, conf or {},
        category=category, always=bool(always), deleting=True,
    )

