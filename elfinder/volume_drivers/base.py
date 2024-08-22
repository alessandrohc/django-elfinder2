# coding=utf-8
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from urllib.parse import urlencode
from elfinder.conf import settings as elfinder_settings
from django.utils.safestring import mark_safe
from elfinder.utils import get_bytes


class BaseVolumeDriver(object):
    content_encoding = 'UTF-8'
    # https://github.com/Studio-42/elFinder/wiki/Connector-configuration-options-2.1#root-options

    # List of disabled client's commands
    opt_disabled = []  # disabled

    # Directory separator - required by client
    opt_separator = '/'  # separator

    # on paste file -  if true - old file will be replaced with new one,
    # if false new file get name - original_name-number.ext
    opt_copy_overwrite = True  # copyOverwrite

    opt_upload_maxsize = 0  # uploadMaxSize

    def __init__(self, request=None, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.request = request

    def get_volume_id(self):
        """ Returns the volume ID for the volume, which is used as a prefix
            for client hashes.
        """
        raise NotImplementedError

    def _get_volumes(self) -> list:
        """ Returns a set of volume names for the connector to control
        """
        volumes = []
        if request_volumes := self.request.GET.getlist('volume'):
            counter, iteration = 0, elfinder_settings.ELFINDER_MAX_VOLUME_INTERATION
            # avoid javascript injection
            for volume_name in request_volumes:
                if elfinder_settings.ELFINDER_VOLUME_DRIVERS.get(volume_name):
                    if volume_name not in volumes:
                        volumes.append(volume_name)
                counter += 1
                # prevents system overload by malicious bot
                if counter > iteration:
                    break
        return volumes

    def _get_connector_url(self):
        """:return url of driver connector
        """
        view_name = self.kwargs.get('connector_url_view_name',
                                    'elfinder_connector')
        if collection_id := self.kwargs.get('collection_id'):
            url = reverse(view_name, kwargs={'coll_id': collection_id})
        else:
            url = reverse(view_name)

        if volumes := self._get_volumes():
            url += "?" + urlencode([("volume", volume) for volume in volumes])
        # it's safe because it's already validated against the variable (ELFINDER_VOLUME_DRIVERS).
        return mark_safe(url)

    connector_url = cached_property(_get_connector_url)

    @cached_property
    def login_required(self):
        return bool(self.kwargs.get('login_required'))

    @cached_property
    def login_url(self):
        return self.kwargs.get('login_url')

    @staticmethod
    def _login_test(user):
        """Tests whether the user is active and authenticated"""
        return user.is_active and user.is_authenticated

    @cached_property
    def login_test_func(self):
        func = self.kwargs.get('login_test_func')
        if isinstance(func, str):
            func = import_string(func)
        else:
            func = self._login_test
        return func

    def get_options(self, path=None):
        """Volume config defaults"""
        js_options = self.kwargs.get('js_api_options', {})
        opts = {
            'disabled': self.opt_disabled,
            'separator': self.opt_separator,
            'copyOverwrite': self.opt_copy_overwrite,
            'uploadMaxSize': self.opt_upload_maxsize,
        }
        opts.update(js_options)
        # unit convert
        opts['uploadMaxSize'] = get_bytes(opts['uploadMaxSize'])
        return opts

    def get_index_template(self, template):
        """Template that render the index view."""
        return self.kwargs.get('index_template', template)

    def get_info(self, target):
        """ Returns a dict containing information about the target directory
            or file. This data is used in response to 'open' commands to
            populates the 'cwd' response var.

            :param target: The hash of the directory for which we want info.
            If this is '', return information about the root directory.
            :returns: dict -- A dict describing the directory.
        """
        raise NotImplementedError

    def zip_download(self, targets, dl=False):
        """ Prepare files for download
            :param targets: array of hashed paths of the nodes
            :param dl:
            :returns: dict -- A dict describing the zip file.
        """
        raise NotImplementedError

    def archive(self, targets, target, name, ttype):
        """Packs directories / files into an archive.
        :param name: file name of the archive to create
        :param ttype: mime-type for the archive
        :param target: hash of the directory that are added to the archive directories / files
        :param targets: an array of hashes of the directories / files to archive
        """
        raise NotImplementedError

    def extract(self, target, makedir=True):
        """Unpacks an archive.
        :param target: target hash of the archive file
         :param makedir: "True" to extract to new directory

         added : (Array) Information about File/Directory of extracted items
        """
        raise NotImplementedError

    def get_tree(self, target, ancestors=False, siblings=False):
        """ Gets a list of dicts describing children/ancestors/siblings of the
            target.

            :param target: The hash of the directory the tree starts from.
            :param ancestors: Include ancestors of the target.
            :param siblings: Include siblings of the target.
            :param children: Include children of the target.
            :returns: list -- a list of dicts describing directories.
        """
        raise NotImplementedError

    def read_file_view(self, request, target, **kwargs):
        """ Django view function, used to display files in response to the
            'file' command.

            :param request: The original HTTP request.
            :param target: The hash of the target file.
            :returns: dict -- a dict describing the new directory.
        """
        raise NotImplementedError

    def get(self, target, conv):
        """ Returns the content as String (As UTF-8)
        :param target : hash of the file
        :param conv : instructions for character encoding conversion of the text file
            1 : auto detect encoding(Return false as content in response data when failed)
            0 : auto detect encoding(Return { "doconv" : "unknown" } as response data when failed)
            Original Character encoding : original character encoding as specified by the user
        """
        raise NotImplementedError

    def search(self, text, target, reqid):
        """ Search for file/directory

            :param text: search string.
            :param target: The hash of the parent directory.
            :param reqid: request session id.
            :returns: mimes
        """
        raise NotImplementedError

    def mkdir(self, name, parent):
        """ Creates a directory.

            :param name: The name of the new directory.
            :param parent: The hash of the parent directory.
            :returns: dict -- a dict describing the new directory.
        """
        raise NotImplementedError

    def mkfile(self, name, parent):
        """ Creates a directory.

            :param name: The name of the new file.
            :param parent: The hash of the parent directory.
            :returns: dict -- a dict describing the new file.
        """
        raise NotImplementedError

    def putfile(self, target, content, **kwargs):
        """ Update the contents of an existing file..

            :param target: The hash of the file being changed.
            :param content: The contents of the file.
            :param kwargs: optional encoding
            :returns: list -- of files that were successfully uploaded.
        """
        raise NotImplementedError

    def rename(self, name, target):
        """ Renames a file or directory.

            :param name: The new name of the file/directory.
            :param target: The hash of the target file/directory.
            :returns: dict -- a dict describing which objects were added and
            removed.
        """
        raise NotImplementedError

    def duplicate(self, targets):
        """Creates a copy of the directory / file. Copy name is generated as follows:
        basedir_name_filecopy+serialnumber.extension (if any)
        """

    def list(self, target, **kwargs):
        """ Lists the contents of a directory.

            :param target: The hash of the target directory.
            :returns: list -- a list containing the names of files/directories
            in this directory.
        """
        raise NotImplementedError

    def paste(self, targets, dest, cut, **kwargs):
        """ Moves/copies target files/directories from source to dest.

            If a file with the same name already exists in the dest directory
            it should be overwritten (the client asks the user to confirm this
            before sending the request).

            :param targets: A list of hashes of files/dirs to move/copy.
            :param source: The current parent of the targets.
            :param dest: The new parent of the targets.
            :param cut: Boolean. If true, move the targets. If false, copy the
            targets.
            :returns: dict -- a dict describing which targets were moved/copied.
        """
        raise NotImplementedError

    def size(self, targets):
        """ Returns the size of a directory or file.

            size: The total size for all the supplied targets.
            fileCnt: The total counts of the file for all the supplied targets. (Optional to API >= 2.1025)
            dirCnt: The total counts of the directory for all the supplied targets. (Optional to API >= 2.1025)
            sizes: An object of each target size infomation. (Optional to API >= 2.1030)
        """
        raise NotImplementedError

    def remove(self, target):
        """ Deletes the target files/directories.

            The 'rm' command takes a list of targets - this function is called
            for each target, so should only delete one file/directory.

            :param target: A hash of files/dir to delete.
            :returns: list -- warnings generated when trying to remove a file or directory.
        """
        raise NotImplementedError

    def upload(self, files, parent):
        """ Uploads one or more files in to the parent directory.

            :param files: A list of uploaded file objects, as described here:
            https://docs.djangoproject.com/en/dev/topics/http/file-uploads/
            :param parent: The hash of the directory in which to create the
            new files.
            :returns: TODO
        """

    def dim(self, target, **kwargs):
        """
        Returns the dimensions of an image/video
        Arguments:
            cmd : dim
            target : hash path of the node
            substitute : pixel that requests substitute image (optional) - API >= 2.1030
        Response:
            dim: The dimensions of the media in the format {width}x{height} (e.g. "640x480").
            url: The URL of requested substitute image. (optional)
        """
        raise NotImplementedError

    def resize(self, target, **kwargs):
        """ Change the size of an image.

            :param target: The hash of the target file/directory.
            :kwargs: dict --
                cmd : resize
                mode : 'resize' or 'crop' or 'rotate'
                target : hash of the image path
                width : new image width
                height : new image height
                x : x of crop (mode='crop')
                y : y of crop (mode='crop')
                degree : rotate degree (mode='rotate')
                quality
        """
        raise NotImplementedError

    def upload_chunked(self, files, target, cid, chunk, bytes_range):
        """
        Chunking arguments:
        chunk : chunk name "filename.[NUMBER]_[TOTAL].part"
        cid : unique id of chunked uploading file
        range : Bytes range of file "Start byte,Chunk length,Total bytes
        """
        pass

    def upload_chunked_req(self, files, parent, chunk):
        """Chunk merge request (When receive _chunkmerged, _name)"""
        pass

    def abort(self, reqid):
        """Aborts an operation in progress."""
        pass
