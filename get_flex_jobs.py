#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
sys.dont_write_bytecode = True
import argparse, shutil, pandas, os, time, subprocess
from datetime import datetime
from inspect import indentsize
import flexjobs

def clear(): 
    os.system('cls' if os.name == 'nt' else 'clear')
def goto_file(f:str):
    if os.name=='nt': subprocess.Popen(f'explorer /select,"{f}"')
def logmsg(msg:str=None, quiet:bool=False):
    null2empty = lambda s: "" if s is None else s
    if quiet==True or null2empty(msg)=="": return
    print(msg)
    return
def run(args):
    clear()
    time.sleep(1)
    _token = args.token if args.token is not None else os.getenv('FLEXJOBS_AUTH')
    _keywords = args.keywords
    _already_applied = args.skip_list if len(args.skip_list) > 0 else []
    page_count = args.max_pages

    with flexjobs.flexJobsAdapter(_token, use_random_agent=args.random_agent, maximum_wait=15, base_url=args.base_url) as fja:
        for _kw in _keywords:
            logmsg(f'\n╭ Querying FlexJobs for keyword(s): "{_kw}"', args.quiet)
            _results = fja.query(keyword=_kw, max_pages=page_count)
            logmsg(f'╰⎯⎯› {str(_results)} results found for "{_kw}"', args.quiet)
            for _id in _already_applied: fja.drop_job(_id)

            # TODO: implement logic for saving to separate files
            #if args.separate_by_keyword == True: pass
            
        _filename = os.path.abspath(os.path.join(os.path.normpath(args.working_dir), datetime.now().isoformat('T','seconds').replace(':', '.') + '_flexjobs.csv'))
        fja.jobs_found.to_csv(path_or_buf= _filename, sep='\t', header=True, index=False, mode='w', encoding='utf-8', compression=None)
        
    logmsg(f'\n***Finished scrape.***', args.quiet)
    goto_file(_filename)
    sys.exit(0)
    return
