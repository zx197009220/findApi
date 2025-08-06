## 异步爬取api，数据来源于响应包，同时将流量代理到burp suite，方便HaE进行分析
import asyncio
import json
import re
import time
from urllib.parse import urljoin,urlparse
from log import setup_logger
import httpx
from urllib3.util.retry import Retry
from httpx import RemoteProtocolError, ConnectError, ReadTimeout
from link_extractor import parse_links
from messageparse import message
from config import config
from datetime import datetime


loggerRequest = setup_logger('requestlog', 'requestlog.log')
# 去除url上下文
re_remove_url_context = re.compile(r"(https?://[^/]+)/[^/]+(/.*)")


url_completed = set()



gic = message()
headers = gic.headers
data = gic.body

async def network_request(request_queue, process_queue, method="get", ui_queue=None):
    """
    网络请求函数
    :param proxies: 代理配置，None表示不使用代理
    :param request_queue: 请求队列
    :param process_queue: 处理队列
    :param method: 请求方法
    :param ui_queue: UI队列，用于向UI发送网络请求状态和进度信息
    :return:
    """
    if method.lower() == "get":
        body = None
    else:
        body = data

    timeout_config = httpx.Timeout(
        connect=10.0,  # 连接超时 5s
        read=60.0,  # 读取超时 60s（根据文件大小调整）
        write=10.0,  # 发送超时 10s
        pool=20.0  # 连接池等待 15s
    )
    # 创建一个重试策略
    retries = Retry(
        total=config.crawler_max_retries,  # 最大重试次数
        backoff_factor=2,  # 重试间隔（秒）
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
        allowed_methods=["GET", "POST"],  # 允许重试的 HTTP 方法
    )


    # 防止同时发起过多请求导致服务端压力
    transport = httpx.AsyncHTTPTransport(retries=retries)
    proxies = config.crawler_proxies if config.crawler_proxy_switch else None
    async with httpx.AsyncClient(proxy=proxies, headers=headers, timeout=timeout_config, transport=transport, verify=False) as client:
        while True:
            url,urlProperty = await request_queue.get()
            if url is None:
                break  # 接收到 None 作为停止信号
            urlFuzz, depth,regex_names = urlProperty
            if len(depth.split(".")) > int(config.crawler_max_depth):
                continue
            if url in url_completed:
                request_queue.task_done()
                continue
            url_completed.add(url)
            host = urlparse(url).netloc
            timestamp = datetime.now().strftime("%m-%d %H:%M:%S")
            try:
                start_time = time.time()
                headers["host"] = host
                response = await client.request(method, url, headers=headers, json=body)

                if urlFuzz == "fuzz" and response.status_code in (404,500):
                    url = re_remove_url_context.sub(r"\1\2", url)
                    response = await client.request(method, url, headers=headers, json=body)

                if 302 == response.status_code:
                    url = response.headers.get("Location")
                    response = await client.request(method, url, headers=headers, json=body)
                
                # 记录日志
                loggerRequest.info(f"【{response.status_code}】【{depth}】【{urlFuzz}】: {url}")
                
                # 将网络请求状态发送到UI队列
                if ui_queue is not None:
                    ui_data = {
                        'timestamp': timestamp,
                        'status': response.status_code,
                        'url': url,
                        'depth': depth,
                        'type': urlFuzz,
                        'content_type': response.headers.get('Content-Type', 'unknown'),
                        'size': len(response.text),
                        'regex_names': regex_names,
                    }
                    await ui_queue.put(ui_data)
                
                await process_queue.put((response.text,url,depth))  # 存放(url, response_content)
            except RemoteProtocolError as rpe:
                loggerRequest.info(f"【服务器协议中断】：{rpe} {url}")  # 如连接被服务器主动关闭
                if ui_queue is not None:
                    await ui_queue.put({
                        'timestamp': timestamp,
                        'status': 'error',
                        'url': url,
                        'depth': depth,
                        'type': urlFuzz,
                        'regex_names': regex_names,
                        'error': f"服务器协议中断: {str(rpe)}"
                    })
            except ConnectError as ce:
                loggerRequest.info(f"【网络层异常】：{ce} {url}")  # 涵盖防火墙、DNS等问题
                if ui_queue is not None:
                    await ui_queue.put({
                        'timestamp': timestamp,
                        'status': 'error',
                        'url': url,
                        'depth': depth,
                        'type': urlFuzz,
                        'regex_names': regex_names,
                        'error': f"网络层异常: {str(ce)}"
                    })
            except ReadTimeout as ce:
                loggerRequest.info(f"【连接层异常】：{ce} {url}")  # 如服务器主动断开、防火墙拦截等（网页6）
                if ui_queue is not None:
                    await ui_queue.put({
                        'timestamp': timestamp,
                        'status': 'error',
                        'url': url,
                        'depth': depth,
                        'type': urlFuzz,
                        'regex_names': regex_names,
                        'error': f"连接层异常: {str(ce)}"
                    })
            except Exception as e:
                loggerRequest.info(f"【其他异常：】【{e}】{url}")
                if ui_queue is not None:
                    await ui_queue.put({
                        'timestamp': timestamp,
                        'status': 'error',
                        'url': url,
                        'depth': depth,
                        'type': urlFuzz,
                        'regex_names': regex_names,
                        'error': f"其他异常: {str(e)}"
                    })
            finally:
                request_queue.task_done()

        await request_queue.put((None, None))


async def content_processor(process_queue, request_queue, event, exclude_queue=None):
    """
    内容处理函数
    :param process_queue: 处理队列
    :param request_queue: 请求队列
    :param event: 事件
    :param exclude_queue: 排除队列，用于向UI发送排除链接信息
    :return:
    """
    while True:
        response_content, url, depth = await process_queue.get()
        if response_content is None:
            break  # 接收到 None 作为停止信号
        
        # 解析链接
        new_urls, exclude_matches = await parse_links(response_content, url, depth)
        event.set()


        
        # 处理排除的链接
        if exclude_matches and exclude_queue is not None:

            timestamp = datetime.now().strftime("%m-%d %H:%M:%S")
            for excluded_url, rules in exclude_matches.items():
                # 为每个规则创建一个排除日志条目
                for rule in rules:
                    await exclude_queue.put({
                        'timestamp': timestamp,
                        'rule': rule,
                        'link': excluded_url,
                        'source': url,
                        'parent_index': depth
                    })
        
        # 将新URL放回网络请求队列
        for new_url, urlProperty in new_urls.items():
            await request_queue.put((new_url, urlProperty))  # 将新 URL 放回网络请求队列
        
        process_queue.task_done()

    # 发送结束信号
    await process_queue.put((None, None, None))

async def monitor_queues(process_queue, request_queue,event):
    await event.wait()
    while True:
        if request_queue.empty() and process_queue.empty():
            empty_checks = 3
            while empty_checks:
                await asyncio.sleep(4)
                if request_queue.empty() and process_queue.empty():
                    empty_checks-=1
                else:
                    break
            if empty_checks == 0:
                await request_queue.put((None, None))
                await process_queue.put((None, None, None))
                print("Both queues are empty. Ending tasks.")
                break

        await asyncio.sleep(1)  # 短暂休眠后再次检查

async def main(start_url, method, ui_queue=None, exclude_queue=None, max_depth=None, timeout=None, user_agent=None, proxies=None):
    """
    爬虫主函数
    :param start_url: 起始URL或URL列表
    :param method: 请求方法
    :param ui_queue: UI队列，用于向UI发送网络请求状态和进度信息
    :param exclude_queue: 排除队列，用于向UI发送排除链接信息
    :param max_depth: 爬取深度，默认为None（使用配置文件中的值）
    :param timeout: 请求超时时间，默认为None（使用默认超时配置）
    :param user_agent: 用户代理，默认为None（使用默认用户代理）
    :param proxy: 代理服务器，默认为None（使用配置文件中的值）
    :return:
    """

    # 如果提供了timeout参数，更新timeout配置
    # 注意：这里没有直接修改timeout_config，因为它是在network_request函数内部定义的
    # 如果需要修改timeout，应该在network_request函数中添加相应的逻辑

    request_queue = asyncio.Queue()
    process_queue = asyncio.Queue()

    # 初始化队列和任务
    if isinstance(start_url,str):
        await request_queue.put((start_url,("source","1","N")))

    if isinstance(start_url,list):
        depth = 0
        for url in start_url:
            depth +=1
            await request_queue.put((url,("source",f"{depth}","N")))

    event = asyncio.Event()

    # 创建生产者任务，传递UI队列
    producer_task = [asyncio.create_task(network_request(request_queue, process_queue, method, ui_queue)) for _ in range(5)]

    # 创建消费者任务
    # 传递UI队列和排除队列给content_processor
    consumer_task = [asyncio.create_task(content_processor(process_queue, request_queue, event, exclude_queue)) for _ in range(3)]

    # 队列监控线程
    monitor = asyncio.create_task(monitor_queues(process_queue, request_queue,event))
    await asyncio.gather(*producer_task,*consumer_task,monitor)

    monitor.cancel()

def getstarturls(start_file,context=""):

    start_url = []
    domain = "https://gic.test.cgbchina.com.cn:1443"

    with open(start_file, "r", encoding='utf-8')as file:
        for line in file.readlines():
            line = line.rstrip('\n')
            if line.startswith("http"):
                start_url.append(line)
            else:
                line = context+"/"+line
                url = line.replace("//","/")
                start_url.append(urljoin(domain, url))
    return start_url



# 提供一个函数，供外部调用时创建并传递UI队列和排除队列
def run_crawler_with_ui_queue(start_url, result_queue=None, reset_state=True):
    """
    使用UI队列运行爬虫
    
    Args:
        start_url: 起始URL或URL列表，从UI传入
        result_queue: 结果队列，用于接收爬取结果
        reset_state: 是否重置爬虫状态，默认为True
        
    Returns:
        ui_queue: 包含爬虫数据的队列，格式为：
            {
                'status': 状态码或'error',
                'url': URL,
                'depth': 深度,
                'type': URL类型,
                'response_time': 响应时间（秒）,
                'content_type': 内容类型,
                'size': 响应大小（字节）,
                'error': 错误信息（如果有）
            }
        exclude_queue: 包含排除链接数据的队列，格式为：
            {
                'rule': 排除规则,
                'link': 被排除的链接,
                'source': 源URL,
                'parent_index': 父深度
            }
        crawler_task: 爬虫任务，可以用于等待爬虫完成
    """
    # 重置爬虫状态
    if reset_state:
        global url_completed
        url_completed = set()

    async def run_with_queue():
        ui_queue = asyncio.Queue()
        exclude_queue = asyncio.Queue()
        # 创建一个任务来运行主爬虫函数
        crawler_task = asyncio.create_task(main(
            start_url=start_url,
            method="GET",
            ui_queue=ui_queue,
            exclude_queue=exclude_queue
        ))
        # 返回队列和任务，让调用者可以从队列中获取数据并等待任务完成
        return ui_queue, exclude_queue, crawler_task

    # 返回协程，让调用者可以在自己的事件循环中运行
    return run_with_queue()
