# _How To Install_

下载或者克隆项目到本地

进入文件夹目录

执行:
```commandline
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```
---

# _How To Use_


打开**conf.json**
```
{
  "ocr_captcha": "1",               是否使用自动识别验证码
  "debug": "0",                     是否输出调试文件
  "bx_or_xx": "0",                  0是必修，1是选修
  "bx": [                           必修的格式
    {
      "KCH": "TE204003",            课程号
      "KXH": "02"                   课序号(小卡片左上角：[01])(必填)
    }
  ],
  "xx": [                           选修的格式
    {
      "KCH": "FL006066"             课程号
    }
  ],
  "data": {
    "loginname": "username",        学号
    "password": "password",         密码
    "captcha": "xxxx",
    "uuid": "xxxx"
  }
}
```
将 **学号（username）密码（password）** 填入，然后保存

---
# _How To Run_
1、在conf.json中相应位置填入**课程号**或**课程名**，**可以填多个**

2、修改"bx_or_xx"的参数，0表示必修，1表示选修

**！单次只能选择一种类别（必修/选修）**

用任意IDE运行xk_main.py，或者拖动到cmd里面执行

---

# _How To Run _ 2 (unfinish)_
为了提供一种更加灵活的选课方法，在xk_main.py中提供了
`add_1(bx_or_xx, KCM=[""], KCH=[""], always=1)`
函数，优先级高于conf.json
```
参数:
 - bx_or_xx: 必修_or_选修 : 0_or_1
 - KCM=[""]: 课程名，例如["高等数学","线性代数"]
 - KCH=[""]: 课程号，例如["TE204004", "TE204001"]
 - always  : 是否连续选课
   - 为1表示，按照顺序，选课成功后才会进行下一门课
   - 为0表示，仅执行一次选课操作
   ```
若要使用add_1函数,将xk_main.py下面代码中main()改为add_1()
```commandline
if __name__ == '__main__':
    print('{:-^30}'.format(""))
    print('{: ^30}'.format("Welcome"))
    print('{:-^30}'.format(""))
    add_1(bx_or_xx, KCM=[""], KCH=[""], always=1)
    # main()
    print("Done")
```
del_1函数同add_1

---
# Attention
 - 如果conf.json中没填学号密码，运行时可以手动输入
 - 如果运行时提示**验证码错误**，可以**重新运行**，或者**改为手动识别验证码(不建议)**
 - 手动输入验证码需要将图片关闭后，再输入
 - 通过对add_1函数的组合，可以同时实现必修和选修