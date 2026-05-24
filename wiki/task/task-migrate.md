先看下 wiki/history 的逻辑。 

当前 pull 和 push 时是直接覆盖。

调整成：
对于 explore:
push 前先自动 pull 下，
如同 git 一样进行 migrate，用 rebase
如果没冲突，合并完后自动 confirm ，然后自动push

如果有冲突，由 AI 自行处理冲突， 并提示用户由冲突
用户之后需要运行 loom confirm 确认对冲突的解决。 之后用户再 运行 loom push 同步。

对于 ./loom/raw
pull 完后（如果有冲突则等 confirm 后） 根据最新的结果更新 .loom 里的
如果线上本地一致则不用做任何处理

对于 test-project/loom/loom_raw 里的文件，如果有冲突不要替换，只在 loom.md 旁新建一个 xxx.md（名字你定）  记录这个已经和服务端的不一致了，并提醒用户。 

