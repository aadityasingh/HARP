import os
import pickle as pkl
import time

import requests
from tqdm import tqdm

from scraping.utils import all_year_contest_problem_map, total_problems


if __name__ == "__main__":
    os.makedirs('data/raw/aops_wiki', exist_ok=True)

    raw_save_path = 'data/raw/aops_wiki/{year}_{contest}_{number}.pkl'

    url_form = 'https://artofproblemsolving.com/wiki/index.php/{year}_{contest}_Problems/Problem_{number}'

    request_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0', 
                        'Accept-Encoding': 'gzip, deflate, br', 
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 
                        'Accept-Language': 'en-US,en;q=0.5',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1'}

    test_year_contest_problem_map = dict()

    # test_year_contest_problem_map[1990] = dict()
    # test_year_contest_problem_map[1990]['AIME'] = [1,2,3,4]

    # year_contest_problem_map = test_year_contest_problem_map
    year_contest_problem_map = all_year_contest_problem_map


    num_retries = 10
    num_failures = 0

    print("Scraping all files...")
    with tqdm(total=total_problems) as pbar:
        for y in year_contest_problem_map:
            for c in year_contest_problem_map[y]:
                for n in year_contest_problem_map[y][c]:
                    save_at = raw_save_path.format(year=y, contest=c, number=n)
                    if os.path.exists(save_at):
                        print("skipping year={year} contest={contest} number={number}".format(year=y, contest=c, number=n))
                        continue
                    for retry in range(num_retries):
                        try:
                            r = requests.get(url_form.format(year=y, contest=c, number=n), headers=request_headers)
                            break
                        except:
                            print('An error occurred. Waiting a minute then retrying {}'.format(retry), flush=True)
                            time.sleep(60)
                            continue
                    if retry == num_retries:
                        print('Failed at retrieving year={year} contest={contest} number={number}'.format(year=y, contest=c, number=n))
                        num_failures += 1
                    else:
                        with open(save_at, 'wb') as f:
                            pkl.dump(r, f)
                    time.sleep(2)
                    pbar.update(1)
    print("Done scraping all files")
    print("Failed scrape on {}/{} = {:.3f} files".format(num_failures, total_problems, num_failures/total_problems))

