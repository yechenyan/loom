重新写 readme.md , 
另外需要注明：
1. 需要你调整部分代码
2. 增加让别人使用 loom package/cli 的skill
3. 下面的一些命令未必正确，需要你修复成对的
4. 生成的 readme.md 用英语，简明易读


再前面加上思想：
1. 数据资料往往非常大，让 AI 直接查数据即浩时间也费 token
2. 把数据现转成数据卡片，再让 AI 从数据卡片搜索数据
3. 再按需下载你要的数据


在最前面加上如何使用：

大纲如下

1. 推荐使用 uv 安装
(uv) 的安装方法

2. 安装
uv add loom-data


3. 初始化
uv run loom-data install <工作区名称>

（这里需要调整下代码： 目前安装在了 test-project/loom 下， 实际要安装在当前项目的根目录的 loom 中）
(安装的时候需要安装下 skill， 你也需要准备下 skill， 可以问下是 codex，claude，curse，copilot 然后安装到各自skill 下面)

4. 添加数据
请用户把资料手动放到 loom_raw 中

5. 生成数据卡片
在 chat 聊天中输入 loom scan <工作区名称>
或者由 AI agent 自己出发
如果不加工作区名称则扫描整个 loom_raw

6. 用户确认 （可略过）
确认你总结的数据没有问题
loom confirm <工作区名称>
如果不加工作区名称则confirm整个 loom_raw


7. 查找数据
让 AI agent 建模，或者问 AI 会自查找数据


8. 使用数据
```python
import loom
loom.get(<path>)
```



更多功能：

1. push 数据到服务端
chat 聊天 or bash：
loom push <工作区名称>
如果不加工作区名称则 push 所有


1. pull 更新服务端端数据
chat 聊天 or bash：
loom pull <工作区名称>
如果不加工作区名称则 pull 所有

1. 在线查数据
访问：https://loom-web.onrender.com


4. 设置 CLI api
chat 聊天 or bash：
loom set-api https://loom-api-free.onrender.com