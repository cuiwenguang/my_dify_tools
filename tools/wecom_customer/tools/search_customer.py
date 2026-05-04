from collections.abc import Generator
from typing import Any
from datetime import datetime

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .customer_db import CustomerDB


class SearchCustomerTool(Tool):
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
    
    def _build_customer_summary(self, customer: dict) -> dict:
        user_data = customer.get("user_data", {})
        wecom_info = customer.get("wecom_info", {})
        customer_detail = wecom_info.get("customer_detail", {})
        tags = wecom_info.get("tags", [])
        
        tag_names = [t.get("tag_name", "") for t in tags if t.get("tag_name")]
        
        summary = {
            "user_id": customer.get("user_id", ""),
            "name": user_data.get("name") or customer_detail.get("name") or "",
            "phone": user_data.get("phone") or "",
            "store": user_data.get("store") or user_data.get("店面") or "",
            "contact": user_data.get("contact") or user_data.get("联系方式") or "",
            "remarks": user_data.get("remarks") or user_data.get("备注") or "",
            "position": customer_detail.get("position", ""),
            "corp_name": customer_detail.get("corp_name", ""),
            "tags": tag_names,
            "tag_count": len(tag_names),
            "created_at": customer.get("created_at", ""),
            "updated_at": customer.get("updated_at", ""),
            "last_sync_time": customer.get("last_sync_time", "")
        }
        
        return summary
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        user_id = tool_parameters.get("user_id", "")
        keyword = tool_parameters.get("keyword", "")
        sync_wecom = tool_parameters.get("sync_wecom", False)
        include_full_detail = tool_parameters.get("include_full_detail", False)
        
        if not user_id and not keyword:
            yield self.create_json_message({
                "success": False,
                "error": "user_id 或 keyword 至少提供一个"
            })
            return
        
        try:
            results = []
            
            if user_id:
                customer = CustomerDB.get_customer(user_id)
                
                if customer is None:
                    try:
                        wecom_api = self.provider.get_wecom_api()
                        wecom_info = self._fetch_wecom_info(wecom_api, user_id)
                        
                        customer = CustomerDB.save_customer(
                            user_id=user_id,
                            user_data={},
                            wecom_info=wecom_info,
                            sync_now=True
                        )
                        
                        results.append({
                            "customer": customer,
                            "summary": self._build_customer_summary(customer),
                            "is_initialized": True,
                            "sync_status": {
                                "success": len(wecom_info.get("fetch_errors", [])) == 0,
                                "errors": wecom_info.get("fetch_errors", [])
                            }
                        })
                    except Exception as e:
                        yield self.create_json_message({
                            "success": False,
                            "error": f"初始化客户信息失败: {str(e)}"
                        })
                        return
                else:
                    if sync_wecom:
                        try:
                            wecom_api = self.provider.get_wecom_api()
                            wecom_info = self._fetch_wecom_info(wecom_api, user_id)
                            
                            customer = CustomerDB.update_wecom_info(user_id, wecom_info)
                            
                            results.append({
                                "customer": customer,
                                "summary": self._build_customer_summary(customer),
                                "is_initialized": False,
                                "is_updated": True,
                                "sync_status": {
                                    "success": len(wecom_info.get("fetch_errors", [])) == 0,
                                    "errors": wecom_info.get("fetch_errors", [])
                                }
                            })
                        except Exception as e:
                            results.append({
                                "customer": customer,
                                "summary": self._build_customer_summary(customer),
                                "is_initialized": False,
                                "is_updated": False,
                                "sync_status": {
                                    "success": False,
                                    "errors": [str(e)]
                                }
                            })
                    else:
                        results.append({
                            "customer": customer,
                            "summary": self._build_customer_summary(customer),
                            "is_initialized": False,
                            "is_updated": False,
                            "sync_status": {
                                "success": True,
                                "message": "使用缓存数据"
                            }
                        })
            else:
                customers = CustomerDB.search_customer(keyword=keyword)
                
                for customer in customers:
                    results.append({
                        "customer": customer,
                        "summary": self._build_customer_summary(customer),
                        "is_initialized": False,
                        "is_updated": False,
                        "sync_status": {
                            "success": True,
                            "message": "使用缓存数据"
                        }
                    })
            
            if not include_full_detail:
                for r in results:
                    r.pop("customer", None)
            
            response = {
                "success": True,
                "count": len(results),
                "results": results
            }
            
            yield self.create_json_message(response)
        except Exception as e:
            yield self.create_json_message({
                "success": False,
                "error": f"查询客户信息失败: {str(e)}"
            })
