import sqlite3

# 创建数据库并连接
conn = sqlite3.connect('ConfigSchedulerWeb.db')

# 创建任务表 (tasks) 和日志表 (logs)
cursor = conn.cursor()

# 创建任务表
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL
)
''')

# 创建日志表
cursor.execute('''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    filename TEXT,
    user TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# 提交并关闭连接
conn.commit()
conn.close()

print("数据库和表创建成功！")
