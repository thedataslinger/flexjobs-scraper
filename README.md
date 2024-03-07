# FlexJobs.com Scraper

This Python library/project is a quick example of some basic web scraping from the popular jobs website [FlexJobs.com](https://flexjobs.com/).

I found myself snooping around the page source for a FlexJobs listing I'd come across a few weeks ago whilst looking for work. I was just about at my wit's-end trying to get the search engine multi-select filter to *actually* allow multiple selections whereupon I'd discovered that the web responses were also returning the results embedded as some pretty basic JSON.

Sooo... here we are.

I decided to throw together a small demo of scraping, parsing, and exporting search results to .csv. Once imported into a spreadsheet/datavis tool of your liking, I've found it a lot easier to weed-out jobs that—counter to FlexJobs' search form—were *not* relevant to my interests.

Another bonus: the job description is included in the JSON for each match found, so it's a bit easier to sift out jobs with matching titles but inapplicable hard skill(s) requirements.

## Paywall
>Note: this is not an #ad.

FlexJobs only exposes a very small amount of information to non-member accounts. You'll need to [grab a FlexJobs account](https://www.flexjobs.com/registration/signup) to pull information.

As of time of writing, I think there's a week-long trial if you want to check it out. Beyond that, you'll have to fork over about $20 USD/mo for their basic service (not a #ad, btw).

Once you've created an account and logged-in, find and save the URL-decoded `Auth` cookie from your browser since this authenticates you with the little data worker on the other end of the web requests.

## Requirements

This is written and tested on Python **3.10.0**.

Non-stanard libraries you'll have to grab:

```
pip install argparse
pip install pandas
pip install requests
pip install bs4
pip install fake_useragent
pip install pycountry
```

## Usage
You can get started right away by cloning the repo and firing off a command like:

```
python __main__.py -t <TOKEN> -k <KEYWORD> [, <KEYWORD> ...] -p <#>
```

There's some additional options/filters created for my own purposes that I've left in for others to play with at will. Get the full list of options via: 
```
python __main__.py --help
```

## Logging

Pff... no. The scope of this little script is much too small for me to need any kind of robust logging.

## Shout Out/Mention

Special thanks to [@lizTheDeveloper](https://github.com/lizTheDeveloper) for coaxing (and coaching) so many of us out from underneath the covers and back into the forray of job hunting. Would probably still be glue to my bed without your splendidly monotoned motivationals. 😃
