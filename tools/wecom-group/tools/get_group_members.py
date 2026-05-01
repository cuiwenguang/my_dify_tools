from collections.abc import Generator
from typing import Any
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class GetGroupMembersTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        chat_id = tool_parameters.get("chat_id", "")
        
        if not chat_id:
            yield self.create_json_message({
                "success": False,
                "error": "chat_id 不能为空"
            })
            return
        
        try:
            wecom_api = self.provider.get_wecom_api()
            success, message, members = wecom_api.get_group_members(chat_id)
            
            if not success:
                yield self.create_json_message({
                    "success": False,
                    "error": message
                })
                return
            
            for member in members:
                if member.get("join_time"):
                    join_time = member.get("join_time")
                    member["join_time_str"] = datetime.fromtimestamp(join_time).strftime("%Y-%m-%d %H:%M:%S")
            
            owner_count = sum(1 for m in members if m.get("is_owner"))
            admin_count = sum(1 for m in members if m.get("is_admin"))
            
            summary = {
                "total_count": len(members),
                "owner_count": owner_count,
                "admin_count": admin_count,
                "member_count": len(members) - owner_count
            }
            
            yield self.create_json_message({
                "success": True,
                "message": message,
                "summary": summary,
                "members": members
            })
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"获取群成员列表失败: {str(e)}"
            })
