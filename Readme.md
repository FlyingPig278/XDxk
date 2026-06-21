# XDXK

建议第一次使用时先运行“只读兼容性检测”。

## 安装

在项目目录执行：

```commandline
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## 启动

运行 `xk_main.py`，程序会显示菜单：

```text
1. 正常选课
2. 只读兼容性检测（推荐先运行）
3. 编辑配置
4. 退课
0. 退出
```

不需要添加命令行参数。

### 推荐使用顺序

1. 进入“编辑配置”，填写学号、密码和课程。
2. 运行“只读兼容性检测”。
3. 确认登录、批次和课程字段检测通过后，再选择“正常选课”或“退课”。

只读检测仅请求以下内容：

- 验证码；
- 登录；
- 学生信息与选课批次；
- 必修课和选修课列表。

检测过程不会调用选课接口 `/elective/clazz/add` 或退课接口 `/elective/clazz/del`。

## 配置

全部配置统一保存在被 Git 忽略的 `.env`。可以通过启动菜单编辑，也可以复制 `.env.example` 为 `.env` 后直接修改：

```dotenv
XK_LOGINNAME="学号"
XK_PASSWORD="密码"
XK_OCR_CAPTCHA="1"
XK_DEBUG="0"
XK_BATCH_KEYWORD="2026级"
XK_CAMPUS="S"
XK_REQUEST_TIMEOUT=12
XK_REQUEST_INTERVAL=1
XK_MAX_ATTEMPTS=0
XK_CATEGORY=0
XK_REQUIRED_COURSES="TE204004:06,TE204004:07"
XK_ELECTIVE_COURSES="FL006066,FL006121"
```

主要配置含义：

- `XK_OCR_CAPTCHA`：`1` 自动识别验证码，`0` 显示图片后手动输入；
- `XK_DEBUG`：`1` 保存接口原始响应，`0` 不保存；
- `XK_BATCH_KEYWORD`：可编辑的批次名称关键词，例如 `2026级`；留空则自动选择第一个当前可选批次；
- `XK_CAMPUS`：课程列表接口使用的校区代码；
- `XK_REQUEST_TIMEOUT`：单次网络请求超时秒数；
- `XK_REQUEST_INTERVAL`：连续选课/退课请求的间隔秒数；
- `XK_MAX_ATTEMPTS`：每门课最大尝试次数；`0` 表示不限制；
- `XK_CATEGORY`：`0` 必修，`1` 选修；
- `XK_REQUIRED_COURSES`：必修课，格式为 `课程号:课序号`；
- `XK_ELECTIVE_COURSES`：选修课，只填写课程号。

在菜单编辑器中，直接回车表示保留原值，输入 `-` 表示清空该项。多门课程使用逗号分隔，例如：

## 容错行为

- 网络超时、非 JSON 响应、字段缺失和登录失败会显示原因并返回主菜单；
- 连续选课或退课发生 5 次网络/协议错误后，会停止当前课程操作；
- 按 `Ctrl+C` 会取消当前操作并返回菜单，而不是退出整个程序；
- 缺少可选依赖时会给出安装提示，不会在打开程序时直接闪退。
