# from __future__ import unicode_literals

# import itertools
# from collections import namedtuple

# from django.conf.urls import url
# from django.core.exceptions import ImproperlyConfigured
# from django.core.urlresolvers import NoReverseMatch

# from rest_framework import views
# from rest_framework.compat import OrderedDict
# from rest_framework.response import Response
# from rest_framework.reverse import reverse
# from rest_framework.urlpatterns import format_suffix_patterns

# from rest_framework import routers

# from pprint import pprint

# class SC_Router(routers.DefaultRouter):

#     def get_api_root_view(self):
#         """
#         Return a view to use as the API root.
#         """
#         api_root_dict = OrderedDict()
#         list_name = self.routes[0].name
#         for prefix, viewset, basename in self.registry:
#             api_root_dict[prefix] = list_name.format(basename=basename)

#         print 'api_root_dict'
#         for i in api_root_dict:
#           print i 


#         class APIRoot(views.APIView):
#             _ignore_model_permissions = True

#             def get(self, request, *args, **kwargs):
#                 ret = OrderedDict()
#                 namespace = request.resolver_match.namespace
#                 for key, url_name in api_root_dict.items():
#                     if namespace:
#                         url_name = namespace + ':' + url_name
#                     try:
#                         ret[key] = reverse(
#                             url_name,
#                             args=args,
#                             kwargs=kwargs,
#                             request=request,
#                             format=kwargs.get('format', None)
#                         )
#                         # print 'ok APIRoot', key, url_name, args, kwargs, request
#                     except NoReverseMatch:
#                         print 'err APIRoot', key, url_name, args, kwargs, request
#                         # Don't bail out if eg. no list routes exist, only detail routes.

#                         continue
#                 # ret['charting'] = reverse(
#                 #   'charting-list', request = request
#                 #   )

#                 return Response(ret)

#         return APIRoot.as_view()