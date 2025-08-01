from PySide6.QtCore import Signal, QObject
import asyncio
import queue
import threading
from datetime import datetime
import web_crawler

class CrawlerController(QObject):
    """真实爬虫控制器，用于UI与爬虫的交互"""

    status_changed_signal = Signal(str)
    log_signal = Signal(str, str, str)  # level, message, timestamp

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.result_queue = queue.Queue()  # 使用队列存储爬虫数据
        self.depth_to_row = {}  # 用于存储深度和行号的映射关系
        
        # 爬虫相关
        self.crawler_task = None
        self.ui_queue = None
        self.queue_monitor = None

    def start_crawler(self, config):
        """启动爬虫"""
        if self.is_running:
            return
            
        self.is_running = True
        self.status_changed_signal.emit("爬虫已启动")
        self.log_signal.emit("INFO", "开始爬取", datetime.now().isoformat())

        # 清空结果队列
        self.result_queue = queue.Queue()
        
        # 重置深度到行号的映射
        self.depth_to_row = {}
        
        # 获取配置参数
        start_url = config.get("start_url", "https://example.com")
        method = config.get("method", "GET")
        
        # 记录配置信息
        self.log_signal.emit("INFO", f"配置信息: URL={start_url}, 方法={method}, 最大深度={config.get('max_depth', 3)}", 
                            datetime.now().isoformat())
        
        # 创建事件循环
        self.loop = asyncio.new_event_loop()
        
        # 在新线程中运行爬虫
        def run_crawler_in_thread():
            asyncio.set_event_loop(self.loop)
            try:
                # 运行爬虫并获取UI队列
                self.ui_queue, self.crawler_task = self.loop.run_until_complete(
                    web_crawler.run_crawler_with_ui_queue(start_url, method)
                )
                # 启动队列监控
                self.queue_monitor = self.loop.create_task(self.monitor_ui_queue())
                # 运行事件循环，直到爬虫完成
                self.loop.run_until_complete(self.crawler_task)
            except Exception as e:
                self.log_signal.emit("ERROR", f"爬虫运行出错: {str(e)}", datetime.now().isoformat())
            finally:
                # 关闭事件循环
                self.loop.close()
                # 标记爬虫已停止
                self.is_running = False
                self.status_changed_signal.emit("爬虫已停止")
                self.log_signal.emit("INFO", "爬取已完成", datetime.now().isoformat())
        
        # 启动爬虫线程
        self.crawler_thread = threading.Thread(target=run_crawler_in_thread)
        self.crawler_thread.daemon = True
        self.crawler_thread.start()

    def stop_crawler(self):
        """停止爬虫"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.status_changed_signal.emit("正在停止爬虫...")
        self.log_signal.emit("INFO", "正在停止爬取", datetime.now().isoformat())
        
        # 停止事件循环
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        # 等待爬虫线程结束
        if hasattr(self, 'crawler_thread') and self.crawler_thread.is_alive():
            self.crawler_thread.join(timeout=5)
        
        self.status_changed_signal.emit("爬虫已停止")
        self.log_signal.emit("INFO", "爬取已停止", datetime.now().isoformat())
    
    def has_results(self):
        """检查是否有结果"""
        return not self.result_queue.empty()
    
    async def monitor_ui_queue(self):
        """监控UI队列，将数据转移到结果队列"""
        row = 0  # 行号计数器
        
        while True:
            try:
                # 从UI队列获取数据
                ui_data = await self.ui_queue.get()
                
                # 如果收到None，表示爬虫已完成
                if ui_data is None:
                    break
                
                # 获取深度
                depth = ui_data.get('depth', "1")
                
                # 保存深度和行号的映射关系
                self.depth_to_row[depth] = row
                row += 1
                
                # 将数据添加到结果队列
                self.result_queue.put(ui_data)
                
                # 记录日志
                self.log_signal.emit(
                    "INFO", 
                    f"收到数据: {ui_data['url']} (深度: {depth}, 类型: {ui_data['type']})", 
                    datetime.now().isoformat()
                )
                
                # 标记UI队列任务已完成
                self.ui_queue.task_done()
            except Exception as e:
                self.log_signal.emit("ERROR", f"处理UI队列数据时出错: {str(e)}", datetime.now().isoformat())
        
        # 记录深度到行号的映射关系
        self.log_signal.emit("DEBUG", f"深度到行号映射: {self.depth_to_row}", datetime.now().isoformat())
