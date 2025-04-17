import os
import shutil
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

CONFIG_DIR = "configs"  # 启用中的配置文件夹
DISABLED_DIR = "disabled_configs"  # 禁用的配置文件夹
DB_PATH = "ConfigSchedulerWeb.db"  # SQLite 数据库路径

# 获取数据库连接
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 获取所有任务
def load_schedule():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return tasks

# 获取 config 目录下的所有 .yml 文件（主播名）
def get_yml_files():
    yml_files = []
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith('.yml'):
            yml_files.append(filename.replace('.yml', ''))  # 获取文件名去掉 .yml 后缀
    return yml_files

# 添加新任务
def add_task_to_db(filename, start, end):
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (filename, start_date, end_date) VALUES (?, ?, ?)', (filename, start, end))
    conn.commit()
    conn.close()

# 删除任务
def delete_task_from_db(filename):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE filename = ?', (filename,))
    conn.commit()
    conn.close()

# 启用配置文件
def enable_task(filename):
    config_path = os.path.join(DISABLED_DIR, f"DMR-{filename}.yml")
    target_path = os.path.join(CONFIG_DIR, f"DMR-{filename}.yml")
    shutil.move(config_path, target_path)
    add_task_to_db(f"DMR-{filename}.yml", "2025-01-01", "2025-12-31")  # 默认时间，可以后续修改

# 禁用配置文件
def disable_task(filename):
    config_path = os.path.join(CONFIG_DIR, f"DMR-{filename}.yml")
    target_path = os.path.join(DISABLED_DIR, f"DMR-{filename}.yml")
    shutil.move(config_path, target_path)
    delete_task_from_db(f"DMR-{filename}.yml")

@app.route('/')
def index():
    yml_files = get_yml_files()  # 获取 .yml 文件列表
    tasks = load_schedule()  # 获取任务
    status_list = []
    for task in tasks:
        status_list.append({
            'filename': task['filename'],
            'start': task['start_date'],
            'end': task['end_date'],
            'status': "启用中" if os.path.exists(os.path.join(CONFIG_DIR, task['filename'])) else "禁用"
        })
    return render_template('index.html', schedule=status_list, yml_files=yml_files)

@app.route('/add', methods=['POST'])
def add():
    filename = f"DMR-{request.form['filename']}.yml"  # 自动加上 DMR 前缀
    start = request.form['start']
    end = request.form['end']
    add_task_to_db(filename, start, end)
    return redirect(url_for('index'))

@app.route('/delete/<filename>')
def delete(filename):
    delete_task_from_db(filename)
    return redirect(url_for('index'))

@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit(filename):
    if request.method == 'POST':
        start = request.form['start']
        end = request.form['end']
        # 更新任务的时间
        conn = get_db_connection()
        conn.execute('UPDATE tasks SET start_date = ?, end_date = ? WHERE filename = ?', (start, end, filename))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    # 获取任务信息
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE filename = ?', (filename,)).fetchone()
    conn.close()

    return render_template('edit.html', task=task)

@app.route('/toggle_task/<filename>')
def toggle_task(filename):
    # 获取当前文件的状态
    config_path = os.path.join(CONFIG_DIR, filename)
    disabled_path = os.path.join(DISABLED_DIR, filename)

    if os.path.exists(config_path):  # 如果是启用状态，禁用它
        shutil.move(config_path, disabled_path)
    else:  # 如果是禁用状态，启用它
        shutil.move(disabled_path, config_path)

    return redirect(url_for('index'))

@app.route('/create_template', methods=['POST'])
def create_template():
    taskname = request.form['taskname']
    url = request.form['url']
    tag = request.form['tag']
    is_repost = 'is_repost' in request.form  # 检查是否勾选了转载
    
    # 保存模板内容到配置文件
    config_file = os.path.join(CONFIG_DIR, f"DMR-{taskname}.yml")
    with open(config_file, 'w') as f:
        # 写入 common_event_args
        f.write("common_event_args:\n")
        f.write("  auto_render: False\n")
        f.write("  auto_upload: True\n")
        f.write("  auto_transcode: False\n")
        
        # 写入 download_args
        f.write("download_args:\n")
        f.write(f"  dltype: live\n")
        f.write(f"  url: {url}\n")
        f.write(f"  output_dir: ./直播回放/{taskname}\n")
        f.write("  output_name: '{STREAMER.NAME}-{CTIME.YEAR}年{CTIME.MONTH:02d}月{CTIME.DAY:02d}日{CTIME.HOUR:02d}点{CTIME.MINUTE:02d}分'\n")
        f.write("  segment: 7200\n")
        f.write("  engine: ffmpeg\n")
        f.write("  danmaku: False\n")
        f.write("  video: True\n")
        
        # 写入 upload_args
        f.write("upload_args:\n")
        f.write("  src_video:\n")
        f.write("    account: bilibili\n")
        f.write("    cookies: ~\n")
        f.write("    retry: 3\n")
        f.write("    realtime: True\n")
        f.write("    min_length: 10\n")
        f.write("    line: ~\n")
        f.write("    limit: 3\n")
        f.write(f"    copyright: 1\n")
        f.write(f"    source: {url}\n")
        f.write("    tid: 65\n")
        f.write("    cover: ''\n")
        f.write("    title: '[{STREAMER.NAME}/直播回放] {TITLE} {CTIME.YEAR}年{CTIME.MONTH:02d}月{CTIME.DAY:02d}日'\n")
        
        # 写入多行desc
        f.write("    desc: |\n")
        f.write("      {STREAMER.NAME} 的直播回放\n")
        f.write("      标题：{TITLE} \n")
        f.write("      时间：{CTIME.YEAR}年{CTIME.MONTH:02d}月{CTIME.DAY:02d}日\n")
        f.write("      直播地址：{STREAMER.URL} \n")
        
        # 写入其他字段
        f.write(f"    tag: '直播录像,{tag}'\n")
        f.write("    dtime: 0\n")
        f.write("    dolby: 0\n")
        f.write("    no_reprint: 1\n")
        f.write("    open_elec: 1\n")
        # 新增dynamic字段
        f.write("    dynamic: '{STREAMER.NAME} 的直播回放，{CTIME.YEAR}年{CTIME.MONTH:02d}月{CTIME.DAY:02d}日'\n")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)