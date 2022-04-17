import os


def main():
    os.system("scrapy crawl github -o parsed_github.json")

main()