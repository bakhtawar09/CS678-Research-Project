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
import subprocess
import argparse
import sys
import random
import json


class InstallPackages:
    def install_packages(self, packages) -> list:
        failed_packages = []
        for package in packages:
            try:
                subprocess.check_call(['pip', 'install', package])
            except subprocess.CalledProcessError:
                failed_packages.append(package)
        return failed_packages


class InstallDriver:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.set_capability(
            "loggingPrefs", {'performance': 'ALL'})

    def install(self):
        return ChromeDriverManager(
            version='111.0.5563.64',  name='chromedriver', os_type='linux64', path=os.getcwd()
        ).install()


class TrendingScraper(InstallDriver):
    def __init__(self):
        super().__init__()
        self.chrome_ser = InstallDriver().install()
        self.chrome_service = ChromeService(executable_path=self.chrome_ser)
        self.driver = webdriver.Chrome(
            service=self.chrome_service, options=self.chrome_options)
        self.SCROLL_NUMBER: int = 20
        self.final_videos = []
        self.trending_videos = []
        self.videos = {}
        self.videos_longer_than_hour = {}

    def __get_video_duration(self):
        return self.driver.execute_script(
            'return document.getElementById("movie_player").getDuration()'
        )

    def __sort_by_duration(self) -> float:
        for video in self.trending_videos:
            self.driver.get(video)
            time.sleep(2)
            try:
                duration = self.__get_video_duration()
                self.videos[video] = duration
                print(self.videos)
            except Exception as e:
                print(e)
                continue

        self.videos = dict(
            sorted(self.videos.items(), key=lambda item: item[1]))
        self.videos_longer_than_hour = {
            k: v for k, v in self.videos.items() if v > 3600.0}

        for video in self.videos_longer_than_hour:
            del self.videos[video]

        self.trending_videos = list(self.videos.keys())

    def __len__(self):
        return len(self.trending_videos)

    def __run(self):
        with open('trending_categories.txt', 'r') as file:
            lines = file.readlines()
            for link in lines:
                try:
                    self.trending_videos.append(self.__scrape(link))
                except Exception as e:
                    print(e)
                    continue

    def __scrape(self, url: str) -> None:
        self.driver.get(url)
        time.sleep(2)
        for i in range(self.SCROLL_NUMBER):
            html = self.driver.find_element(
                by=By.TAG_NAME, value='html')
            html.send_keys(Keys.PAGE_DOWN)
            videos = self.driver.find_elements(
                by=By.XPATH, value="//a[@href[contains(., 'watch?v=') and not(contains(., '&list=')) and not(contains(., 'channel')) and not(contains(., 'user')) and not(contains(., 'playlist'))  and not(contains(., 'shorts'))]]")
            videos = [video.get_attribute('href') for video in videos]
            self.final_videos.append(videos)
            print('Scroll number: ', i)

    def __process(self):
        self.trending_videos = list(itertools.chain(*self.final_videos))
        self.trending_videos = list(set(self.trending_videos))

    def __write_to_file(self):
        with open('trending_videos.txt', 'w') as file:
            for video in self.trending_videos:
                file.write('%s\n' % video)
        with open('trending_videos_longer_than_hour.txt', 'w') as file:
            videos = list(self.videos_longer_than_hour.keys())
            for video in videos:
                file.write('%s\n' % video)

    def __del__(self):
        self.driver.close()

    def main(self):
        self.__run()
        self.__process()
        self.__sort_by_duration()
        self.__write_to_file()
        print('Total videos without live videos: ', len(self))


class NonTrending(InstallDriver):
    def __init__(self):
        super().__init__()
        self.chrome_ser = InstallDriver().install()
        self.chrome_service = ChromeService(executable_path=self.chrome_ser)
        self.driver = webdriver.Chrome(
            service=self.chrome_service, options=self.chrome_options)
        self.SCROLL_NUMBER: int = 40
        self.URL = 'https://www.youtube.com/'
        self.list_videos = []
        self.homepage_videos = []
        self.videos = {}
        self.videos_longer_than_hour = {}

    def __get_video_duration(self):
        return self.driver.execute_script(
            'return document.getElementById("movie_player").getDuration()'
        )

    def __scrape(self):
        time.sleep(5)
        scroll_number: int = self.SCROLL_NUMBER
        for i in range(scroll_number):
            html = self.driver.find_element(
                by=By.TAG_NAME, value='html')
            html.send_keys(Keys.PAGE_DOWN)
            videos = self.driver.find_elements(
                by=By.XPATH, value="//a[@href[contains(., 'watch?v=') and not(contains(., '&list=')) and not(contains(., 'channel')) and not(contains(., 'user')) and not(contains(., 'playlist'))  and not(contains(., 'shorts'))]]")
            videos = [video.get_attribute('href') for video in videos]
            self.list_videos.append(videos)
            print('Scroll number: ', i)

    def __process(self):
        self.homepage_videos = list(itertools.chain(*self.list_videos))
        self.homepage_videos = list(set(self.homepage_videos))

    def __write_to_file(self):
        with open('non_trending.txt', 'w') as f:
            for item in self.homepage_videos:
                f.write("%s\n" % item)
        with open('non_trending_longer_than_hour.txt', 'w') as f:
            videos = list(self.videos_longer_than_hour.keys())
            for video in videos:
                f.write('%s\n' % video)

    def __len__(self):
        return len(self.homepage_videos)

    def __remove_trending(self):
        with open('non_trending.txt', 'r') as file:
            lines = file.readlines()
            self.homepage_videos = lines
        print('len of homepage videos before removing trending:',
              len(self.homepage_videos))
        with open('trending_videos.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line in self.homepage_videos:
                    self.homepage_videos.remove(line)
        print('after removing trending videos', len(self.homepage_videos))

    def __remove_live(self):
        print('removing live')
        for video in self.homepage_videos:
            print(f'video: {video}')
            self.driver.get(video)
            time.sleep(2)
            duration = self.__get_video_duration()
            print(f'duration: {duration}')
            self.videos[video] = duration  # for sorting later on
            try:
                live = self.driver.find_element(
                    by=By.XPATH, value="//*[@id=\"movie_player\"]/div[28]/div[2]/div[1]/div[1]/button/text()")
                print(f'live: {live}')
            except:
                pass

    def __sort_by_duration(self):
        self.videos = dict(
            sorted(self.videos.items(), key=lambda item: item[1]))
        self.videos_longer_than_hour = {
            k: v for k, v in self.videos.items() if v > 3600.0}

        # remove videos longer than an hour from self.videos
        for video in self.videos_longer_than_hour:
            del self.videos[video]

        self.homepage_videos = list(self.videos.keys())

    def __random_sample(self):
        if not os.path.exists('trending_videos.txt'):
            raise FileNotFoundError(
                'trending_videos.txt not found. Scrape trending videos first')
        if not os.path.exists('non_trending.txt'):
            raise FileNotFoundError(
                'non_trending.txt not found. Scrape non trending videos first')

        if os.stat('trending_videos.txt').st_size == 0:
            raise ValueError('trending_videos.txt is empty')
        if os.stat('non_trending.txt').st_size == 0:
            raise ValueError('non_trending.txt is empty')

        with open('trending_videos.txt', 'r') as file:
            trending = file.read().splitlines()
        with open('non_trending.txt', 'r') as file:
            non_trending = file.read().splitlines()
        trending = list(filter(None, trending))
        non_trending = list(filter(None, non_trending))
        size_trending = len(trending)
        random_sample = random.sample(non_trending, size_trending)
        with open('non_trending_random.txt', 'w') as file:
            for video in random_sample:
                file.write("%s\n" % video)

    def __del__(self):
        self.driver.quit()

    def main(self):
        if sys.argv[1] == '--random' or sys.argv[1] == '-r':
            self.__random_sample()
            return
        self.driver.get(self.URL)
        self.__scrape()
        self.__process()
        self.__write_to_file()
        self.__remove_trending()
        self.__remove_live()
        self.__sort_by_duration()
        print('Number of videos: ', len(self))
        self.__write_to_file()


class Install(InstallPackages):
    def __init__(self):
        super().__init__()

    def main(self):
        with open('packages.txt', 'r') as f:
            packages = f.read().splitlines()
        self.install_packages(packages)


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-i', '--install', help='Install packages', action='store_true')
        parser.add_argument(
            '-t', '--trending', help='Scrape trending videos', action='store_true')
        parser.add_argument(
            '-n', '--non-trending', help='Scrape non trending videos', action='store_true')
        parser.add_argument(
            '-r', '--random', help='Scrape random non trending videos', action='store_true')
        args = parser.parse_args()
        if args.install:
            Install().main()
        elif args.trending:
            TrendingScraper().main()
        elif args.non_trending:
            NonTrending().main()
        elif args.random:
            NonTrending().main()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        sys.exit(0)
