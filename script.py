import time
from unittest import skip
import warnings
import json
import orjson
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
from collections import Counter
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
import os
import sys

mobile_emulation = {
    "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
    "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19",
}

# mobile_emulation = { "deviceName": "Nexus 6" }
# Removing Throttling
latencyInMilliseconds = 1
downloadLimitMbps = 17.9
uploadLimitMbps = 100

TIME_TO_SLEEP = float(2 / downloadLimitMbps)

warnings.filterwarnings("ignore", category=DeprecationWarning)
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
chrome_options.headless = False
error_list = []
auto_play_toggle = False


def most_frequent(List):
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]


def to_seconds(timestr):
    seconds = 0
    for part in timestr.split(":"):
        seconds = seconds * 60 + int(part, 10)
    return seconds


def accept_cookies(driver: webdriver.Chrome):
    for _ in range(3):
        driver.find_element(
            by=By.XPATH, value="/html/body/div[2]/ytm-consent-bump-v2-renderer/div/div[3]/ytm-button-renderer/button").click()
    driver.find_element(
        by=By.XPATH, value="/html/body/div[2]/ytm-consent-bump-v2-renderer/div/div[2]/div[3]/ytm-button-renderer[1]/button").click()


def enable_stats_for_nerds(driver):

    settings = driver.find_element_by_xpath(
        "/html/body/ytm-app/ytm-mobile-topbar-renderer/header/div/button[2]"
    )
    settings.click()

    playback_settings = driver.find_element_by_xpath(
        "/html/body/ytm-app/bottom-sheet-container/bottom-sheet-layout/div/div[2]/div/div/div/ytm-menu-item[3]"
    )
    playback_settings.click()

    try:
        stats_for_nerds = driver.find_element_by_xpath(
            "/html/body/div[2]/dialog/div[2]/ytm-menu-item[2]"
        )
        stats_for_nerds.click()
    except:
        try:
            stats_for_nerds = driver.execute_script(
                "document.getElementsByClassName('menu-item-button')[1].click()"
            )
        except Exception as e:
            raise e

    exit_dialog = driver.find_element_by_xpath(
        "/html/body/div[2]/dialog/div[3]/c3-material-button/button"
    )
    exit_dialog.click()


def start_playing_video(driver):
    player_state = driver.execute_script(
        "return document.getElementById('movie_player').getPlayerState()"
    )
    print("Player State: ", player_state)
    if player_state == 5:
        driver.execute_script(
            "document.getElementsByClassName('ytp-large-play-button ytp-button')[0].click()"
        )

    if player_state == 1:
        return


def play_video_if_not_playing(driver):

    player_state = driver.execute_script(
        "return document.getElementById('movie_player').getPlayerState()"
    )
    if player_state == 0:
        return

    if player_state == -1:
        driver.execute_script(
            "document.getElementsByClassName('video-stream html5-main-video')[0].play()"
        )
    if player_state != 1:
        driver.execute_script(
            "document.getElementsByClassName('video-stream html5-main-video')[0].play()"
        )


def record_ad_buffer(driver, movie_id):
    ad_playing = driver.execute_script(
        "return document.getElementsByClassName('ad-showing').length"
    )
    ad_buffer_list = {}
    ad_id = []
    ad_skippable = {}
    all_numbers = {}
    both_skippable = []
    skip_dur = []
    while ad_playing:
        ad_buffer = float(
            driver.execute_script(
                'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[10].children[1].textContent.split(" ")[1]'
            )
        )

        res = driver.execute_script(
            'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[2].children[1].textContent.replace(" ","").split("/")[0]'
        )

        current_time_retry = 0
        while current_time_retry < 10:
            try:
                ad_played = float(
                    driver.execute_script(
                        "return document.getElementsByClassName('video-stream html5-main-video')[0].currentTime"
                    )
                )
                break
            except:
                current_time_retry += 1

        try:
            ad_id_temp = driver.execute_script(
                'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[0].children[1].textContent.replace(" ","").split("/")[0]'
            )
            if str(ad_id_temp).strip() != str(movie_id).strip():
                if str(ad_id_temp).strip() not in ad_id:
                    ad_id.append(str(ad_id_temp).strip())
                    ad_skippable[str(ad_id_temp).strip()] = []
                    all_numbers[str(ad_id_temp).strip()] = []
                    ad_buffer_list[str(ad_id_temp).strip()] = []
        except:
            pass

        try:
            skip_duration = driver.execute_script(
                'return document.getElementsByClassName("ytp-ad-text ytp-ad-preview-text")[0].innerText'
            )
            numba = int(skip_duration.split(" ")[-1])
            if len(ad_id) == 1:
                all_numbers[ad_id[0]].append(numba)
            if len(ad_id) == 2:
                all_numbers[ad_id[1]].append(numba)
        except:
            if len(ad_id) == 1:
                all_numbers[ad_id[0]].append(-2)
            if len(ad_id) == 2:
                all_numbers[ad_id[1]].append(-2)

        ad_played_in_seconds = ad_played
        # Buffer, Seconds Played, Res
        if len(ad_id) == 1:
            ad_buffer_list[ad_id[0]].append(
                (ad_buffer, ad_played_in_seconds, res))
        if len(ad_id) == 2:
            ad_buffer_list[ad_id[1]].append(
                (ad_buffer, ad_played_in_seconds, res))

        ad_playing = driver.execute_script(
            "return document.getElementsByClassName('ad-showing').length"
        )
        skippable = int(driver.execute_script(
            "return document.getElementsByClassName('ytp-ad-skip-button-container').length"
        ))

        if len(ad_id) == 1:
            ad_skippable[ad_id[0]].append(skippable)
        if len(ad_id) == 2:
            ad_skippable[ad_id[1]].append(skippable)

        play_video_if_not_playing(driver)

    if len(ad_id) == 2:
        both_skippable = [most_frequent(
            ad_skippable[ad_id[0]]),  most_frequent(ad_skippable[ad_id[1]])]
        skip_dur = [max(all_numbers[ad_id[0]]), max(all_numbers[ad_id[1]])]

    if len(ad_id) == 1:
        both_skippable = [most_frequent(ad_skippable[ad_id[0]])]
        skip_dur = [max(all_numbers[ad_id[0]])]

    return ad_id, both_skippable, ad_buffer_list, skip_dur


def driver_code(driver, filename):
    with open(filename, "r") as f:
        list_of_urls = f.read().splitlines()

    for index, url in enumerate(list_of_urls):
        global error_list
        global auto_play_toggle
        video_info_details = {}
        ad_buffer_information = {}
        error_list = []
        unique_add_count = 0
        ad_just_played = False
        buffer_list = []
        actual_buffer_reads = []
        buffer_size_with_ad = []
        vid_res_at_each_second = []
        main_res_all = []
        previous_ad_id = url.split("=")[1]
        movie_id = url.split("=")[1]
        filename = str(filename)
        folder_name = filename.split('.')
        new_dir = "./" + str(folder_name[0]) + "-" + str(index + 1)

        driver.get(url)
        time.sleep(2)
        try:
            try:
                accept_cookies(driver)
            except:
                pass
            # Enable Stats
            retry_count = 0
            while retry_count < 5:
                try:
                    enable_stats_for_nerds(driver)
                    break
                except:
                    retry_count += 1

            # Start Playing Video
            start_playing_video(driver)

            # Check If ad played at start
            # time.sleep(TIME_TO_SLEEP)
            ad_playing = driver.execute_script(
                "return document.getElementsByClassName('ad-showing').length"
            )
            print("Playing Video: ", movie_id)

            video_duration_in_seconds = driver.execute_script(
                'return document.getElementById("movie_player").getDuration()'
            )

            Path(new_dir).mkdir(parents=False, exist_ok=True)

            video_playing = driver.execute_script(
                "return document.getElementById('movie_player').getPlayerState()"
            )

            ad_playing = driver.execute_script(
                "return document.getElementsByClassName('ad-showing').length"
            )

            # Turning off Autoplay
            if not auto_play_toggle:
                try:
                    driver.execute_script(
                        "document.getElementsByClassName('ytm-autonav-toggle-button-container')[0].click()"
                    )
                    auto_play_toggle = True
                except:
                    pass

            # Turning off Volumne.
            try:
                driver.execute_script(
                    "document.getElementsByClassName('video-stream html5-main-video')[0].volume=0"
                )
            except:
                pass

            while True:
                # time.sleep(0.5)
                play_video_if_not_playing(driver)
                video_playing = driver.execute_script(
                    "return document.getElementById('movie_player').getPlayerState()"
                )

                # time.sleep(0.5)
                ad_playing = driver.execute_script(
                    "return document.getElementsByClassName('ad-showing').length"
                )
                # time.sleep(0.5)
                video_played_in_seconds = driver.execute_script(
                    'return document.getElementById("movie_player").getCurrentTime()'
                )

                if ad_playing:
                    # Ad is being played
                    ad_just_played = True
                    print("Ad Playing")

                    ad_id_list, skippable, ad_buf_details, skip_duration = record_ad_buffer(
                        driver, movie_id
                    )

                    for ad_id in range(len(ad_id_list)):
                        if (str(ad_id_list[ad_id]).strip()) == "empty_video":
                            continue
                        if not (skippable[ad_id]):
                            skip_duration[ad_id] = 999

                        print(
                            "Ad ID: ",
                            ad_id_list[ad_id],
                            "Skippable? ",
                            skippable[ad_id],
                            " Skip Duration: ",
                            skip_duration[ad_id],
                        )

                        if (str(ad_id_list[ad_id]).strip()) != (str(movie_id).strip()):
                            if ad_id_list[ad_id] != previous_ad_id:
                                print("Ad id is: ", ad_id_list[ad_id])
                                previous_ad_id = ad_id_list[ad_id]

                            if len(actual_buffer_reads) >= 1:
                                buffer_size_with_ad.append(
                                    [
                                        ad_id_list[ad_id],
                                        actual_buffer_reads[-1],
                                        video_played_in_seconds,
                                    ]
                                )
                            else:
                                buffer_size_with_ad.append(
                                    [ad_id_list[ad_id], 0.0,
                                        video_played_in_seconds]
                                )
                            if ad_id_list[ad_id] not in video_info_details.keys():
                                unique_add_count += 1
                                video_info_details[ad_id_list[ad_id]] = {
                                    "Count": 1,
                                    "Skippable": skippable[ad_id],
                                    "SkipDuration": skip_duration[ad_id],
                                }
                                to_write = {
                                    "buffer": ad_buf_details[ad_id_list[ad_id]],
                                }
                                ad_buffer_information[ad_id_list[ad_id]
                                                      ] = to_write
                                print("Advertisement " +
                                      str(unique_add_count) + " Data collected.")

                            else:
                                current_value = video_info_details[ad_id_list[ad_id]]["Count"]
                                video_info_details[ad_id_list[ad_id]
                                                   ]["Count"] = current_value + 1

                                name = (
                                    ad_id_list[ad_id]
                                    + "_"
                                    + str(video_info_details[ad_id_list[ad_id]]["Count"])
                                )
                                to_write = {
                                    "buffer": ad_buf_details[ad_id_list[ad_id]],
                                }
                                ad_buffer_information[name] = to_write
                                print("Repeated Ad! Information Added!")

                elif video_playing == 0:
                    # Video has ended
                    file_dir = new_dir + "/stream_details.txt"
                    file_dir_two = new_dir + "/buffer_details.txt"
                    file_dir_three = new_dir + "/error_details.txt"
                    file_dir_four = new_dir + "/ResolutionChanges.txt"
                    file_dir_five = new_dir + "/BufferAdvert.txt"
                    file_dir_six = new_dir + "/AdvertBufferState.txt"
                    Main_res = max(main_res_all, key=main_res_all.count)
                    video_info_details["Main_Video"] = {
                        "Url": url,
                        "Total Duration": video_duration_in_seconds,
                        "UniqueAds": unique_add_count,
                        "Resolution": Main_res,
                    }
                    with open(file_dir, "wb+") as f:
                        f.write(orjson.dumps(video_info_details))

                    with open(file_dir_two, "wb+") as f:
                        f.write(orjson.dumps(actual_buffer_reads))

                    with open(file_dir_three, "wb+") as f:
                        f.write(orjson.dumps(error_list))

                    # with open(file_dir_four, "wb+") as f:
                    #     f.write(orjson.dumps(vid_res_at_each_second))

                    with open(file_dir_five, "wb+") as f:
                        f.write(orjson.dumps(buffer_size_with_ad))

                    with open(file_dir_six, "wb+") as f:
                        f.write(orjson.dumps(ad_buffer_information))
                    video_info_details = {}
                    unique_add_count = 0
                    print("Video Finished and details written to files!")
                    break
                else:
                    # Video is playing normally

                    # Record Resolution at each second
                    res = driver.execute_script(
                        'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[2].children[1].textContent.replace(" ","").split("/")[0]'
                    )

                    new_data_point = (res, video_played_in_seconds)
                    main_res_all.append(res)
                    vid_res_at_each_second.append(new_data_point)

                    # Get Current Buffer
                    current_buffer = float(
                        driver.execute_script(
                            'return document.getElementsByClassName("html5-video-info-panel-content")[0].children[10].children[1].textContent.split(" ")[1]'
                        )
                    )
                    # Actual Buffer
                    # [ID,Last Buffer Before Ad, How much video played when ad played, Buffer after ad finished]
                    if ad_just_played:
                        for i in range(len(buffer_size_with_ad)):
                            if len(buffer_size_with_ad[i]) <= 2:
                                buffer_size_with_ad[i].append(current_buffer)

                        ad_just_played = False

                    # Tuple (Buffer, Video Played in seconds timestamp)
                    actual_buffer_reads.append(
                        (current_buffer, video_played_in_seconds))
                    # Current Buffer/(Video Left)
                    try:
                        buffer_ratio = float(
                            current_buffer
                            / (video_duration_in_seconds - video_played_in_seconds)
                        )
                    except:
                        buffer_ratio = 0

                    buffer_list.append(buffer_ratio)
                    previous_ad_id = url.split("=")[1]
        except Exception as e:
            print(e)
            print("Error occured while collecting data! Moving to next video!")
            print("Video: ", url)
            with open("faultyVideos.txt", "a") as f:
                to_write = str(url) + "\n"
                f.write(to_write)

            continue


class Install:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_experimental_option(
            "mobileEmulation", mobile_emulation)
        self.chrome_options.set_capability(
            "loggingPrefs", {'performance': 'ALL'})

    def install(self):
        return ChromeDriverManager(
            # modify this as per the device you're using
            version='111.0.5563.64',  name='chromedriver',  os_type='linux64', path=os.getcwd()
        ).install()


chrome_opt = Install().chrome_options
chrome_ser = Install().install()
driver = webdriver.Chrome(service=ChromeService(
    executable_path=chrome_ser), options=chrome_opt)
filename = sys.argv[1]
driver_code(driver, filename)
driver.quit()
