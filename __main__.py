#!/usr/bin/python3
# -*- coding: utf-8 -*-

# example invocation of script: python ./__main__.py -d "C:\\scratch\\" -p 3 -k "data engineer" -k "etl developer" -e 1850491 -e 1868281
import sys
sys.dont_write_bytecode = True
import argparse
import os.path as path
import get_flex_jobs

def check_path(p):
    _p = path.dirname(path.realpath(__file__)) if p is None else path.normpath(p)
    _p = f'{_p}\\' if path.isdir(_p) else '\\'
    return _p

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="__main__.py", description='This script is intended to initialize web scraping/parsing/filtering operations for job queries to FlexJobs.com, as abstracted in the separate "flexjobs.py" module.' )
    parser.add_argument("-t", "--auth_token", type=str, nargs="?", dest="token", help="(Required) Authorization token passed in requests cookies. Will check env for `FLEXJOB_AUTH` var if nothing passed")
    parser.add_argument("-d", "--working_dir", type=check_path,  nargs='?', const=True, default=check_path(None), help="(Optional) Default directory to which script will export optional data (e.g. html dumps)")
    parser.add_argument("-k", "--keyword", type=str, nargs="+", action="extend", dest="keywords", metavar="KEYWORD", help='(Required) Keyword(s) to use when searching for jobs; e.g.: "data engineer","ETL","ELT","data warehousing","data warehouse","sql developer","snowflake"')
    parser.add_argument("-p", "--max_pages", type=int, nargs="?", default=1, help="(Required; default=1) Maximum number of pages of results to aggregate (per search term)")  
    parser.add_argument("-e", "--skip", type=int, nargs="*", action="extend", dest="skip_list", help="(Optional) Will remove/exclude all job ids found in `skip_list`")
    parser.add_argument("-q", "--quiet", action='store_true', help="(Optional) Flag to specify whether to suppress printing extraneous info to stdout.")
    parser.add_argument("--alt_url", type=str, nargs="?", dest="base_url", help='(Optional) Instructs process to pass keyword search to a non-default url (e.g. when limiting searches to a location or candidate type)')
    parser.add_argument("--usa_only", action='store_true', dest="usa_only", help="(Optional) Instructs process to only look for jobs postings open to US Nationals")
    parser.add_argument("--random_agent", action='store_true', dest="random_agent", help="(Optional) Instructs requests.session to send a randomized User Agent in header to flexjobs, otherwise just specify Chromium")
    
    # TODO: implement option to save each resultset (per keyword searched) to individual files rather than all results for all keywords to one big .csv
    # parser.add_argument("--separate_by_keyword", action='store_true', help="Specify to output an individual results file per keyword, rather than outputting a single result set.")

    args = parser.parse_args()
    if args.base_url is None:
        args.base_url = "https://www.flexjobs.com/search?" if args.usa_only == True else "https://www.flexjobs.com/remote-jobs/USA/US-National?"

    get_flex_jobs.run(args)
