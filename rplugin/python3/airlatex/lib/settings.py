__version__ = "0.2"


# Singleton
class Settings:
  _instance = None

  def __new__(cls, *args, **kwargs):
    if not isinstance(cls._instance, cls):
      cls._instance = super(Settings, cls).__new__(cls)
      cls._instance.initialize(*args, **kwargs)
    return cls._instance

  def initialize(
      self, wait_for=0, cookie="", domain="", mount_root="",
      dropbox_mount=False, https=True, insecure=False):
    self.wait_for = wait_for
    self.cookie = cookie
    self.domain = domain
    self.dropbox_mount = dropbox_mount
    self.mount_root = mount_root
    self.https = https
    self.insecure = insecure
    self.url = ("https://" if https else "http://") + domain
