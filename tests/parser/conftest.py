import pytest
import os


absolute_file_path = os.path.abspath(__file__)
directory_path = os.path.dirname(absolute_file_path)


@pytest.fixture
def valid_html():
    with open(directory_path + "\\ebayPages\\200_page.html", "r", encoding="utf-8") as f_o:
        return f_o.read()


@pytest.fixture
def empty_html():
    with open(directory_path + "\\ebayPages\\200_page_without_info.html", "r", encoding="utf-8") as f_o:
        return f_o.read()


@pytest.fixture
def catalog_page():
    with open(directory_path + "\\ebayPages\\200_catalog_page.html", "r", encoding="utf-8") as f_o:
        return f_o.read()
