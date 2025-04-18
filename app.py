import os
import shutil
import logging
import sqlite3
import time
import argparse
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
import requests
from logging.handlers import RotatingFileHandler
from glob import glob
from os.path import exists, splitext

# ======================
# 配置参数
# ======================
CONFIG_DIR = "configs"
DISABLED_DIR = "disabled_configs"
DB_PATH = "ConfigSchedulerWeb.db"
BACKUP_DIR = "backups"
GITHUB_REPO = "https://api.github.com/repos/jiabenguiyin/DanmakuRender_Configuration_Task_Management"
CURRENT_VERSION = "2025.04.18"  # 当前版本

# ======================
# 日志系统配置 (Python 3.9+)
# ======================
def setup_logging():
    """配置带滚动和UTF-8编码的日志系统"""
    log_format = '[%(asctime)s][%(levelname)s]: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    
    # 文件输出（每天滚动）
    os.makedirs('logs', exist_ok=True)
    log_file = f'logs/DMR-{datetime.now().strftime("%Y%m%d")}.log'
    if os.path.exists(log_file):
        _cnt = len(glob(splitext(log_file)[0] + '*'))
        log_file = splitext(log_file)[0] + f'({_cnt})' + splitext(log_file)[1]
    file_handler = logging.handlers.TimedRotatingFileHandler(log_file, when='D', interval=1, backupCount=3, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    
    # 设置logger
    logger = logging.getLogger('DMR')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# ======================
# 数据库操作（修复重启丢失问题）
# ======================
def init_db():
    """安全初始化数据库（保留现有数据）"""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
            filename TEXT PRIMARY KEY,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL
        )''')
        logging.info("数据库初始化/验证完成")
    except Exception as e:
        logging.error(f"数据库初始化失败: {str(e)}")
        raise
    finally:
        conn.commit()
        conn.close()

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ======================
# 文件状态监控增强
# ======================
def get_file_status(filename):
    """获取文件实际状态"""
    enabled_path = os.path.join(CONFIG_DIR, filename)
    disabled_path = os.path.join(DISABLED_DIR, filename)
    
    if os.path.exists(enabled_path):
        return "启用中", enabled_path
    elif os.path.exists(disabled_path):
        return "禁用", disabled_path
    return "文件丢失", None

def sync_db_with_files():
    """自动同步数据库与文件系统状态"""
    conn = get_db_connection()
    try:
        # 清理无效记录
        tasks = conn.execute('SELECT filename FROM tasks').fetchall()
        for (filename,) in tasks:
            if not (os.path.exists(os.path.join(CONFIG_DIR, filename)) or
                    os.path.exists(os.path.join(DISABLED_DIR, filename))):
                conn.execute('DELETE FROM tasks WHERE filename = ?', (filename,))
                logging.warning(f"清理无效记录: {filename}")
        
        # 添加缺失记录（仅添加新文件，保留原有日期设置）
        for f in os.listdir(CONFIG_DIR):
            if f.endswith('.yml') and f != 'global.yml':
                conn.execute('''INSERT OR IGNORE INTO tasks (filename, start_date, end_date)
                                 VALUES (?, DATE('now'), DATE('now', '+7 days'))''', (f,))
        conn.commit()
    finally:
        conn.close()

# ======================
# 业务逻辑函数
# ======================
def load_schedule():
    """加载任务计划（带自动同步）"""
    sync_db_with_files()
    
    conn = get_db_connection()
    try:
        tasks = conn.execute('SELECT filename, start_date, end_date FROM tasks ORDER BY start_date DESC').fetchall()
        result = []
        for task in tasks:
            status, _ = get_file_status(task['filename'])
            result.append({
                'filename': task['filename'],
                'start': task['start_date'],
                'end': task['end_date'],
                'status': status
            })
        return result
    finally:
        conn.close()

def get_yml_files():
    """获取可用的YML配置文件列表"""
    return [
        f.replace('.yml', '') 
        for f in os.listdir(CONFIG_DIR) 
        if f.endswith('.yml') and f.lower() != 'global.yml'
    ]

# ======================
# 启动功能
# ======================
def backup_db():
    """启动时自动备份数据库"""
    if os.path.exists(DB_PATH):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"{DB_PATH}.backup.{timestamp}")
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copyfile(DB_PATH, backup_path)
        logging.info(f"数据库已备份至: {backup_path}")

# ======================
# 路由处理
# ======================
app = Flask(__name__)

@app.route('/')
def index():
    """主界面"""
    return render_template('index.html', 
                         schedule=load_schedule(),
                         yml_files=get_yml_files())

@app.route('/add', methods=['POST'])
def add():
    """添加任务路由"""
    filename = f"{request.form['filename']}.yml"
    
    # 全局文件保护
    if 'global.yml' in filename.lower():
        logging.warning("尝试操作全局配置文件")
        return "禁止操作系统配置文件", 403

    # 验证日期格式
    try:
        start_date = datetime.strptime(request.form['start'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end'], '%Y-%m-%d')
        if start_date > end_date:
            logging.error("日期范围错误")
            return "错误：结束日期不能早于开始日期", 400
    except ValueError:
        logging.error("无效日期格式")
        return "无效的日期格式，请使用YYYY-MM-DD格式", 400

    # 处理重复配置
    try:
        add_task_to_db(filename, request.form['start'], request.form['end'])
    except sqlite3.IntegrityError:
        return f'''
            <script>
                if(confirm("配置 {filename} 已存在！\\n是否覆盖？")){{
                    window.location = "/force_add/{request.form['filename']}?start={request.form['start']}&end={request.form['end']}"; 
                }}else{{
                    window.location = "/";
                }}
            </script>
        ''', 400
    
    return redirect(url_for('index'))

@app.route('/force_add/<filename>')
def force_add(filename):
    """强制覆盖配置"""
    fullname = f"{filename}.yml"
    try:
        delete_task_from_db(fullname)
        add_task_to_db(fullname, 
                      request.args.get('start'),
                      request.args.get('end'))
        logging.info(f"强制覆盖成功: {fullname}")
    except Exception as e:
        logging.error(f"强制覆盖失败: {str(e)}")
        return f"强制覆盖失败: {str(e)}", 500
    return redirect(url_for('index'))

@app.route('/delete/<filename>')
def delete(filename):
    """删除任务路由"""
    if 'global.yml' in filename.lower():
        logging.warning("尝试删除全局配置文件")
        return "禁止编辑系统配置文件", 403
    
    try:
        delete_task_from_db(filename)
        # 删除所有位置的文件
        config_path = os.path.join(CONFIG_DIR, filename)
        disabled_path = os.path.join(DISABLED_DIR, filename)
        for path in [config_path, disabled_path]:
            if os.path.exists(path):
                os.remove(path)
        logging.info(f"完全删除配置: {filename}")
    except Exception as e:
        logging.error(f"删除失败: {str(e)}")
        return f"删除失败: {str(e)}", 500
    return redirect(url_for('index'))

@app.route('/toggle_task/<filename>')
def toggle_task(filename):
    """状态切换路由"""
    try:
        enabled_path = os.path.join(CONFIG_DIR, filename)
        disabled_path = os.path.join(DISABLED_DIR, filename)
        
        if os.path.exists(enabled_path):
            shutil.move(enabled_path, disabled_path)
            new_status = "禁用"
        elif os.path.exists(disabled_path):
            shutil.move(disabled_path, enabled_path)
            new_status = "启用中"
        else:
            raise FileNotFoundError(f"文件 {filename} 不存在")
        
        logging.info(f"状态切换成功: {filename} -> {new_status}")
    except Exception as e:
        logging.error(f"状态切换失败: {str(e)}")
        return f"状态切换失败: {str(e)}", 500
    
    return redirect(url_for('index'))

@app.route('/edit/<filename>', methods=['POST'])
def edit(filename):
    """编辑任务时间"""
    if 'global.yml' in filename.lower():
        return "禁止编辑系统配置文件", 403
    
    start = request.form['start']
    end = request.form['end']
    
    conn = get_db_connection()
    try:
        conn.execute('''UPDATE tasks 
                        SET start_date = ?, end_date = ? 
                        WHERE filename = ?''', 
                     (start, end, filename))
        logging.info(f"编辑任务: {filename}")
    except Exception as e:
        logging.error(f"编辑失败: {str(e)}")
        return f"编辑失败: {str(e)}", 500
    finally:
        conn.commit()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/create_template', methods=['POST'])
def create_template():
    """创建新模板"""
    taskname = request.form['taskname']
    url = request.form['url']
    tags = request.form['tags']
    is_repost = 'is_repost' in request.form
    
    filename = f"DMR-{taskname}.yml"
    try:
        with open(os.path.join(CONFIG_DIR, filename), 'w', encoding='utf-8') as f:
            f.write(f'''common_event_args:
  auto_render: False
  auto_upload: True
  auto_transcode: False

download_args:
  dltype: live
  url: {url}
  output_dir: ./直播回放/{taskname}
  output_name: '{{STREAMER.NAME}}-{{CTIME.YEAR}}年{{CTIME.MONTH:02d}}月{{CTIME.DAY:02d}}日{{CTIME.HOUR:02d}}点{{CTIME.MINUTE:02d}}分'
  segment: 7200
  engine: ffmpeg
  danmaku: False
  video: True

upload_args:
  src_video:
    account: bilibili
    cookies: ~
    retry: 3
    realtime: True
    min_length: 10
    line: ~
    limit: 3
    copyright: {'2' if is_repost else '1'}
    source: {url}
    tid: 65
    cover: ''
    title: '[{{STREAMER.NAME}}/直播回放] {{TITLE}} {{CTIME.YEAR}}年{{CTIME.MONTH:02d}}月{{CTIME.DAY:02d}}日'
    desc: |
      {{STREAMER.NAME}} 的直播回放
      标题：{{TITLE}} 
      时间：{{CTIME.YEAR}}年{{CTIME.MONTH:02d}}月{{CTIME.DAY:02d}}日
      直播地址：{{STREAMER.URL}} 
    tag: '{tags}'
    dtime: 0
    dolby: 0
    no_reprint: {0 if is_repost else 1}
    open_elec: 1
    dynamic: '{{STREAMER.NAME}} 的直播回放，{{CTIME.YEAR}}年{{CTIME.MONTH:02d}}月{{CTIME.DAY:02d}}日'
''')
        logging.info(f"创建模板成功: {filename}")
    except Exception as e:
        logging.error(f"模板创建失败: {str(e)}")
        return f"模板创建失败: {str(e)}", 500
    return redirect(url_for('index'))

# ======================
# 安全启动系统
# ======================
def backup_db():
    """启动时自动备份数据库"""
    if os.path.exists(DB_PATH):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"{DB_PATH}.backup.{timestamp}")
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copyfile(DB_PATH, backup_path)
        logging.info(f"数据库已备份至: {backup_path}")

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='DanmakuRender 配置任务管理')
    parser.add_argument('--version', action='store_true', help='查看当前版本')
    parser.add_argument('--skip_update', action='store_true', help='跳过版本检查')

    args = parser.parse_args()

    if args.version:
        print(f"当前版本: {CURRENT_VERSION}")
        # 检查是否有新版本可用
        try:
            response = requests.get(f"{GITHUB_REPO}/releases/latest")
            latest_version = response.json().get('tag_name', '')
            if latest_version != CURRENT_VERSION:
                print(f"有新版本可用: {latest_version}")
                print("更新日志:")
                release_notes = response.json().get('body', '暂无更新日志')
                print(release_notes)
        except requests.RequestException as e:
            print(f"版本检查失败: {e}")
    elif args.skip_update:
        print("跳过版本检查")
    
    # 启动 Flask 应用 (开发环境)
    backup_db()
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(DISABLED_DIR, exist_ok=True)
    
    init_db()

    # 启动 Flask 应用（使用 Flask 开发服务器）
    app.run(host='0.0.0.0', port=5000, debug=True)
