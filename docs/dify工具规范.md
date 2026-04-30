一、项目初始化（已准备好工具，直接执行）
# 1. tools目录下新建插件目录并进入（自定义目录名，此处用text-reverse-plugin）
mkdir text-reverse-plugin && cd text-reverse-plugin

# 2. 初始化插件（按终端提示填写，关键选项如下）
dify plugin init
关键初始化选项（其余默认回车）：
- Plugin name：text-reverse（仅小写、数字、-/_，无其他字符）
- Plugin type：tool（固定选tool）
- Language：python（固定选python）
初始化后核心目录（仅关注需修改的文件）：
text-reverse/
├── .env                # 调试配置（仅需填Dify调试Key和地址）
├── main.py             # 入口文件（默认不动）
├── provider/           # 认证管理（默认不动，无需改）
└── tools/              # 核心工具目录（需修改text_reverse_tool.py）
二、核心接口说明（重点）
插件核心是 Tool 类，所有字符处理逻辑都在 _invoke 方法中（唯一执行入口），接口规范如下：
- 核心方法：_invoke(self, parameters: dict) -> ToolInvokeResponse
- parameters：入参字典，接收Dify前端传递的参数（如本文的「待反转文本」）
- 返回值：必须是 ToolInvokeResponse，包含输出结果或错误信息
- 无需额外定义接口，仅需实现 _invoke 方法即可
三、代码实现（文本反转功能，直接复制）
3.1 修改 tools/text_reverse_tool.py（核心工具文件）
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeResponse

# 文本反转工具类，继承自Tool
class TextReverseTool(Tool):
    # 唯一执行入口，所有逻辑写在这里
    def _invoke(self, parameters: dict) -> ToolInvokeResponse:
        # 1. 获取入参（key为text，对应Dify工作流中配置的参数名）
        text = parameters.get("text", "")
        
        # 2. 异常处理（入参为空时返回错误）
        if not text:
            return ToolInvokeResponse(error="请输入待反转的文本")
        
        # 3. 核心逻辑：文本反转
        reversed_text = text[::-1]
        
        # 4. 返回结果（按指定格式返回，可自定义输出字段）
        return ToolInvokeResponse(
            output={
                "original_text": text,  # 原始文本
                "reversed_text": reversed_text  # 反转后文本
            }
        )
3.2 其他文件（无需修改，直接使用默认）
- main.py：入口文件，默认已注册Provider，无需改动
provider/text_reverse.py：认证管理核心文件（Provider类），负责插件的凭证验证、OAuth授权等，分3种场景说明，结合示例适配：
场景1：无需认证（本文示例，默认即可）
无需用户填写API Key、账号密码等，Provider类空实现即可，默认生成的代码无需修改，核心代码如下：
from typing import Any, Mapping
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

class TextReverseProvider(ToolProvider):
    # 凭证验证方法，无需认证则空实现
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        pass  # 空实现，不做任何验证
场景2：需要认证（如API Key验证）
若插件需用户填写API Key（如调用第三方接口），修改_validate_credentials方法，实现凭证校验，示例：
from typing import Any, Mapping
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

class TextReverseProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        # 从入参中获取用户填写的API Key
        api_key = credentials.get("api_key")
        # 验证逻辑：API Key不能为空、长度符合要求（自定义规则）
        if not api_key or len(api_key) < 10:
            # 验证失败抛出异常，Dify会提示用户凭证错误
            raise ToolProviderCredentialValidationError("API Key不合法，请检查后重新填写")
场景3：飞书认证（OAuth示例，简要）
飞书认证需开启OAuth授权，核心是实现3个OAuth相关方法（默认注释，解开修改），步骤如下：
1. 在飞书开放平台创建应用，获取Client ID、Client Secret，配置回调地址（与Dify调试地址一致）；
2. 解开Provider类中注释的3个OAuth方法，填写飞书授权逻辑，核心代码示例（简化）：
def _oauth_get_authorization_url(self, redirect_uri: str, system_credentials: Mapping[str, Any]) -> str:
    # 生成飞书授权链接（替换为飞书开放平台授权地址+Client ID+回调地址）
    client_id = system_credentials.get("client_id")
    return f"https://open.feishu.cn/open-apis/oauth2/v3/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"

def _oauth_get_credentials(self, redirect_uri: str, system_credentials: Mapping[str, Any], request: Request) -> Mapping[str, Any]:
    # 用授权code换取飞书access_token
    code = request.args.get("code")
    client_id = system_credentials.get("client_id")
    client_secret = system_credentials.get("client_secret")
    # 调用飞书接口换取token（此处省略请求逻辑）
    return {"access_token": "获取到的飞书token", "expires_at": "过期时间"}

def _oauth_refresh_credentials(self, redirect_uri: str, system_credentials: Mapping[str, Any], credentials: Mapping[str, Any]) -> OAuthCredentials:
    # 刷新飞书token（按需实现，简化示例）
    return OAuthCredentials(credentials=credentials, expires_at=-1)
补充：飞书认证需在Dify插件配置中，填写飞书应用的Client ID、Client Secret，其余逻辑与普通OAuth一致。
- provider/text_reverse.yaml：配置文件，默认生成，无需改动
四、调试与使用（关键步骤）
# 1. 配置.env文件（填写Dify调试信息）
nano .env
# 写入以下内容（替换为你的Dify信息）
DIFY_DEBUG_KEY=你的Dify调试Key（Settings→Plugins→Debugging获取）
DIFY_API_URL=http://你的DifyIP:8000

# 2. 安装依赖（若未安装）
pip install dify-plugin

# 3. 启动调试（挂载到Dify）
python main.py
Dify中使用：工作流→添加工具节点→选择「text-reverse」→输入text参数→运行即可得到反转结果。
五、核心总结
- 1. 项目初始化：按提示选tool、python，插件名规范即可
- 2. 核心代码：仅需修改tools下的Tool文件，实现_invoke方法
- 3. 接口：无需额外定义，_invoke是唯一执行入口，入参为dict，返回值为ToolInvokeResponse