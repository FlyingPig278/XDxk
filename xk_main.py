from login import *


if __name__ == '__main__':
    print('{:-^30}'.format(""))
    print('{: ^30}'.format("Welcome"))
    print('{:-^30}'.format(""))


    with open("conf.json", 'r') as f:
        conf = json.load(f)     # 加载配置

    json = login(conf=conf)     # 登录
    show_msg(json)              # 显示个人信息
