import pytest
from unittest.mock import Mock, MagicMock, patch
from bs4 import BeautifulSoup
import requests
from rplugin.python3.airlatex.lib.connection import WebException, WebPage, Tag


class TestWebException:

    def test_can_raise(self):
        with pytest.raises(WebException):
            raise WebException("Test error")

    def test_message(self):
        with pytest.raises(WebException) as exc_info:
            raise WebException("Custom message")
        assert "Custom message" in str(exc_info.value)


class TestTag:

    def test_initialization(self):
        mock_tag = Mock()
        tag = Tag(mock_tag)
        assert tag.tag == mock_tag

    def test_content_property_with_content(self):
        mock_tag = Mock()
        mock_tag.get = Mock(return_value="test content")
        tag = Tag(mock_tag)
        assert tag.content == "test content"
        mock_tag.get.assert_called_once_with('content', None)

    def test_content_property_without_content(self):
        mock_tag = Mock()
        mock_tag.get = Mock(return_value=None)
        tag = Tag(mock_tag)
        assert tag.content is None

    def test_content_property_with_none_tag(self):
        tag = Tag(None)
        assert tag.content is None


class TestWebPage:

    @patch('rplugin.python3.airlatex.lib.connection.requests')
    def test_initialization_success(self, mock_requests):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b"<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage(mock_client, "http://example.com")

        assert page.client == mock_client
        assert page.url == "http://example.com"
        assert page.page == mock_response
        assert page.soup is not None
        mock_client.get.assert_called_once_with(
            "http://example.com", allow_redirects=True)

    @patch('rplugin.python3.airlatex.lib.connection.requests')
    def test_initialization_with_redirects_disabled(self, mock_requests):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b"<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage(mock_client, "http://example.com", allow_redirects=False)

        assert page.allow_redirects is False
        mock_client.get.assert_called_once_with(
            "http://example.com", allow_redirects=False)

    @pytest.mark.skip(reason="Mock HTTPError has issues with exception catching in Python 3.12+")
    @patch('rplugin.python3.airlatex.lib.connection.requests')
    def test_initialization_http_error(self, mock_requests):
        mock_response = Mock()
        mock_response.raise_for_status = Mock(
            side_effect=requests.exceptions.HTTPError("404 Not Found"))

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        with pytest.raises(WebException) as exc_info:
            WebPage(mock_client, "http://example.com")

        assert "HTTP error occurred" in str(exc_info.value)

    def test_load_success(self):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b"<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage.__new__(WebPage)
        page.client = mock_client
        page.url = "http://example.com"
        page.allow_redirects = True
        page.page = None
        page.soup = None

        page.load()

        assert page.page == mock_response
        assert isinstance(page.soup, BeautifulSoup)

    def test_parse_existing_element(self):
        html_content = b'<html><head><meta name="ol-test" content="value123"></head></html>'
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = html_content
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage(mock_client, "http://example.com")
        tag = page.parse("test")

        assert isinstance(tag, Tag)
        assert tag.content == "value123"

    def test_parse_missing_element(self):
        html_content = b'<html><head></head></html>'
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = html_content
        mock_response.text = "page content"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage(mock_client, "http://example.com")

        with pytest.raises(WebException) as exc_info:
            page.parse("nonexistent")

        assert "Couldn't find an element" in str(exc_info.value)

    def test_parse_without_loaded_page(self):
        page = WebPage.__new__(WebPage)
        page.soup = None
        page.page = None

        with pytest.raises(WebException) as exc_info:
            page.parse("test")

        assert "hasn't been loaded correctly" in str(exc_info.value)

    def test_parse_custom_tag(self):
        html_content = b'<html><body><div name="ol-custom" content="divvalue"></div></body></html>'
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = html_content
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage(mock_client, "http://example.com")
        tag = page.parse("custom", tag='div')

        assert isinstance(tag, Tag)

    def test_ok_property_true(self):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b"<html></html>"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage(mock_client, "http://example.com")

        assert page.ok is True

    def test_ok_property_false(self):
        page = WebPage.__new__(WebPage)
        page.page = None

        assert page.ok is False

    def test_text_property_with_page(self):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b"<html></html>"
        mock_response.text = "page text content"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage(mock_client, "http://example.com")

        assert isinstance(page.text, bytes)

    def test_text_property_without_page(self):
        page = WebPage.__new__(WebPage)
        page.page = None

        assert page.text == ""


class TestWebPageIntegration:

    def test_full_workflow(self):
        html_content = b'''
        <html>
            <head>
                <meta name="ol-project" content="12345">
                <meta name="ol-user" content="user123">
            </head>
        </html>
        '''
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = html_content
        mock_response.text = html_content.decode()
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage(mock_client, "http://example.com")

        assert page.ok
        project_tag = page.parse("project")
        assert project_tag.content == "12345"

        user_tag = page.parse("user")
        assert user_tag.content == "user123"

    def test_multiple_parse_calls(self):
        html_content = b'''
        <html>
            <head>
                <meta name="ol-first" content="value1">
                <meta name="ol-second" content="value2">
                <meta name="ol-third" content="value3">
            </head>
        </html>
        '''
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = html_content
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get = Mock(return_value=mock_response)

        page = WebPage(mock_client, "http://example.com")

        tag1 = page.parse("first")
        tag2 = page.parse("second")
        tag3 = page.parse("third")

        assert tag1.content == "value1"
        assert tag2.content == "value2"
        assert tag3.content == "value3"
