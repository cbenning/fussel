import os

DEFAULT_WATERMARK_PATH = "web/src/images/fussel-watermark.png"
DEFAULT_WATERMARK_SIZE_RATIO = 0.3
DEFAULT_RECURSIVE_ALBUMS_NAME_PATTERN = "{parent_album} > {album}"
DEFAULT_OUTPUT_PHOTOS_PATH = "site/"
DEFAULT_SITE_TITLE = "Fussel Gallery"
DEFAULT_PHOTO_SIZES = [(500, 500), (800, 800), (1024, 1024), (1600, 1600)]


class Config:
    _instance = None
    _yaml_config = None

    def __init__(self):
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            # Put any initialization here.
        return cls._instance

    @classmethod
    def init(cls, yaml_config):
        cls._instance = cls.__new__(cls)
        cls._yaml_config = yaml_config
        cls._populate_instance(yaml_config)

    @classmethod
    def _populate_instance(cls, yaml_config):
        cls._instance.input_photos_dir = str(yaml_config.getKey("gallery.input_path"))
        cls._instance.people_enabled = bool(yaml_config.getKey("gallery.people.enable", True))
        cls._instance.albums_enabled = bool(yaml_config.getKey("gallery.albums.enable", True))
        cls._instance.photos_enabled = bool(yaml_config.getKey("gallery.photos.enable", True))
        cls._instance.watermark_enabled = bool(yaml_config.getKey("gallery.watermark.enable", True))
        cls._instance.watermark_path = str(yaml_config.getKey("gallery.watermark.path", DEFAULT_WATERMARK_PATH))
        cls._instance.watermark_ratio = float(
            yaml_config.getKey("gallery.watermark.size_ratio", DEFAULT_WATERMARK_SIZE_RATIO)
        )
        cls._instance.recursive_albums = bool(yaml_config.getKey("gallery.albums.recursive", True))
        cls._instance.recursive_albums_name_pattern = str(
            yaml_config.getKey("gallery.albums.recursive_name_pattern", DEFAULT_RECURSIVE_ALBUMS_NAME_PATTERN)
        )
        cls._instance.overwrite = bool(yaml_config.getKey("gallery.overwrite", False))
        cls._instance.output_photos_path = str(yaml_config.getKey("gallery.output_path", DEFAULT_OUTPUT_PHOTOS_PATH))
        cls._instance.http_root = str(yaml_config.getKey("site.http_root", "/"))
        cls._instance.site_name = str(yaml_config.getKey("site.title", DEFAULT_SITE_TITLE))
        cls._instance.supported_extensions = (".jpg", ".jpeg", ".gif", ".png")

        _parallel_tasks = os.cpu_count() / 2
        if _parallel_tasks < 1:
            _parallel_tasks = 1
        cls._instance.parallel_tasks = int(yaml_config.getKey("gallery.parallel_tasks", _parallel_tasks))

        cls._instance.exif_transpose = bool(yaml_config.getKey("gallery.exif_transpose", False))

        cls._instance.allow_download = bool(yaml_config.getKey("gallery.allow_download", True))

        cls._instance.photos_sort_by = str(yaml_config.getKey("gallery.photos.sort_by", "date"))
        cls._instance.photos_sort_order = str(yaml_config.getKey("gallery.photos.sort_order", "desc"))

        _raw_sizes = yaml_config.getKey("gallery.photo_sizes", None)
        if _raw_sizes:
            cls._instance.photo_sizes = [tuple(s) for s in _raw_sizes]
        else:
            cls._instance.photo_sizes = DEFAULT_PHOTO_SIZES
