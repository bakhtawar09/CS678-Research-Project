# CS678-Research-Project

This repository entails all our source files and project deliverables for the research project we did in CS 678 (Topics in Internet research).

## Instructions to run the scraper

```bash
usage: scrape.py [-h] [-t] [-n]

options:
  -h, --help          show this help message and exit
  -t, --trending      Scrape trending videos
  -n, --non-trending  Scrape non trending videos
```

First, Navigate to the InstallDriver class and modify the line 29 in the scrape.py file using any of the following acceptable os_type values:

- Mac OS: mac_arm64
- Ubuntu/ Server: linux64
- Windows: win32

```python
def install(self):
    return ChromeDriverManager(
        version='111.0.5563.64',  name='chromedriver', os_type='linux64', path=os.getcwd()
    ).install()
```

If you're using a different chrome version make sure to change that also. You can refer to chromedriver's website for this.

### Caution

Make sure to have `trending_videos.txt` file in your working directory before scraping non trending videos.

### Trending Scraper

To access the trending scraper, type the following in the terminal:

```bash
python scraper.py -t
```

### NonTrending Scraper

To access the scraper for non trending vidoes, type the following in the terminal:

```bash
python scraper.py -n
```
