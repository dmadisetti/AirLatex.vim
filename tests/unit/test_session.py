import pytest
import json
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from rplugin.python3.airlatex.session import AirLatexSession


class TestAirLatexSession:

    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    def test_initialization(self, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)

        assert session.projects == {}
        assert session.project_data == {}
        assert session.authenticated is False
        assert session.httpHandler is not None

    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    def test_cookies_property_empty(self, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)
        session.httpHandler.cookies.get_dict = Mock(return_value={})

        assert session.cookies == ""

    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    def test_cookies_property_with_data(self, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)
        session.httpHandler.cookies.get_dict = Mock(
            return_value={"cookie1": "value1", "cookie2": "value2"})

        cookies = session.cookies
        assert "cookie1=value1" in cookies
        assert "cookie2=value2" in cookies

    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    def test_project_list_empty(self, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)
        assert session.projectList == []

    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    def test_project_list_sorted(self, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)
        session.project_data = {
            "p1": {"id": "p1", "lastUpdated": 100},
            "p2": {"id": "p2", "lastUpdated": 200},
            "p3": {"id": "p3", "lastUpdated": 150},
        }

        project_list = session.projectList
        assert len(project_list) == 3
        assert project_list[0]["id"] == "p2"
        assert project_list[1]["id"] == "p3"
        assert project_list[2]["id"] == "p1"

    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    @patch('rplugin.python3.airlatex.session.generateTimeStamp')
    def test_websocket_url_https(self, mock_timestamp, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings_instance.url = "https://example.com"
        mock_settings_instance.domain = "example.com"
        mock_settings_instance.https = True
        mock_settings.return_value = mock_settings_instance

        mock_timestamp.return_value = "1234567890"

        session = AirLatexSession(mock_nvim)
        mock_response = Mock()
        mock_response.text = "channel123:extra:data"
        session.httpHandler.get = Mock(return_value=mock_response)

        url = session.webSocketURL("project123")

        assert url.startswith("wss://")
        assert "example.com" in url
        assert "channel123" in url
        assert "project123" in url

    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    @patch('rplugin.python3.airlatex.session.generateTimeStamp')
    def test_websocket_url_http(self, mock_timestamp, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings_instance.url = "http://example.com"
        mock_settings_instance.domain = "example.com"
        mock_settings_instance.https = False
        mock_settings.return_value = mock_settings_instance

        mock_timestamp.return_value = "1234567890"

        session = AirLatexSession(mock_nvim)
        mock_response = Mock()
        mock_response.text = "channel456:extra"
        session.httpHandler.get = Mock(return_value=mock_response)

        url = session.webSocketURL("project456")

        assert url.startswith("ws://")
        assert "example.com" in url

    @pytest.mark.asyncio
    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    @patch('rplugin.python3.airlatex.session.WebPage')
    async def test_check_login_success(self, mock_webpage, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings_instance.cookie = "name1=value1;name2=value2"
        mock_settings_instance.url = "https://example.com"
        mock_settings.return_value = mock_settings_instance

        mock_sidebar_instance = Mock()
        mock_sidebar_instance.animation = Mock()
        mock_sidebar_instance.animation.return_value.__enter__ = Mock()
        mock_sidebar_instance.animation.return_value.__exit__ = Mock()
        mock_sidebar.return_value = mock_sidebar_instance

        mock_page = Mock()
        mock_page.ok = True
        mock_webpage.return_value = mock_page

        session = AirLatexSession(mock_nvim)
        result = await session._checkLogin()

        assert result is True
        assert session.httpHandler.cookies["name1"] == "value1"
        assert session.httpHandler.cookies["name2"] == "value2"

    @pytest.mark.asyncio
    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    async def test_check_login_already_authenticated(self, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)
        session.authenticated = True

        result = await session._checkLogin()
        assert result is True

    @pytest.mark.asyncio
    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    async def test_check_login_invalid_cookie(self, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings_instance.cookie = "invalid_cookie_format"
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)

        with pytest.raises(ValueError):
            await session._checkLogin()

    @pytest.mark.asyncio
    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    @patch('rplugin.python3.airlatex.session.WebPage')
    @patch('rplugin.python3.airlatex.session.Task')
    async def test_build_project_list_success(self, mock_task, mock_webpage, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings_instance.url = "https://example.com"
        mock_settings.return_value = mock_settings_instance

        mock_sidebar_instance = Mock()
        mock_sidebar_instance.animation = Mock()
        mock_sidebar_instance.animation.return_value.__enter__ = Mock()
        mock_sidebar_instance.animation.return_value.__exit__ = Mock()
        mock_sidebar.return_value = mock_sidebar_instance

        project_data = {
            "projects": [
                {"id": "p1", "name": "Project 1"},
                {"id": "p2", "name": "Project 2"}
            ]
        }

        mock_meta = Mock()
        mock_meta.content = json.dumps(project_data)

        mock_user_id = Mock()
        mock_user_id.content = "user123"

        mock_page = Mock()
        mock_page.ok = True
        mock_page.parse = Mock(side_effect=lambda x: mock_meta if x == "prefetchedProjectsBlob" else mock_user_id)
        mock_webpage.return_value = mock_page

        session = AirLatexSession(mock_nvim)
        result = await session._buildProjectList()

        assert "p1" in result
        assert "p2" in result

    @pytest.mark.asyncio
    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    async def test_build_project_list_already_authenticated(self, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)
        session.authenticated = True
        session.project_data = {"existing": "data"}

        result = await session._buildProjectList()
        assert result == {"existing": "data"}

    @pytest.mark.asyncio
    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    @patch('rplugin.python3.airlatex.session.Task')
    async def test_start(self, mock_task, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)
        session._checkLogin = Mock(return_value=True)
        session._buildProjectList = Mock(return_value={"p1": {}})

        await session.start()

        assert session._checkLogin.called
        assert session._buildProjectList.called

    @pytest.mark.asyncio
    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    @patch('rplugin.python3.airlatex.session.Task')
    async def test_cleanup(self, mock_task, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)

        mock_project1 = Mock()
        mock_project1.disconnect = Mock()
        mock_project2 = Mock()
        mock_project2.disconnect = Mock()

        session.projects = {"p1": mock_project1, "p2": mock_project2}

        await session.cleanup("Test message")

        assert mock_task.called

    @pytest.mark.asyncio
    @patch('rplugin.python3.airlatex.session.Splash')
    @patch('rplugin.python3.airlatex.session.Sidebar')
    @patch('rplugin.python3.airlatex.session.Comments')
    @patch('rplugin.python3.airlatex.session.Settings')
    @patch('rplugin.python3.airlatex.session.Task')
    async def test_connect_project_not_authenticated(self, mock_task, mock_settings, mock_comments, mock_sidebar, mock_splash):
        mock_nvim = Mock()
        mock_settings_instance = Mock()
        mock_settings_instance.insecure = False
        mock_settings.return_value = mock_settings_instance

        session = AirLatexSession(mock_nvim)
        session.authenticated = False

        result = await session.connectProject({"id": "p1"})
        assert result is None
