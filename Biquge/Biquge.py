import os
import requests

from lxml import etree
from concurrent.futures import ThreadPoolExecutor


class Novel:
    def __init__(self):
        self.workers = 32
        self.headers = {
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/88.0.4324.150 Safari/537.36'
        }

    def get_text(self, expr, link, params=None):
        response = None
        for _ in range(3):
            try:
                response = requests.get(link, params, headers=self.headers, timeout=(5.0, 10.0))
                break
            except requests.exceptions.RequestException:
                pass
        if not response or response.status_code != 200:
            return []
        html = etree.HTML(response.text)
        text = html.xpath(expr)
        return text

    def get_data(self, info):
        text = self.get_text("//div[@id='content']/text()", info["link"])
        text[0] = "\u3000\u3000" + text[0].strip()
        text[-2] = "\u3000\u3000" + text[-2].strip()
        info["data"] = "\n".join(text[:-1])
        return info

    def get_mark(self, title):
        expr = "//div[@class='item']/dl/dt/a/@href"
        link = "https://www.biqugeu.net/searchbook.php"
        params = {"keyword": title}
        mark = self.get_text(expr, link, params)
        if not mark:
            return ""
        return str(mark[0])

    def get_info(self, mark):
        expr = "//div[@id='list']/dl/dd"
        link = "https://www.biqugeu.net" + mark
        info_list = self.get_text(expr, link)
        if not info_list or len(info_list) <= 12:
            return []
        info = []
        for i in info_list[12:]:
            link = str(i.xpath("./a/@href")[0])
            name = str(i.xpath("./a/text()")[0])
            info.append({"link": "https://www.biqugeu.net" + link, "name": name, "data": ""})
        return info

    def download(self, title):
        if not title:
            print("Error: 书名不能为空")
        mark = self.get_mark(title)
        if not mark:
            print("Error: 书名获取失败")
            return
        info = self.get_info(mark)
        if not info:
            print("Error: 章节获取失败")
            return
        if not os.path.exists("./Novel"):
            os.makedirs("./Novel")
        count = 1.0
        executor = ThreadPoolExecutor(max_workers=self.workers)
        with open(f"./Novel/《{title}》.txt", "w", encoding="utf-8") as f:
            pool = executor.map(self.get_data, info)
            for p in pool:
                f.write(p["name"] + "\n" + p["data"] + "\n\n")
                print(f"\rInfo: 《{title}》.txt 正在下载 - {int(count / len(info) * 100)}%", end="")
                count += 1.0
        executor.shutdown()
        print(f"\rInfo: 《{title}》.txt 下载完成", end="")
        print("\n")


if __name__ == '__main__':
    novel = Novel()
    while True:
        novel.download(input("请输入小说名："))
