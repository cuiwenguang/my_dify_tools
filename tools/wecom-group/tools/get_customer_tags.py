from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class GetCustomerTagsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        external_userid = tool_parameters.get("external_userid", "")
        
        if not external_userid:
            yield self.create_json_message({
                "success": False,
                "error": "external_userid 不能为空"
            })
            return
        
        try:
            wecom_api = self.provider.get_wecom_api()
            success, message, tags = wecom_api.get_customer_tags(external_userid)
            
            if not success:
                yield self.create_json_message({
                    "success": False,
                    "error": message
                })
                return
            
            tag_groups = {}
            for tag in tags:
                group_name = tag.get("group_name", "未分组")
                if group_name not in tag_groups:
                    tag_groups[group_name] = []
                tag_groups[group_name].append({
                    "tag_name": tag.get("tag_name", ""),
                    "tag_id": tag.get("tag_id", ""),
                    "type": tag.get("type", 0),
                    "follow_userid": tag.get("follow_userid", "")
                })
            
            all_tag_names = [tag.get("tag_name", "") for tag in tags]
            
            yield self.create_json_message({
                "success": True,
                "message": message,
                "total_count": len(tags),
                "all_tag_names": all_tag_names,
                "tag_groups": tag_groups,
                "full_tags": tags
            })
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"获取客户标签失败: {str(e)}"
            })
