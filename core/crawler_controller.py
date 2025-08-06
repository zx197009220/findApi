from PySide6.QtCore import Signal, QObject
import asyncio
import concurrent.futures
import queue
import threading
import asyncio
from datetime import datetime
import web_crawler
from config import config


class CrawlerController(QObject):
    """真实爬虫控制器，用于UI与爬虫的交互"""

    status_changed_signal = Signal(str)
    data_received_signal = Signal(dict)  # 爬虫数据信号，发送爬取到的数据到UI
    log_signal = Signal(str, str, str)  # level, message, timestamp
    exclude_log_signal = Signal(dict)  # timestamp, rule, link, source, parent_index

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.depth_to_row = {}  # 用于存储深度和行号的映射关系

        # 爬虫相关
        self.crawler_task = None
        self.ui_queue = None
        self.exclude_queue = None
        self.ui_queue_monitor = None
        self.exclude_queue_monitor = None
        self.loop = None
        self.crawler_thread = None

    def start_crawler(self, start_url):
        """启动爬虫
        
        Args:
            start_url: 起始URL，从UI输入框获取
        """
        print("[DEBUG] 收到启动爬虫请求")  # 调试输出
        if self.is_running:
            print("[DEBUG] 爬虫已在运行，忽略请求")  # 调试输出
            return

        # 确保之前的爬虫已完全停止和清理
        if hasattr(self, 'crawler_thread') and self.crawler_thread and self.crawler_thread.is_alive():
            self.stop_crawler()
            self.log_signal.emit("WARNING", "检测到之前的爬虫未完全停止，已强制停止", datetime.now().isoformat())

        # 确保事件循环已关闭
        if self.loop and not self.loop.is_closed():
            try:
                self.loop.close()
                self.log_signal.emit("DEBUG", "关闭了之前未完全关闭的事件循环", datetime.now().isoformat())
            except Exception as e:
                self.log_signal.emit("ERROR", f"关闭旧事件循环时出错: {str(e)}", datetime.now().isoformat())

        self.is_running = True
        self.status_changed_signal.emit("爬虫已启动")
        self.log_signal.emit("INFO", "开始爬取", datetime.now().isoformat())

        # 不再需要结果队列

        # 重置深度到行号的映射
        self.depth_to_row = {}

        # 记录配置信息
        self.log_signal.emit("INFO", 
                           f"配置信息: 最大深度={config.crawler_max_depth}, 最大重试={config.crawler_max_retries}",
                           datetime.now().isoformat())

        # 创建新的事件循环
        self.loop = asyncio.new_event_loop()

        # 在新线程中运行爬虫
        def run_crawler_in_thread():
            print("[DEBUG] 线程函数开始执行")
            
            try:
                # 创建新的事件循环
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                print(f"[DEBUG] 新事件循环已创建: {self.loop.is_running()}")
                
                # 准备爬虫协程
                print("[DEBUG] 准备运行爬虫协程")
                coro = web_crawler.run_crawler_with_ui_queue(
                    start_url,
                    reset_state=True
                )
                
                # 在事件循环中运行协程获取UI队列、排除队列和爬虫任务
                print("[DEBUG] 开始获取UI队列、排除队列和爬虫任务...")
                self.ui_queue, self.exclude_queue, self.crawler_task = self.loop.run_until_complete(coro)
                print(f"[DEBUG] 获取到UI队列、排除队列和爬虫任务: {self.crawler_task}")
                
                # 启动队列监控
                self.ui_queue_monitor = self.loop.create_task(self.monitor_ui_queue())
                print(f"[DEBUG] UI队列监控任务已创建: {self.ui_queue_monitor}")
                
                # 启动排除队列监控
                self.exclude_queue_monitor = self.loop.create_task(self.monitor_exclude_queue())
                print(f"[DEBUG] 排除队列监控任务已创建: {self.exclude_queue_monitor}")
                
                # 添加爬虫任务完成的回调函数
                def on_crawler_task_done(task):
                    try:
                        task.result()  # 获取结果，如果有异常会在这里抛出
                        print("[DEBUG] 爬虫任务已完成")
                    except asyncio.CancelledError:
                        print("[DEBUG] 爬虫任务被取消")
                    except Exception as e:
                        print(f"[ERROR] 爬虫任务出错: {e}")
                    finally:
                        print("[DEBUG] 爬虫任务回调执行完毕")
                
                # 为爬虫任务添加完成回调
                self.crawler_task.add_done_callback(on_crawler_task_done)
                print("[DEBUG] 已为爬虫任务添加完成回调")
                
                # 运行事件循环，直到爬虫任务完成
                print("[DEBUG] 开始运行事件循环，等待爬虫任务完成...")
                self.loop.run_until_complete(self.crawler_task)
                print("[DEBUG] 爬虫任务已完成，事件循环退出")
            except Exception as e:
                print(f"[ERROR] 爬虫执行过程中出错: {e}")
                import traceback
                traceback.print_exc()

                # 清理：取消所有未完成的任务（除了爬虫任务和队列监控任务）
                print("[DEBUG] 开始清理其他未完成的任务...")
                pending = asyncio.all_tasks(self.loop)
                tasks_to_cancel = []
                for task in pending:
                    if (not task.done() and 
                        not task.cancelled() and 
                        task != self.crawler_task and 
                        task != self.queue_monitor):
                        tasks_to_cancel.append(task)
                        task.cancel()
                        print(f"[DEBUG] 取消了任务: {task}")
                
                # 等待被取消的任务完成
                if tasks_to_cancel:
                    print(f"[DEBUG] 等待 {len(tasks_to_cancel)} 个被取消的任务完成...")
                    self.loop.run_until_complete(asyncio.gather(*tasks_to_cancel, return_exceptions=True))
                    print("[DEBUG] 所有被取消的任务已完成")
                
                # 关闭事件循环
                if not self.loop.is_closed():
                    print("[DEBUG] 关闭事件循环")
                    self.loop.close()
                    print("[DEBUG] 事件循环已关闭")
                
                # 标记爬虫已停止
                self.is_running = False
                self.status_changed_signal.emit("爬虫已停止")
                self.log_signal.emit("INFO", "爬取已完成", datetime.now().isoformat())
                print("[DEBUG] 爬虫线程函数执行完毕")
            except Exception as e:
                print(f"[ERROR] 爬虫线程清理过程中出错: {e}")
                import traceback
                traceback.print_exc()
                
                # 确保在出错时也能正确关闭事件循环和标记爬虫已停止
                if self.loop and not self.loop.is_closed():
                    try:
                        self.loop.close()
                    except:
                        pass
                
                self.is_running = False
                self.status_changed_signal.emit("爬虫出错并停止")
                self.log_signal.emit("ERROR", f"爬虫出错并停止: {str(e)}", datetime.now().isoformat())


        # 启动爬虫线程
        print("[DEBUG] 准备创建爬虫线程")  # 调试输出
        self.crawler_thread = threading.Thread(target=run_crawler_in_thread)
        self.crawler_thread.daemon = True
        print(f"[DEBUG] 线程状态 before start: alive={self.crawler_thread.is_alive()}")  # 调试输出
        self.crawler_thread.start()
        print(f"[DEBUG] 线程状态 after start: alive={self.crawler_thread.is_alive()}")  # 调试输出
        print(f"[DEBUG] 线程标识符: {self.crawler_thread.ident}")  # 调试输出

    def stop_crawler(self):
        """停止爬虫"""
        if not self.is_running:
            return

        self.is_running = False
        self.status_changed_signal.emit("正在停止爬虫...")
        self.log_signal.emit("INFO", "正在停止爬取", datetime.now().isoformat())

        # 先保存任务引用，然后清理引用，防止后续访问已取消的任务
        ui_queue_monitor = self.ui_queue_monitor
        exclude_queue_monitor = self.exclude_queue_monitor
        crawler_task = self.crawler_task
        self.ui_queue_monitor = None
        self.exclude_queue_monitor = None
        self.crawler_task = None
        
        # 在事件循环关闭前取消任务
        if self.loop and not self.loop.is_closed():
            # 使用Future对象来同步任务取消
            future = concurrent.futures.Future()
            
            def cancel_tasks():
                # 取消UI队列监控任务
                if ui_queue_monitor is not None and not ui_queue_monitor.done() and not ui_queue_monitor.cancelled():
                    ui_queue_monitor.cancel()
                    self.log_signal.emit("INFO", "UI队列监控任务已取消", datetime.now().isoformat())
                
                # 取消排除队列监控任务
                if exclude_queue_monitor is not None and not exclude_queue_monitor.done() and not exclude_queue_monitor.cancelled():
                    exclude_queue_monitor.cancel()
                    self.log_signal.emit("INFO", "排除队列监控任务已取消", datetime.now().isoformat())
                
                # 取消爬虫任务
                if crawler_task is not None and not crawler_task.done() and not crawler_task.cancelled():
                    crawler_task.cancel()
                    self.log_signal.emit("INFO", "爬虫任务已取消", datetime.now().isoformat())
                
                # 取消所有未完成的任务
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    if not task.done() and not task.cancelled():
                        task.cancel()
                
                # 标记Future为完成
                future.set_result(None)
            
            # 在事件循环线程中执行取消操作
            self.loop.call_soon_threadsafe(cancel_tasks)
            
            # 等待取消操作完成
            future.result(timeout=5)  # 设置超时，避免无限等待
            
            # 停止事件循环
            if self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
                self.log_signal.emit("INFO", "事件循环停止请求已发送", datetime.now().isoformat())
            else:
                self.log_signal.emit("INFO", "事件循环未运行，无需停止", datetime.now().isoformat())

        # 等待爬虫线程结束
        if hasattr(self, 'crawler_thread') and self.crawler_thread and self.crawler_thread.is_alive():
            self.crawler_thread.join(timeout=5)
            if self.crawler_thread.is_alive():
                self.log_signal.emit("WARNING", "爬虫线程未能在超时时间内结束", datetime.now().isoformat())

        # 重置爬虫相关资源
        self.crawler_task = None
        self.ui_queue = None

        # 确保事件循环被关闭
        if self.loop and not self.loop.is_closed():
            self.loop.close()

        self.loop = None

        # 不再需要向结果队列发送None

        self.status_changed_signal.emit("爬虫已停止")
        self.log_signal.emit("INFO", "爬取已停止", datetime.now().isoformat())


    def has_results(self):
        """检查是否有结果"""
        # 不再使用result_queue，直接返回False
        return False

    async def monitor_ui_queue(self):
        """监控UI队列，将数据转移到结果队列并发送到UI"""
        row = 0  # 行号计数器

        try:
            while True:
                try:
                    # 从UI队列获取数据，设置超时以便能够响应取消
                    ui_data = await asyncio.wait_for(self.ui_queue.get(), timeout=1.0)
                    
                    # 如果收到None，表示爬虫已完成
                    if ui_data is None:
                        break

                    # 获取深度
                    depth = ui_data.get('depth', "1")

                    # 保存深度和行号的映射关系
                    self.depth_to_row[depth] = row
                    row += 1

                    # 直接发送数据到UI，不再使用中间队列
                    self.data_received_signal.emit(ui_data)

                    # 记录日志
                    self.log_signal.emit(
                        "INFO",
                        f"收到数据: {ui_data['url']} (深度: {depth}, 类型: {ui_data['type']})",
                        datetime.now().isoformat()
                    )

                    # 标记UI队列任务已完成
                    self.ui_queue.task_done()

                except asyncio.TimeoutError:
                    # 检查爬虫任务是否已完成
                    if self.crawler_task and self.crawler_task.done():
                        break
                    # 否则继续等待
                    continue

        except asyncio.CancelledError:
            self.log_signal.emit("DEBUG", "UI队列监控任务被取消", datetime.now().isoformat())
        except Exception as e:
            self.log_signal.emit(
                "ERROR",
                f"UI队列监控出错: {str(e)}",
                datetime.now().isoformat()
            )
        finally:
            # 记录深度到行号的映射关系
            self.log_signal.emit("DEBUG", f"深度到行号映射: {self.depth_to_row}", datetime.now().isoformat())
            self.log_signal.emit("INFO", "UI队列监控任务已结束", datetime.now().isoformat())
            
    async def monitor_exclude_queue(self):
        """监控排除队列，将排除链接数据发送到UI"""
        try:
            while True:
                try:
                    # 从排除队列获取数据，设置超时以便能够响应取消
                    exclude_data = await asyncio.wait_for(self.exclude_queue.get(), timeout=1.0)
                    
                    # 如果收到None，表示爬虫已完成
                    if exclude_data is None:
                        break

                    # 处理排除链接消息
                    self.exclude_log_signal.emit(exclude_data)


                    # 标记排除队列任务已完成
                    self.exclude_queue.task_done()

                except asyncio.TimeoutError:
                    # 检查爬虫任务是否已完成
                    if self.crawler_task and self.crawler_task.done():
                        break
                    # 否则继续等待
                    continue

        except asyncio.CancelledError:
            self.log_signal.emit("DEBUG", "排除队列监控任务被取消", datetime.now().isoformat())
        except Exception as e:
            self.log_signal.emit(
                "ERROR",
                f"排除队列监控出错: {str(e)}",
                datetime.now().isoformat()
            )
        finally:
            self.log_signal.emit("INFO", "排除队列监控任务已结束", datetime.now().isoformat())


if __name__ == '__main__':
    start_url = "https://www.baidu.com"
    crawler_controller = CrawlerController()
    crawler_controller.start_crawler(start_url)
    
    # 等待爬虫线程完成
    print("[MAIN] 等待爬虫线程完成...")
    if hasattr(crawler_controller, 'crawler_thread') and crawler_controller.crawler_thread:
        crawler_controller.crawler_thread.join()
    print("[MAIN] 爬虫线程已完成，程序退出")
