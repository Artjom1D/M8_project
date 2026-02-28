import sqlite3
from typing import List, Dict, Optional, Any


class Bot:
    """Лёгкая логика работы с базой вакансий и профилями пользователей."""

    def __init__(self, db_path: str = "jobs.db"):
        self.db = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db, check_same_thread=False)

    def _row_to_dict(self, row, columns: List[str]) -> Dict[str, Any]:
        """Преобразует кортеж БД в словарь."""
        return dict(zip(columns, row)) if row else None

    def init_db(self) -> None:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
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
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                interests TEXT,
                level TEXT,
                meta TEXT
            )
        """)

        conn.commit()
        conn.close()

    def add_job(self, company: str, title: str, salary_from: Optional[int], salary_to: Optional[int], 
                skills: str, level: str, category: str) -> int:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jobs (company, title, salary_from, salary_to, skills, level, category) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company, title, salary_from or 0, salary_to or 0, skills, level, category))
        job_id = cur.lastrowid
        conn.commit()
        conn.close()
        return job_id

    def find_jobs(self, keyword: Optional[str] = None, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        clauses = []
        params = []
        
        if keyword:
            clauses.append("(title LIKE ? OR skills LIKE ? OR company LIKE ?)")
            pattern = f"%{keyword}%"
            params.extend([pattern, pattern, pattern])
        
        if category:
            clauses.append("category = ?")
            params.append(category)
        
        where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
        q = f"""SELECT id, company, title, salary_from, salary_to, skills, level, category 
                FROM jobs{where_clause} ORDER BY id DESC LIMIT ?"""
        params.append(limit)

        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(q, params)
        rows = cur.fetchall()
        conn.close()
        
        columns = ["id", "company", "title", "salary_from", "salary_to", "skills", "level", "category"]
        return [self._row_to_dict(r, columns) for r in rows]

    def add_or_update_user(self, user_id: int, name: Optional[str] = None, interests: Optional[str] = None, 
                          level: Optional[str] = None, meta: Optional[str] = None) -> None:
        conn = self._get_conn()
        cur = conn.cursor()
        
        # Проверяем существование пользователя
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        exists = cur.fetchone()
        
        if exists:
            # Строим UPDATE динамически
            updates = []
            params = []
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if interests is not None:
                updates.append("interests = ?")
                params.append(interests)
            if level is not None:
                updates.append("level = ?")
                params.append(level)
            if meta is not None:
                updates.append("meta = ?")
                params.append(meta)
            
            if updates:
                params.append(user_id)
                cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", params)
        else:
            cur.execute("""
                INSERT INTO users (user_id, name, interests, level, meta) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name or "", interests or "", level or "", meta or ""))
        
        conn.commit()
        conn.close()

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, interests, level, meta FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        
        columns = ["user_id", "name", "interests", "level", "meta"]
        return self._row_to_dict(row, columns)

    def recommend_jobs(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Рекомендация вакансий по интересам и уровню пользователя."""
        user = self.get_user(user_id)
        if not user:
            return []
        
        interests = [i.strip().lower() for i in user.get("interests", "").split(",") if i.strip()]
        if not interests:
            return self.find_jobs(limit=limit)

        candidates = {}
        for interest in interests:
            jobs = self.find_jobs(keyword=interest, limit=limit * 5)
            for job in jobs:
                job_id = job["id"]
                if job_id not in candidates:
                    candidates[job_id] = {"job": job, "score": 0}
                
                score = 0
                if interest in (job.get("category") or "").lower():
                    score += 2
                if interest in (job.get("skills") or "").lower():
                    score += 1
                candidates[job_id]["score"] += score

        if not candidates:
            return self.find_jobs(limit=limit)
        
        sorted_jobs = sorted(candidates.values(), key=lambda x: x["score"], reverse=True)
        return [c["job"] for c in sorted_jobs[:limit]]

    def format_job(self, job: Dict[str, Any]) -> str:
        """Форматирует вакансию для вывода в чат."""
        if not job:
            return "Вакансия не найдена"
        
        salary_from = job.get("salary_from") or 0
        salary_to = job.get("salary_to") or 0
        salary = f"{salary_from}-{salary_to}" if salary_from or salary_to else "з/п не указана"
        
        return (
            f"<b>{job.get('title')}</b> ({job.get('company')})\n"
            f"💰 {salary}\n"
            f"🛠 {job.get('skills')}\n"
            f"📂 {job.get('category')}, {job.get('level')}"
        )

