# API Discovery Crawler

一个基于异步IO和PySide6的网络爬虫工具，专注于发现网页API端点，并集成Burp Suite进行流量分析。

## 功能特性

- **API端点发现**：自动识别和收集REST API端点
- **Burp Suite集成**：所有流量自动代理到Burp Suite方便分析
- **异步高性能**：基于asyncio和httpx的异步爬虫引擎
- **智能链接提取**：从HTML/JS/CSS中提取API链接
- **深度控制**：可配置的爬取深度限制
- **图形界面**：基于PySide6的可视化操作界面
- **多种导出格式**：支持JSON/CSV/文本结果导出
- **完整日志系统**：详细记录爬取过程和错误

## 安装依赖

```bash
pip install PySide6 requests beautifulsoup4
```

## 使用说明

### 图形界面模式

1. 运行主程序：
```bash
python run_ui.py
```

2. 在GUI界面中配置爬虫参数：
   - **目标URL**：要爬取的起始URL
   - **爬取深度**：0表示仅当前页，1表示当前页+直接链接
   - **Burp代理**：勾选启用并配置Burp Suite监听地址
   - **线程数**：并发请求数量(默认10)

3. 点击"开始"按钮启动爬虫

4. 在"结果"标签页查看实时发现的API端点

5. 使用"导出"功能保存结果到JSON/CSV/文本

### 命令行模式

```bash
python web_crawler.py -u <URL> -d <DEPTH> [--proxy <PROXY>]
```

参数说明：
- `-u/--url`: 目标URL (必需)
- `-d/--depth`: 爬取深度 (默认1)
- `--proxy`: Burp代理地址 (如 127.0.0.1:8080)
- `-o/--output`: 结果输出文件路径
- `-v/--verbose`: 显示详细日志

示例：
```bash
python web_crawler.py -u https://example.com/api -d 2 --proxy 127.0.0.1:8080 -o results.json
```

## 项目结构

```
├── .git
├── .idea
├── config.ini       # 配置文件
├── config.py        # 配置加载模块
├── core/            # 核心功能
│   ├── crawler_controller.py  # 爬虫控制器
│   └── __init__.py
├── integration/     # 集成模块
├── link_extractor.py # 链接提取模块
├── log.py           # 日志模块
├── message/         # 消息处理
├── messageparse.py  # 消息解析
├── rules.yml        # 爬取规则
├── run_ui.py        # 主程序入口
├── start.txt        # 启动说明
├── ui/              # 用户界面
├── web_crawler.py   # 爬虫主模块
└── __pycache__
```

## 核心模块说明

### web_crawler.py
- 主爬虫逻辑实现
- 异步HTTP请求处理
- API端点发现与收集
- 深度控制和去重机制
- 代理集成(Burp Suite)

### link_extractor.py
- 从HTML/JS/CSS中提取链接
- API端点模式识别
- 相对路径转绝对路径
- 资源文件过滤

### core/crawler_controller.py
- 爬虫任务调度
- 并发控制
- 状态监控
- 错误处理与恢复
- UI事件通知

### ui/main_window.py
- 主界面实现
- 标签页管理(配置/爬取/结果/日志)
- 用户操作事件处理
- 实时数据显示

### config.py
- 配置加载与解析
- 运行时配置管理
- 默认值处理
- 配置验证

## 配置选项

编辑`config.ini`文件配置以下选项：

```ini
[proxy]
enabled = false
host = 127.0.0.1
port = 8080

[crawler]
max_depth = 3
timeout = 10
user_agent = Mozilla/5.0
```

## 高级配置

### 自定义爬取规则
编辑`rules.yml`文件定义自定义爬取规则：

```yaml
api_patterns:
  - path: "/api/"
  - path: "/v1/"
  - regex: "\\.json$"

exclude_patterns:
  - path: "/admin/"
  - path: "/login"
  - regex: "\\.png$"
```

### 开发说明

1. 扩展爬虫功能：
   - 修改`web_crawler.py`添加新的请求处理器
   - 更新`link_extractor.py`添加新的链接匹配规则

2. 扩展UI功能：
   - 在`ui/views/`目录下添加新的标签页
   - 更新`main_window.py`集成新功能

3. 运行测试：
```bash
python -m unittest discover
```

## 示例截图

(此处可添加GUI界面截图)

## 贡献指南

欢迎通过Pull Request提交改进，请确保：
1. 代码符合PEP8规范
2. 包含必要的单元测试
3. 更新相关文档
4. 通过所有现有测试
