#coding: utf-8
import webob
import simplejson
import os
import shelve
from webob.dec import wsgify
from NormalUtil import *
from DBUtil.UsingInstancesDBUtil import UsingInstancesDBUtil
from NovaUtil.TomcatInstanceUtil import TomcatInstanceUtil
from CeilometerUtil.SampleUtil import SampleUtil
from DBUtil.PerformanceDBUtil import PerformanceDBUtil
from DBUtil.WorkloadDBUtil import WorkloadDBUtil
from DBUtil.WorkloadVMMapDBUtil import WorkloadVMMapDBUtil
from ACRCUtil.ACRController import ACRController
from ACRCUtil.ExperimentInit import ExperimentInit
from ACRCUtil.ACRCPlacementComponent import ACRCPlacementComponent

ipEndOfComputes = [50, 60, 70, 80, 210, 220, 230, 240]
ipEndOfController = 40

class Controller(object):


    def testAction(self, req):
        raise Exception('lalalalalalala')

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
        avgCpuUtil = round(SampleUtil.getAllUsingInstancesPeriodAVGCpuUtil() / 100.0, 4)
        avgMemoryUtil = round(SampleUtil.getAllUsingInstancesPeriodAVGMemoryUtil() / 100.0, 4)


        if  not (isDecimal(minResponseTime) or isNumber(minResponseTime)) or not (isDecimal(maxResponseTime) or isNumber(maxResponseTime)) or not (isDecimal(avgResponseTime) or isNumber(avgResponseTime)) or not isNumber(totalRequestCount) or not isNumber(breakSLACount):
            return errorResultJson('Please pass the params correctly')
        elif avgCpuUtil == None or avgMemoryUtil == None:
            raise Exception("can not get avgCpuUtil or avgMemoryUtil data")
        else:
            minResponseTime = float(minResponseTime)
            avgResponseTime = float(avgResponseTime)
            maxResponseTime = float(maxResponseTime)
            totalRequestCount = int(totalRequestCount)
            breakSLACount = int(breakSLACount)


            #确认periodNo
            periodNoDB = shelve.open(periodRecoderFile)
            periodNo = periodNoDB.get(periodRecoder, None)

            if not periodNo:
                periodNo = 1

            periodNoDB[periodRecoder] = periodNo + 1
            periodNoDB.close()

            #计算breakSLAPercent
            breakSLAPercent = float(breakSLACount) / totalRequestCount
            breakSLAPercent = round(breakSLAPercent, 4)


            #计算刚刚过去的这个周期的可用性
            placementTool = ACRCPlacementComponent()
            availabilityData = placementTool.calculateAvailability()

            #得到刚刚过去这个周期的虚拟机数目
            vmNumbers = UsingInstancesDBUtil.getUsingInstancesCount()

            #添加上个周期应该提供的虚拟机数目
            shouldVMNumbers = WorkloadVMMapDBUtil.getTargetVMsToSpecificWorkload(totalRequestCount)


            if periodNo == 1:
                ppVMNumbers = vmNumbers
                rpVMNumbers = 0
            else:
                provisionInfoDB = shelve.open(provisionInfoFile)
                ppVMNumbers = provisionInfoDB.get(predictProvisionVMNumbers, None)
                rpVMNumbers = provisionInfoDB.get(reactiveProvisionVMNumbers, None)



            #添加performanceData
            performanceData = {'minResponseTime':minResponseTime, 'maxResponseTime':maxResponseTime, 'avgResponseTime':avgResponseTime, 'breakSLAPercent':breakSLAPercent, 'avgCpuUtil':avgCpuUtil, 'avgMemoryUtil':avgMemoryUtil, 'availability':availabilityData, 'vmNumbers':vmNumbers, 'shouldVMNumbers':shouldVMNumbers, 'predictProvisionVMNumbers':ppVMNumbers, 'reactiveProvisionVMNumbers':rpVMNumbers}
            PerformanceDBUtil.addPerformanceDataToSpecificPeriod(periodNo, performanceData)


            #向数据库中添加workload信息
            if periodNo == 1:
                WorkloadDBUtil.addFirstPeriodRealWorkload(totalRequestCount)
            else:
                WorkloadDBUtil.addRealWorkloadToSpecificPeriod(periodNo, totalRequestCount)

            acrCtl = ACRController()
            acrCtl.autonomicPeriodHandler()

            TomcatInstanceUtil.ensureAllUsingInstancesActive()
            return UsingInstancesDBUtil.getAllUsingInstancesInfo()

    def initExperiment(self, req):
        check = 1

        try:
            token = req.headers['X-Auth-Token']
            if token != 'sk':
                check = 0

        except KeyError:
            check = 0

        if check:
            ExperimentInit().getInitialScheme()
            return UsingInstancesDBUtil.getAllUsingInstancesInfo()
        else:
            return errorResultJson('You are not allowed to do this!')
