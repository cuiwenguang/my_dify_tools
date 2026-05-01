from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .customer_db import CustomerDB


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
