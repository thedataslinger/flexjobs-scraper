#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
sys.dont_write_bytecode = True
import requests, shutil, re, json, pandas, os, time
import pycountry
import urllib.parse as urlparse
from fake_useragent import UserAgent
from datetime import datetime
from inspect import indentsize
from bs4 import BeautifulSoup

class flexJobsAdapter:
    def __init__(self, auth_cookie:str, use_random_agent:bool=False, maximum_wait:int=15, base_url:str="https://www.flexjobs.com/search?"):
        self._flex_jobs_session = None
        self._auth_cookie = auth_cookie
        self._base_url = base_url
        self._user_agent = UserAgent().random if use_random_agent==True else UserAgent().chrome
        self._timeout = maximum_wait
        self._last_url_queried: str
        self._all_jobs_found = None
        self._last_jobs_found = None
        self._searched_terms = {}
        # TODO: rework to correctly construct CookieJar object (requests.cookies.cookiejar_from_dict; https://requests.readthedocs.io/en/latest/api/#api-cookies) 
        self._flex_jobs_cookies = { 
                                    'authsigninstate': '1', 
                                    'Auth': self._auth_cookie
                                  }
        self._flex_jobs_headers = { 
                                    'User-Agent':      self._user_agent,
                                    'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                    'Accept-Language': 'en-US,en;q=0.5',
                                    'Accept-Encoding': 'gzip,deflate',
                                    'Accept-Charset':  'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                                    'Connection':      'keep-alive',
                                    'Keep-Alive':      'timeout=5, max=300',
                                    'Pragma':          'no-cache',
                                    'Cache-Control':   'no-cache'
                                  }

        self._countries = self.get_world_countries()
        self._us_states = self.get_us_states()

        if (self._auth_cookie is None or self._auth_cookie == ""): raise ValueError("Need a user auth token to fully search job listings!.")
        self._flex_jobs_session = requests.Session()

    def __enter__(self): return self
    def __exit__(self, type, value, traceback):
        self._flex_jobs_session.close()

    # ------------------------------------------------------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------------------------------------------------------
    @property
    def last_searched_url(self): return self._last_url_queried
    @property
    def last_searched_content(self): return self._last_response_content
    @property
    def last_searched_status(self): return self._last_response_status
    @property
    def jobs_found(self): return self._all_jobs_found
    @property
    def last_searched_found(self): return self._last_jobs_found
    @property
    def searched_terms(self): return self._searched_terms
    
    # ------------------------------------------------------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------------------------------------------------------
    def get_results(self, page:int=1, search_term:str='data engineer'):
        
        _term = urlparse.quote(search_term)
        _url = f'{self._base_url}searchkeyword="{_term}"'
        _url = _url if page <= 1 else _url + f'&page={str(page)}'
        self._last_url_queried = _url
        
        try:
            # before starting new queries, remove ARRAffinity cookies; allows FlexJobs site to assign correct Azure worker id from their backend
            if page == 1:
                if 'ARRAffinity' in self._flex_jobs_cookies: del self._flex_jobs_cookies['ARRAffinity']
                if 'ARRAffinitySameSite' in self._flex_jobs_cookies: del self._flex_jobs_cookies['ARRAffinitySameSite']
            # grab the <search>.html page info              
            _response = self._flex_jobs_session.get(
                                                    _url, 
                                                    headers=self._flex_jobs_headers, 
                                                    cookies=self._flex_jobs_cookies, 
                                                    timeout=self._timeout
                                                    )
            self._last_response_status = _response.status_code

            # http response 200 => 'OK'
            if _response.status_code == 200:
                self._last_response_content = _response.content
                # re-add ARRAffinity cookies upon new query
                if page == 1:
                    if "Set-Cookie" in _response.headers:
                        # TODO: null2empty() is implicitly casting dict() type; this is clunky, rework this
                        set_cookies = null2empty(_response.headers["Set-Cookie"]).split(";")
                        for _cookie in set_cookies:
                            if _cookie.split("=")[0] == "ARRAffinity":
                                _arra = _cookie.split("=")[1]
                                self._flex_jobs_cookies["ARRAffinity"] = _arra
                                self._flex_jobs_cookies["ARRAffinitySameSite"] = _arra
            else:
                print(f'* Error fetching listings (response: {str(_response.status_code)} ({_response.reason})).')
                print(f'** Cookies:\n\n{_response.cookies}')
                print(f'** Header:\n\n{_response.headers}')
                self._flex_jobs_session.close()
                sys.exit(1)

        except requests.exceptions.Timeout:
            print('Error: request timed out.')
            self._flex_jobs_session.close()
            sys.exit(1)

        return _response.content

    def get_job(self, id:str=""):
        url = f'https://www.flexjobs.com/HostedJob.aspx?id={id}'
        try:
            _response = self._flex_jobs_session.post(url, cookies=self._flex_jobs_cookies, timeout=15)
            if _response.status_code != 200:
                print(f'* Error fetching individual listing (response: {str(_response.status_code)} ({_response.reason})).')
                return None
        except requests.exceptions.Timeout:
            print('Error: request timed out.')
            return None
        return _response.content
    
    def get_json(self, html, single_posting:bool=False):
        parsed_html = BeautifulSoup(html, 'html.parser')
        obj_string_content = parsed_html.body.find('script', attrs={'id': '__NEXT_DATA__'})
        obj_string_content = obj_string_content.string if obj_string_content is not None else ""
        if obj_string_content != "":
            results_json = json.loads(str(obj_string_content))
            results_json = results_json["props"]["pageProps"]["jobList"] if single_posting==True else results_json["props"]["pageProps"]["jobsData"]["jobs"]["results"]
        return results_json
    
    def get_world_countries(self):
        country_list = []
        for c in pycountry.countries: country_list.append(c.name)
        country_list = [re.sub(r'([ ])(\(.*)$', '', c) for c in country_list ]
        country_list.sort()
        del country_list[country_list.index('United States')]
        del country_list[country_list.index('United States Minor Outlying Islands')]
        return country_list

    def get_us_states(self):
        sd = [ x for x in pycountry.subdivisions if x.country_code == 'US' ]
        us_states = [ x.code.split('-')[-1] for x in sd ]
        us_states.sort()
        return us_states

    def parse_results(self, html, json, searched_keyword, searched_dttm, column_names:list):
        wait = lambda seconds : time.sleep(seconds)
        _jobs = {}
        for _col in column_names: _jobs[_col] = list()
        for job in json:
            job_id = int(job.get("id","0").strip())

            _jobs["searched_keywords"].append(searched_keyword)
            _jobs["searched"].append(searched_dttm)
            _jobs["url"].append(f'https://www.flexjobs.com/HostedJob.aspx?id={job_id}')

            _jobs["id"].append(str(job_id))
            _jobs["title"].append(job.get("title",""))
            _jobs["postedDate"].append(self.scrub_date(job.get("postedDate","2035-12-31T00:00:00Z")))
            _jobs["jobLocations"].append(";".join(job.get("jobLocations",[])))
            _jobs["allowedCandidateLocation"].append(";".join(job.get("allowedCandidateLocation",[])))
            _jobs["remoteOptions"].append(";".join(job.get("remoteOptions",[])))
            _jobs["jobSchedules"].append(";".join(job.get("jobSchedules",[])))
            _jobs["jobTypes"].append(";".join(job.get("jobTypes",[])))
            _jobs["featured"].append(job.get("featured","false"))
            _jobs["saved"].append(job.get("saved","false"))
            _jobs["slug"].append(job.get("slug",""))
            _jobs["createdOn"].append(self.scrub_date(job.get("createdOn","2035-12-31T00:00:00Z")))
            _jobs["expireOn"].append(self.scrub_date(job.get("expireOn","2035-12-31T00:00:00Z")))
            _jobs["salaryRange"].append(job.get("salaryRange",""))
            _jobs["applyJobStatus"].append(job.get("applyJobStatus",""))
            _jobs["jobBenefits"].append(";".join(job.get("jobBenefits",[])))
            _jobs["careerLevel"].append(";".join(job.get("careerLevel",[])))
            _jobs["travelRequired"].append(job.get("travelRequired",""))
            _jobs["states"].append(";".join(job.get("states",[])))
            _jobs["countries"].append(";".join(job.get("countries",[])))
            _jobs["cities"].append(";".join(job.get("cities",[])))
            _jobs["description"].append(job.get("description",""))
            _jobs["jobSummary"].append(job.get("jobSummary",""))

            _locations = ", ".join(job.get("allowedCandidateLocation",[]))
            _jobs["us-based"].append(str(bool2int(self.is_us_job(_locations))))

            # some company names missing in JSON data for some reason...
            if job.get("company",None) is not None: company_name = job.get("company").get("name", None)
            company_name = company_name if company_name is not None else self.get_job_attrib(html, job_id, 'h5', 'company-name-')
            if company_name is None or company_name == "":
                wait(1)
                r2 = self.get_job(id=job_id)
                j2 = self.get_json(html=r2, single_posting=True) if r2 is not None else None
                company_info = None if j2 is None else j2.get("company", None)
                if company_info is not None:
                    company_name = j2.get("company").get("name", None)
                    company_name = company_name if company_name is not None else j2.get("company").get("slug", None)
                    company_name = company_name if company_name is not None else self.get_job_attrib(html=r2, id=job_id, obj_type='h2', id_prefix=None)
                    company_name = null2empty(company_name)
                else: company_name = ""

            _jobs["company"].append(company_name)
            company_name = None
            company_info = None

        # scrub malformed/embedded linefeeds
        _jobs["description"] = [re.sub(r'[\r\n]','<br>', x) for x in _jobs["description"]]
        _jobs["jobSummary"] = [re.sub(r'[\r\n]','<br>', x) for x in _jobs["jobSummary"]]

        # decode unicode escape sequences
        _jobs["description"] = [x.encode('utf-8').decode('latin-1') for x in _jobs["description"]]
        _jobs["jobSummary"] = [x.encode('utf-8').decode('latin-1') for x in _jobs["jobSummary"]]
        _jobs["company"] = [x.encode('utf-8').decode('latin-1') for x in _jobs["company"]]

        _jobs["description"] = [re.sub(r'[\t]','\\\t', x) for x in _jobs["description"]]
        _jobs["jobSummary"] = [re.sub(r'[\t]','\\\t', x) for x in _jobs["jobSummary"]]

        return _jobs

    def query(self, keyword:str, max_pages:int=1, base_url:str=None):
        wait = lambda seconds : time.sleep(seconds)
        self._base_url = base_url if base_url is not None else self._base_url
        #TODO: need to devise better surrogate id (e.g. keyword+dttm) for self._searched_terms keys since same keyword can be searched via global vs US-National urls
        self._searched_terms[keyword] = self._base_url
        self._last_jobs_found = None
        _df1 = None
        _dttm = datetime.now().strftime("%Y-%m-%dT%H.%M.%S")
        _k = keyword
        _c = [ 'id', 'searched', 'url','title','searched_keywords','postedDate','jobLocations','allowedCandidateLocation','remoteOptions','jobSchedules','jobTypes','featured','company','saved','slug','createdOn','expireOn','salaryRange','applyJobStatus','jobBenefits','careerLevel','travelRequired','states','countries','cities','us-based','description','jobSummary' ]
        
        for page_num in range(1, max_pages+1, 1):
            wait(2)                                               # Rate limit queries like a polite little web scraper ;)
            _r = self.get_results(page=page_num, search_term=_k)  # Perform GET request for searched term  
            _j = self.get_json(html=_r, single_posting=False)     # Scoop out the json data from the bottom of the HTML response
            _d = self.parse_results(_r, _j, _k, _dttm, _c)        # Convert the json data into a dict (for loading into dataframe)

            _df1 = pandas.DataFrame(data=_d, dtype='string')
            if len(_df1.index) > 0:  #i.e. if at least 1 result found 
                self._last_jobs_found = _df1 if self._last_jobs_found is None else pandas.concat([_df1, self._last_jobs_found], sort=False)
            if len(_j) < 50: break  # i.e. skip checking for additional pages if there's no more results
        
        if _df1 is not None: del _df1
        if len(self._last_jobs_found) > 0: 
            self._all_jobs_found = self._last_jobs_found if self._all_jobs_found is None else pandas.concat([self._last_jobs_found, self._all_jobs_found], sort=False)

        # de-duplicate the current results, merge into all results, dedupe all results 
        if len(self._last_jobs_found.index) > 0:
            self._last_jobs_found.sort_values('id', ascending=True, inplace=True, na_position='first')
            self._last_jobs_found.drop_duplicates(subset='id', keep='first', inplace=True)
            self._all_jobs_found.sort_values('id', ascending=True, inplace=True, na_position='first')
            self._all_jobs_found.drop_duplicates(subset='id', keep='first', inplace=True)
        
        if self._last_jobs_found is None: return 0
        else: return len(self._last_jobs_found.index)

    def get_job_attrib(self, html, id:str="", obj_type:str='a', id_prefix:str=None):
        obj_id = id_prefix + id if id_prefix is not None else None
        parsed_html = BeautifulSoup(html, 'html.parser')
        obj_string_content = parsed_html.body.find(obj_type, attrs={'id': obj_id}) if obj_id is not None else parsed_html.body.find(obj_type)
        obj_string_content = obj_string_content.string if obj_string_content is not None else ""
        return obj_string_content

    def is_us_job(self, location:str=""):
        if re.match(r'^([A-Z]{2})$', location) and location in self._us_states: return True        # matches e.g. 'GA' or 'CT'
        if re.match(r'(.*)(Work from Anywhere)(.*)', location, flags=re.I): return True      # matches e.g. 'Work from Anywhere'
        if len(re.sub(r'(,)(\s+)',',',location).split(',')) == 2:
            if re.sub(r'(,)(\s+)',',',location).split(',')[1] in self._us_states: return True      # matches e.g. 'Miami, FL'
        if location in self._countries: return False                                            # matches e.g. 'Italy'
        if re.match(r'(.*)(US National)(.*)', location, flags=re.I): return True             # matches e.g. 'Canada, or US National'
        if re.match(r'([A-Z]{2},){2,}', location): return True                               # matches e.g. 'DC, FL, GA'
        if re.match(r'^(([\w\s]+)(,)(\s*))(\w{3,})$', location):                             # matches e.g. 'Florence, Italy'
            if re.split(r'\w+', location)[1] in self._countries:
                return False
        if re.match(r'^([^,]+)(, )([A-Z]{2})', location):                                    # matches e.g. 'Miami, FL'
            if re.sub(r'(,)(\s+)',',',location).split(',')[1] in self._us_states:
                return True
        return False
    def scrub_date(self, datetime_string:str='2035-12-31T00:00:00Z'):
        _d = '12/31/2035'
        try:
            _dt = datetime_string.split('T')[0] + ' ' + datetime_string.split('T')[1].strip('Z')
            _dt = datetime.strptime(_dt, '%Y-%m-%d %H:%M:%S')
            _dt = datetime.strftime(_dt, '%#m/%#d/%Y')
            _d = _dt
        except: pass
        return _d
    def drop_job(self, id):
        if self._last_jobs_found is not None:
            _dfmatch = self._last_jobs_found[self._last_jobs_found['id'] == str(id)].index
            self._last_jobs_found.drop(_dfmatch, inplace=True)
        if self._all_jobs_found is not None: 
            _dfmatch = self._all_jobs_found[self._all_jobs_found['id'] == str(id)].index
            self._all_jobs_found.drop(_dfmatch, inplace=True)
    def drop_non_usa(self):
        if self._last_jobs_found is not None: 
            _dfmatch = self._last_jobs_found[ (self._last_jobs_found["us-based"] == "0") ].index
            self._last_jobs_found.drop(_dfmatch, inplace=True)
        if self._all_jobs_found is not None:
            _dfmatch = self._all_jobs_found[ (self._all_jobs_found["us-based"] == "0") ].index
            self._all_jobs_found.drop(_dfmatch, inplace=True)
# ------------------------------------------------------------------------------------------------------------------
# Some utility functions
# ------------------------------------------------------------------------------------------------------------------
def bool2str(b):
    _b = ""
    if isinstance(b, bool):
        _b = "true" if b == True else "false"
    return _b
def bool2int(b):
    _b = None
    if isinstance(b, bool):
        _b = 1 if b == True else 0
    return _b
def str2bool(s:str=None):
    _s = None if s is None else s.lower()
    match _s:
        case _s if _s in ['true','1','t','y','yes','yeah','yup','certainly','uh-huh']: return True
        case _s if _s in ['false','-1','0','f','n','no','nah','nope','cap','uh-uh']: return False
        case _: return None
    return None
def null2empty(s:str=""):
    _s = "" if s is None else s
    return _s
