# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class GithubCrawlerItem(scrapy.Item):
    github_repo_url = scrapy.Field()
    user_name = scrapy.Field()
    no_of_contributions = scrapy.Field()
    user_repositories = scrapy.Field()
