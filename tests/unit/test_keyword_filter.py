import pytest

from filter_service.keyword_filter import KeywordFilter


class TestKeywordFilter:
    def test_match_single_keyword(self, sample_keywords):
        kf = KeywordFilter(sample_keywords)
        result = kf.match("I know python very well")
        assert "python" in [m.lower() for m in result]

    def test_match_multiple_keywords(self, sample_keywords):
        kf = KeywordFilter(sample_keywords)
        result = kf.match("Ищу разработчик на python для парсинг проекта")
        lower = [m.lower() for m in result]
        assert "python" in lower
        assert "парсинг" in lower

    def test_case_insensitive(self, sample_keywords):
        kf = KeywordFilter(sample_keywords)
        result = kf.match("PYTHON developer needed")
        assert len(result) > 0

    def test_no_match(self, sample_keywords):
        kf = KeywordFilter(sample_keywords)
        result = kf.match("Today the weather is nice")
        assert result == []

    def test_empty_text(self, sample_keywords):
        kf = KeywordFilter(sample_keywords)
        result = kf.match("")
        assert result == []

    def test_empty_keywords(self):
        kf = KeywordFilter([])
        result = kf.match("python developer needed")
        assert result == []

    def test_special_characters_escaped(self):
        kf = KeywordFilter(["c++", "c#", "node.js"])
        assert kf.match("I use c++ daily") == ["c++"]
        assert kf.match("node.js backend") == ["node.js"]
        assert kf.match("c# developer") == ["c#"]

    def test_partial_word_match(self):
        kf = KeywordFilter(["python"])
        result = kf.match("pythonic code")
        assert len(result) == 1

    def test_russian_keywords(self):
        kf = KeywordFilter(["парсер", "бот", "разработчик"])
        result = kf.match("Нужен парсер для сайта")
        assert "парсер" in result

    def test_multi_word_keyword(self):
        kf = KeywordFilter(["telegram bot", "rest api"])
        result = kf.match("Need a telegram bot for my business")
        assert "telegram bot" in [m.lower() for m in result]

    def test_keywords_property_returns_copy(self, sample_keywords):
        kf = KeywordFilter(sample_keywords)
        kw = kf.keywords
        kw.append("extra")
        assert "extra" not in kf.keywords

    def test_overlapping_matches(self):
        kf = KeywordFilter(["python", "python developer"])
        result = kf.match("Looking for a python developer")
        assert len(result) >= 1
