import pytest
from rplugin.python3.airlatex.lib.settings import Settings, __version__


class TestVersion:

    def test_version_exists(self):
        assert __version__ is not None

    def test_version_format(self):
        assert isinstance(__version__, str)
        assert len(__version__) > 0


class TestSettings:

    def setup_method(self):
        Settings._instance = None

    def teardown_method(self):
        Settings._instance = None

    def test_singleton_pattern(self):
        settings1 = Settings()
        settings2 = Settings()
        assert settings1 is settings2

    def test_initialization_default_values(self):
        settings = Settings()
        assert settings.wait_for == 0
        assert settings.cookie == ""
        assert settings.domain == ""
        assert settings.mount_root == ""
        assert settings.dropbox_mount is False
        assert settings.https is True
        assert settings.insecure is False

    def test_initialization_with_custom_values(self):
        settings = Settings(
            wait_for=10,
            cookie="test_cookie",
            domain="example.com",
            mount_root="/mnt/test",
            dropbox_mount=True,
            https=False,
            insecure=True
        )
        assert settings.wait_for == 10
        assert settings.cookie == "test_cookie"
        assert settings.domain == "example.com"
        assert settings.mount_root == "/mnt/test"
        assert settings.dropbox_mount is True
        assert settings.https is False
        assert settings.insecure is True

    def test_url_with_https(self):
        settings = Settings(domain="example.com", https=True)
        assert settings.url == "https://example.com"

    def test_url_with_http(self):
        Settings._instance = None
        settings = Settings(domain="example.com", https=False)
        assert settings.url == "http://example.com"

    def test_url_construction(self):
        Settings._instance = None
        settings = Settings(domain="test.overleaf.com", https=True)
        assert settings.url == "https://test.overleaf.com"

    def test_singleton_preserves_first_initialization(self):
        settings1 = Settings(domain="first.com", wait_for=5)
        settings2 = Settings(domain="second.com", wait_for=10)

        assert settings1.domain == "first.com"
        assert settings2.domain == "first.com"
        assert settings1.wait_for == 5
        assert settings2.wait_for == 5

    def test_multiple_instance_calls(self):
        instances = [Settings() for _ in range(10)]
        first_instance = instances[0]

        for instance in instances:
            assert instance is first_instance

    def test_initialize_method_directly(self):
        settings = Settings()
        settings.initialize(
            wait_for=20,
            cookie="new_cookie",
            domain="new.domain.com",
            mount_root="/new/root",
            dropbox_mount=True,
            https=True,
            insecure=False
        )

        assert settings.wait_for == 20
        assert settings.cookie == "new_cookie"
        assert settings.domain == "new.domain.com"
        assert settings.mount_root == "/new/root"
        assert settings.dropbox_mount is True
        assert settings.https is True
        assert settings.insecure is False
        assert settings.url == "https://new.domain.com"

    def test_settings_persistence_across_calls(self):
        settings1 = Settings(cookie="persistent_cookie")
        Settings._instance = None
        settings2 = Settings()

        assert settings2.cookie == ""

    def test_all_parameters(self):
        Settings._instance = None
        settings = Settings(
            wait_for=100,
            cookie="full_cookie",
            domain="full.example.com",
            mount_root="/full/mount",
            dropbox_mount=True,
            https=False,
            insecure=True
        )

        assert settings.wait_for == 100
        assert settings.cookie == "full_cookie"
        assert settings.domain == "full.example.com"
        assert settings.mount_root == "/full/mount"
        assert settings.dropbox_mount is True
        assert settings.https is False
        assert settings.insecure is True
        assert settings.url == "http://full.example.com"

    def test_boolean_flags(self):
        Settings._instance = None
        settings = Settings(
            dropbox_mount=False,
            https=True,
            insecure=False
        )

        assert settings.dropbox_mount is False
        assert settings.https is True
        assert settings.insecure is False

    def test_empty_string_parameters(self):
        settings = Settings(
            cookie="",
            domain="",
            mount_root=""
        )

        assert settings.cookie == ""
        assert settings.domain == ""
        assert settings.mount_root == ""
        assert settings.url == "https://"

    def test_numeric_wait_for(self):
        Settings._instance = None
        settings = Settings(wait_for=0)
        assert settings.wait_for == 0

        Settings._instance = None
        settings = Settings(wait_for=999999)
        assert settings.wait_for == 999999
