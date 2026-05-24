.loom-server-storage
提供 python package，

使用方法
```
import loom

data = loom.get('<workspace>/<path>`)
```

第一次运行时候
- 自动把数据下载下来，放到 .loom/raw（或其他名字） 里
- 如果本地 raw_data 由， 就自动建立一个 .loom 和 .raw_data 的文件 link，不需要从 远端下载
- 如果 link 失效再从远端下载

第二次运行的时候，就直接读取缓存

每次运行 loom pull 根据增量检查下 .loom 的是不是最新。


同时 cli 也支持用一个命令 ，下载数据

.loom/raw 按原文件路径排列， 只下载最新的版本，不下载历史数据