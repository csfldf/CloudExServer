#coding: utf-8
import routes
import routes.middleware
import webob
import webob.dec
from webob.dec import wsgify
import controllers

class Router(object):
    def __init__(self):
        self.mapper = routes.Mapper()
        self.add_routes()
        self._router = routes.middleware.RoutesMiddleware(self._dispatch,
                                                          self.mapper)

    def add_routes(self):
        controller = controllers.Controller()
        self.mapper.connect("/instances",
                           controller=controller, action="create",
                           conditions=dict(method=["POST"]))

        self.mapper.connect("/getUtils",
                           controller=controller, action="getUtil",
                           conditions=dict(method=["POST"]))

        self.mapper.connect("/changeUtilsAndPeriods",
                           controller=controller, action="changeUtilPeriod",
                           conditions=dict(method=["POST"]))

        self.mapper.connect("/clearUtilsData",
                           controller=controller, action="clearSamples",
                           conditions=dict(method=["GET"]))


    @wsgify(RequestClass=webob.Request)
    def __call__(self, request):
        #print request.params
        return self._router

    @staticmethod
    @wsgify(RequestClass=webob.Request)
    def _dispatch(request):

        #输出{'instance_id': u'6e49233f-c5ea-48b0-b222-eef5f4d2d23e', 在mapper中/instances/{instance_id}这样定义url则在request.environ['wsgiorg.routing_args'][1]中生成instance_id:XXX 这样的键值对
            #'action': u'show',
            #'controller': <controllers.Controller object at 0x10dd8e610>}
        #f = open('debugLog.txt', 'w')
        #print >> f, request.environ['wsgiorg.routing_args'][1]

        match = request.environ['wsgiorg.routing_args'][1]
        if not match:
            return _err()
        app = match['controller']
        return app

def _err():
    return 'The Resource is Not Found.'

def app_factory(global_config, **local_config):
    return Router()

