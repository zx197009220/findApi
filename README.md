# 异步网络爬虫工具

这是一个基于Python的异步网络爬虫工具，具有UI界面，支持链接提取、请求队列管理和日志记录等功能。

## 主要功能

- 异步HTTP请求处理
- 链接提取和解析
- 请求队列管理
- 错误处理和日志记录
- 与UI交互的队列系统
- 可配置的正则规则(rules.yml)
- 消息解析功能

## 安装和运行

1. 确保已安装Python 3.7+
2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```
3. 运行UI界面：
   ```
   python run_ui.py
   ```

## 配置说明

配置文件位于`config.ini`和`config.py`，主要配置项包括：

- 爬虫设置(深度、重试次数、代理等)
- 正则表达式规则(rules.yml)
- 文件排除规则
- 子域名配置

## 使用示例

1. 启动UI界面
2. 输入起始URL
3. 点击"开始爬取"按钮
4. 查看爬取结果和日志

## 文件结构说明

```
├── .git/                # Git版本控制目录
├── .idea/              # IDE配置文件
├── config.ini          # 配置文件
├── config.py           # 配置管理模块
├── core/               # 核心功能模块
│   ├── config.ini      # 核心配置文件
│   ├── crawler_controller.py  # 爬虫控制器
│   ├── mock_crawler_controller.py  # 模拟爬虫控制器
│   └── __init__.py     # 包初始化文件
├── demo.py             # 示例脚本
├── link_extractor.py   # 链接提取模块
├── log.py              # 日志模块
├── messageparse.py     # 消息解析模块
├── README.md           # 项目说明文件
├── rules.yml           # 正则规则定义
├── run_ui.py           # UI启动脚本
├── ui/                 # UI界面代码
└── web_crawler.py      # 主爬虫逻辑
```

## 注意事项

1. 使用前请确保已正确配置`config.ini`和`rules.yml`
2. 爬取深度和频率请合理设置，避免对目标网站造成过大压力
3. 部分功能可能需要额外的依赖库，请参考`requirements.txt`
