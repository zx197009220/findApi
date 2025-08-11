import logging

def setup_logger(name, log_file, level=logging.INFO,add_console_handler=True):
    """设置日志器，配置文件处理器和格式化器"""
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 配置文件处理器（显示时间）
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m-%d %H:%M')
    file_handler.setFormatter(file_formatter)
    # 添加处理器
    logger.addHandler(file_handler)

    if add_console_handler:
        # 配置控制台处理器（不显示时间）
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)

        # 添加处理器
        logger.addHandler(console_handler)

    return logger



if __name__ == '__main__':
    # 使用示例
    # 创建不同的日志器
    logger1 = setup_logger('Logger', 'app1.log')
    logger2 = setup_logger('Logger', 'app2.log')
    logger1.info("用户登录成功")
    logger1.error("文件读取失败")
    logger2.info("用户注册成功")
    logger2.warning("密码尝试次数过多")