import re
import requests
from prettytable import PrettyTable
import time

# Insert your GitHub API username and access key below
USERNAME = ''
ACCESS_KEY = ''


def check_num_of_pages(link):
    if link is not None:
        link_last = [l for l in link.split(',') if 'rel="last"' in l]

        if len(link_last) > 0:
            pages_num = re.findall("page=[0-9]*&", link_last[0])[0]
            pages_num = int(str(pages_num).lstrip('page=').rstrip('&'))

        return pages_num + 1
    else:
        return 1


if __name__ == '__main__':
    # Insert name of the user you want to fetch data from
    user = 'finematte'

    repo_request = requests.get(f"https://api.github.com/users/{user}/repos", auth=(USERNAME, ACCESS_KEY),
                                params={'page': 1, 'per_page': 100})

    link = repo_request.headers.get('link', None)

    pages_num = check_num_of_pages(link)

    pages = list(range(1, pages_num + 1))

    all_repos = []
    all_final_repos = []

    for current_page in pages:
        repo_request = requests.get(f"https://api.github.com/users/{user}/repos", auth=(USERNAME, ACCESS_KEY),
                                    params={'page': current_page, 'per_page': 100}).json()

        for repo in repo_request:
            repo_name = repo['name']
            repo_size = repo['size']
            branch_name = repo['default_branch'] if repo['default_branch'] else '---'

            branch_request = requests.get(f"https://api.github.com/repos/{user}/{repo_name}/branches",
                                          auth=(USERNAME, ACCESS_KEY)).json()
            try:
                branch_protection = branch_request[0]['protected']
            except:
                branch_protection = '---'

            contributors_request = requests.get(f"https://api.github.com/repos/{user}/{repo_name}/contributors",
                                                auth=(USERNAME, ACCESS_KEY))

            link = contributors_request.headers.get('link', None)

            if not link:
                contributors_pages = 1
            else:
                link_last = [l for l in link.split(',') if 'rel="last"' in l]
                if len(link_last) > 0:
                    pages_num = re.findall("page=[0-9].*>|page=[0-9].*&", link_last[0])[0]
                    contributors_pages = int(str(pages_num).lstrip('page=').rstrip('&').rstrip('>'))

            all_repos.append([repo_name, repo_size, branch_name, branch_protection, contributors_pages])

    for repo in all_repos:
        repo_name = repo[0]
        repo_size = repo[1]
        branch_name = repo[2]
        branch_protection = repo[3]
        repo_pages = repo[4]

        contributors_num = 0

        for page in range(repo_pages):
            contributors_num_request = requests.get(f"https://api.github.com/repos/{user}/{repo_name}/contributors",
                                                    auth=(USERNAME, ACCESS_KEY),
                                                    params={'page': page, 'per_page': 100})

            if contributors_num_request.status_code != 204:
                contributors_num += len(contributors_num_request.json())
            else:
                break

        all_final_repos.append([repo_name, repo_size, contributors_num, branch_name, branch_protection])

    x = PrettyTable()

    x.field_names = ['Name', 'Size', 'Contributors Num', 'Branch Name', 'Protection']

    x.add_rows(all_final_repos)

    print(x)
