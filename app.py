import os
import shutil
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

CONFIG_DIR = "configs"
DISABLED_DIR = "disabled_configs"
DB_PATH = "ConfigSchedulerWeb.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('DROP TABLE IF EXISTS tasks')
        conn.execute('''
            CREATE TABLE tasks (
                filename TEXT PRIMARY KEY,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL
            )
        ''')
        print("数据库表已创建")
    except Exception as e:
        print(f"数据库初始化错误: {str(e)}")
    finally:
        conn.commit()
        conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_schedule():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return tasks

def get_yml_files():
    return [f.replace('.yml', '') for f in os.listdir(CONFIG_DIR) if f.endswith('.yml')]

def add_task_to_db(filename, start, end):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT OR REPLACE INTO tasks 
            (filename, start_date, end_date)
            VALUES (?, ?, ?)
        ''', (filename, start, end))
    finally:
        conn.commit()
        conn.close()

def delete_task_from_db(filename):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM tasks WHERE filename = ?', (filename,))
    finally:
        conn.commit()
        conn.close()

@app.route('/')
def index():
    tasks = []
    for task in load_schedule():
        tasks.append({
            'filename': task['filename'],
            'start': task['start_date'],
            'end': task['end_date'],
            'status': "启用中" if os.path.exists(os.path.join(CONFIG_DIR, task['filename'])) else "禁用"
        })
    return render_template('index.html', 
                         schedule=tasks,
                         yml_files=get_yml_files())

@app.route('/add', methods=['POST'])
def add():
    filename = f"{request.form['filename']}.yml"
    start = request.form['start']
    end = request.form['end']
    
    if datetime.strptime(start, '%Y-%m-%d') > datetime.strptime(end, '%Y-%m-%d'):
        return "错误：结束日期不能早于开始日期", 400
        
    add_task_to_db(filename, start, end)
    return redirect(url_for('index'))

@app.route('/delete/<filename>')
def delete(filename):
    try:
        delete_task_from_db(filename)
        config_path = os.path.join(CONFIG_DIR, filename)
        if os.path.exists(config_path):
            os.remove(config_path)
    except Exception as e:
        return f"删除失败: {str(e)}", 500
    return redirect(url_for('index'))

@app.route('/edit/<filename>', methods=['POST'])
def edit(filename):
    start = request.form['start']
    end = request.form['end']
    
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE tasks 
            SET start_date = ?, end_date = ?
            WHERE filename = ?
        ''', (start, end, filename))
    finally:
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/toggle_task/<filename>')
def toggle_task(filename):
    src = os.path.join(CONFIG_DIR, filename)
    dst = os.path.join(DISABLED_DIR, filename)
    
    try:
        if os.path.exists(src):
            shutil.move(src, dst)
        else:
            shutil.move(dst, src)
    except Exception as e:
        return f"状态切换失败: {str(e)}", 500
    return redirect(url_for('index'))

@app.route('/create_template', methods=['POST'])
def create_template():
    taskname = request.form['taskname']
    url = request.form['url']
    tags = request.form['tags']
    is_repost = 'is_repost' in request.form
    
    filename = f"DMR-{taskname}.yml"
    try:
        with open(os.path.join(CONFIG_DIR, filename), 'w') as f:
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
    except Exception as e:
        return f"模板创建失败: {str(e)}", 500
    return redirect(url_for('index'))

if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(DISABLED_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
