你可以看 wiki/history 了解前面做了哪些工作。

我现在想加一个新能力：
现在本地以及有了 test-project/loom/loom_explore 我想做一个变更记录的能力，
当刚运行完 loom scan 后，用户能看到有哪些文件变更, 然后运行 

```
loom confirm
```
确认变更，类似在 git 中的提交





服务器同步的功能， 能把这个按照 workspace（也就是loom_explore 下的第一级别文件夹（如 energy） 和服务器进行同步。相当于用户在codex chat 里输入：

```
loom push
```

会把里面的内容自动同步给服务器， 类似在 git 中的 push

如果输入
```
loom pull
```
会自动更新服务器的版本， 类似在 git 中的 pull


你觉得我如何实现这个功能，wrap git？ 还是自己做一套类似 git 的功能。
如果 wrap git 可以利用 vscode 插件或者一些 git 工具，可视化看到文件的变更。
如果 自己做类似功能， 可能用户体验更好？但需要自己做这类 UI 工具。
