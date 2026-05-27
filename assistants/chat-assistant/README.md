# 1号AI · 闲聊检索助理

## 启动方式
cd ~/ai-assistant-system/assistants/chat-assistant
source venv-chat/bin/activate
python3.12 src/main.py

## 可用指令
| 指令 | 功能 | 示例 |
|:---|:---|:---|
| 直接输入文字 | 与AI闲聊 | 你好 |
| 搜索 + 关键词 | 联网搜索并归档 | 搜索 Python |
| 本地搜索 + 词 | 检索本地知识库 | 本地搜索 Python |
| clear | 清空对话历史 | clear |
| help | 显示帮助 | help |
| exit | 退出 | exit |

## 文件说明
- src/main.py  主入口
- src/chat.py  对话历史管理
- src/search.py  搜索 + 知识库
- logs/  对话历史存储
- knowledge_base/  搜索归档存储
- tests/  测试脚本目录
