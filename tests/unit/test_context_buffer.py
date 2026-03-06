import pytest

from telegram_collector.context_buffer import ContextBuffer


class TestContextBuffer:
    def test_add_and_get(self):
        buf = ContextBuffer(max_size=5)
        buf.add("chat1", "hello")
        buf.add("chat1", "world")
        assert buf.get_context("chat1") == ["hello", "world"]

    def test_max_size_respected(self):
        buf = ContextBuffer(max_size=3)
        for i in range(5):
            buf.add("chat1", f"msg{i}")
        ctx = buf.get_context("chat1")
        assert len(ctx) == 3
        assert ctx == ["msg2", "msg3", "msg4"]

    def test_separate_chats(self):
        buf = ContextBuffer(max_size=5)
        buf.add("chat1", "a")
        buf.add("chat2", "b")
        assert buf.get_context("chat1") == ["a"]
        assert buf.get_context("chat2") == ["b"]

    def test_empty_chat(self):
        buf = ContextBuffer(max_size=5)
        assert buf.get_context("nonexistent") == []

    def test_clear_specific_chat(self):
        buf = ContextBuffer(max_size=5)
        buf.add("chat1", "a")
        buf.add("chat2", "b")
        buf.clear("chat1")
        assert buf.get_context("chat1") == []
        assert buf.get_context("chat2") == ["b"]

    def test_clear_all(self):
        buf = ContextBuffer(max_size=5)
        buf.add("chat1", "a")
        buf.add("chat2", "b")
        buf.clear()
        assert buf.get_context("chat1") == []
        assert buf.get_context("chat2") == []

    def test_default_max_size(self):
        buf = ContextBuffer()
        for i in range(10):
            buf.add("chat1", f"msg{i}")
        assert len(buf.get_context("chat1")) == 5

    def test_returns_list_copy(self):
        buf = ContextBuffer(max_size=5)
        buf.add("chat1", "a")
        ctx = buf.get_context("chat1")
        ctx.append("extra")
        assert buf.get_context("chat1") == ["a"]
