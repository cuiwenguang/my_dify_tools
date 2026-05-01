from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from .wecom_api import WeComAPI, WeComAccessToken


class WecomGroupProvider(ToolProvider):
    
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            corp_id = credentials.get("corp_id", "")
            secret = credentials.get("secret", "")
            agent_id = credentials.get("agent_id", "")
            
            if not corp_id:
                raise ToolProviderCredentialValidationError("企业ID (Corp ID) 不能为空")
            if not secret:
                raise ToolProviderCredentialValidationError("应用Secret不能为空")
            if not agent_id:
                raise ToolProviderCredentialValidationError("应用Agent ID不能为空")
            
            wecom_api = WeComAPI(corp_id, secret, agent_id)
            success, message = wecom_api.validate_credentials()
            
            if not success:
                raise ToolProviderCredentialValidationError(f"凭证验证失败: {message}")
        except ToolProviderCredentialValidationError:
            raise
        except Exception as e:
            raise ToolProviderCredentialValidationError(f"凭证验证发生错误: {str(e)}")
    
    def get_wecom_api(self) -> WeComAPI:
        credentials = self.credentials
        corp_id = credentials.get("corp_id", "")
        secret = credentials.get("secret", "")
        agent_id = credentials.get("agent_id", "")
        
        return WeComAPI(corp_id, secret, agent_id)
    
    def clear_access_token_cache(self):
        credentials = self.credentials
        corp_id = credentials.get("corp_id", "")
        agent_id = credentials.get("agent_id", "")
        
        WeComAccessToken.clear_cache(corp_id, agent_id)
