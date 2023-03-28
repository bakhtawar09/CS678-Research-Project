# !/usr/bin/python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import os
import time
import itertools
import argparse
import sys
import random
import json
from typing import *
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import WebDriverException


class InstallDriver:
    def __init__(self) -> None:
        self.chrome_options: Options = Options()
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.set_capability(
            "loggingPrefs", {'performance': 'ALL'})

    def install(self) -> str:
        # Install Chrome Driver
        try:
            return ChromeDriverManager(
                version='111.0.5563.64',  name='chromedriver', os_type='linux64', path=os.getcwd()
            ).install()
        except:
            raise Exception("Could not install Chrome Driver!")


class TrendingScraper(InstallDriver):
    def __init__(self) -> None:
        super().__init__()
        self.chrome_ser: str = InstallDriver().install()
        self.chrome_service: ChromeService = ChromeService(
            executable_path=self.chrome_ser)
        self.driver: webdriver.Chrome = webdriver.Chrome(
            service=self.chrome_service, options=self.chrome_options)
        self.SCROLL_NUMBER: int = 20
        self.final_videos: List[str] = []
        self.trending_videos: List[str] = []
        self.trending_videos_dict: Dict[str, float] = {}
        self.trending_videos_longer_than_hour: Dict[str, float] = {}
        self.trending_videos_shorter_than_hour: Dict[str, float] = {}

    def __get_video_duration(self) -> float:
        # Get the duration of the video in seconds
        try:
            return self.driver.execute_script(
                'return document.getElementById("movie_player").getDuration()'
            )
        except WebDriverException:
            return 0

    def __accept_cookies(self) -> float:
        try:
            self.driver.find_element(
                by=By.XPATH, value='/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/form[2]/div/div/button').click()
        except:
            pass

    def __categorize_by_duration(self) -> float:
        for video in self.trending_videos:
            try:
                self.driver.get(video)
                time.sleep(2)
                try:
                    self.driver.execute_script(
                        "document.getElementsByClassName('video-stream html5-main-video')[0].volume=0"
                    )
                    duration: float = 0.0
                    i = 0
                    while i < 10:
                        try:
                            duration = self.__get_video_duration()
                            if duration:
                                break
                        except:
                            i += 1
                    if not duration:
                        print(f'Could not get duration for video: {video}')
                        continue
                    print(f'Video: {video} | Duration: {duration}')
                    self.trending_videos_dict[video] = duration
                except Exception as e:
                    print(e)
                    continue
            except Exception as e:
                print(e)
                continue

        self.trending_videos_longer_than_hour = {
            k: v for k, v in self.trending_videos_dict.items() if v >= 3600.0}
        self.trending_videos_shorter_than_hour = {
            k: v for k, v in self.trending_videos_dict.items() if v < 3600.0}

        trending_longer_keys = list(
            self.trending_videos_longer_than_hour.keys())
        random.shuffle(trending_longer_keys)
        trending_longer_shuffled = {
            key: self.trending_videos_longer_than_hour[key] for key in trending_longer_keys}
        self.trending_videos_longer_than_hour = trending_longer_shuffled

        trending_shorter_keys = list(
            self.trending_videos_shorter_than_hour.keys())
        random.shuffle(trending_shorter_keys)
        trending_shorter_shuffled = {
            key: self.trending_videos_shorter_than_hour[key] for key in trending_shorter_keys}
        self.trending_videos_shorter_than_hour = trending_shorter_shuffled

    def __len__(self) -> int:
        return len(self.trending_videos_dict.keys())

    def __run(self) -> None:
        with open('trending_categories.txt', 'r') as file:
            lines: List[str] = file.readlines()
            for link in lines:
                try:
                    self.trending_videos.append(self.__scrape(link))
                except Exception as e:
                    print(e)
                    continue

    def __scrape(self, url: str) -> None:
        self.driver.get(url)
        time.sleep(2)
        try:
            self.__accept_cookies()
        except:
            pass
        time.sleep(2)
        for i in range(self.SCROLL_NUMBER):
            print('Scroll number: ', i)
            html: WebElement = self.driver.find_element(
                by=By.TAG_NAME, value='html')
            html.send_keys(Keys.PAGE_DOWN)
            videos: List[WebElement] = self.driver.find_elements(
                by=By.XPATH, value="//a[@href[contains(., 'watch?v=') and not(contains(., '&list=')) and not(contains(., 'channel')) and not(contains(., 'user')) and not(contains(., 'playlist'))  and not(contains(., 'shorts'))]]")
            videos = [video.get_attribute('href') for video in videos]
            self.final_videos.append(videos)

    def __process(self) -> None:
        self.trending_videos = list(itertools.chain(*self.final_videos))
        self.trending_videos = list(set(self.trending_videos))
        self.trending_videos = list(filter(None, self.trending_videos))
        if not self.trending_videos:
            raise Exception("Trending videos are not found")

    def __write_to_file(self) -> None:
        try:
            with open('trending_videos.txt', 'w') as file:
                for video in self.trending_videos:
                    file.write('%s\n' % video)
        except OSError as e:
            print('Could not open file: %s' % e)
        try:
            with open('trending_videos_longer_than_hour.txt', 'w') as file:
                videos = list(self.trending_videos_longer_than_hour.keys())
                for video in videos:
                    file.write('%s\n' % video)
        except OSError as e:
            print('Could not open file: %s' % e)
        try:
            with open('trending_videos_shorter_than_hour.txt', 'w') as file:
                videos = list(self.trending_videos_shorter_than_hour.keys())
                for video in videos:
                    file.write('%s\n' % video)
        except OSError as e:
            print('Could not open file: %s' % e)

    def __dump(self) -> None:
        try:
            with open('trending_videos_longer_than_hour.json', 'w') as file:
                json.dump(self.trending_videos_longer_than_hour,
                          file, indent=4)
        except Exception as e:
            print(f"Error: {e}")

        try:
            with open('trending_videos_shorter_than_hour.json', 'w') as file:
                json.dump(self.trending_videos_shorter_than_hour,
                          file, indent=4)
        except Exception as e:
            print(f"Error: {e}")

    def __del__(self) -> None:
        try:
            self.driver.close()
        except Exception:
            pass

    def main(self) -> None:
        self.__run()
        self.__process()
        self.__categorize_by_duration()
        self.__write_to_file()
        self.__dump()
        print('Total videos without live videos: ', len(self))


class NonTrending(TrendingScraper):
    def __init__(self):
        super().__init__()
        self.chrome_ser = InstallDriver().install()
        self.chrome_service = ChromeService(executable_path=self.chrome_ser)
        self.driver = webdriver.Chrome(
            service=self.chrome_service, options=self.chrome_options)
        self.SCROLL_NUMBER: int = 40
        self.URL: str = 'https://www.youtube.com/'
        self.list_videos: list = []
        self.homepage_videos: list = []
        self.random_sample: list = []
        self.max_duration_trending: float = 0.0
        self.nontrending_videos: Dict[str, float] = {}
        self.nontrending_videos_longer_than_hour: Dict[str, float] = {}
        self.nontrending_videos_shorter_than_hour: Dict[str, float] = {}
        self.nontrending_videos_shorter_than_max_duration: Dict[str, float] = {
        }

    def __get_video_duration(self) -> float:
        duration = self.driver.execute_script(
            'return document.getElementById("movie_player").getDuration()'
        )

        return duration

    def __accept_cookies_homepage(self):
        try:
            self.driver.find_element(
                by=By.XPATH, value="//*[@id=\"content\"]/div[2]/div[6]/div[1]/ytd-button-renderer[2]/yt-button-shape/button").click()
        except Exception:
            pass

    def __get_max_duration(self):
        with open('trending_videos_longer_than_hour.json', 'r') as file:
            trending_videos: dict = json.load(file)

        max_duration: float = 0.0
        for _, duration in trending_videos.items():
            if duration > max_duration:
                max_duration = duration

        self.max_duration_trending = max_duration

    def __scrape(self) -> None:
        time.sleep(5)
        scroll_number: int = self.SCROLL_NUMBER
        for i in range(scroll_number):
            html = self.driver.find_element(by=By.TAG_NAME, value='html')
            html.send_keys(Keys.PAGE_DOWN)
            videos = self.driver.find_elements(
                by=By.XPATH, value="//a[@href[contains(., 'watch?v=') and not(contains(., '&list=')) and not(contains(., 'channel')) and not(contains(., 'user')) and not(contains(., 'playlist'))  and not(contains(., 'shorts'))]]")
            videos = [video.get_attribute('href') for video in videos]
            self.list_videos.append(videos)
            print('Scroll number: ', i)

    def __process(self) -> None:
        self.homepage_videos = list(set(itertools.chain(*self.list_videos)))
        self.homepage_videos = [
            video
            for video in self.homepage_videos
            if video in self.homepage_videos
        ]

    def __write_to_file(self) -> None:
        videos_shorter_than_hour: List[str] = list(
            self.nontrending_videos_shorter_than_hour.keys())
        videos_shorter_than_max_duration: List[str] = list(
            self.nontrending_videos_shorter_than_max_duration.keys())
        self.__write_to_file_helper(
            videos_shorter_than_hour, 'non_trending_shorter_than_hour.txt')
        self.__write_to_file_helper(
            videos_shorter_than_max_duration, 'non_trending_shorter_than_max_duration.txt')

    def __write_to_file_helper(self, videos: List[str], file_name: str) -> None:
        try:
            with open(file_name, 'w') as f:
                for video in videos:
                    f.write('%s\n' % video)
        except:
            print("Error writing to file.")

    def __dump(self) -> None:
        try:
            with open('nontrending_videos_shorter_than_hour.json', 'w') as file:
                json.dump(self.nontrending_videos_shorter_than_hour,
                          file, indent=4)

            with open('nontrending_videos_shorter_than_max_duration.json', 'w') as file:
                json.dump(self.nontrending_videos_shorter_than_max_duration,
                          file, indent=4)
        except Exception as e:
            print(e)

    def __len__(self) -> int:
        return len(self.homepage_videos)

    def __remove_trending(self) -> None:
        try:
            with open('trending_videos.txt', 'r') as file:
                lines = file.readlines()
            for line in lines:
                if line in self.homepage_videos:
                    self.homepage_videos.remove(line)
        except FileNotFoundError as e:
            print('Could not open the file: ', e)
        except Exception as e:
            print(f'Unknown error: {e}')

    def __remove_live(self):  # remove live videos from the sample
        for video in self.random_sample:
            self.driver.get(video)
            time.sleep(3)
            try:
                self.driver.execute_script(
                    "document.getElementsByClassName('video-stream html5-main-video')[0].volume=0"
                )
                live: str = ""
                i = 0
                while i < 5:
                    try:
                        live = self.driver.execute_script(
                            "return document.getElementsByClassName(\"ytp-chrome-bottom\")[0].children[1].children[0].children[4].children[3].textContent")
                        if live:
                            break
                    except:
                        i += 1
                print(f'live: {live}')
                if live == 'Watch live stream':
                    print(f'Removing live video: {video}')
                    self.random_sample.remove(video)
                    print(
                        f'New sample size: {len(self.random_sample)}\n Continuing to next video!')
                    continue
                duration: float = 0.0
                i = 0
                while i < 5:
                    try:
                        duration = self.__get_video_duration()
                        if duration:
                            break
                    except:
                        i += 1
                if not duration:
                    print(f'Could not get duration for video: {video}')
                    continue
                # for sorting later on
                print(f'video: {video} | duration: {duration}')
                self.nontrending_videos[video] = duration
            except:
                pass

    def __categorize_by_duration(self) -> None:

        self.nontrending_videos_longer_than_hour = {
            k: v for k, v in self.nontrending_videos.items() if v >= 3600.0}
        self.nontrending_videos_shorter_than_hour = {
            k: v for k, v in self.nontrending_videos.items() if v < 3600.0}

        self.__get_max_duration()

        self.nontrending_videos_shorter_than_max_duration = dict(
            filter(lambda elem: elem[1] <= self.max_duration_trending, self.nontrending_videos_longer_than_hour.items()))

        nontrending_shorter_keys = list(
            self.nontrending_videos_shorter_than_hour.keys())
        random.shuffle(nontrending_shorter_keys)
        nontrending_shorter_shuffled = {
            key: self.nontrending_videos_shorter_than_hour[key] for key in nontrending_shorter_keys}
        self.nontrending_videos_shorter_than_hour = nontrending_shorter_shuffled

        nontrending_shorter_max_duration = list(
            self.nontrending_videos_shorter_than_max_duration.keys())
        random.shuffle(nontrending_shorter_max_duration)
        nontrending_shorter_max_duration_shuffled = {
            key: self.nontrending_videos_shorter_than_max_duration[key] for key in nontrending_shorter_max_duration}
        self.nontrending_videos_shorter_than_max_duration = nontrending_shorter_max_duration_shuffled

    def __random_sample(self) -> None:
        if not os.path.exists('trending_videos.txt'):
            raise FileNotFoundError(
                'trending_videos.txt not found. Scrape trending videos first')

        if os.stat('trending_videos.txt').st_size == 0:
            raise ValueError('trending_videos.txt is empty')

        with open('trending_videos.txt', 'r') as file:
            trending_videos = file.read().splitlines()

        # Choose a random sample of trending videos.
        if len(self.homepage_videos) < len(trending_videos):
            self.random_sample = self.homepage_videos
        else:
            self.random_sample = random.sample(
                self.homepage_videos, len(trending_videos))
        print(f'Length of random sample: {len(self.random_sample)}')

    def __prepare_dataset(self) -> None:
        self.__remove_trending()
        self.__random_sample()
        self.__remove_live()
        self.__categorize_by_duration()

        # total number of videos in self.videos_shorter_than_hour and self.videos_shorter_than_max_duration
        nontrending_total = len(self.nontrending_videos_shorter_than_hour.keys()) + \
            len(self.nontrending_videos_shorter_than_max_duration.keys())
        trending_total = len(self.trending_videos_shorter_than_hour.keys()) + \
            len(self.trending_videos_longer_than_hour.keys())
        if nontrending_total < trending_total:
            nontrending_videos_shorter_than_max_duration = dict(
                random.sample(self.nontrending_videos.items(), trending_total - nontrending_total))
            self.__get_max_duration()
            nontrending_videos_shorter_than_max_duration = {
                k: v for k, v in nontrending_videos_shorter_than_max_duration.items() if v <= self.max_duration_trending}
            self.nontrending_videos_shorter_than_max_duration = {
                **self.nontrending_videos_shorter_than_max_duration, **nontrending_videos_shorter_than_max_duration}

        self.__write_to_file()
        self.__dump()

    def __del__(self) -> None:
        self.driver.quit()

    def main(self) -> None:
        self.driver.get(self.URL)
        time.sleep(2)
        try:
            self.__accept_cookies_homepage()
        except:
            pass
        time.sleep(2)
        self.__scrape()
        self.__process()
        self.__prepare_dataset()


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-t', '--trending', help='Scrape trending videos', action='store_true')
        parser.add_argument(
            '-n', '--non-trending', help='Scrape non trending videos', action='store_true')
        args = parser.parse_args()
        if args.trending:
            TrendingScraper().main()
        elif args.non_trending:
            NonTrending().main()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        sys.exit(0)
