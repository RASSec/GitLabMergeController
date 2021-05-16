#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys
import yaml
import os
import time
import json
import datetime
import consul

import pymysql
from string import Template

dirname, _ = os.path.split(os.path.abspath(__file__))
sys.path.append(dirname+"/../common_utils")

import email_utils as email_utils

def yaml_handler():
    current_path = os.path.abspath(os.path.dirname(__file__))
    with open(current_path + '/../config/common.yaml', 'r') as f: common = yaml.load(f.read())
    return common

def getYesterday():
    today=datetime.date.today()
    oneday=datetime.timedelta(days=1)
    yesterday=today-oneday
    return yesterday

class ReviewComment(object):
    def __init__(self, jira_id, mr_url, target):
        self.jira_id = jira_id
        self.mr_url = mr_url
        self.target = target
        self.comments= []
        self.changefiles=0
        self.additionlines=0
        self.deletelines=0
        self.mr_auther = "Unknow"

    def addComment(self,comment):
        self.comments.append(comment)

    def updateChangeStat(self, changefiles, additionlines, deletelines):
        self.changefiles=changefiles
        self.additionlines=additionlines
        self.deletelines=deletelines

    def setMRAuther(self,mr_auther):
        self.mr_auther=mr_auther

def aggReviewCommentsDaily():
    #1. Get current data, the format should like 2020-07-23
    #2, Based on step1 get the time duration like 2020-07-23 00:00:00 and 2020-07-23 24:00:00
    #3, Based on the time duration to create SQL
    #4, Based on SQL query result and parse result as ReviewComment obj
    #5, Based on ReviewComments array pass to sendDailyReportEmail and generate email content template and send out email
    #currentDate = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    yesterdayDate=getYesterday()
    #yesterdayDate = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    querySQL="select * from gitlab_merge_request_comment where comment_update_at > '"+str(yesterdayDate)+" 00:00:00' and comment_update_at < '"+str(yesterdayDate)+" 24:00:00'"
    print(querySQL)
    common = yaml_handler()
    devops_DataSource = common['dataSource']

    currentTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    #currentTime = "2020-07-22 17:12:40"
    dbconnection = pymysql.connect(devops_DataSource['host'], devops_DataSource['user'], devops_DataSource['password'],
                                   devops_DataSource['db'])
    dbcursor = dbconnection.cursor()

    dbcursor.execute(querySQL)
    dbconnection.commit()

    commentsSet=dbcursor.fetchall()

    mrCommentHash={}

    for comment in commentsSet:
        jira_id = comment[8] if comment[8] != "" else "Sync Code"
        mr_url = comment[2]
        target = comment[7]
        approver = comment[5]
        rawcontent = comment[6]
        content = approver + ": " + rawcontent

        if comment[2] not in mrCommentHash:
            _commentRecord = ReviewComment(jira_id,mr_url,target)
        else:
            _commentRecord = mrCommentHash[mr_url]

        _commentRecord.addComment(content)

        mrCommentHash[mr_url]=_commentRecord

    #here need to add logic go through mrCommentHash and based on mr_url to query table gitlab_merge_request_state to get the changefile / additionlines / deleteline


    for mr_url in mrCommentHash:
        queryChangeStatusSQL = "select mr_auther,changefiles,additionslines,deletelines from gitlab_merge_request_state where mr_url='"+mr_url+"'"
        dbcursor.execute(queryChangeStatusSQL)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(queryChangeStatusSQL)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        changeset = dbcursor.fetchone()
        _mrComment = mrCommentHash[mr_url]
        if changeset[1] !=None and changeset[2] !=None and changeset[3] !=None:
          print(changeset)
        # changefiles= changeset[0] if changeset[0] !=None else "0"
        # additionslines = changeset[1] if changeset[1] != None else "0"
        # deletelines = changeset[2] if changeset[2] != None else "0"

          _mrComment.updateChangeStat(int(changeset[1]),int(changeset[2]),int(changeset[3]))
        _mrComment.setMRAuther(changeset[0])
        mrCommentHash[mr_url]=_mrComment


    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(mrCommentHash)
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")

    dbconnection.close()

    sendDailyReportEmail(mrCommentHash)

def sendDailyReportEmail(mrCommentHash):
      yesterdayDate = getYesterday()
      #yesterdayDate = time.strftime('%Y-%m-%d', time.localtime(time.time()))
      contentStart = """
      <!DOCTYPE html>
      <html>
      <head>
      <meta charset="utf-8">
      <title>title</title>
      </head>
      <body>
      <p>
      Hi Teams <br>
      
        The following is the review comments summary for merge request be merged during  """+str(yesterdayDate)+""" 00:00:00 - """+str(yesterdayDate)+""" 24:00:00
      </p>
      """

      for mr_url in mrCommentHash:
          mrComments=mrCommentHash[mr_url]
          mrCommentTable = """
                      <br>
                      <table border="1" cellspacing="0"  >
                      <tr>
                        <td>JIRA_ID: <a href='"""+mrComments.mr_url+"""'>"""+mrComments.jira_id+"""</a> &nbsp&nbsp Target:"""+mrComments.target+"""</td>
                      </tr>
                      <tr>
                        <td>MR Auther: """+mrComments.mr_auther+"""</td>
                      </tr>
                      <tr>
                        <td>changefiles: """+str(mrComments.changefiles)+"""  &nbsp&nbsp  additionlines: """+str(mrComments.additionlines)+""" &nbsp&nbsp deletelines: """+str(mrComments.deletelines)+"""</td>
                      </tr>
                      <tr>
                      <td>
                          CommentList
                      </td>
                      </tr>
                     </table>
                     <br>
                     """
          mrCommentList=""
          for comment in mrComments.comments:
               commentlists="<li>"+comment+"</li>"
               mrCommentList=mrCommentList+commentlists

          mrCommentTable=mrCommentTable.replace("CommentList",mrCommentList)

          contentStart=contentStart+mrCommentTable

      contentEnd="""
      </body>
      </html>
      """

      emailContent = contentStart + contentEnd

      print(emailContent)

      try:
                email_utils.send_email("Review Comments Daily Summary", emailContent, ['dongjh1@lenovo.com','liudz4@lenovo.com','wangzl8@lenovo.com','kongyi1@lenovo.com','bixy2@lenovo.com'])
                #email_utils.send_email("Review Comments Daily Summary", emailContent, ['kongyi1@lenovo.com'])
      except Exception as e:
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "->sendFailCaseGroup: " + e)

if __name__ == "__main__":
    aggReviewCommentsDaily()