from PySide6.QtCore import Signal, QObject, QTimer
import random
from datetime import datetime
import queue

class MockCrawlerController(QObject):
    """模拟爬虫控制器，用于UI测试"""

    status_changed_signal = Signal(str)
    log_signal = Signal(str, str, str)  # level, message, timestamp

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.mock_timer = QTimer()
        self.mock_timer.timeout.connect(self.generate_mock_data)
        self.result_queue = queue.Queue()  # 使用队列存储模拟数据
        self.has_results = False  # 标记是否有结果
        
        # 深度序号跟踪
        self.current_depth = "1"
        self.depth_counters = {"1": 0}
        self.last_url_type = None  # 用于跟踪上一个URL的类型
        self.consecutive_api_count = 0  # 连续API计数
        self.depth_to_row = {}  # 用于存储深度和行号的映射关系


        # 预定义的模拟数据
        self.mock_urls = [
            "https://example.com",
            "https://example.com/about",
            "https://example.com/contact",
            "https://example.com/products",
            "https://example.com/blog",
            "https://api.example.com/v1/users",
            "https://api.example.com/v1/products",
            "https://api.example.com/v1/orders"
        ]

        self.mock_statuses = [200, 301, 302, 404, 500]
        self.mock_types = ["fuzz","source"]
        self.mock_depth = ["1.1","1.2","1.3","1.2.1","1.2.2","1.3.1","1.3.2","1.3.2.1"]

    def start_crawler(self, config):
        """启动模拟爬虫"""
        self.is_running = True
        self.status_changed_signal.emit("模拟爬虫已启动")
        self.log_signal.emit("INFO", "开始模拟爬取", datetime.now().isoformat())

        # 清空结果队列
        self.result_queue = queue.Queue()
        
        # 重置深度序号跟踪
        self.current_depth = "1"
        self.depth_counters = {"1": 0}
        self.last_url_type = None
        self.consecutive_api_count = 0
        self.consecutive_link_count = 0
        self.depth_to_row = {}  # 重置深度到行号的映射

        # 启动模拟数据生成器
        self.mock_timer.start(500)  # 每500毫秒生成一条模拟数据

    def stop_crawler(self):
        """停止模拟爬虫"""
        self.is_running = False
        self.mock_timer.stop()
        self.status_changed_signal.emit("模拟爬虫已停止")
        self.log_signal.emit("INFO", "模拟爬取已停止", datetime.now().isoformat())
        
    def has_results(self):
        """检查是否有结果"""
        return not self.result_queue.empty()



    def generate_mock_data(self):
        """生成模拟爬取数据"""
        if not self.is_running:
            return
        
        # 只生成一次数据，然后停止定时器
        # 初始化行号计数器
        row = 0
        
        # 首先生成起始URL，深度为1
        start_url = self.mock_urls[0]  # 使用第一个URL作为起始URL
        start_result = {
            'status': 200,  # 起始URL通常是200状态码
            'url': start_url,
            'depth': "1",  # 设置深度为1
            'type': "source"  # 起始URL通常是source类型
        }
        # 添加到结果队列
        self.result_queue.put(start_result)
        # 保存深度和行号的映射关系
        self.depth_to_row["1"] = row
        row += 1
        
        # 然后生成其他URL，深度从mock_depth列表中获取
        data_count = len(self.mock_depth)
        for depth in self.mock_depth:
            result = {
                'status': random.choice(self.mock_statuses),
                'url': random.choice(self.mock_urls[1:]),  # 排除第一个URL（已作为起始URL）
                'depth': depth,
                'type': random.choice(self.mock_types)
            }
            # 添加到结果队列
            self.result_queue.put(result)
            # 保存深度和行号的映射关系
            self.depth_to_row[depth] = row
            row += 1
        
        # 记录日志，表明已生成数据
        self.log_signal.emit("INFO", f"已生成{data_count + 1}条模拟数据", datetime.now().isoformat())
        self.log_signal.emit("DEBUG", f"深度到行号映射: {self.depth_to_row}", datetime.now().isoformat())
        
        # 停止定时器，防止重复生成数据
        self.mock_timer.stop()

    
