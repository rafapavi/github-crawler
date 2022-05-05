import scrapy
from scrapy.http import HtmlResponse
from items import GithubCrawlerItem
import re


class GithubSpider(scrapy.Spider):
    name = "github"
    repo_counter = 0
    file_name = ''
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        "FEEDS": {
            './%(file_name)s.json': {
                'format': 'json'
            }
        },
        "DOWNLOADER_MIDDLEWARES": {
            # ...
            'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
            # ...
        },
        "ROTATING_PROXY_LIST_PATH": 'proxylist.txt'
    }

    def __init__(self, parsing_url=None, file_name = None, *args, **kwargs):
        super(GithubSpider, self).__init__(*args, **kwargs)
        self.parsing_url = parsing_url
        self.file_name = file_name


    def start_requests(self):
        item = GithubCrawlerItem()
        yield scrapy.Request(url=_get_github_fork_url(self.parsing_url), callback=self.parse, meta={"item": item.copy()})

    def parse(self, response: HtmlResponse):
        item = response.meta['item']
        counter = 0
        for repo in response.css("div.repo"):
            user_name = repo.xpath(
                "a[1][@data-hovercard-type='user']/@href").get()
            if (user_name):
                item["user_name"] = user_name.lstrip("/")
                item["user_url"] = _get_user_profile(user_name)
                yield scrapy.Request(item["user_url"], callback=self.parse_user_profile, meta={"item": item.copy()})
                counter += 1
                if (counter == 10):
                    break

    def parse_user_profile(self, response):
        item = response.meta['item']
        contribution_div = response.css("div.js-yearly-contributions")
        item["no_of_contributions"] = _clean_contributions_str(
            contribution_div.css("h2.f4.text-normal.mb-2::text").get())
        yield scrapy.Request(_get_user_repositories_url(item["user_name"]), callback=self.parse_user_repositories, meta={"item": item.copy()})

    def parse_user_repositories(self, response):
        item = response.meta['item']
        repo_urls = []
        for repo in response.css("h3.wb-break-all"):
            repo_urls.append(_get_full_repo_url(repo.xpath("a/@href").get()))

        item["user_repositories"] = repo_urls
        yield scrapy.Request(_get_github_commit_page(item["user_repositories"][0]), callback=self.parse_user_commits, meta={"item": item.copy(), "repo_counter": 0})

    def parse_user_commits(self, response):
        item = response.meta['item']
        repo_counter = response.meta['repo_counter']

        if (repo_counter == 0):
            item["user_commits"] = {}

        for commit in response.css("li.js-commits-list-item"):
            if (item["user_name"] in commit.css("a.commit-author.user-mention::text").extract()):
                item["user_commits"][item["user_repositories"][repo_counter]] = _get_commit_hash(commit.attrib["data-url"])
                break
        
        repo_counter += 1
        if (repo_counter < len(item["user_repositories"]) and len(item["user_commits"].keys()) == 0):
            yield scrapy.Request(_get_github_commit_page(item["user_repositories"][repo_counter]), callback=self.parse_user_commits, meta={"item": item.copy(), "repo_counter": repo_counter})
        else:
            yield item


def _get_commit_hash(commit_url: str):
    return commit_url.split("/")[-2]


def _clean_contributions_str(no_of_contributions: str):
    return re.findall(r"\d+", no_of_contributions)[0]


def _get_user_repositories_url(user_name: str):
    return f"https://github.com/{user_name.lstrip('/')}?tab=repositories&q=&type=&language=&sort="


def _get_user_profile(user_name: str):
    return f"https://github.com/{user_name.lstrip('/')}"


def _get_github_commit_page(repo_url: str):
    return f"{repo_url.rstrip('/')}/commits"


def _get_github_fork_url(repo_url: str):
    return f"{repo_url.rstrip('/')}/network/members"

def _get_full_repo_url(repo_url: str):
    return f"https://github.com/{repo_url.lstrip('/')}"
