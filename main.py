import os
import time
import json
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from twisted.internet import reactor
from scrapy.utils.log import configure_logging
from spiders.GithubSpider import GithubSpider
import xlsxwriter
from pydriller import Git
from git import Repo
import shutil
from multiprocessing import Pool
import functools


REPO_COUNTER = 2
HEADERS = ["FirstName", "email", "Github Link",
           "No of Contributions", "Projects"]


def get_gitlog_data(data):
    data["first_name"] = ""
    data["email"] = ""
    if (len(data["user_commits"].items()) > 0):
        for k, v in data["user_commits"].items():
            print(f"***** STARTED CLONE REPO: {k} *****")
            # File name is the commit hash
            Repo.clone_from(k, v)
            gr = Git(v)
            print(f"***** FINISHED CLONE REPO: {k} *****")
            commit = gr.get_commit(v)
            if (commit.author):
                data["first_name"] = commit.author.name
                data["email"] = commit.author.email

                break
            shutil.rmtree(v)

        # Fail safe for the break
        if (os.path.exists(v)):
            shutil.rmtree(v)
        print(f"***** REMOVED CLONED REPO: {k} *****")
    return data


def create_excel_sheet(worksheet, parsed_info):
    # Write Headers
    row = 0
    worksheet.write_row(row, 0,  tuple(HEADERS))
    running = functools.partial(get_gitlog_data)
    with Pool(10) as p:
        parsed_info = p.map(running, parsed_info)

    for data in parsed_info:
        values_to_write = [data["first_name"], data["email"],
                           data["user_url"], data["no_of_contributions"]]
        values_to_write.extend(data["user_repositories"][:REPO_COUNTER])
        row += 1
        worksheet.write_row(row, 0,  tuple(values_to_write))


def clean_up_files(output_files):
    for f in output_files:
        os.remove(f"{f}.json")


def scrape_urls(output_files):
    print("*** STARTED SCRAPING URLS ***")

    configure_logging()
    process = CrawlerRunner()
    with open("urls.txt", "r") as url_file:
        for url in url_file.readlines():
            print (f"*** STARTED SCRAPING URL: {url} ***")
            url_split = [i.replace('\n', '') for i in url.split('/')]
            output_file_name = f"{url_split[-1]}_{url_split[-2]}"
            output_files.append(output_file_name)
            process.crawl(GithubSpider, parsing_url=url, file_name=output_file_name)
            time.sleep(1)
            print (f"*** FINISHED SCRAPING URL: {url} ***")
        deferred = process.join()
        deferred.addBoth(lambda _: reactor.stop())
        reactor.run() 

    print("*** FINISHED SCRAPING URLS ***")

def get_worksheet_name(name: str):
    if (len(name) > 30):
        return name[:31]
    return name

def main():
    print("*** STARTED GITHUB PROFILE PARSER ***")
    os.system("docker-compose up -d")
    time.sleep(5)
    start_timer = time.time()
    output_files = []
    scrape_urls(output_files)
    print("*** STARTED EXCEL FILE GENERATION ***")
    workbook = xlsxwriter.Workbook('github_parse.xlsx')
    for output_file in output_files:
        print(f"*** STARTED FILE {output_file} ***")
        with open(f"{output_file}.json", "r") as f:
            parsed_info = json.load(f)
            worksheet = workbook.add_worksheet(name=get_worksheet_name(output_file))
            create_excel_sheet(worksheet, parsed_info)
        print(f"*** FINISHED FILE {output_file} ***")
    workbook.close()
    print("*** FINISHED EXCEL FILE GENERATION ***")
    print("*** FINSHED GITHUB PROFILE PARSER ***")

    print("*** CLEANING UP DIRECTORY ***")
    # clean_up_files(output_files)

    time_taken = time.time() - start_timer
    print("** STATS **")
    print(f"TIME TAKEN: {time_taken}secs")
    print(f"URLs SCRAPED: {len(output_files)}")
    os.system("docker-compose down")


if (__name__ == "__main__"):
    main()
