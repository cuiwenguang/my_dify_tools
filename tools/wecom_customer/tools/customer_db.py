import json
import sqlite3
import os
from datetime import datetime
from typing import Optional


class CustomerDB:
    DB_PATH = os.path.join(os.path.dirname(__file__), "..", "customer_data.db")

    @classmethod
    def get_connection(cls):
        conn = sqlite3.connect(cls.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                user_data TEXT DEFAULT '{}',
                wecom_info TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_sync_time TEXT
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_id ON customers(user_id)
        ''')
        conn.commit()
        conn.close()

    @classmethod
    def get_customer(cls, user_id: str) -> Optional[dict]:
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM customers WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "user_id": row["user_id"],
                "user_data": json.loads(row["user_data"]) if row["user_data"] else {},
                "wecom_info": json.loads(row["wecom_info"]) if row["wecom_info"] else {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "last_sync_time": row["last_sync_time"]
            }
        return None

    @classmethod
    def save_customer(cls, user_id: str, user_data: dict = None, 
                       wecom_info: dict = None, sync_now: bool = False) -> dict:
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        existing = cls.get_customer(user_id)
        
        if existing:
            final_user_data = existing.get("user_data", {})
            if user_data:
                final_user_data.update(user_data)
            
            final_wecom_info = existing.get("wecom_info", {})
            if wecom_info:
                final_wecom_info.update(wecom_info)
            
            cursor.execute('''
                UPDATE customers 
                SET user_data = ?, wecom_info = ?, updated_at = ?
                WHERE user_id = ?
            ''', (json.dumps(final_user_data, ensure_ascii=False),
                  json.dumps(final_wecom_info, ensure_ascii=False),
                  now, user_id))
        else:
            final_user_data = user_data or {}
            final_wecom_info = wecom_info or {}
            
            cursor.execute('''
                INSERT INTO customers (user_id, user_data, wecom_info, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id,
                  json.dumps(final_user_data, ensure_ascii=False),
                  json.dumps(final_wecom_info, ensure_ascii=False),
                  now, now))
        
        conn.commit()
        
        if sync_now:
            cursor.execute('''
                UPDATE customers 
                SET last_sync_time = ?
                WHERE user_id = ?
            ''', (now, user_id))
            conn.commit()
        
        cursor.execute('SELECT * FROM customers WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        return {
            "user_id": row["user_id"],
            "user_data": json.loads(row["user_data"]) if row["user_data"] else {},
            "wecom_info": json.loads(row["wecom_info"]) if row["wecom_info"] else {},
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_sync_time": row["last_sync_time"]
        }

    @classmethod
    def update_wecom_info(cls, user_id: str, wecom_info: dict) -> dict:
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        existing = cls.get_customer(user_id)
        
        if existing:
            final_wecom_info = existing.get("wecom_info", {})
            if wecom_info:
                final_wecom_info.update(wecom_info)
            
            cursor.execute('''
                UPDATE customers 
                SET wecom_info = ?, updated_at = ?, last_sync_time = ?
                WHERE user_id = ?
            ''', (json.dumps(final_wecom_info, ensure_ascii=False),
                  now, now, user_id))
            conn.commit()
        
        cursor.execute('SELECT * FROM customers WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "user_id": row["user_id"],
                "user_data": json.loads(row["user_data"]) if row["user_data"] else {},
                "wecom_info": json.loads(row["wecom_info"]) if row["wecom_info"] else {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "last_sync_time": row["last_sync_time"]
            }
        return {}

    @classmethod
    def search_customer(cls, user_id: str = None, keyword: str = None) -> list:
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('SELECT * FROM customers WHERE user_id = ?', (user_id,))
        elif keyword:
            search_pattern = f'%{keyword}%'
            cursor.execute('''
                SELECT * FROM customers 
                WHERE user_id LIKE ? OR user_data LIKE ? OR wecom_info LIKE ?
            ''', (search_pattern, search_pattern, search_pattern))
        else:
            cursor.execute('SELECT * FROM customers ORDER BY updated_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "user_id": row["user_id"],
                "user_data": json.loads(row["user_data"]) if row["user_data"] else {},
                "wecom_info": json.loads(row["wecom_info"]) if row["wecom_info"] else {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "last_sync_time": row["last_sync_time"]
            })
        
        return results
