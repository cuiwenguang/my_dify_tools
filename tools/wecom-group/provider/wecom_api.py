import json
import os
import time
from typing import Optional
import requests


class WeComAccessToken:
    CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "access_token_cache.json")
    
    @classmethod
    def _get_cache(cls) -> dict:
        if os.path.exists(cls.CACHE_FILE):
            try:
                with open(cls.CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    @classmethod
    def _save_cache(cls, cache: dict):
        try:
            with open(cls.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
    
    @classmethod
    def _get_cached_token(cls, corp_id: str, agent_id: str) -> Optional[dict]:
        cache = cls._get_cache()
        key = f"{corp_id}_{agent_id}"
        if key in cache:
            token_data = cache[key]
            if token_data.get("expires_at", 0) > time.time():
                return token_data
        return None
    
    @classmethod
    def _set_cached_token(cls, corp_id: str, agent_id: str, token_data: dict):
        cache = cls._get_cache()
        key = f"{corp_id}_{agent_id}"
        cache[key] = token_data
        cls._save_cache(cache)
    
    @classmethod
    def get_access_token(cls, corp_id: str, secret: str, agent_id: str) -> tuple[bool, str, dict]:
        cached_token = cls._get_cached_token(corp_id, agent_id)
        if cached_token:
            return True, "从缓存获取", cached_token
        
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": corp_id,
            "corpsecret": secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                access_token = result.get("access_token")
                expires_in = result.get("expires_in", 7200)
                expires_at = time.time() + expires_in - 300
                
                token_data = {
                    "access_token": access_token,
                    "expires_at": expires_at,
                    "corp_id": corp_id,
                    "agent_id": agent_id
                }
                
                cls._set_cached_token(corp_id, agent_id, token_data)
                return True, "获取成功", token_data
            else:
                return False, f"企业微信API错误: {result.get('errmsg', '未知错误')}", {}
        except requests.exceptions.RequestException as e:
            return False, f"网络请求错误: {str(e)}", {}
        except Exception as e:
            return False, f"获取AccessToken失败: {str(e)}", {}
    
    @classmethod
    def clear_cache(cls, corp_id: str = None, agent_id: str = None):
        if corp_id and agent_id:
            cache = cls._get_cache()
            key = f"{corp_id}_{agent_id}"
            if key in cache:
                del cache[key]
                cls._save_cache(cache)
        else:
            if os.path.exists(cls.CACHE_FILE):
                os.remove(cls.CACHE_FILE)


class WeComAPI:
    def __init__(self, corp_id: str, secret: str, agent_id: str):
        self.corp_id = corp_id
        self.secret = secret
        self.agent_id = agent_id
        self._access_token: Optional[str] = None
    
    def _get_access_token(self) -> tuple[bool, str]:
        success, message, token_data = WeComAccessToken.get_access_token(
            self.corp_id, self.secret, self.agent_id
        )
        if success:
            self._access_token = token_data.get("access_token")
            return True, message
        return False, message
    
    def validate_credentials(self) -> tuple[bool, str]:
        success, message = self._get_access_token()
        return success, message
    
    def _request(self, method: str, url: str, **kwargs) -> tuple[bool, str, dict]:
        if not self._access_token:
            success, message = self._get_access_token()
            if not success:
                return False, message, {}
        
        base_url = "https://qyapi.weixin.qq.com/cgi-bin"
        full_url = base_url + url if not url.startswith("http") else url
        
        params = kwargs.get("params", {})
        params["access_token"] = self._access_token
        kwargs["params"] = params
        
        try:
            if method.upper() == "GET":
                response = requests.get(full_url, timeout=10, **kwargs)
            elif method.upper() == "POST":
                response = requests.post(full_url, timeout=10, **kwargs)
            else:
                return False, f"不支持的请求方法: {method}", {}
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("errcode") == 0:
                return True, "请求成功", result
            elif result.get("errcode") == 42001:
                WeComAccessToken.clear_cache(self.corp_id, self.agent_id)
                self._access_token = None
                success, message = self._get_access_token()
                if success:
                    return self._request(method, url, **kwargs)
                return False, message, {}
            else:
                return False, f"企业微信API错误: {result.get('errmsg', '未知错误')}", {}
        except requests.exceptions.RequestException as e:
            return False, f"网络请求错误: {str(e)}", {}
        except Exception as e:
            return False, f"API请求失败: {str(e)}", {}
    
    def get_group_detail(self, chat_id: str) -> tuple[bool, str, dict]:
        url = "/externalcontact/groupchat/get"
        payload = {
            "chat_id": chat_id,
            "need_name": 1
        }
        
        success, message, result = self._request("POST", url, json=payload)
        if not success:
            return False, message, {}
        
        group_chat = result.get("group_chat", {})
        
        group_detail = {
            "chat_id": group_chat.get("chat_id", ""),
            "group_name": group_chat.get("name", ""),
            "owner": group_chat.get("owner", ""),
            "create_time": group_chat.get("create_time", 0),
            "member_count": group_chat.get("member_count", 0),
            "admin_list": group_chat.get("admin_list", []),
            "member_list": [],
            "notice": group_chat.get("notice", "")
        }
        
        member_list = group_chat.get("member_list", [])
        for member in member_list:
            member_info = {
                "userid": member.get("userid", ""),
                "type": member.get("type", 0),
                "join_time": member.get("join_time", 0),
                "join_scene": member.get("join_scene", 0),
                "invitor": member.get("invitor", {}),
                "group_nickname": member.get("group_nickname", ""),
                "name": member.get("name", ""),
                "unionid": member.get("unionid", "")
            }
            group_detail["member_list"].append(member_info)
        
        return True, "获取群详情成功", group_detail
