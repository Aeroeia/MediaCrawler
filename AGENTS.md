# MediaCrawler 项目理解（面向后续开发）

本文件用于在每次任务开始时快速建立项目上下文。重点不是命令罗列，而是当前架构、主链路、约束和改动切入点。

## 1. 核心定位

- 这是一个多平台自媒体公开信息采集框架，统一入口，平台分治实现。
- 支持平台：`xhs`、`dy`、`ks`、`bili`、`wb`、`tieba`、`zhihu`。
- 支持模式：`search`（关键词）、`detail`（指定 ID/URL）、`creator`（创作者主页）。
- 核心目标是“复用统一抓取流程”，而不是把所有平台逻辑混在一起。

## 2. 我对运行主链路的理解

### 2.1 CLI 主链路

1. `main.py` 调用 `cmd_arg.parse_cmd()` 解析参数。
2. CLI 参数会覆盖 `config` 中的运行时配置。
3. 如果传入 `--init_db`，直接初始化数据库结构后退出。
4. `CrawlerFactory` 基于 `config.PLATFORM` 创建平台爬虫。
5. 平台爬虫执行：浏览器启动 -> 登录检查 -> 按模式抓取 -> 数据存储。
6. 主流程结束后执行清理（浏览器/数据库连接），并按条件执行 Excel flush、词云生成。

### 2.2 API/WebUI 主链路

- `api/main.py` 提供 FastAPI 控制接口与静态 WebUI。
- `api/services/crawler_manager.py` 以子进程方式执行 `uv run python main.py ...`。
- API 层是控制面：负责启停、状态、日志和数据文件查询；抓取逻辑仍在 `main.py` 及平台模块。

## 3. 模块分层理解

- `main.py`：统一入口与生命周期编排。
- `base/`：抽象协议层（Crawler/Login/Store/API Client）。
- `cmd_arg/`：CLI 参数定义与枚举，负责把参数映射回全局 `config`。
- `config/`：基础配置、平台配置、数据库配置。
- `media_platform/`：平台核心逻辑（`core/client/login/field/help` 等）。
- `store/`：平台存储适配与工厂分发（按 `SAVE_DATA_OPTION` 选择实现）。
- `database/`：ORM 模型、异步 session、建表入口。
- `proxy/`：代理提供商适配与 IP 池管理。
- `cache/`：本地过期缓存与 Redis 缓存工厂。
- `api/`：控制面 API + WebUI 静态资源。
- `tools/`：日志、CDP 浏览器管理、异步文件写入等横切工具。
- `test/`、`tests/`：测试代码（并存）。

## 4. 关键设计约束

- `config` 是全局可变状态，解析 CLI 后的值会影响全局行为。
- 浏览器启动有两套路径：标准 Playwright 和 CDP，平台 `core.py` 基本都按 `ENABLE_CDP_MODE` 分支。
- 存储后端不是全局统一注册，而是“按平台各自工厂注册”。新增后端需要逐平台补齐映射。
- `SAVE_DATA_OPTION` 中 `db` 语义上是 MySQL，`postgres` 为单独选项。
- 项目主链路是异步 I/O，阻塞调用会直接破坏并发效果。

## 5. 配置优先级（按类别）

- 爬虫行为参数：`CLI 参数 > config/base_config.py 默认值`。
- 数据库连接参数：`环境变量 > config/db_config.py 默认值`。
- 说明：数据库连接项不是通过 CLI 覆盖，而是通过环境变量在配置加载时生效。

## 6. 对后续开发最关键的改动入口

### 6.1 新增平台

1. 新建 `media_platform/<platform>/`，实现 `core/client/login/field`。
2. 在 `main.py` 的 `CrawlerFactory.CRAWLERS` 注册平台代号。
3. 在 `config/` 添加平台配置并在 `base_config.py` 引入。
4. 新建 `store/<platform>/` 并实现平台存储工厂与存储类。
5. 视情况新增 `model/m_<platform>.py`。
6. 更新 `cmd_arg/arg.py` 枚举和 ID 参数映射。
7. 更新 API 层枚举与平台选项（`api/schemas/crawler.py`、`api/main.py`）。

### 6.2 新增存储后端

1. 在各平台实现新的 `AbstractStore` 子类。
2. 在各平台 `StoreFactory` 注册新的 `SAVE_DATA_OPTION`。
3. 更新 CLI/API 的 `SaveDataOptionEnum`，保持入口一致。
4. 如果是 DB 型后端，补 `config/db_config.py` 与 `database/` 初始化逻辑。

## 7. 已知风险与常见坑

- `pyproject.toml` 当前默认 `uv` 索引为清华镜像，偶发 403；可用 `--default-index https://pypi.org/simple` 临时覆盖。
- 抓取失败经常来自登录态、验证码、平台风控，而非纯代码逻辑错误。
- 部分测试依赖 Redis/MongoDB 等外部服务，本地执行前需确认依赖环境。
- Python 文件头由 pre-commit 强约束，新增文件前后都要检查头部。

## 8. 建议开发工作流

1. 先判断改动层级（平台逻辑 / 存储 / 参数入口 / API 控制面）。
2. 在单层内最小改动，避免跨层顺手重构导致回归面扩大。
3. 本地做最小验证：目标场景 smoke run + 受影响测试 + pre-commit。
4. 涉及 CLI/API 参数时，同步检查：枚举、默认值、帮助文案、WebUI 选项。

## 9. 常用命令（最小集合）

```bash
# 依赖安装
uv sync
uv run playwright install

# CLI 调试
uv run main.py --help
uv run main.py --platform xhs --lt qrcode --type search

# API 调试
uv run uvicorn api.main:app --port 8080 --reload

# 测试与质量
uv run pytest
uv run pre-commit run --all-files
```

## 10. 协作与安全约定

- 项目用途限定为学习研究，禁止商业用途。
- 变更遵循最小原则，不回滚任务无关改动。
- 禁止使用破坏性 Git 命令（如 `reset --hard`、`checkout --`）除非明确授权。
- 面对不确定行为，优先做小范围可复现实验，再扩大改动。
