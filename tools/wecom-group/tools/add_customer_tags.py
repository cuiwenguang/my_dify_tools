import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class AddCustomerTagsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        external_userid = tool_parameters.get("external_userid", "")
        userid = tool_parameters.get("userid", "")
        tag_names_str = tool_parameters.get("tag_names", "")
        
        if not external_userid:
            yield self.create_json_message({
                "success": False,
                "error": "external_userid 不能为空"
            })
            return
        
        if not userid:
            yield self.create_json_message({
                "success": False,
                "error": "userid 不能为空（需要指定添加标签的跟进员工）"
            })
            return
        
        if not tag_names_str:
            yield self.create_json_message({
                "success": False,
                "error": "tag_names 不能为空"
            })
            return
        
        try:
            if isinstance(tag_names_str, str):
                if tag_names_str.startswith("[") and tag_names_str.endswith("]"):
                    tag_names = json.loads(tag_names_str)
                else:
                    tag_names = [t.strip() for t in tag_names_str.split(",") if t.strip()]
            else:
                tag_names = tag_names_str
            
            if not isinstance(tag_names, list):
                tag_names = [tag_names]
            
            tag_names = [str(t).strip() for t in tag_names if str(t).strip()]
            
            if not tag_names:
                yield self.create_json_message({
                    "success": False,
                    "error": "标签名称不能为空"
                })
                return
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"解析标签名称失败: {str(e)}"
            })
            return
        
        try:
            wecom_api = self.provider.get_wecom_api()
            success, message = wecom_api.add_customer_tags(external_userid, userid, tag_names)
            
            if not success:
                yield self.create_json_message({
                    "success": False,
                    "error": message
                })
                return
            
            yield self.create_json_message({
                "success": True,
                "message": message,
                "external_userid": external_userid,
                "userid": userid,
                "added_tags": tag_names,
                "tag_count": len(tag_names)
            })
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"添加客户标签失败: {str(e)}"
            })
