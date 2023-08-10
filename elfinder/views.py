import json

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from elfinder.conf import settings
from elfinder.connector import ElFinderConnector
from elfinder.volume_drivers import get_volume_driver


class Volume:
    # Whether to return responses in json (used with the connector).
    json_response = False

    def get_volume_drivers(self, request, **options) -> list:
        """Returns a list with volumes"""
        volume_drivers = []
        options.setdefault('request', request)
        iteration = settings.ELFINDER_MAX_VOLUME_INTERATION
        for counter, volume_name in enumerate(self.get_volume_alias(request)):
            try:
                volume = get_volume_driver(volume_name, **options)
            except ImproperlyConfigured:
                continue
            if counter > iteration:
                break
            volume_drivers.append(volume)
        return volume_drivers

    def get_volume_alias(self, request) -> list:
        return list(request.GET.getlist('volume', ['default']))

    def _login_test(self, request):
        """Executing this method indicates that login validation has passed and no authentication is required."""
        return False

    def get_login_view(self, request, volume):
        """Checks if volume is project by authentication (redirect to view accordingly)."""
        decorator = user_passes_test(test_func=volume.login_test_func,
                                     login_url=volume.login_url)
        response = decorator(self._login_test)(request)
        if response:
            if self.json_response:
                return JsonResponse({'error': "Login required!"})
            else:
                return response
        return response


class VolumeMixin(Volume):
    # Whether to check through the volume if login is required.
    volume_login_check = True

    def dispatch(self, request, *args, **kwargs):
        self.volumes = self.get_volume_drivers(request, collection_id=kwargs.get('coll_id'))
        if self.volume_login_check:
            for volume_driver in self.volumes:
                if volume_driver.login_required and (login_view := self.get_login_view(request, volume_driver)):
                    return login_view
        return super().dispatch(request, *args, **kwargs)


class IndexView(VolumeMixin, View):

    @method_decorator(ensure_csrf_cookie)
    @method_decorator(never_cache)
    def get(self, request, coll_id=None):
        """ Displays the elFinder file browser template for the specified collection.
        """
        volume = self.volumes[0]
        context = {
            'coll_id': coll_id,
            'volume_driver': volume
        }
        return render(request,
                      # Possibility to configure a custom template
                      volume.get_index_template("elfinder/index.html"),
                      context=context,
                      using=settings.ELFINDER_TEMPLATE_ENGINE)


class ConnectorView(VolumeMixin, View):
    http_method_names = ['get', 'post']
    json_response = True

    def post(self, request, **kwargs):
        return self.get(request, **kwargs)

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, coll_id=None):
        """ Handles requests for the elFinder connector.
        """
        finder = ElFinderConnector(self.volumes)
        try:
            finder.run(request)
        except:
            if settings.ELFINDER_DEBUG:
                import traceback
                traceback.print_exc()
            raise
        # Some commands (e.g. read file) will return a Django View - if it
        # is set, return it directly instead of building a response
        if finder.return_view:
            return finder.return_view

        response = HttpResponse(content_type=finder.httpHeader['Content-type'])
        response.status_code = finder.httpStatusCode
        if finder.httpHeader['Content-type'] == 'application/json':
            response.content = json.dumps(finder.httpResponse,
                                          cls=DjangoJSONEncoder,
                                          ensure_ascii=False)
        else:
            response.content = finder.httpResponse
        return response


def read_file(request, volume, file_hash, template="elfinder/read_file.html"):
    """ Default view for responding to "open file" requests.

        coll: FileCollection this File belongs to
        file: The requested File object
    """
    return render(request, template,
                  context={'file': file_hash},
                  using=settings.ELFINDER_TEMPLATE_ENGINE)


index = IndexView.as_view()
connector_view = ConnectorView.as_view()
