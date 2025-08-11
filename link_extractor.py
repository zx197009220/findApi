import re
from urllib.parse import urlparse, urljoin
import os
from config import ConfigManager

config = ConfigManager()
newline_pattern = re.compile(r'\n')

#正则排除Content-Type
#匹配=号参数，或者/:item类型参数
param_regex = re.compile(r'(\w+)=([\w]*)|/:(\w+)')
# 输入参数yd03
# param_data = {"redirectUri":"http://www.baidu.com","webViewUrl":"http://www.baidu.com","itemId": "119100100777004", "userId": "166053", "shopId": "2100191001", "orderId": "40538079003","reverseOrderId":"10535793001","urgeId": "1349044","id":"11","asid":"11","skuOrderId":"1111","code":"11","activityId":"111"}
param_dict = {}




async def parse_links(html_content,source_url,depth_Parent=0):
# def parse_links(html_content,source_url,depth_Parent=0):


    html_content = newline_pattern.sub('', html_content)




    # 查找匹配项
    matches,exclude_matches = config.matcher.find_matches(html_content)


    urls = {}

    depth_Child = 0
    for link, regex_names in matches.items():

        url,url_status= normalize_link(link,source_url)
        exclude_rule = is_exclusion_rules(url,url_status,source_url)
        if exclude_rule:
            exclude_matches.setdefault(url,set()).add(exclude_rule)
        else:
            url = fuzz(url, config.param_data)
            depth_Child += 1
            depth = f"{depth_Parent}.{depth_Child}"
            urlProperty = (url_status,depth,regex_names)
            urls.setdefault(url,urlProperty)

    return urls,exclude_matches


def get_extension(path):
    """从文件路径中提取扩展名"""
    _, ext = os.path.splitext(path)
    return ext

def is_subdomain(domain,subdomain):

    pattern = subdomain.replace(".",r"\.").replace("*",".*")
    return re.match(pattern, domain) is not None

def baseurl(source_url):

    url_parse = urlparse(source_url)
    return url_parse.scheme+"://"+url_parse.netloc

def add_context(link,source_url):

    url = urlparse(source_url)
    context = url.path.split("/")[1] if url.path != "" else ""

    link = link if link.startswith("/") else "/"+link
    path = re.sub(r'\./|\.\./', '', link)

    if context in path:
        # return context+link if link.startswith(("/herd","/design","/scripts")) else link
        return url.scheme+"://"+url.netloc+path
    else:
        return url.scheme+"://"+url.netloc+"/"+context+path

def is_exclusion_rules(url,url_status,source_url):
    # 解析链接
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    # 是否是目标域名
    if not is_subdomain(domain, config.crawler_sub_domain):
        return config.crawler_sub_domain

    # 获取链接的扩展名
    extension = get_extension(parsed_url.path)
    if extension.lower() in config.extractor_Suffix.split(","):
        return extension.lower()

    return False

def normalize_link(link,source_url):

    if link.startswith("http"):
        url_status = "source"
        url = link
    elif link.startswith("//"):
        url_status = "source"
        url = urlparse(source_url).scheme+":"+link
    else:
        url_status = "fuzz"
        url = add_context(link,source_url)

    return url, url_status





def param_count(param):
    param_dict.setdefault(param, 0)
    param_dict[param] += 1

def fuzz(url, data):
    # 合并后的正则表达式，匹配查询参数和路径参数
    # 匹配形式如 ?param1=value1&param2=value2 或 /:param1/value1/:param2/value2
    # 替换函数
    if data is None:
        return url
    def replacer(match):

        if match.group(2)=="":
            param_count(match.group(1))
        # 如果是查询参数或路径参数的键值对形式，如 ?param=value 或 /:param/value
        if match.group(1):  # 如 ?param=value
            return f"{match.group(1)}={data.get(match.group(1),match.group(2))}"
        # 如果是路径参数的形式，
        elif match.group(3):  # 如 /:param
            param_count(match.group(3))
            return f"/{data.get(match.group(3), ':' + match.group(3))}"
    return param_regex.sub(replacer, url)

if __name__ == '__main__':
    with open("20250508.js","r",encoding="utf-8")as f:
        content = f.read()

    parse_links(content,"https://necp-yd03.test.cgbchina.com.cn/assets/js/app-f075b844-835d2378794369d5f62d.js")
    exit()
