import datetime
import logging
import os
import re
import subprocess
import time

from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument(r"--user-data-dir=/home/tgrining/.config/google-chrome")

handler = logging.getLogger()
handler.setLevel("INFO")
formatter = logging.Formatter("%(name)s - %(levelname)s - %(asctime)s - %(message)s")
ch = logging.StreamHandler()
ch.setLevel("INFO")
ch.setFormatter(formatter)
handler.addHandler(ch)


def get_file(now):
    with webdriver.Chrome(options=options) as driver:
        driver.get("https://discord.com/channels/850137217828388904/1014728928864243824")
        time.sleep(10)

        month = now.strftime("%B")
        day = int(now.strftime("%-d")) - 1
        last_tourney = re.findall(rf"Champion Tournament Results:  {month} {day} 2023[\s\S]*\"(.*.csv)", driver.page_source)

        if last_tourney:
            logging.info("got new results, downloading...")
            driver.get(last_tourney[0])
            time.sleep(5)
            return True
        else:
            return False


def sync_file(date):
    time.sleep(5)
    date = date - datetime.timedelta(days=1)

    if os.path.exists("/home/tgrining/Downloads/tourney_data.csv"):
        logging.info("copying results...")
        time.sleep(5)
        subprocess.run(f"mv /home/tgrining/Downloads/tourney_data.csv /home/tgrining/tourney/data/{date.isoformat()}.csv", shell=True)
        subprocess.run("rsync -azP ~/tourney hetzner:/", shell=True)
        subprocess.run("ssh hetzner 'systemctl restart streamlit'", shell=True)

        return True
    return False


def fire_message():
    pass


def download_and_sync():
    while True:
        now = datetime.datetime.now()
        date_now = now.date()

        correct_day_of_the_week = now.weekday() == 3 or now.weekday() == 6
        its_time = now.hour == 1 and now.minute >= 2

        if correct_day_of_the_week and its_time:
            downloaded = get_file(now)
            synced = sync_file(date_now)
            fire_message()

            if downloaded and synced:
                logging.info("downloaded and synced, bye bye")
                break
            logging.info("couldn't download or sync, trying again")
        else:
            logging.info("Too early. Sleeping...")
            time.sleep(100)


if __name__ == "__main__":
    download_and_sync()
