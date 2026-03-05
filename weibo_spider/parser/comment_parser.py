import logging
import random
import requests
import re
from time import sleep
from lxml.html import tostring
from lxml.html import fromstring
from lxml import etree
from .parser import Parser
from .util import handle_garbled, handle_html
from ..comment import Comment

logger = logging.getLogger('spider.comment_parser')


class CommentParser(Parser):
    def __init__(self, cookie, weibo_id):
        self.cookie = cookie
        self.url = 'https://weibo.cn/comment/' + weibo_id
        self.selector = handle_html(self.cookie, self.url)

    def get_long_weibo(self):
        """获取长原创微博"""
        try:
            for i in range(5):
                self.selector = handle_html(self.cookie, self.url)
                if self.selector is not None:
                    info_div = self.selector.xpath("//div[@class='c' and @id='M_']")[0]
                    info_span = info_div.xpath("//span[@class='ctt']")[0]
                    # 1. 获取 info_span 中的所有 HTML 代码作为字符串
                    html_string = etree.tostring(info_span, encoding='unicode', method='html')
                    # 2. 将 <br> 替换为 \n
                    html_string = html_string.replace('<br>', '\n')
                    # 3. 去掉所有 HTML 标签，但保留标签内的有效文本
                    new_content = fromstring(html_string).text_content()
                    # 4. 替换多个连续的 \n 为一个 \n
                    new_content = re.sub(r'\n+\s*', '\n', new_content)
                    weibo_content = handle_garbled(new_content)
                    if weibo_content is not None:
                        return weibo_content
                sleep(random.randint(6, 10))
        except Exception:
            logger.exception(u'网络出错')

    def get_long_retweet(self):
        """获取长转发微博"""
        return self.get_long_weibo()

    def get_video_page_url(self):
        """获取微博视频页面的链接"""
        video_url = ''
        try:
            self.selector = handle_html(self.cookie, self.url)
            if self.selector is not None:
                # 来自微博视频号的格式与普通格式不一致，不加 span 层级
                links = self.selector.xpath("body/div[@class='c' and @id][1]/div//a")
                for a in links:
                    if 'm.weibo.cn/s/video/show?object_id=' in a.xpath(
                            '@href')[0]:
                        video_url = a.xpath('@href')[0]
                        break
        except Exception:
            logger.exception(u'网络出错')

        return video_url

    def _get_page_num(self, selector):
        try:
            inputs = selector.xpath("//input[@name='mp']")
            if inputs:
                return int(inputs[0].attrib.get('value', '1'))
            return 1
        except Exception:
            return 1

    def _parse_comment_div(self, div, weibo_id):
        try:
            comment = Comment()
            comment.weibo_id = weibo_id
            cid = div.xpath("@id")
            if cid:
                comment.comment_id = cid[0]
            user_link = div.xpath("a[1]")
            if user_link:
                href = user_link[0].xpath("@href")[0]
                name = user_link[0].xpath("text()")[0] if user_link[0].xpath("text()") else ''
                comment.username = handle_garbled(name) if name else ''
                m = re.search(r'/(\d{4,})', href)
                if m:
                    comment.user_id = m.group(1)
            ctt = div.xpath("span[@class='ctt']")
            if ctt:
                html_string = etree.tostring(ctt[0], encoding='unicode', method='html').replace('<br>', '\n')
                new_content = fromstring(html_string).text_content()
                new_content = re.sub(r'\n+\s*', '\n', new_content)
                comment.content = handle_garbled(new_content)
            ct_span = div.xpath("span[@class='ct']")
            if ct_span:
                ct_text = handle_garbled(ct_span[0])
                publish_time = ct_text.split(u'来自')[0]
                publish_time = publish_time[:16]
                comment.publish_time = publish_time
            a_texts = div.xpath(".//a/text()")
            for t in reversed(a_texts):
                m = re.search(r'赞\[(\d+)\]', t)
                if m:
                    comment.up_num = int(m.group(1))
                    break
            return comment
        except Exception:
            return None

    def get_comments(self, weibo_id, max_pages=3):
        comments = []
        try:
            selector = handle_html(self.cookie, self.url)
            if selector is None:
                return comments
            total_pages = self._get_page_num(selector)
            pages = min(total_pages, max_pages)
            for page in range(1, pages + 1):
                url = self.url + "?page=%d" % page
                selector = handle_html(self.cookie, url)
                if selector is None:
                    continue
                divs = selector.xpath("//div[@class='c' and starts-with(@id,'C')]")
                for d in divs:
                    c = self._parse_comment_div(d, weibo_id)
                    if c and c.content:
                        comments.append(c)
                sleep(random.randint(2, 5))
        except Exception:
            logger.exception(u'网络出错')
        return comments
