#coding: utf-8
import uuid
import webob
import simplejson
import types
import os
import shelve
from webob.dec import wsgify
from NormalUtil import *
from DBUtil.UsingInstancesDBUtil import UsingInstancesDBUtil
from NovaUtil.TomcatInstanceUtil import TomcatInstanceUtil
from CeilometerUtil.SampleUtil import SampleUtil
from DBUtil.PerformanceDBUtil import PerformanceDBUtil

ipEndOfComputes = [50, 60, 70, 80, 210, 220, 230, 240]
ipEndOfController = 40

class Controller(object):


    def testAction(self, req):
        check = 1

        try:
            token = req.headers['X-Auth-Token']
            if token != 'sk':
                check = 0

        except KeyError:
            check = 0

        if check:
            return successResultJson('test data successfully!')
        else:
            return errorResultJson('you are not allowed to do this!')

    def clearSamples(self, req):
        check = 1

        try:
            token = req.headers['X-Auth-Token']
            if token != 'sk':
                check = 0

        except KeyError:
            check = 0

        if check:
            os.system('/home/sk/cloudEx/shellScript/clearSamples.sh > /dev/null')
            return successResultJson('clear meter data successfully!')
        else:
            return errorResultJson('you are not allowed to do this!')


    def changeUtilPeriod(self, req):
        period = req.params.get('period')
        windowSize = req.params.get('windowSize')

        if  not period or not windowSize or not isNumber(period) or not isNumber(windowSize):
            result = errorResultJson('The period and windowSize must be Int Number')
        else:
            period = int(period)
            windowSize = int(windowSize)
            if period % windowSize != 0:
                result = errorResultJson('The period must be exact divided by windowSize')
            else:
                interval = period / windowSize
                for ipEnd in ipEndOfComputes:
                    os.system('/home/sk/cloudEx/shellScript/changeCeilometerInterval.sh ' + str(ipEnd) + ' ' + str(period) + ' ' + str(windowSize) + ' > /dev/null')
                #os.system('/home/sk/cloudEx/shellScript/setTTL.sh ' + str(period))
                result = successResultJson('Change Util poll period and windowSize successfully')
        return result


    def getUtil(self, req):
        vmIdList = req.params.get('vmIdList')
        try:
            vmIdList = eval(vmIdList)
            result = {}
            for vmId in vmIdList:
                cpuUtilAVG = SampleUtil.getCpuUtilPeriodAVGByResourceId(vmId)
                memoryUtilAVG = SampleUtil.getMemoryUtilPeriodAVGByResourceId(vmId)
                result[vmId] = {'memory':memoryUtilAVG, 'cpu':cpuUtilAVG}
        except Exception:
            result = errorResultJson('The Post body must be vmIdList=["id1", "id2"]!')
        return result


    def create(self, req):
        rc = req.params.get('requireCount')
        resetFlag = req.params.get('reset')
        if rc and isNumber(rc) and resetFlag and isNumber(resetFlag):
            rc = int(rc)
            resetFlag = int(resetFlag)

            if resetFlag:
                TomcatInstanceUtil.resetAllUsingInstances()

            uic = UsingInstancesDBUtil.getUsingInstancesCount()
            if rc > uic:
                needC = rc - uic
                while needC > 0:
                    TomcatInstanceUtil.createTomcatInstance()
                    needC -= 1
            elif rc < uic:
                deleteC = uic - rc
                TomcatInstanceUtil.deleteSpecifyNumberInstances(deleteC)

            TomcatInstanceUtil.ensureAllUsingInstancesActive()
            return UsingInstancesDBUtil.getAllUsingInstancesInfo()
        else:
            result = errorResultJson('The Post Body Must be {requireCount:x, reset:y} (ps:x must be number, reset must be 0 or 1)')
        return result
    @wsgify(RequestClass=webob.Request)
    def __call__(self, req):
        arg_dict = req.environ['wsgiorg.routing_args'][1]
        action = arg_dict.pop('action')
        del arg_dict['controller']

        method = getattr(self, action)
        result = method(req, **arg_dict)

        if result is None:
            #返回Response的标准格式
            return webob.Response(body='',
                                  status='204 Not Found',
                                  headerlist=[('Content-Type',
                                               'application/json')])
        else:
            #test result type
            #f = open('debugLog.txt', 'a')
            #print >> f, type(result), '\n', result

            #函数返回的result是dict类型，通过调用simplejson.dumps(result)方法，最后转化为str类型返回
            if not isinstance(result, basestring):
                result = simplejson.dumps(result)
            #test result type
            #print >> f, type(result), '\n', result
            return result

    def periodPerformanceDataHandler(self, req):
        minResponseTime = req.params.get('minResponseTime')
        avgResponseTime = req.params.get('avgResponseTime')
        maxResponseTime = req.params.get('maxResponseTime')
        totalRequestCount = req.params.get('totalRequestCount')
        breakSLACount = req.params.get('breakSLACount')

        if  not isDecimal(minResponseTime) or not isDecimal(maxResponseTime) or not isDecimal(avgResponseTime) or not isNumber(totalRequestCount) or not isNumber(breakSLACount):
            result = errorResultJson('Please pass the params correctly')
        else:
            periodNoDB = shelve.open(periodRecoderFile)
            periodNo = periodNoDB.get(periodRecoder, None)

            if not periodNo:
                periodNo = 1

            periodNoDB[periodRecoder] = periodNo + 1
            periodNoDB.close()

            breakSLAPercent = float(breakSLACount) / totalRequestCount
            breakSLAPercent = round(breakSLAPercent, 4)

            performanceData = {'minResponseTime':minResponseTime, 'maxResponseTime':maxResponseTime, 'avgResponseTime':avgResponseTime, 'breakSLAPercent':breakSLAPercent, 'avgCpuUtil':avgCpuUtil, 'avgMemoryUtil':avgMemoryUtil}
            PerformanceDBUtil.addPerformanceDataToSpecificPeriod(periodNo, performanceData)

        return result
