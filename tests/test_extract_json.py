import pytest
from unittest import TestCase

from academia_mcp.utils import extract_json


class TestJSONExtractor(TestCase):
    def test_simple_json_code_block(self) -> None:
        text = """Here's the data:
        ```json
        {"name": "John", "age": 30}
        ```
        """
        expected = {"name": "John", "age": 30}
        result = extract_json(text)
        assert result == expected

    def test_json_code_block_case_insensitive(self) -> None:
        text = """```JSON
        {"status": "success"}
        ```"""
        expected = {"status": "success"}
        result = extract_json(text)
        assert result == expected

    def test_generic_code_block(self) -> None:
        text = """Here's the response:
        ```
        {"message": "Hello World", "code": 200}
        ```
        """
        expected = {"message": "Hello World", "code": 200}
        result = extract_json(text)
        assert result == expected

    def test_direct_json_parsing(self) -> None:
        text = '{"direct": true, "value": 42}'
        expected = {"direct": True, "value": 42}
        result = extract_json(text)
        assert result == expected

    def test_json_array(self) -> None:
        text = """The items are:
        ```json
        [1, 2, 3, {"name": "test"}]
        ```
        """
        expected = [1, 2, 3, {"name": "test"}]
        result = extract_json(text)
        assert result == expected

    def test_nested_json_objects(self) -> None:
        text = """```json
        {
            "user": {
                "id": 123,
                "profile": {
                    "name": "Alice",
                    "settings": {"theme": "dark"}
                }
            },
            "metadata": {"version": "1.0"}
        }
        ```"""
        expected = {
            "user": {"id": 123, "profile": {"name": "Alice", "settings": {"theme": "dark"}}},
            "metadata": {"version": "1.0"},
        }
        result = extract_json(text)
        assert result == expected

    def test_json_with_trailing_comma(self) -> None:
        text = """{
            "name": "test",
            "values": [1, 2, 3,],
            "nested": {"a": 1,},
        }"""
        expected = {"name": "test", "values": [1, 2, 3], "nested": {"a": 1}}
        result = extract_json(text)
        assert result == expected

    def test_json_with_single_quotes(self) -> None:
        text = """json: {
            'name': 'John',
            'age': 30,
            'active': true
        }"""
        expected = {"name": "John", "age": 30, "active": True}
        result = extract_json(text)
        assert result == expected

    def test_json_with_comments(self) -> None:
        text = """{
            "name": "test", // This is a comment
            /* Multi-line
               comment */
            "value": 42
        }"""
        expected = {"name": "test", "value": 42}
        result = extract_json(text)
        assert result == expected

    def test_json_with_prefix_text(self) -> None:
        prefixes = [
            "json: ",
            "JSON: ",
            "Here is the JSON: ",
            "The JSON is: ",
            "Result: ",
            "Output: ",
            "Response: ",
        ]

        base_json = {"test": "value"}

        for prefix in prefixes:
            text = prefix + '{"test": "value"}'
            result = extract_json(text)
            assert result == base_json, f"Failed for prefix: {prefix}"

    def test_empty_input(self) -> None:
        with pytest.raises(AssertionError):
            extract_json("")

        with pytest.raises(AssertionError):
            extract_json(None)  # type: ignore

    def test_non_string_input(self) -> None:
        with pytest.raises(AssertionError):
            extract_json(123)  # type: ignore

        with pytest.raises(AssertionError):
            extract_json(["not", "a", "string"])  # type: ignore

    def test_no_json_found(self) -> None:
        text = "This is just plain text with no JSON whatsoever."
        result = extract_json(text)
        assert result is None

    def test_malformed_json_in_code_block(self) -> None:
        text = """```json
        {"name": "test", "invalid": }
        ```"""

        result = extract_json(text)
        assert result is None

    def test_json_with_special_characters(self) -> None:
        text = """```json
        {
            "message": "Hello 🌍",
            "path": "/users/test",
            "emoji": "😀",
            "unicode": "café"
        }
        ```"""

        expected = {"message": "Hello 🌍", "path": "/users/test", "emoji": "😀", "unicode": "café"}

        result = extract_json(text)
        assert result == expected

    def test_json_with_numbers_and_booleans(self) -> None:
        text = """```json
        {
            "integer": 42,
            "float": 3.14159,
            "boolean_true": true,
            "boolean_false": false,
            "null_value": null,
            "negative": -100
        }
        ```"""

        expected = {
            "integer": 42,
            "float": 3.14159,
            "boolean_true": True,
            "boolean_false": False,
            "null_value": None,
            "negative": -100,
        }

        result = extract_json(text)
        assert result == expected

    def test_complex_mixed_content(self) -> None:
        text = """
        Based on your request, here's the user data analysis:

        The system found 3 users in the database. Here's the detailed breakdown:

        ```json
        {
            "total_users": 3,
            "users": [
                {
                    "id": 1,
                    "name": "Alice Johnson",
                    "email": "alice@example.com",
                    "active": true,
                    "roles": ["user", "moderator"]
                },
                {
                    "id": 2,
                    "name": "Bob Smith",
                    "email": "bob@example.com",
                    "active": false,
                    "roles": ["user"]
                }
            ],
            "metadata": {
                "generated_at": "2024-01-15T10:30:00Z",
                "query_time_ms": 45
            }
        }
        ```

        This data was generated from the user management system.
        """

        result = extract_json(text)

        assert isinstance(result, dict)
        assert result["total_users"] == 3
        assert len(result["users"]) == 2
        assert "metadata" in result

        alice = result["users"][0]
        assert alice["name"] == "Alice Johnson"
        assert alice["roles"] == ["user", "moderator"]
