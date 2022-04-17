import scrapy
from scrapy.http import HtmlResponse
from scrapy.loader import ItemLoader
from items import GithubCrawlerItem
import re

class GithubSpider(scrapy.Spider):
    name = "github"

    def start_requests(self):
        item = GithubCrawlerItem()
        with open("urls.txt", "r") as urls:
            for url in urls:
                item["github_repo_url"] = url
                yield scrapy.Request(url=_get_github_fork_url(url), callback=self.parse, meta = { "item": item })

    def parse(self, response: HtmlResponse):
        item = response.meta['item']
        for repo in response.css("div.repo"):
            user_name = repo.xpath("a[1][@data-hovercard-type='user']/@href").get()
            if (user_name):
                item["user_name"] = user_name.lstrip("/")
                yield scrapy.Request(_get_user_profile(user_name), callback=self.parse_user_profile, meta={ "item": item })
                break
    
    def parse_user_profile(self, response):
        item = response.meta['item']
        contribution_div = response.css("div.js-yearly-contributions")
        item["no_of_contributions"] = _clean_contributions_str(contribution_div.css("h2.f4.text-normal.mb-2::text").get())
        yield scrapy.Request(_get_user_repositories_url(item["user_name"]), callback=self.parse_user_repositories, meta={ "item": item })

    def parse_user_repositories(self, response):
        item = response.meta['item']
        repo_urls = []
        for repo in response.css("h3.wb-break-all"):
            repo_urls.append(repo.xpath("a/@href").get())
            item["user_repositories"] = repo_urls
        yield item

def _clean_contributions_str(no_of_contributions: str):
    return re.findall(r"\d+", no_of_contributions)[0]

def _get_user_repositories_url(user_name: str):
    return f"https://github.com/{user_name.lstrip('/')}?tab=repositories&q=&type=&language=&sort="

def _get_user_profile(user_name: str):
    return f"https://github.com/{user_name.lstrip('/')}"

def _get_github_fork_url(repo_url: str):
    return f"{repo_url.rstrip('/')}/network/members"
