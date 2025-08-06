import configparser
import os
import re
import time
from threading import Lock
from typing import Dict, List, Pattern, Tuple
import yaml

class RegexMatcher:
    def __init__(self, yaml_file: str):
        self.patterns: Dict[str, Pattern] = {}
        # 如果传入的是相对路径，转换为基于config.py所在目录的绝对路径
        if not os.path.isabs(yaml_file):
            yaml_file = os.path.join(os.path.dirname(__file__), yaml_file)
        self.load_patterns(yaml_file)

    def load_patterns(self, yaml_file: str) -> None:
        """从YAML文件加载正则表达式并预编译"""
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for group in data.get('rules', []):
            if 'group' in group:
                tmp = self.patterns.setdefault(group["group"],{})
            if 'rule' in group:
                for rule in group['rule']:
                    pattern = re.compile(rule['f_regex'])
                    tmp[rule['name']] = pattern

    def find_matches(self, content: str) -> Dict[str, List[Tuple[str, str]]]:
        """在内容中查找所有匹配项，并记录每个匹配项对应的正则名"""
        results = {}
        exclude_results = {}

        for name, pattern in self.patterns["FindLink"].items():
            # start_time = time.time()
            matches = pattern.findall(content)
            # end_time = time.time()
            # print(name,end_time - start_time)
            for match in matches:
                # 如果匹配结果是元组列表，获取第一个元素
                match_str = match if isinstance(match, str) else match[0]
                results.setdefault(match_str,set()).add(name)

        # print(results)
        # 第二轮排除
        for match_str in list(results.keys()):
            for exclude_name, exclude_pattern in self.patterns["excludeLink"].items():
                if exclude_pattern.match(match_str):
                    del results[match_str]
                    exclude_results.setdefault(match_str,set()).add(exclude_name)
                    break

        return results,exclude_results

def loadParamData(config_path="paramdict.yml",ParamSwitch=False):
    if os.path.exists(config_path) and ParamSwitch:
        with open(config_path, "r", encoding="utf-8") as f:
            param_data = yaml.safe_load(f)
    else:
        param_data = None
    return param_data

def initialize_config(config_path="config.ini"):
    """初始化配置文件，若不存在则创建默认配置"""
    if not os.path.exists(config_path):
    # if True:
        create_default_config(config_path)
    config = configparser.RawConfigParser(allow_no_value=True)
    config.read("config.ini", encoding='utf-8')
    return config

def create_default_config(config_path):

    config = configparser.RawConfigParser(allow_no_value=True)
    """生成默认配置模板"""
    config['CRAWLER'] = {
        '# 最大爬取深度': None,
        'MaxDepth': 5,
        '# 最大失败重试次数': None,
        'MaxRetries': 3,
        '# 代理地址': None,
        'Proxies': 'http://127.0.0.1:8080',
        '# 代理地址开关': None,
        'ProxySwitch': False,
        '# 参数字典开关': None,
        'ParamSwitch': True,
        '# 扫描范围,*匹配所有': None,
        'SubDomain':'*.baidu.com'
    }
    config['REGEX'] = {
        '# 移除URL上下文': None,
        'RemoveUrlContext': '(https?://[^/]+)/[^/]+(/.*)'
    }
    config['EXTRACTOR']={
        '# 排除大文件后缀': None,
        'A':'.css,.png,.jpg,.ico,.jepg,.exe,.zip,.dmg,.pdf'
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)






class ConfigManager:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_config()
        return cls._instance
    
    def _init_config(self):
        """初始化配置"""
        if not os.path.exists("config.ini"):
            create_default_config("config.ini")
        self._config = configparser.RawConfigParser(allow_no_value=True)
        self._config.read("config.ini", encoding='utf-8')
        rules_path = os.path.join(os.path.dirname(__file__), 'rules.yml')
        self._matcher = RegexMatcher(rules_path)
        self._param_data = loadParamData(ParamSwitch=self.get_boolean('CRAWLER','ParamSwitch'))
    
    def get(self, section, option, default=None):
        """获取配置项"""
        return self._config.get(section, option, fallback=default)
    
    def get_boolean(self, section, option, default=False):
        """获取布尔值配置项"""
        return self._config.getboolean(section, option, fallback=default)
    
    def get_int(self, section, option, default=0):
        """获取整型配置项"""
        return self._config.getint(section, option, fallback=default)
    
    def set(self, section, option, value):
        """设置配置项"""
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, option, str(value))
        self._save_config()
    
    def remove_option(self, section, option):
        """删除配置项"""
        if self._config.has_section(section):
            self._config.remove_option(section, option)
            self._save_config()
    
    def _save_config(self):
        """保存配置到文件"""
        with open("config.ini", 'w', encoding='utf-8') as f:
            self._config.write(f)
    
    @property
    def matcher(self):
        """获取正则匹配器实例"""
        return self._matcher
    
    @property
    def param_data(self):
        """获取参数数据"""
        return self._param_data
    
    @property
    def crawler_max_depth(self):
        """获取爬虫最大深度"""
        return self.get_int('CRAWLER', 'MaxDepth', 5)
    
    @property
    def crawler_max_retries(self):
        """获取爬虫最大重试次数"""
        return self.get_int('CRAWLER', 'MaxRetries', 3)
    
    @property
    def crawler_sub_domain(self):
        """获取爬虫子域名"""
        return self.get('CRAWLER', 'SubDomain', '')
    
    @property
    def crawler_proxies(self):
        """获取爬虫代理设置"""
        return self.get('CRAWLER', 'Proxies', None)

    @property
    def crawler_proxy_switch(self):
        """获取爬虫代理设置"""
        return self.get_boolean('CRAWLER', 'ProxySwitch', False)


# 配置单例实例
config = ConfigManager()



