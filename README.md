# DanmakuRender Configuration Task Management—— 一个批量管理DanmakuRender5配置文件的小工具
结合网络上的代码写的一个能录制带弹幕直播流的小工具，主要用来录制包含弹幕的视频流。     
- 可以一键配置启用禁用录制主播
- 设置录制天数
- 可以设置批量主播
    
初衷是DanmakuRender5管理配置文件太麻烦，所以我为了方便自己使用，写了这个小工具，配合DanmakuRender5使用。效果很棒！

### 安装与使用文档      
## Windows安装 

1. 安装Python            
[点击这里下载Python 3.9安装包](https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe)，需要下载其他版本的可以前往[官网](https://www.python.org/downloads/)自行下载。下载完成后点击安装，安装时注意选择`Add Python xxx to PATH`这个选项，其他默认就可以。  （不过一般安装了DanmakuRender5应该不需要安装）   

2. 下载DMR主程序    
[点击这里下载](https://github.com/jiabenguiyin/DanmakuRender_Configuration_Task_Management/releases/latest)，选择下面的`Source code.zip`，下载完成之后解压把里面的所有内容全部丢进`DanmakuRender`文件夹里。

3. 安装flask     
安装flask需要用pip命令安装：
```pip
pip install flask
```

4.创建表单
在`DanmakuRender`文件夹里启动cmd，并输入以下命令创建表单，该表单是管理定时配置文件的非常重要：
```shell
python create_db.py
```

5.启动程序
在`DanmakuRender`文件夹里启动cmd，并输入以下命令启动直播配置任务管理程序：
```shell
python app.py
```
6.浏览器gui管理界面
启动`app.py`后在浏览器输入`127.0.0.1:5000`即可进入管理界面。
```shell
127.0.0.1:5000
```

## 更多
感谢 SmallPeaches/DanmakuRender 的工作付出。            

**本程序仅供研究学习使用！**



