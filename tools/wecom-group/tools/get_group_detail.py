from collections.abc import Generator
from typing import Any
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class GetGroupDetailTool(Tool):
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
            success, message, group_detail = wecom_api.get_group_detail(chat_id)
            
            if not success:
                yield self.create_json_message({
                    "success": False,
                    "error": message
                })
                return
            
            if group_detail.get("create_time"):
                create_time = group_detail.get("create_time")
                group_detail["create_time_str"] = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S")
            
            if "member_list" in group_detail:
                for member in group_detail["member_list"]:
                    if member.get("join_time"):
                        join_time = member.get("join_time")
                        member["join_time_str"] = datetime.fromtimestamp(join_time).strftime("%Y-%m-%d %H:%M:%S")
            
            group_summary = {
                "chat_id": group_detail.get("chat_id", ""),
                "group_name": group_detail.get("group_name", ""),
                "owner": group_detail.get("owner", ""),
                "create_time": group_detail.get("create_time", 0),
                "create_time_str": group_detail.get("create_time_str", ""),
                "member_count": group_detail.get("member_count", 0),
                "admin_list": group_detail.get("admin_list", []),
                "notice": group_detail.get("notice", "")
            }
            
            yield self.create_json_message({
                "success": True,
                "message": message,
                "group_summary": group_summary,
                "full_detail": group_detail
            })
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"获取群详情失败: {str(e)}"
            })
