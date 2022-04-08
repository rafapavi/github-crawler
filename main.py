import argparse
import requests
import csv
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repos", help="Repository names to fork")
    args = parser.parse_args()
    repos_to_check = args.repos.split(",")
    for i in repos_to_check:
        # repo_url https://github.com/wwcodekl/pyp-u1-c1-car-dealership
        split_url = i.split("/")
        user_logins = get_forks(split_url[-2], split_url[-1])
        write_to_csv(user_logins)

def get_forks(username, repo_name):
    users = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{username}/{repo_name}/forks?page={page}"
        print ("url", url)
        res = requests.get(url)
        data = res.json()
        if (type(data) != "list"):
            print (data)
        if (len(data) == 0):
            break
        users.extend([f["owner"] for f in data])
        page += 1
    return users
    

def write_to_csv(user_data):
    with open("saved_data.csv", "w") as f:
        writer = csv.writer(f)
        # Headers
        writer.writerow(["UserLogin", "Email", "Name"])

        for user in user_data:
            user_info = get_user_data(user["url"])
            if (not user_info):
                continue
            writer.writerow([user_info['login'], user_info['email'], user_info['name']])

def get_user_data(git_user_url):
    res = requests.get(git_user_url)
    data = res.json()
    return data

main()