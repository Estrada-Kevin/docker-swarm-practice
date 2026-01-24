import os
import time
from typing import List, Dict, Any

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="TaskBoard API", version="1.0.0")


def read_secret(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def get_db_dsn() -> str:
    host = os.getenv("DB_HOST", "postgres")
    port = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME", "taskboard")
    user = os.getenv("DB_USER", "taskboard")

    pw_file = os.getenv("DB_PASSWORD_FILE", "/run/secrets/postgres_password")
    password = read_secret(pw_file)

    return (
        f"host={host} "
        f"port={port} "
        f"dbname={dbname} "
        f"user={user} "
        f"password={password}"
    )


def wait_for_db(max_seconds: int = 60) -> None:
    deadline = time.time() + max_seconds
    last_err = None
    while time.time() < deadline:
        try:
            with psycopg.connect(get_db_dsn(), connect_timeout=3):
                return
        except Exception as e:
            last_err = e
            time.sleep(2)
    raise RuntimeError(f"DB not ready after {max_seconds}s. Last error: {last_err}")


def init_db_and_seed() -> None:
    with psycopg.connect(get_db_dsn(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            cur.execute("SELECT COUNT(*) FROM tasks;")
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute("""
                    INSERT INTO tasks (title, done) VALUES
                    ('Learn Docker Swarm basics', false),
                    ('Add secrets + seeded DB', false),
                    ('Test scaling and VIP load balancing', false),
                    ('Practice rolling updates', false),
                    ('Write a CV-ready README', false);
                """)


@app.on_event("startup")
def on_startup():
    wait_for_db()
    init_db_and_seed()


class TaskIn(BaseModel):
    title: str
    done: bool = False


class TaskOut(TaskIn):
    id: int
    created_at: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> List[Dict[str, Any]]:
    with psycopg.connect(get_db_dsn(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, done, created_at FROM tasks ORDER BY id;"
            )
            return cur.fetchall()


@app.post("/tasks", status_code=201)
def create_task(task: TaskIn) -> Dict[str, Any]:
    with psycopg.connect(
        get_db_dsn(),
        autocommit=True,
        row_factory=dict_row
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (title, done)
                VALUES (%s, %s)
                RETURNING id, title, done, created_at;
                """,
                (task.title, task.done),
            )
            return cur.fetchone()


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskIn) -> Dict[str, Any]:
    with psycopg.connect(
        get_db_dsn(),
        autocommit=True,
        row_factory=dict_row
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tasks
                SET title=%s, done=%s
                WHERE id=%s
                RETURNING id, title, done, created_at;
                """,
                (task.title, task.done, task_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Task not found")
            return row


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with psycopg.connect(get_db_dsn(), autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id=%s;", (task_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Task not found")
    return None
