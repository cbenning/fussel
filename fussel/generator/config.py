import os

DEFAULT_WATERMARK_PATH = "web/src/images/fussel-watermark.png"
DEFAULT_WATERMARK_SIZE_RATIO = 0.3
DEFAULT_RECURSIVE_ALBUMS_NAME_PATTERN = "{parent_album} > {album}"
DEFAULT_OUTPUT_PHOTOS_PATH = "site/"
DEFAULT_SITE_TITLE = "Fussel Gallery"
DEFAULT_PHOTO_SIZES = [(500, 500), (800, 800), (1024, 1024), (1600, 1600)]


class Config:
    _instance: "Config | None" = None
    _yaml_config = None

    # Set by init(). Declared here so type checkers and editors know the attribute names and types.
    input_photos_dir: str
    people_enabled: bool
    albums_enabled: bool
    photos_enabled: bool
    watermark_enabled: bool
    watermark_path: str
    watermark_ratio: float
    recursive_albums: bool
    recursive_albums_name_pattern: str
    overwrite: bool
    output_photos_path: str
    http_root: str
    site_name: str
    supported_extensions: tuple[str, ...]
    parallel_tasks: int
    exif_transpose: bool
    allow_download: bool
    photos_sort_by: str
    photos_sort_order: str
    photo_sizes: list[tuple[int, ...]]

    def __init__(self):
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls) -> "Config":
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            # Put any initialization here.
        return cls._instance

    @classmethod
    def init(cls, yaml_config):
        instance = cls.__new__(cls)
        cls._yaml_config = yaml_config
        cls._populate_instance(instance, yaml_config)
        cls._instance = instance

    @classmethod
    def _populate_instance(cls, instance, yaml_config):
        instance.input_photos_dir = str(yaml_config.getKey("gallery.input_path"))
        instance.people_enabled = bool(yaml_config.getKey("gallery.people.enable", True))
        instance.albums_enabled = bool(yaml_config.getKey("gallery.albums.enable", True))
        instance.photos_enabled = bool(yaml_config.getKey("gallery.photos.enable", True))
        instance.watermark_enabled = bool(yaml_config.getKey("gallery.watermark.enable", True))
        instance.watermark_path = str(yaml_config.getKey("gallery.watermark.path", DEFAULT_WATERMARK_PATH))
        instance.watermark_ratio = float(
            yaml_config.getKey("gallery.watermark.size_ratio", DEFAULT_WATERMARK_SIZE_RATIO)
        )
        instance.recursive_albums = bool(yaml_config.getKey("gallery.albums.recursive", True))
        instance.recursive_albums_name_pattern = str(
            yaml_config.getKey("gallery.albums.recursive_name_pattern", DEFAULT_RECURSIVE_ALBUMS_NAME_PATTERN)
        )
        instance.overwrite = bool(yaml_config.getKey("gallery.overwrite", False))
        instance.output_photos_path = str(yaml_config.getKey("gallery.output_path", DEFAULT_OUTPUT_PHOTOS_PATH))
        instance.http_root = str(yaml_config.getKey("site.http_root", "/"))
        instance.site_name = str(yaml_config.getKey("site.title", DEFAULT_SITE_TITLE))
        instance.supported_extensions = (".avif", ".jpg", ".jpeg", ".gif", ".png", ".webp")

        _parallel_tasks = (os.cpu_count() or 2) / 2
        if _parallel_tasks < 1:
            _parallel_tasks = 1
        instance.parallel_tasks = int(yaml_config.getKey("gallery.parallel_tasks", _parallel_tasks))

        instance.exif_transpose = bool(yaml_config.getKey("gallery.exif_transpose", False))

        instance.allow_download = bool(yaml_config.getKey("gallery.allow_download", True))

        instance.photos_sort_by = str(yaml_config.getKey("gallery.photos.sort_by", "date"))
        instance.photos_sort_order = str(yaml_config.getKey("gallery.photos.sort_order", "desc"))

        _raw_sizes = yaml_config.getKey("gallery.photo_sizes", None)
        if _raw_sizes:
            instance.photo_sizes = [tuple(s) for s in _raw_sizes]
        else:
            instance.photo_sizes = DEFAULT_PHOTO_SIZES
