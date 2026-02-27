import sqlite3
from typing import List, Dict, Optional, Any


class Bot:
    """Лёгкая логика работы с базой вакансий и профилями пользователей.

    Функции:
    - инициализация БД с двумя таблицами: `jobs` и `users`
    - добавление вакансий
    - сохранение/обновление профиля пользователя (interests, level)
    - поиск вакансий и персонализированные рекомендации
    - утилита, возвращающая формат данных, которые можно дополнять
    """

    def __init__(self, db_path: str = "jobs.db"):
        self.db = db_path

    def get_conn(self):
        return sqlite3.connect(self.db, check_same_thread=False)

    def init_db(self) -> None:
        conn = self.get_conn()
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(jobs)")
        cols = [row[1] for row in cur.fetchall()]
        expected_jobs = ["id", "company", "title", "salary_from", "salary_to", "skills", "level", "category"]
        if cols and cols != expected_jobs:
            cur.execute("DROP TABLE IF EXISTS jobs")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                title TEXT,
                salary_from INTEGER,
                salary_to INTEGER,
                skills TEXT,
                level TEXT,
                category TEXT
            )
        """
        )

        cur.execute("PRAGMA table_info(users)")
        cols_u = [row[1] for row in cur.fetchall()]
        expected_users = ["user_id", "name", "interests", "level", "meta"]
        if cols_u and cols_u != expected_users:
            cur.execute("DROP TABLE IF EXISTS users")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                interests TEXT,
                level TEXT,
                meta TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def add_job(self, company: str, title: str, salary_from: Optional[int], salary_to: Optional[int], skills: str, level: str, category: str) -> int:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO jobs (company,title,salary_from,salary_to,skills,level,category) VALUES (?,?,?,?,?,?,?)",
            (company, title, salary_from or 0, salary_to or 0, skills, level, category),
        )
        job_id = cur.lastrowid
        conn.commit()
        conn.close()
        return job_id

    def find_jobs(self, keyword: Optional[str] = None, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        q = "SELECT id,company,title,salary_from,salary_to,skills,level,category FROM jobs"
        params: List[Any] = []
        clauses: List[str] = []
        if keyword:
            clauses.append("(title LIKE ? OR skills LIKE ? OR company LIKE ?)")
            kw = f"%{keyword}%"
            params += [kw, kw, kw]
        if category:
            clauses.append("category = ?")
            params.append(category)
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(q, params)
        rows = cur.fetchall()
        conn.close()
        names = ["id", "company", "title", "salary_from", "salary_to", "skills", "level", "category"]
        return [dict(zip(names, r)) for r in rows]

    def add_or_update_user(self, user_id: int, name: Optional[str] = None, interests: Optional[str] = None, level: Optional[str] = None, meta: Optional[str] = None) -> None:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cur.fetchone():
            if name is not None:
                cur.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))
            if interests is not None:
                cur.execute("UPDATE users SET interests = ? WHERE user_id = ?", (interests, user_id))
            if level is not None:
                cur.execute("UPDATE users SET level = ? WHERE user_id = ?", (level, user_id))
            if meta is not None:
                cur.execute("UPDATE users SET meta = ? WHERE user_id = ?", (meta, user_id))
        else:
            cur.execute(
                "INSERT INTO users (user_id,name,interests,level,meta) VALUES (?,?,?,?,?)",
                (user_id, name or "", interests or "", level or "", meta or ""),
            )
        conn.commit()
        conn.close()

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id,name,interests,level,meta FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        names = ["user_id", "name", "interests", "level", "meta"]
        return dict(zip(names, row))

    def recommend_jobs(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Простейшая рекомендация: совпадение по интересам и навыкам.

        Алгоритм:
        - берем interests пользователя (csv / comma-separated)
        - ищем вакансии, где category совпадает с интересом или skills содержит интерес
        - сортируем по числу совпадений (примитивно)
        """
        user = self.get_user(user_id)
        if not user:
            return []
        interests = [i.strip().lower() for i in user.get("interests", "").split(",") if i.strip()]
        if not interests:
            
            return self.find_jobs(limit=limit)

        
        candidates: Dict[int, Dict[str, Any]] = {}
        for it in interests:
            rows = self.find_jobs(keyword=it, limit=limit * 5)
            for r in rows:
                jid = r["id"]
                if jid not in candidates:
                    candidates[jid] = {"job": r, "score": 0}
                
                score = 0
                if it in (r.get("category") or "").lower():
                    score += 2
                if it in (r.get("skills") or "").lower():
                    score += 1
                candidates[jid]["score"] += score

        sorted_jobs = sorted(candidates.values(), key=lambda x: x["score"], reverse=True)
        result = [c["job"] for c in sorted_jobs[:limit]]
        if not result:
            return self.find_jobs(limit=limit)
        return result

    def format_job(self, job: Dict[str, Any]) -> str:
        sf = job.get("salary_from") or 0
        st = job.get("salary_to") or 0
        salary = f"{sf}-{st}" if sf or st else "з/п не указана"
        return (
            f"<b>{job.get('title')}</b> ({job.get('company')})\n"
            f"💰 {salary}\n"
            f"🛠 {job.get('skills')}\n"
            f"📂 {job.get('category')}, {job.get('level')}"
        )

    def describe_db_format(self) -> str:
        """Возвращает строковое описание структуры данных, которые можно добавить в БД."""
        return (
            "Формат вакансии (разделять '|' при быстрой вставке):\n"
            "company|title|salary_from|salary_to|skills(comma-separated)|level|category\n\n"
            "Пример:\n"
            "ACME|Junior Python Developer|40000|80000|python,sql|junior|IT\n\n"
            "Профиль пользователя: user_id, name, interests(comma-separated), level"
        )
