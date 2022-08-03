import re
import requests
from prettytable import PrettyTable
import asyncio
import aiohttp
import itertools

# Insert your GitHub API username and access key below
USERNAME = ''
ACCESS_KEY = ''


async def get_repo_data(user, repo, session):
    repo_name = repo['name']
    repo_size = repo['size']
    branch_name = repo['default_branch'] if repo['default_branch'] else '---'

    async with session.get(f"https://api.github.com/repos/{user}/{repo_name}/branches",
                           auth=aiohttp.BasicAuth(USERNAME, ACCESS_KEY)) as response:
        try:
            response = await response.json()
            branch_protection = response[0]['protected']
        except:
            branch_protection = '---'

    async with session.get(f"https://api.github.com/repos/{user}/{repo_name}/contributors",
                           auth=aiohttp.BasicAuth(USERNAME, ACCESS_KEY)) as response:
        link = response.headers.get('link', None)

        if not link:
            contributors_pages = 1
        else:
            link_last = [l for l in link.split(',') if 'rel="last"' in l]

            if len(link_last) > 0:
                pages_num = re.findall("page=[0-9].*>|page=[0-9].*&", link_last[0])[0]
                contributors_pages = int(str(pages_num).lstrip('page=').rstrip('&').rstrip('>'))

    return [repo_name, repo_size, branch_name, branch_protection, contributors_pages]


async def get_repos(user, repos):
    async with aiohttp.ClientSession() as session:
        tasks = []

        for repo in repos:
            task = asyncio.ensure_future(get_repo_data(user, repo, session))
            tasks.append(task)

        response = await asyncio.gather(*tasks)

    return response


async def get_contributors_number(user, repo, contributors_pages, session):
    contributors_num = 0

    async with session.get(f"https://api.github.com/repos/{user}/{repo}/contributors", params={'page': contributors_pages},
                           auth=aiohttp.BasicAuth(USERNAME, ACCESS_KEY)) as response:

        if response.status == 200:
            if contributors_pages > 1:
                contributors_num = len(await response.json())
                contributors_num += (contributors_pages - 2) * 100
            else:
                contributors_num = len(await response.json())
        elif response.status == 204:
            contributors_num = 0
            return contributors_num
        else:
            return contributors_num

    return contributors_num


async def get_contributors(user, all_repos):
    async with aiohttp.ClientSession() as session:
        tasks = []

        for repo in all_repos:
            contributors_pages = repo[4]
            repo_name = repo[0]

            task = asyncio.ensure_future(get_contributors_number(user, repo_name, contributors_pages, session))
            tasks.append(task)

        response = await asyncio.gather(*tasks)

    return response


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
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Insert name of the user you want to fetch data from
    user = 'finematte'

    stop_requests = False

    repo_request = requests.get(f"https://api.github.com/users/{user}/repos", auth=(USERNAME, ACCESS_KEY),
                                params={'page': 1, 'per_page': 100})

    link = repo_request.headers.get('link', None)

    pages_num = check_num_of_pages(link)

    pages = list(range(1, pages_num + 1))

    temp_repos = []
    final_repos = []

    for current_page in pages:
        repo_request = requests.get(f"https://api.github.com/users/{user}/repos", auth=(USERNAME, ACCESS_KEY),
                                    params={'page': current_page, 'per_page': 100})

        if repo_request.status_code == 200:
            temp_repos.append(asyncio.run(get_repos(user, repo_request.json())))
        else:
            print('Error:\n', repo_request.json())
            stop_requests = True
            break

    if not stop_requests:
        all_repos = list(itertools.chain(*temp_repos))

        contributors_num = asyncio.run(get_contributors(user, all_repos))

        index = 0

        for repo in all_repos:
            repo_name = repo[0]
            repo_size = repo[1]
            branch_name = repo[2]
            branch_protection = repo[3]
            contributors_pages = contributors_num[index]

            del repo[-1]

            final_repos.append([repo_name, repo_size, contributors_num[index], branch_name, branch_protection])

            index += 1

        x = PrettyTable()

        x.field_names = ['Name', 'Size', 'Contributors Num', 'Branch Name', 'Protection']

        x.add_rows(final_repos)

        print(x)
