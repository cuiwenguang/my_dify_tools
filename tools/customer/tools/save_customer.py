import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .customer_db import CustomerDB


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
