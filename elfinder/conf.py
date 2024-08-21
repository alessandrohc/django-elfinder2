# -*- coding: utf-8 -*-
from django.conf import settings as user_settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import LazyObject


class Settings(object):
    pass


class LazySettings(LazyObject):
    def _setup(self):
        self._wrapped = Settings()
        self.ELFINDER_DEBUG = getattr(user_settings, 'ELFINDER_DEBUG',
                                      user_settings.DEBUG)
        self.ELFINDER_VOLUME_DRIVERS = getattr(
            user_settings, "ELFINDER_VOLUME_DRIVERS", {
                "default": {
                    "BACKEND": "elfinder.volume_drivers.model_driver.ModelVolumeDriver",
                },
                "fs": {
                    "BACKEND": "elfinder.volume_drivers.fs_driver.FileSystemVolumeDriver",
                    "OPTIONS": {
                        "fs_driver_root": user_settings.MEDIA_ROOT,
                        "login_url": user_settings.LOGIN_URL,
                        "login_required": False,
                        "js_api_options": {}
                    }
                }
            })
        if not isinstance(self.ELFINDER_VOLUME_DRIVERS, dict):
            raise ImproperlyConfigured('ELFINDER_VOLUME_DRIVERS is not a dict!')

        self.ELFINDER_TEMPLATE_ENGINE = getattr(
            user_settings, "ELFINDER_TEMPLATE_ENGINE",
            "django"
        )

        self.ELFINDER_XADMIN_REGISTER = getattr(
            user_settings, "ELFINDER_XADMIN_REGISTER",
            True
        )

        self.ELFINDER_FS_DRIVER_URL = getattr(
            user_settings, "ELFINDER_FS_DRIVER_URL",
            user_settings.MEDIA_URL
        )

        # special settings for TinyMCE connector
        self.ELFINDER_TINYMCE_PATH_TO_POPUP_JS = getattr(
            user_settings, "ELFINDER_TINYMCE_PATH_TO_POPUP_JS",
            None
        )

        # Maximum number of volumes supported by the 'volume' parameter
        self.ELFINDER_MAX_VOLUME_INTERATION = getattr(
            user_settings, "ELFINDER_MAX_VOLUME_INTERATION",
            300
        )

        # uplMaxFile (Number) Allowed upload max number of file per request. For example 20
        settings.ELFINDER_UPLOAD_MAX_FILE = getattr(
            user_settings, "ELFINDER_UPLOAD_MAX_FILE",
            20
        )

        # uplMaxSize (String) Allowed upload max size per request. For example "32M"
        settings.ELFINDER_UPLOAD_REQUEST_MAX_SIZE = getattr(
            user_settings, "ELFINDER_UPLOAD_REQUEST_MAX_SIZE",
            '32M'
        )


settings = LazySettings()
