# DanmakuRender Configuration Task Management———— 一个批量管理DanmakuRender5配置文件的小工具

- 可以一键配置启用禁用录制主播
- 设置录制天数
- 可以设置批量主播
    
初衷是DanmakuRender5管理配置文件太麻烦，所以我为了方便自己使用，写了这个小工具，配合DanmakuRender5使用。效果很棒！

其他新功能有需求就开发吧，新建模板目前是固定的录制无弹幕2小时后自动上传b站的。想要diy功能请查看[**danmakurender-5使用文档**](https://github.com/SmallPeaches/DanmakuRender/blob/v5/docs/usage.md)

### 安装与使用说明      
## Windows安装（Linux安装懒得写） 
- 懒人一键启动 （后面的内容就可以忽略了）   
[点击这里下载](https://github.com/jiabenguiyin/DanmakuRender_Configuration_Task_Management/releases/latest)，选择下面的`DanmakuRender_Configuration_Task_Management.exe`，下载完成之后放在`DanmakuRender`文件夹即可双击启动。启动后在浏览器输入`127.0.0.1:5000`即可进入管理界面。
```shell
127.0.0.1:5000
```


1. 安装Python            
[点击这里下载Python 3.9安装包](https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe)，需要下载其他版本的可以前往[官网](https://www.python.org/downloads/)自行下载。下载完成后点击安装，安装时注意选择`Add Python xxx to PATH`这个选项，其他默认就可以。  （不过一般安装了DanmakuRender5应该不需要再次安装）   

2. 下载DMRCTM主程序    
[点击这里下载](https://github.com/jiabenguiyin/DanmakuRender_Configuration_Task_Management/releases/latest)，选择下面的`DanmakuRender_Configuration_Task_Management.zip`，下载完成之后解压把里面的所有内容全部丢进`DanmakuRender`文件夹里。

3. 安装flask和werkzeug（只能用这个版本因为我懒得升）   
安装flask降级werkzeug需要用pip命令安装：
```pip
pip install flask==1.1.2
pip install werkzeug==1.0.1
```

4. 启动程序    
在`DanmakuRender`文件夹里启动cmd，并输入以下命令启动直播配置任务管理程序：
```shell
python app.py
```
5. 创建表单（可选）    
在启动`app.py`会自动创建好表单，如果失效的话请在`DanmakuRender`文件夹里启动cmd，并输入以下命令创建表单，该表单是管理定时配置文件：
```shell
python create_db.py
```
6. 浏览器gui管理界面    
启动`app.py`后在浏览器输入`127.0.0.1:5000`即可进入管理界面。
```shell
127.0.0.1:5000
```
7. 恢复备份数据库
如果出现数据库丢失的情况下，可以通过这个指令进行恢复备份数据。
```shell
copy ..\backups\ConfigSchedulerWeb.db.backup.20250418043206 ..\ConfigSchedulerWeb.db
```
8. 查询版本    
输入该指令即可查询版本号 
```shell
python app.py --version
```

## 更多
感谢 SmallPeaches/DanmakuRender 的工作付出。            

**本程序仅供研究学习使用！**



