# -*- coding: utf-8 -*-

from webob import Response
from webob.dec import wsgify
from webob import exc
import webob

class Auth(object):

    def __init__(self, app):
        self.app = app

    @classmethod
    def factory(cls, global_config, **local_config):
        def _factory(app):
            return cls(app)
        return _factory

    @wsgify(RequestClass=webob.Request)
    def __call__(self, req):
        
        #可以通过req.params访问 post 的 body字典
        #f = open('debugLog.txt', 'w')
        #print >> f, req.params
        
        #可以通过req.environ['QUERY_STRING'] 访问get请求中XXX?a=5&b=8后面的字符串
        #f = open('debugLog.txt', 'w')
        #print >> f, req.environ['QUERY_STRING']
        
        
        #测req.response(用于封装app直接返回的字符串)的类，结果是<class 'webob.response.Response'>
        #f = open('debugLog.txt', 'w')
        #print >> f, type(req.response)
        
        resp = self.process_request(req)
        if resp:
            return resp
        return req.get_response(self.app)

    def process_request(self, req):
        if req.headers.get('X-Auth-Token') != 'open-sesame':
            return exc.HTTPForbidden()
   
