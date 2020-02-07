#!/usr/bin/env python
# encoding: utf-8
'''
@author: Annk Jack
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: jiaoank@mail2.sysu.edu.com
@software: pycharm
@file: contributionModel.py
@time: 2020/2/1 16:45
@desc: compute reviewers' (contribution)expertise in each code change.
@input: data file
@output: changeIdScore; type(changeIdScore) is dict, e.g.,
{
    "103683": {
        "1003981": [
            1.0,
            1.0,
            1.0
        ]
    },
    "103669": {
        "1010118": [
            0.75,
            0.5,
            1.0
        ],
        "1016743": [
            0.25,
            0.5,
            1.0
        ]
    }
}
'''

from datetime import datetime, date, timedelta
import pandas as pd
import json
from collections import OrderedDict

# inputFile is the data file
def expertise(inputFile):
    df = pd.read_csv(inputFile)
    changeIdCols = df["changeId"]
    ownerCols = df["owner"]
    tmpHisCols = df["reviewHistory"]
    changeIdScore = OrderedDict()# e.g., changeId：（reviewer：score）
    for index in range(len(tmpHisCols)):
        changeId= changeIdCols[index]
        ownerId = int(ownerCols[index])
        tmpHis = tmpHisCols[index]# this is a code change
        tmpHis = json.loads(tmpHis)
        # strore the three details
        idThreeDetails = {} # e.g., reviewid :(totalNum, workday, recentDay)
        idDays = {}
        for tmpHisOnce in tmpHis:
            id = int(tmpHisOnce["account_id"])
            day = tmpHisOnce["date"]
            dayTime = day.split(".")[0]
            date = day.split(" ")[0]
            datetimeObj = datetime.strptime(dayTime, "%Y-%m-%d %H:%M:%S")
            dateObj = datetime.strptime(date, "%Y-%m-%d")
            if ownerId == id:
                raise Exception("review histories contain owner!")
            if id not in idThreeDetails.keys():
                idThreeDetails[id] = [1, 0, datetimeObj]
                idDays[id] = [dateObj]
            else:
                tmp = idThreeDetails[id]
                times = tmp[0] +1
                idThreeDetails[id][0] = times
                if dateObj not in idDays[id]:
                    tmpDate =  idDays[id]
                    tmpDate.append(dateObj)
                #recent
                if datetimeObj>idThreeDetails[id][2]:#recent day
                    idThreeDetails[id][2] = datetimeObj
        for idItem in idDays.keys():
            dayNum = len(idDays[idItem])
            idThreeDetails[idItem][1] = dayNum
        #sum
        numTotal = 0.0
        dayTotal = 0.0
        recentDay = datetime.strptime("1990-01-01", "%Y-%m-%d") # initial value, set it an older day
        for value in idThreeDetails.values():
            numTotal = numTotal + value[0]
            dayTotal = dayTotal + value[1]
            if value[2] >recentDay:
                recentDay = value[2]
        reviewerIdScore = {}
        for key, value in idThreeDetails.items():
            # we define three specific metrics to quantify the contributions of reviewers.
            score1 = value[0]/numTotal
            score2 = value[1]/dayTotal
            score3 = (recentDay - value[2]).days
            if score3 ==0:
                score3 = 1.0
            else:
                score3 = 1.0/score3
            reviewerIdScore[key] = (score1, score2, score3)
        changeIdScore[str(changeId)] = reviewerIdScore
    return changeIdScore




