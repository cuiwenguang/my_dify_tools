import json
import sqlite3
import os
from collections.abc import Generator
from typing import Any
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


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
                user_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_id ON customers(user_id)
        ''')
        conn.commit()
        conn.close()

    @classmethod
    def save_customer(cls, user_id: str, user_data: dict) -> dict:
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        user_data_json = json.dumps(user_data, ensure_ascii=False)
        
        try:
            cursor.execute('''
                INSERT INTO customers (user_id, user_data, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, user_data_json, now, now))
        except sqlite3.IntegrityError:
            cursor.execute('''
                UPDATE customers 
                SET user_data = ?, updated_at = ?
                WHERE user_id = ?
            ''', (user_data_json, now, user_id))
        
        conn.commit()
        
        cursor.execute('SELECT * FROM customers WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        return {
            "user_id": row["user_id"],
            "user_data": json.loads(row["user_data"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

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
                WHERE user_id LIKE ? OR user_data LIKE ?
            ''', (search_pattern, search_pattern))
        else:
            cursor.execute('SELECT * FROM customers ORDER BY updated_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "user_id": row["user_id"],
                "user_data": json.loads(row["user_data"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        return results


class SaveCustomerTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        user_id = tool_parameters.get("user_id", "")
        user_data_str = tool_parameters.get("user_data", "{}")
        
        if not user_id:
            yield self.create_json_message({
                "success": False,
                "error": "user_id 不能为空"
            })
            return
        
        try:
            if isinstance(user_data_str, str):
                user_data = json.loads(user_data_str)
            else:
                user_data = user_data_str
        except json.JSONDecodeError as e:
            yield self.create_json_message({
                "success": False,
                "error": f"user_data JSON 解析失败: {str(e)}"
            })
            return
        
        try:
            result = CustomerDB.save_customer(user_id, user_data)
            yield self.create_json_message({
                "success": True,
                "data": result
            })
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"保存客户信息失败: {str(e)}"
            })


class SearchCustomerTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        user_id = tool_parameters.get("user_id", "")
        keyword = tool_parameters.get("keyword", "")
        
        try:
            if user_id:
                results = CustomerDB.search_customer(user_id=user_id)
            elif keyword:
                results = CustomerDB.search_customer(keyword=keyword)
            else:
                results = CustomerDB.search_customer()
            
            yield self.create_json_message({
                "success": True,
                "count": len(results),
                "data": results
            })
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"查询客户信息失败: {str(e)}"
            })
