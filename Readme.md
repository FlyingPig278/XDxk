# How To Use

---

打开**conf.json**
```
{
  "ocr_captcha": "1",               是否使用自动识别验证码
  "debug": "0",                     是否输出调试文件
  "data": {
    "loginname": "username",        学号
    "password": "password",         密码
    "captcha": "xxxx",
    "uuid": "xxxx"
  }
}
```
只需将**学号密码**填入，然后保存即可

---
打开xk_main.py

运行

---
 - 如果conf.json中没填学号密码，运行时可以手动输入
 - 如果运行时提示**验证码错误**，可以**重新运行**，或者**改为手动识别验证码(不建议)**
 - 手动识别验证码需要将图片关闭后，再输入验证码