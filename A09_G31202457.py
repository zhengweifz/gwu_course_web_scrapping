# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 12:21:47 2015

@author: weizheng
"""
from bs4 import BeautifulSoup 
import requests as rq
import re
import pandas as pd
import matplotlib.pyplot as plt

def creat_link(topic, query_dict):
    """return a list links for each month given years
    """
    reg_link = "http://my.gwu.edu/mod/pws/" + topic + ".cfm?"
    qry_parts = [key + "=" + val for key, val in query_dict.iteritems()]
    qry_str = "&".join(qry_parts)
    return reg_link + qry_str
    
def get_subjects(query_dict):
    """return all subjects in a year as a list
    """
    term = query_dict["termId"]
    link = creat_link("subjects", query_dict)
    request = rq.get(link)
    soup = BeautifulSoup(request.text)
    re_ptn = "campId=1&termId=" + term #create a reg exp patten
    subject_links = soup.findAll(href=re.compile(re_ptn)) #get link with href match pattern 
    subjects = [sub["href"].split("=")[-1] for sub in subject_links]
    return subjects
    
def get_courses(term):
    """return all courses for a term as a df
    """
    query_dict = {
            "termId" : term,
            "campId" : "1"
        }
    subjects = get_subjects(query_dict)
    i = 0
    for sub in subjects:
        sub_qry_dict = query_dict.copy()
        sub_qry_dict["subjId"] = sub
        link = creat_link("courses", sub_qry_dict)
        if i == 0:
            df = get_data(sub, link)
        else:
            df = df.append(get_data(sub, link))
        i += 1
    return df
    
def get_data(sub, link):
    """return course data 
    """
    request = rq.get(link)
    soup  = BeautifulSoup(request.text)
    header = soup.find("tr",{"class": "tableHeaderFont"})
    tds = header.findAll("td")
    col_names = [td.getText().replace(" ", "").replace("/","_").replace(".","") for td in tds]
    col_names.pop() #get rid of find book columns
    data_rows = soup.findAll("tr",{"align":"center"})
    rows = []
    #get course data
    for tr in data_rows:
        tds = tr.findAll("td")
        data = [td.getText() for td in tds]
        data[2] = sub
        data.pop()
        data = tuple(data)
        rows.append(data)
    df = pd.DataFrame(rows, columns=col_names)
    return  df
    
def cal_prop(sp, top10_subs):
    """return open proportion 
    """
    sp_top10 = sp.ix[sp['SUBJECT'].isin( top10_subs),:] #subset top10
    sp_top10_gr = sp_top10.groupby('SUBJECT')
    sp_top10_gr_status = sp_top10_gr['STATUS']
    sp_top10_counts = sp_top10_gr_status.aggregate({"total": len, "open": lambda x: len(x[x=="OPEN"])})
    return sp_top10_counts['open'] / sp_top10_counts['total']
    
def main():
    sp14 = get_courses("201401")
    sp15 = get_courses("201501")
    sub_grs = sp14.groupby('SUBJECT')
    crs_cnts = sub_grs['COURSE'].count()
    crs_cnts.sort(inplace=True, ascending=False) 
    top10_subs = crs_cnts[:10].index.values #get top 10 subjects
    sp14_top10_prop = cal_prop(sp14, top10_subs)
    sp15_top10_prop = cal_prop(sp15, top10_subs)
    prop_df = pd.concat([sp14_top10_prop, sp15_top10_prop], axis=1)
    prop_df.columns = ['201401', '201501']
    prop_df.plot(kind="bar")
    plt.show()
    
if __name__== "__main__":
    main()