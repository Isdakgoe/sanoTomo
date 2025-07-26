
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import requests
from bs4 import BeautifulSoup
import time
import json


def extract_team_name(soup):
    for c in ['H3', 'E3', 'M3', 'B3', 'F3', 'L3', 'G3', 'C3', 'S3', 'D3', 'T3', 'DB3']:
        span = soup.find('span', class_=c)
        if span:
            return span.text.strip()
    return ""


def extract_player_name(soup):
    for c in ['H2', 'E2', 'M2', 'B2', 'F2', 'L2', 'G2', 'C2', 'S2', 'D2', 'T2', 'DB2']:
        div = soup.find('div', class_=c)
        if div:
            span = div.find('span', style=lambda s: s and "font-size:24px" in s)
            if span:
                return span.text.strip()
    return ""


def extract_table_by_caption(soup, caption_title):
    tables = soup.find_all('table', class_='Base_P')
    for table in tables:
        caption = table.find('div', class_='Title')
        if caption and caption_title in caption.text:
            trs = table.find_all('tr')
            data_rows = [tr for tr in trs if tr.find('td')]
            row = []
            for tr in data_rows:
                row.extend([td.text.strip() for td in tr.find_all('td')])
            return row
    return []


# 作動時刻
def get_current_time():
    DIFF_JST_FROM_UTC = 9
    dt_now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    dt_now = dt_now.strftime('%Y/%m/%d %H:%M:%S')
    return dt_now


# データ設定
url_list_batter = [
    # パ・リーグ
    "https://nf3.sakura.ne.jp/Pacific/H/f/4_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/F/f/2_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/F/f/99_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/M/f/22_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/M/f/99_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/E/f/12_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/E/f/23_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/B/f/36_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/B/f/54_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/L/f/26_stat.htm",
    "https://nf3.sakura.ne.jp/Pacific/L/f/40_stat.htm",

    # # セリーグ
    # "https://nf3.sakura.ne.jp/Central/G/f/13_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/G/f/42_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/T/f/95_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/DB/f/3_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/C/f/61_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/C/f/95_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/S/f/13_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/S/f/25_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/D/f/4_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/D/f/24_stat.htm",
    # "https://nf3.sakura.ne.jp/Central/D/f/95_stat.htm",
]
url_list_pitcher = [
    # パ・リーグ
    " https://nf3.sakura.ne.jp/Pacific/H/p/35_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/H/p/54_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/H/p/63_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/F/p/37_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/F/p/45_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/F/p/96_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/M/p/42_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/M/p/54_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/M/p/97_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/E/p/15_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/E/p/20_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/E/p/89_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/B/p/00_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/B/p/42_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/B/p/59_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/L/p/45_stat.htm",
    " https://nf3.sakura.ne.jp/Pacific/L/p/56_stat.htm",

#     # セリーグ
#     "https://nf3.sakura.ne.jp/Central/G/p/29_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/G/p/33_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/G/p/49_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/G/p/92_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/T/p/00_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/T/p/20_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/T/p/42_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/T/p/99_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/DB/p/42_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/DB/p/62_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/DB/p/69_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/DB/p/96_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/C/p/42_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/C/p/68_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/S/p/11_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/S/p/39_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/S/p/58_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/D/p/52_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/D/p/91_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/D/p/93_stat.htm",
#     "https://nf3.sakura.ne.jp/Central/D/p/94_stat.htm",
]


def scraping(url):
    # 各ページへ
    res = requests.get(url)
    res.encoding = res.apparent_encoding  # 日本語ページの場合
    soup = BeautifulSoup(res.text, 'html.parser')
    time.sleep(3)

    # 球団名を抽出
    team_name = extract_team_name(soup)
    player_name = extract_player_name(soup)
    row1 = extract_table_by_caption(soup, "通算成績")
    row2 = extract_table_by_caption(soup, "通算成績(各種指標)")

    # 連結して1行にまとめる
    final_row = [get_current_time(), team_name, player_name] + row1 + row2
    print(final_row)
    return final_row


results_batter = [scraping(url) for url in url_list_batter]
results_pitcher = [scraping(url) for url in url_list_pitcher]


""" --- Google Spreadsheet出力部分 --- """
#  1. gspread認証
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# 2. シート指定
spreadsheet = client.open_by_key(os.environ['SHEET_ID'])
spreadsheet.worksheet("pitcher").append_rows(results_pitcher)
spreadsheet.worksheet("batter").append_rows(results_batter)
