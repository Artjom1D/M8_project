import sqlite3


class Bot:

    def __init__(self, db="jobs.db"):
        self.db = db

    def conn(self):
        return sqlite3.connect(self.db, check_same_thread=False)

    def init_db(self):
        with self.conn() as c:
            cur = c.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                title TEXT,
                salary_from INTEGER,
                salary_to INTEGER,
                skills TEXT,
                level TEXT,
                category TEXT
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                interests TEXT,
                level TEXT,
                meta TEXT
            )
            """)

    def add_job(self, company, title, sf, st, skills, level, category):
        with self.conn() as c:
            cur = c.cursor()

            cur.execute("""
            INSERT INTO jobs(company,title,salary_from,salary_to,skills,level,category)
            VALUES(?,?,?,?,?,?,?)
            """, (company, title, sf or 0, st or 0, skills, level, category))

            return cur.lastrowid

    def find_jobs(self, keyword=None, category=None, limit=50):

        where = []
        params = []

        if keyword:
            where.append("(title LIKE ? OR skills LIKE ? OR company LIKE ?)")
            k = f"%{keyword}%"
            params += [k, k, k]

        if category:
            where.append("category=?")
            params.append(category)

        query = "SELECT * FROM jobs"

        if where:
            query += " WHERE " + " AND ".join(where)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self.conn() as c:
            cur = c.cursor()
            cur.execute(query, params)

            rows = cur.fetchall()

        cols = ["id","company","title","salary_from","salary_to","skills","level","category"]
        return [dict(zip(cols, r)) for r in rows]

    def add_or_update_user(self, uid, name=None, interests=None, level=None, meta=None):

        with self.conn() as c:
            cur = c.cursor()

            cur.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
            exists = cur.fetchone()

            if exists:
                cur.execute("""
                UPDATE users
                SET name=COALESCE(?,name),
                    interests=COALESCE(?,interests),
                    level=COALESCE(?,level),
                    meta=COALESCE(?,meta)
                WHERE user_id=?
                """, (name, interests, level, meta, uid))

            else:
                cur.execute("""
                INSERT INTO users(user_id,name,interests,level,meta)
                VALUES(?,?,?,?,?)
                """, (uid, name or "", interests or "", level or "", meta or ""))

    def get_user(self, uid):

        with self.conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
            row = cur.fetchone()

        if not row:
            return None

        cols = ["user_id","name","interests","level","meta"]
        return dict(zip(cols, row))

    def recommend_jobs(self, uid, limit=6):

        with self.conn() as c:
            cur = c.cursor()

            cur.execute("""
            SELECT * FROM jobs
            ORDER BY RANDOM()
            LIMIT ?
            """, (limit,))

            rows = cur.fetchall()

        cols = ["id","company","title","salary_from","salary_to","skills","level","category"]
        return [dict(zip(cols, r)) for r in rows]

    def format_job(self, job):

        salary = "з/п не указана"

        if job["salary_from"] or job["salary_to"]:
            salary = f"{job['salary_from']}-{job['salary_to']}"

        return (
            f"<b>{job['title']}</b> ({job['company']})\n"
            f"💰 {salary}\n"
            f"🛠 {job['skills']}\n"
            f"📂 {job['category']}, {job['level']}"
        )