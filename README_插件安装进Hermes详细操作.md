# 忆无限简版插件：装进 Hermes 的详细操作

适用：本文件只讲简版 2 个 PY 的装法，不讲老版 Chroma 版。
简版 2 个 PY：memo_infinity_lite.py（记忆库）+ plugin_local_continuity_lite.py（插件，改名后用）。

## 先说清 3 个容易装错的地方

1. Hermes 家目录不要写死用户名。给你的路径一律用 `%LOCALAPPDATA%\hermes`，
   你电脑上它展开就是 `C:\Users\Administrator\AppData\Local\hermes`，
   别人电脑上用户名不一样，展开也不一样，写死 Administrator 到别人电脑上就找不到。
2. 插件不是散文件。Hermes 认插件是靠“文件夹 + 里面的 __init__.py”，
   必须放成 `plugins\local_continuity\__init__.py` 这种整文件夹结构，
   2 个文件散放在 `plugins\` 根目录下，Hermes 认不出来。
3. 不要放进 `desktop-plugins`。那是 Hermes 自带的桌面插件目录，不要动它，
   我方插件只放 `plugins\`，和老版实装形态一致。

## 第 0 步：先把 Hermes 完全退出

- Hermes 窗口关掉不算，要完全退出 Hermes，任务栏托盘里也退出，
  确认没有 Hermes 进程在跑，再动手。插件是 Hermes 启动时才加载，
  Hermes 开着的时候拷文件，Hermes 认不到，重启了才认。

## 第 1 步：找到 Hermes 家目录，备份

1. 按 Win+R，输入 `explorer %LOCALAPPDATA%\hermes`，回车，打开的就是家目录。
2. 先备份 2 样东西，备份了再改，改坏了能回来：
   - 家目录里的 `config.yaml`，复制一份，改名成 `config.yaml.bak`，放在原地；
   - 如果家目录 `plugins\` 里已经有老版 `local_continuity` 文件夹，
     把整个老文件夹复制一份到别处备份（例如桌面一个备份文件夹里），
     不要直接删了不备份。
3. 简版和老版记忆库不是同一个文件：老版在 `E:\MemoInfinity\Hermes_Memory_DB\continuity\continuity.sqlite3`，
   简版新库叫 `memo_infinity.sqlite3`，装简版是新开一个空记忆库，
   老记忆不会自动搬过来。老库文件不要删，留着就是留着老记忆。

## 第 2 步：放插件，2 个文件，改 1 个名字

1. 在家目录里看有没有 `plugins` 文件夹，没有就新建一个。
2. 在 `plugins` 里新建（或清空后用）一个文件夹，名字就叫 `local_continuity`。
   为什么用这个名字：老版配置里 memory.provider 就是 local_continuity，
   用同名，配置不用大改；如果老文件夹还在，先把老文件夹移走备份，
   再建新的，不要新旧两个 local_continuity 混在一起。
3. 把下面 2 个文件复制进 `plugins\local_continuity\`：
   - `memo_infinity_lite.py`：名字不动，原样放；
   - `plugin_local_continuity_lite.py`：改名成 `__init__.py` 再放。
   放完以后，这个文件夹里应该是：
   ```
   %LOCALAPPDATA%\hermes\plugins\local_continuity\__init__.py
   %LOCALAPPDATA%\hermes\plugins\local_continuity\memo_infinity_lite.py
   ```
   可选再放一个 `plugin.yaml`（本包里有），放不放 Hermes 都能认，
   老版宿主机上 local_continuity 没有 yaml 照样识别启用，放了也不坏。

## 第 3 步：先定记忆放哪个盘，再启动 Hermes

这一步必须在启动 Hermes 之前做，Hermes 启动时才读这个设置，启动后再设不生效。

- 不想放 C 盘（推荐）：在 Windows 系统环境变量里设一个，重启 Hermes 生效：
  - `MEMOINFINITY_ROOT` = `E:\MemoInfinity`，记忆文件在 E 盘这个文件夹里的 `memo_infinity.sqlite3`；
  - 或者 `MEMOINFINITY_DB` = `E:\MemoInfinity\memo_infinity.sqlite3`，直接写完整文件路径。
  - 两个都设了，以 `MEMOINFINITY_DB` 为准；只设一个就行；盘符 D、E 自己换。
- 什么都不设：记忆就在插件文件夹里的 `memo_infinity.sqlite3`，
  插件文件夹在 Hermes 家目录下，默认在 C 盘，重装系统会丢记忆，前面那份盘符说明里已经标过这个危险。
- 想接着用 C 盘已有的简版记忆：把原来那个 `memo_infinity.sqlite3` 复制到新路径，
  再设环境变量、再重启，不要直接在新路径建空库覆盖旧库。

## 第 4 步：改 config.yaml，只改插件这一段，别动模型

文件在：`%LOCALAPPDATA%\hermes\config.yaml`，就是第 1 步备份的那个文件。

1. 用记事本打开，先按 Ctrl+F 搜 `plugins`，全文件只能有 1 处 `plugins:`，
   老版出过重复建了 2 处 `plugins:` 导致 Hermes 报 formatting error、插件不加载的坑，
   有 2 处就删掉重复的那一处，留一处。
2. 在那一处里确认：
   ```
   plugins:
     enabled: [local_continuity]
   ```
   简版只有这 1 个插件，不要再写 `local_continuity_guard`。
   简版没有 guard 插件，老版 guard 是靠老版 continuity_runtime + yaml 配置的，
   简版不提供 yaml，guard 装了也会读不到配置，所以简版只启用 local_continuity 一个。
3. 再确认下面这一行在（如果原来就有，留着；如果没有，补上）：
   ```
   memory:
     provider: local_continuity
   ```
   如果原来有 `context.engine: local_continuity_guard` 这一行，简版要删掉它，
   不然 Hermes 会去找一个不存在的 guard。
4. 千万别动 `model`、`base_url` 那一段，模型端点是客户自己在 Hermes 里选的，
   安装插件不碰模型。改完保存，关掉记事本。
5. 如果你原来根本没有 config.yaml，或者不确定格式，先别自己编一整份，
   先启动 Hermes 让它生成一份，再按上面只改插件这一段。

## 第 5 步：重启 Hermes，激活无限上下文（最重要的一步，别跳过）

插件装好、Hermes 重启了，无限上下文还不算激活。
插件本身只会默默存东西，不会自动替你接着干活，
无限上下文是靠你下面这句话激活的，不说这句话，Hermes 就当新任务聊，
旧记忆存着也用不上。

1. 不要用老版启动器（老启动器会去起 16828、16829、16830、16827 那些服务，
   简版不需要这些服务，用老启动器反而会在服务那一步卡住）。
   直接从开始菜单重新打开 Hermes。
2. 激活分两种情况，两种都要会：
   - 同一个窗口一直干活：不用你手动激活，插件每轮结束会自动归档本轮对话，
     上下文快满要压缩时，插件会在压缩前先归档一次，所以同一个窗口里
     你只管接着说、接着做，不用开新窗口，这就是单窗口无限工作的意思。
   - 最关键的 80% 归档转存清除流程（无限上下文就是靠这个循环转起来的）：
     1. 正常干活，直到系统上下文用到超过 80%，不要等到 100% 才处理，
        80% 就是动手归档的线；
     2. 归档：插件在压缩前先把本轮对话原文 + 任务状态（目标、最新要求、
        你的原话约束、待办）一次性写进 SQLite 记忆库，原文和状态在同一个
        事务里提交，存进去了才算归档成功，存不进去就不要往下清；
     3. 转存：归档成功后，旧的长对话就已经在记忆库里了，不用再背在窗口里，
        窗口里只留总结和状态，就是目标、最新要求、约束、待办这几样；
     4. 清除：Hermes 把旧上下文窗口清掉、压缩掉，只带着上面那份总结进新窗口，
        窗口一下子就空出来了，可以继续装新内容；
     5. 继续干：新窗口里第一句话说“继续”，确认 Hermes 还回来的目标和约束
        是对的，再接着干活；干到下一次 80%，再重复归档、转存、清除这一步，
        这样一轮一轮转下去，任务可以无限长，窗口永远不会被撑爆。
     记住顺序一定是：先归档转存、确认存进去了，再清除，千万别先清窗口、
     再想着去找记忆，清早了、归档没存进去，旧东西就真丢了。
   - 新开窗口、第二天、压缩后换了新会话：必须手动激活，第一句话就要说激活的话，
     不要先聊别的、不要先下新任务。激活的话最稳的是下面这句：
     ```
     继续
     ```
     也可以说“接着上次的做”、“恢复上次任务”，意思一样，但“继续”是最简单、最稳的。
     说完等 Hermes 回你，它应该把上次任务还回来：目标是什么、最新要求是什么、
     你原来定的约束（例如“不要联网”）是什么，这三样对上了，才算激活成功，
     然后再说你下一步要干什么。
   - 如果同项目有多个没做完的任务，Hermes 不会自动选一个，它会列出候选任务，
     让你先定是哪一个，你按目标选一个，例如说“恢复做记账本那个”，
     选定了再接着干，不要让它猜。
   - 千万别在想续接的时候说“不要继续”、“不用恢复”、“开始新任务”、“换个任务”，
     插件听到这种话会直接不绑定、不续接，你再说“继续”也得重新来。
   - 还有一个前提：新窗口和旧窗口必须在同一个项目目录里，
     记忆是按工作目录定的，同目录才是同项目，换了目录就是换了项目，
     换了项目说“继续”也找不回旧任务。
3. 验证 1：新开一个会话，随便说一句话，例如“做一个本地记账本，不要联网”，
   再新开一个会话，第一句话说“继续”，看 Hermes 能不能把上次任务还回来，
   能还回来就是续接通了、无限上下文激活了；只回一句客套话、没提旧目标、
   没提旧约束，那就是没激活，先按下面“装不上时”那一节查插件和重启。
3. 验证 2：在对话里让 Hermes 用 continuity 工具查一下，例如说“查一下记账本”，
   看能不能返回旧摘录；或者在 Hermes 里直接看插件/工具列表里有没有 continuity。
4. 验证 3（看日志，最准）：家目录 `logs\` 里的 agent.log，
   找 `Memory provider 'local_continuity' registered` 和 `activated` 这类字样，
   有就是插件注册成功了，老版日志里就是这么显示的。

## 装不上时，按这个顺序查

- 插件列表里没有 local_continuity：先查文件夹结构对不对，
  是不是 `plugins\local_continuity\__init__.py`，不是散文件、不是 desktop-plugins、
  不是 `__init__.py` 没改名（原名 plugin_local_continuity_lite.py Hermes 不认）。
- Hermes 启动报 config 格式错误：打开 config.yaml，按 Ctrl+F 搜 `plugins:`，
  是不是有 2 处，删掉重复的一处，保存，重启。
- 插件认到了，但说“继续”没反应：先确认 Hermes 是完全退出后重开的，
  不是只关窗口；再确认会话是不是同项目（scope 按工作目录定，换了目录就是换了项目）。
- 记忆又跑回 C 盘了：环境变量是不是在 Hermes 启动之前设的系统变量，
  不是只在命令行里临时设的；设完有没有重启 Hermes。
- 老记忆找不到了：这是预期的，简版是新库，老库文件还在原地，没有自动迁移，
  不要删老库，需要老记忆时按老版方式回去查。

## 卸载/回退

- 想回老版：完全退出 Hermes，把 `plugins\local_continuity\` 这个简版文件夹移走，
  把第 1 步备份的老文件夹放回来，把 `config.yaml.bak` 改回 `config.yaml`，
  再重启 Hermes。
- 想彻底不用简版：完全退出 Hermes，删掉 `plugins\local_continuity\` 文件夹，
  config.yaml 里把 local_continuity 从 enabled 里去掉，重启即可。
  记忆库文件 `memo_infinity.sqlite3` 单独留着不删，就是留着记忆备份。
