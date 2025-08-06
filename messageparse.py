import json
import os.path
import re
from requests.structures import CaseInsensitiveDict


class message:

    headers = None

    body = None

    rex_pattern = None

    def __init__(self,message="message",reg=None):

        messageinfo = self.getmessageinfo(message)

        messageinfo = self.regularsubstitution(reg,messageinfo)

        self.headers,self.body = self.parse(messageinfo)

    def regularsubstitution(self,reg,message):

        if reg:
            for regex,replace in reg.items():
                message = re.compile(regex).sub(replace,message)
            return message
        else:

            return message




    def ismessagetext(self,message):

        http_methods = ('POST', 'GET', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS','HTTP')

        return message.startswith(http_methods)

    def getmessageinfo(self,message):
        if self.ismessagetext(message):
            return message

        # 如果是相对路径，转换为基于当前文件目录的绝对路径
        if not os.path.isabs(message):
            message = os.path.join(os.path.dirname(__file__), message)
            
        assert os.path.exists(message),"报文路径错误或内容解析异常: {}".format(message)
        with open(message,"r",encoding="utf-8")as file:
            messageinfo = file.read()
        return messageinfo


    def parse(self,messageinfo):


        if messageinfo is None:
            return None, None
        info_packets = messageinfo.split("\r\n\r\n") if "\r\n" in messageinfo else messageinfo.split("\n\n")

        if len(info_packets) == 1:
            info_packets.append(None)

        headers = self.getheaders(info_packets[0])
        body = self.getbody(info_packets[1])

        return headers,body



    def getheaders(self, headerstext):
        headers_lines = headerstext.strip().split('\n')  # 分割所有头部行
        # 移除第一行，它通常包含请求方法和路径
        headers_lines.pop(0)

        headers_dict = HttpCaseInsensitiveDict()
        for line in headers_lines:
            res = line.split(':', 1)
            if len(res) == 2:
                key, value = res[0], res[1]
                headers_dict[key.strip()] = value.strip()
            else:
                continue

        # if "Cookie" in headers_dict:
        #     headers_dict["Cookie"] = self.cookie
        # 删除body长度，防止发包时，长度不一致导致的异常

        keys_to_delete = [key for key in headers_dict if key.lower() == "content-length"]
        for key in keys_to_delete:
            del headers_dict[key]

        return headers_dict

    def getbody(self,body=None):
        if body:
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = body
        else:
            body = None

        return body

class HttpCaseInsensitiveDict(CaseInsensitiveDict):

    def __setitem__(self, key, value):
        if key.lower() in self._store:
            # 如果键已经存在，只更新值，保留原始键
            original_key, _ = self._store[key.lower()]
            self._store[key.lower()] = (original_key, value)
        else:
            # 如果键不存在，添加新的键值对
            self._store[key.lower()] = (key, value)
    def force_set(self, key, value):

        lower_key = key.lower()
        self._store[lower_key] = (key, value)


if __name__ == '__main__':


    with open("message", "r", encoding="utf-8") as file:
        messageinfo = file.read()

    cig = message("links.txt")
    print(cig.headers)