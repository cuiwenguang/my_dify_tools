我需要开发一个dify插件，用来记录微信客户群的客户信息，在调用dify聊天接口时回传入用户ID，通过用户id记录为用户建立档案，用sqlite保存user_id字符串和user_data的json客户信息，提供 SearchCustomerTool 和 SaveCustomerTool，需要注意生成代码必须符合dify工具规范(见docs下的规范文档)。代码生成在tools/customer目录下

.2675527194774436:87149b708e7ed1bac8cd4f33fd1f803c_69f43c071c7edbff16db043e.69f43c091c7edbff16db0440.69f43c08f00d69232e65cecb:Trae CN.T(2026/5/1 13:37:13)

https://github.com/cuiwenguang/my_dify_tools/pull/new/pr1

.2675527194774436:3fb3de893fab10d47c24890aa2200e04_69f43c071c7edbff16db043e.69f4406f1c7edbff16db049e.69f4406ff00d69232e65cecc:Trae CN.T(2026/5/1 13:55:59)

-----------------------------------------------------------------------
现在开一个dify的企业微信客户群管理插件，项目我已经初始化好了wecom-group，本次迭代主要完成provider的企微CorpID、Secret，AgentID的配置，然后先在provider中实现封装企微AccessToken获取与本地缓存逻辑则，然后建立通过企业微信api访问实现第一个工具获取群详情（群名、群主、创建时间、群规模）

.2675527194774436:8ff4d5488c3d559acfffb08cbaacb80e_69f43c071c7edbff16db043e.69f45e8e1c7edbff16db04d8.69f45e8df00d69232e65cecd:Trae CN.T(2026/5/1 16:04:30)


 https://github.com/cuiwenguang/my_dify_tools/pull/new/pr3

 ----------------------------------------------------------------------------------------------------------
 上次完成的非常好，下来我们再添加两个工具。1 查询群成员列表、成员角色与基础信息. 通过调用群接口，把返回结果的用户信息提取出来，整理成干净列表，包括成员名字，加入时间，是否管理员，然后返回。2.客户标签操作，接收参数用户id, 群ID，标签名，调用企业微信的查标签和打标签接口完成给客户打标签和查标签的两个工具

 .2675527194774436:47cf84af74132e1d7703af16dfb76c4d_69f43c071c7edbff16db043e.69f464c21c7edbff16db0536.69f464c2f00d69232e65cece:Trae CN.T(2026/5/1 16:30:58)