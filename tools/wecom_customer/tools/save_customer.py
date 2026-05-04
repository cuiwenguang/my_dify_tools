import json
from collections.abc import Generator
from typing import Any
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .customer_db import CustomerDB


class SaveCustomerTool(Tool):
    def _fetch_wecom_info(self, wecom_api, user_id: str) -> dict:
        wecom_info = {
            "customer_detail": {},
            "tags": [],
            "groups": [],
            "fetch_errors": []
        }
        
        try:
            success, message, customer_detail = wecom_api.get_customer_detail(user_id)
            if success:
                wecom_info["customer_detail"] = customer_detail
            else:
                wecom_info["fetch_errors"].append(f"获取客户详情失败: {message}")
        except Exception as e:
            wecom_info["fetch_errors"].append(f"获取客户详情异常: {str(e)}")
        
        try:
            success, message, tags = wecom_api.get_customer_tags(user_id)
            if success:
                wecom_info["tags"] = tags
            else:
                wecom_info["fetch_errors"].append(f"获取客户标签失败: {message}")
        except Exception as e:
            wecom_info["fetch_errors"].append(f"获取客户标签异常: {str(e)}")
        
        wecom_info["last_fetch_time"] = datetime.now().isoformat()
        
        return wecom_info
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        user_id = tool_parameters.get("user_id", "")
        user_data_str = tool_parameters.get("user_data", "{}")
        sync_wecom = tool_parameters.get("sync_wecom", True)
        
        if not user_id:
            yield self.create_json_message({
                "success": False,
                "error": "user_id 不能为空"
            })
            return
        
        try:
            if isinstance(user_data_str, str):
                if user_data_str.strip():
                    user_data = json.loads(user_data_str)
                else:
                    user_data = {}
            else:
                user_data = user_data_str
        except json.JSONDecodeError as e:
            yield self.create_json_message({
                "success": False,
                "error": f"user_data JSON 解析失败: {str(e)}"
            })
            return
        
        wecom_info = None
        sync_status = {
            "success": True,
            "message": "",
            "errors": []
        }
        
        if sync_wecom:
            try:
                wecom_api = self.provider.get_wecom_api()
                wecom_info = self._fetch_wecom_info(wecom_api, user_id)
                
                if wecom_info.get("fetch_errors"):
                    sync_status["errors"] = wecom_info["fetch_errors"]
                    sync_status["message"] = f"部分企微信息获取失败，共{len(wecom_info['fetch_errors'])}个错误"
                    sync_status["success"] = False
                else:
                    sync_status["message"] = "企微信息同步成功"
            except Exception as e:
                sync_status["success"] = False
                sync_status["message"] = f"同步企微信息失败: {str(e)}"
                sync_status["errors"] = [str(e)]
        
        try:
            existing = CustomerDB.get_customer(user_id)
            is_new = existing is None
            
            result = CustomerDB.save_customer(
                user_id=user_id,
                user_data=user_data,
                wecom_info=wecom_info,
                sync_now=sync_wecom and wecom_info is not None
            )
            
            response = {
                "success": True,
                "is_new": is_new,
                "sync_status": sync_status,
                "data": result
            }
            
            yield self.create_json_message(response)
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"保存客户信息失败: {str(e)}"
            })
