import os
from time import sleep

import requests as rc
import pandas as pd

game_table = {}
other = []
without_user_score = []
without_critic_score = []
without_year_of_release = []


# def score_getter(platform, soup):
#    span_tags = soup.body.find_all("a", {"class": "c-gamePlatformTile"})
#    for tag in span_tags:
#        title = str(tag.find('title'))
#        if title.__contains__(platform):
#        return tag.find("span").text


def get_connect_for_info(game):
    url_template = "https://internal-prod.apigee.fandom.net/v1/xapi/composer/metacritic/pages/games/" + game + "/web"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36'}
    response = None
    while response is None:
        try:
            response = rc.get(url_template, headers=headers)
        except (rc.exceptions.SSLError, rc.exceptions.ConnectionError):
            sleep(5)
    return response

def get_connect_for_user_score(game, platform):
    url_template = ("https://internal-prod.apigee.fandom.net/v1/xapi/reviews/metacritic/user/games/" + game +
                    "/platform/" + platform + "/stats/web?")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36'}
    response = None
    while response is None:
        try:
            response = rc.get(url_template, headers=headers)
        except (rc.exceptions.SSLError, rc.exceptions.ConnectionError):
            sleep(5)
    return response


def get_name_for_link(game):
    return game.lower().replace(" ", "-").replace(":", "").replace(".", "").replace(" + ", "-").replace("\"", "").replace("*", "")


def get_score_list(game_list_by_platform, platform_name):
    i = 0
    result = []
    while i != len(game_list_by_platform):
        game_name = get_name_for_link(game_list_by_platform['Name'].iloc[i])
        print(game_name)
        conn_info = get_connect_for_info(game_name)
        if conn_info.status_code == 404:
            tmp = {'Name': game_name, 'Platform': platform_name}
            other.append(tmp)
            i = i + 1
            continue

        rating = None
        release_year = None
        critic_score = None
        user_score = None

        try:
            data = conn_info.json()
            rating = data.get('components')[0].get('data').get('item').get('rating')
            platforms = data.get('components')[0].get('data').get('item').get('platforms')
            for platform in platforms:
                if platform.get('name') == platform_name:
                    if platform.get('releaseDate') is not None:
                        release_year = platform.get('releaseDate')[:4]
                    else:
                        tmp = {'Name': game_name, 'Platform': platform_name}
                        without_year_of_release.append(tmp)
                        i = i + 1
                        continue
                    critic_score = platform.get('criticScoreSummary').get('score')

        except AttributeError:
            tmp = {'Name': game_name, 'Platform': platform_name}
            without_critic_score.append(tmp)
            i = i + 1
            continue
        if critic_score is None:
            without_critic_score.append(game_name)

        conn_user_score = get_connect_for_user_score(game_name, get_name_for_link(platform_name))
        try:
            user_score = conn_user_score.json().get('data').get('item').get('score')

        except AttributeError:
            tmp = {'Name': game_name, 'Platform': platform_name}
            without_user_score.append(tmp)
            i = i + 1
            continue
        if critic_score is None:
            tmp = {'Name': game_name, 'Platform': platform_name}
            without_user_score.append(tmp)
            i = i + 1
            continue

        temp_dict = {'Name': game_list_by_platform['Name'].iloc[i], 'Platform': platform_name,
                     'Year_of_Release': release_year, 'Critic_Score': critic_score,
                     'User_Score': user_score, 'Rating': rating}
        result.append(temp_dict)
        i = i + 1
    return result


datasets = os.listdir("datasets")
for dataset in datasets:
    df_name = '.' + os.sep + 'datasets' + os.sep + dataset
    print(f"\n{dataset[:dataset.find('.')]}\n")
    list_score = get_score_list(pd.read_csv(df_name), dataset[:dataset.find(".")])
    pd.DataFrame(list_score).to_csv(df_name)
pd.DataFrame(other).to_csv("other_games.csv")
pd.DataFrame(without_critic_score).to_csv("without_critic_score.csv")
pd.DataFrame(without_user_score).to_csv("without_user_score.csv")
pd.DataFrame(without_year_of_release).to_csv("without_year_of_release.csv")
