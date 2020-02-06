#!/usr/bin/env python
# encoding: utf-8
'''
@author: Annk Jack
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: jiaoank@mail2.sysu.edu.cn
@software: pycharm
@file: ccrrcs.py
@time: 2020/2/1 16:45
@desc: The main realization of ccrrcs
'''
from datetime import datetime, timedelta
from collections import OrderedDict
import json
import os
import pandas as pd
import numpy
import  collections
import random
import numpy as np
import time


    
class ccrrcs():
    def __init__(self, trainId, trainProject, trainFile, trainReviewerScore, trainEndTime,
                 testId, testOwnerId, testProject, testFile, testReviewer):#ordered 
        self.trainId = trainId
        self.trainProject = trainProject
        self.trainFile = trainFile
        self.trainReviewerScore = trainReviewerScore
        self.trainPath = self.extractPath(trainProject, trainFile)
        self.trainEndTime = trainEndTime

        self.testId = testId
        self.testOwnerId = testOwnerId
        self.testProject = testProject
        self.testFile = testFile
        self.testPath = self.extractPath(testProject, testFile)
        self.realTestReviewer = testReviewer

        self.__robust__()
    
    #check robust
    def __robust__(self):
        if len(self.testId) != len(self.testProject) or len(self.testId) != len(self.testPath) \
                or len(self.testId) != len(self.testPath):
            raise Exception("test number error!")
        if len(self.trainId) != len(self.trainProject) or len(self.trainId) != len(self.trainPath) \
                or len(self.trainId) != len(self.trainPath):
            raise Exception("train number error!")
    #four kinds path comparison techniques
    def __LCP__(self,f1, f2):
        common_path = 0
        min_length = min(len(f1), len(f2))
        for i in range(min_length):
            if f1[i] == f2[i]:
                common_path += 1
            else:
                break
        return common_path
    def __LCSuff__(self,f1, f2):
        common_path = 0
        r = range(min(len(f1), len(f2)))
        r.reverse()
        for i in r:
            if f1[i] == f2[i]:
                common_path += 1
            else:
                break
        return common_path
    def __LCSubstr__(self,f1, f2):
        common_path = 0
        if len(set(f1) & set(f2)) > 0:
            mat = [[0 for x in range(len(f2) + 1)] for x in range(len(f1) + 1)]
            for i in range(len(f1) + 1):
                for j in range(len(f2) + 1):
                    if i == 0 or j == 0:
                        mat[i][j] = 0
                    elif f1[i - 1] == f2[j - 1]:
                        mat[i][j] = mat[i - 1][j - 1] + 1
                        common_path = max(common_path, mat[i][j])
                    else:
                        mat[i][j] = 0
        return common_path
    def __LCSubseq__(self,f1, f2):
        if len(set(f1) & set(f2)) > 0:
            L = [[0 for x in range(len(f2) + 1)] for x in range(len(f1) + 1)]
            for i in range(len(f1) + 1):
                for j in range(len(f2) + 1):
                    if i == 0 or j == 0:
                        L[i][j] = 0
                    elif f1[i - 1] == f2[j - 1]:
                        L[i][j] = L[i - 1][j - 1] + 1
                    else:
                        L[i][j] = max(L[i - 1][j], L[i][j - 1])
            common_path = L[len(f1)][len(f2)]
        else:
            common_path = 0
        return common_path
        
    #freshness(time score)
    def __timeScore__(self, index):
        maxTime = max(self.trainEndTime)
        minTime = min(self.trainEndTime) +timedelta(days=-1)
        denominator = maxTime - minTime
        endTime = self.trainEndTime[index]
        timeScore = (endTime - minTime).total_seconds() / denominator.total_seconds()
        return timeScore
 
    #calculate the precision
    def __precision__(self, comNum, recomNum):
        if len(comNum) != len(recomNum):
            raise Exception("precision error！")
        precision = []
        for k in range(len(comNum)):
            p = float(comNum[k])/recomNum[k]
            precision.append(p)
        return precision
        
    #calculate the recall
    def __recall__(self, comNum, actualNum):
        if len(comNum) != 5:
            raise Exception("recall error！")
        recall = []
        for k in range(len(comNum)):
            r = float(comNum[k])/actualNum
            recall.append(r)
        return recall
        
    #calculate the MRR
    def __MRR__(self, recomReviewers, realReviewers):
        maxMRR = 0.0
        for realR in realReviewers:
            if realR not in recomReviewers:
                mrr = 0.0
            else:
                index = recomReviewers.index(realR)
                mrr = 1.0/(index+1)
                maxMRR = max(maxMRR, mrr)
        return maxMRR
        
    #calculate the F-score
    def __F_score__(self, precisionK, recallK):
        F_scoreA = []
        for i in xrange(len(precisionK)):
            precisioni = precisionK[i]
            recalli = recallK[i]
            if (precisioni + recalli) == 0:
                F_scorei = 0.0
            else:
                F_scorei = (2.0 * precisioni * recalli) / (precisioni + recalli)
            F_scoreA.append(F_scorei)
        return F_scoreA
    
    #obtain path 
    def extractPath(self, Project, File):
        pathTotal = []
        if len(Project) != len(File):
            raise Exception
        for index in range(len(Project)):
            pathOnce = []
            filei =  File[index]
            for f in filei:
                f = f.encode('unicode-escape').decode('string_escape')#change unicode into str
                fileiL = f.split('/')
                pathOnce.append(fileiL)
            pathTotal.append(pathOnce)
        return pathTotal
    
    # in order to obtain the better ratios(λ1, λ2, λ3), we use simulated annealing to get a better solution
    def Simulated_Annealing(self):
        global_xyz = collections.OrderedDict()
        global_xyzMrr = collections.OrderedDict()
        # initial temperature
        temperature = 99
        delta = 1 #set it by your value
        # The minimum temperature, you can set it by youself
        tmin = 1
        # initial ration of λ1, λ2, λ3; (st_x, st_y, st_z) on behalf of (λ1, λ2, λ3)
        st_x = random.randint(0, 100)/100
        st_y = random.randint(0, 100)/100
        st_z = random.randint(0, 100)/100
        bestValue, bestMRR = self.mainFun(st_x, st_y, st_z)
        global_xyz[(st_x,st_y,st_z)] = bestValue
        global_xyzMrr[(st_x,st_y,st_z)] = bestMRR
        while (temperature > tmin):
            #neighbor
            tmp_x = st_x + ((random.random() * 2 - 1) * temperature)/100
            tmp_y = st_y + ((random.random() * 2 - 1) * temperature)/100
            tmp_z = st_z + ((random.random() * 2 - 1) * temperature)/100
            if 1.0 > tmp_x >= 0.0 and 1.0 > tmp_y >= 0.0 and 1.0 > tmp_z >= 0.0:
                if (tmp_x, tmp_y, tmp_z) in global_xyz.keys():
                    continue
                value, MRR = self.mainFun(tmp_x, tmp_y, tmp_z)
                global_xyz[(tmp_x, tmp_y, tmp_z)] = value
                global_xyzMrr[(tmp_x, tmp_y, tmp_z)] = MRR
                if value <= bestValue:  # probability:pp
                    pp = 1 - 1.0 / (1.0 + np.exp(-(bestValue - value) * 1000 / temperature))
                    if random.random() < pp:
                        st_x = tmp_x
                        st_y = tmp_y
                        st_z = tmp_z
                else: #better than bestValue
                    st_x = tmp_x
                    st_y = tmp_y
                    st_z = tmp_z
                    bestValue = value
            else:
                continue
            temperature -= delta  
        
        tmpMaxF_score = max(global_xyz.values())
        tmpMaxF_scoreXYZ = [key for key in global_xyz.keys() if global_xyz[key] == tmpMaxF_score]
        tmpMaxMrr = max(global_xyzMrr.values())
        tmpMaxMrrXYZ = [key for key in global_xyzMrr.keys() if global_xyzMrr[key] == tmpMaxMrr]
        inter = list(set(tmpMaxF_scoreXYZ).intersection(set(tmpMaxMrrXYZ))) #the better λ1, λ2, λ3
        return tmpMaxF_scoreXYZ, tmpMaxMrrXYZ, inter

    def mainFun(self, ration1 = 1.0, ration2 = 1.0, ration3 = 1.0):
        self.clearAccuracy()
        testId = self.testId
        precisionKSum = [0.0] * 5
        recallKSum = [0.0] * 5
        F_scoreKSum = [0.0] *5
        MRRSum = 0.0
        for index in range(len(testId)):
            testIdOnce = testId[index]
            recomRList = self.computeSim(testIdOnce, ration1, ration2, ration3)#return recommend reviewers for testIdOnce
            precisionK, recallK, MRR, F_score= self.checkRusult(testIdOnce, recomRList)
            self.writeJson(testIdOnce, "precision", precisionK)
            self.writeJson(testIdOnce, "recall", recallK)
            self.writeJson(testIdOnce, "MRR", MRR)
            #sum
            for k in range(len(precisionK)):
                precisionKSum[k] = precisionKSum[k] + precisionK[k]
                recallKSum[k] = recallKSum[k] + recallK[k]
                F_scoreKSum[k] = F_scoreKSum[k] + F_score[k]
            MRRSum +=MRR
        #average
        precisionKMean = [p/float(len(testId)) for p in precisionKSum]
        recallKMean = [r/float(len(testId)) for r in recallKSum]
        MRRMean = MRRSum/float(len(testId))
        F_scoreKmean = [f/float(len(testId)) for f in F_scoreKSum]
        print "precision@1,2,3,5,10:\n",precisionKMean
        print "recall@1,2,3,5,10:\n", recallKMean
        print "MRR:\n", MRRMean
        return F_scoreKmean[0], MRRMean

    #create accuracy folder
    def clearAccuracy(self):
        path = "./accuracy/"
        if not os.path.isdir(path):
            os.mkdir(path)
        files = os.listdir(path)
        if len(files)!= 0:
            for f in files:
                os.remove(path+f)

    #accuracy folder is the output folder
    def writeJson(self, testId, filename, accuracy):
        accuracyDict = OrderedDict()
        with open("./accuracy/"+filename+".json", "ab") as f:
            if testId == None:
                testId = 99999#average score
            accuracyDict[int(testId)] = accuracy
            json.dump(accuracyDict, f, indent=4)
            f.close()
    
    #compute file path similarity; combinate similarity score, time score with contribution score(expertise)
    #ration1, ration2, ration3 are the initial ratios
    def computeSim(self,  changeId, ration1 = 1.0, ration2 = 1.0, ration3 =1.0):
        if changeId not in self.testId:
            raise Exception("ID error!")
        indexTest = self.testId.index(changeId)
        testPathi = self.testPath[indexTest]
        testOwnerId = self.testOwnerId[indexTest]
        testOwnerId = str(testOwnerId).decode('unicode-escape')#change into unicode
        simScore = {}
        for index in range(len(self.trainPath)):
            trainPathi = self.trainPath[index]
            timeScore = self.__timeScore__(index)#freshness of the code change, timeScore
            scoreOneMax = 0.0 #sum score
            for testPathiOnce in testPathi:  
                for trainPathiOnce in trainPathi:
                    maxNum = max(len(testPathiOnce), len(trainPathiOnce))
                    commonPathNum_LCP = self.__LCP__(testPathiOnce, trainPathiOnce)
                    commonPathNum_LCSuff = self.__LCSuff__(testPathiOnce, trainPathiOnce)
                    commonPathNum_LCSubstr = self.__LCSubstr__(testPathiOnce, trainPathiOnce)
                    commonPathNum_LCSubseq = self.__LCSubseq__(testPathiOnce, trainPathiOnce)
                    commonPathNum = max(commonPathNum_LCP, commonPathNum_LCSuff,
                                        commonPathNum_LCSubstr, commonPathNum_LCSubseq)
                    simOnce = commonPathNum/float(maxNum)
                    if simOnce > scoreOneMax: 
                        scoreOneMax = simOnce
            averScore = scoreOneMax #max score as average score
            #combine three score into one
            for reviewerId, expertScore in  self.trainReviewerScore[index].items():
                scoreTmp = (expertScore[0]*ration1)+(expertScore[1]*ration2)+(expertScore[2]*ration3)#变换比例值
                scoreUtl = scoreTmp*averScore * timeScore
                if reviewerId not in simScore.keys():
                    simScore[reviewerId] = scoreUtl
                else:
                    tmp = simScore[reviewerId]
                    simScore[reviewerId] = tmp + scoreUtl
        simScoreList = sorted(simScore.items(), key=lambda d: d[1], reverse=True)
        #del the owner, we don't recommend owner as its reviewer
        flagOwner = -1
        for i in range(len(simScoreList)):
            s = simScoreList[i]
            if testOwnerId in s:
                flagOwner = i
        if flagOwner != -1:
            del simScoreList[flagOwner]
        simScoreList = simScoreList[:10]# 10 ahead
        simRList = [sim[0] for sim in simScoreList]
        return simRList #ordered

    #check each recommended reviewers, calculate the precision, recall, MRR
    def checkRusult(self, testChangeId, recomRList):
        if testChangeId not in self.testId:
            raise Exception("test ID error!")
        indexTest = self.testId.index(testChangeId)
        realReviewers = self.realTestReviewer[indexTest]
        # compute the topK (k = 1,2,3,5,10)
        k1 = k2 = k3 = k5 = k10 = 0
        top10 = recomRList[:10]
        for i in range(len(top10)):
            topi = top10[i]
            if topi in realReviewers:
                if i < 1:
                    k1 +=1
                if i < 2:
                    k2 +=1
                if i < 3:
                    k3 +=1
                if i < 5:
                    k5 +=1
                if i < 10:
                    k10 +=1
        kComNum = (k1, k2, k3, k5, k10)
        recomNum = (1, 2, 3, 5, 10)
        actualNum = len(realReviewers)
        precisionK = self.__precision__(kComNum, recomNum)#[precision@1, precision@2, precision@3, precision@5, precision@10]
        recallK = self.__recall__(kComNum, actualNum)#[recall@1, recall@2, recall@3, recall@5, recall@10]
        MRR = self.__MRR__(top10, realReviewers)#float
        F_score = self.__F_score__(precisionK, recallK)
        return precisionK, recallK, MRR, F_score





