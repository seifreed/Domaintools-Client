"""Tests for output formatters."""


from rich.console import Console

from domaintools_client.formatters.output import OutputFormatter


class TestOutputFormatter:
    """Test the OutputFormatter class."""

    def test_init(self):
        """Test formatter initialization."""
        console = Console()
        formatter = OutputFormatter(console)
        assert formatter.console == console

    def test_format_json(self, capsys):
        """Test JSON formatting."""
        console = Console(file=capsys)
        formatter = OutputFormatter(console)

        data = {"test": "value", "number": 42}
        formatter.format_json(data, "Test Data")

        captured = capsys.readouterr()
        assert "Test Data" in captured.out
        assert '"test": "value"' in captured.out
        assert '"number": 42' in captured.out

    def test_format_table_simple(self):
        """Test simple table formatting."""
        console = Console()
        formatter = OutputFormatter(console)

        data = {"name": "example.com", "status": "active", "created": "2000-01-01"}

        # Should not raise exception
        formatter.format_table(data, "Test Table")

    def test_format_table_nested(self):
        """Test table formatting with nested data."""
        console = Console()
        formatter = OutputFormatter(console)

        data = {
            "domain": "example.com",
            "registration": {"created": "2000-01-01", "expires": "2025-01-01"},
            "nameservers": ["ns1.example.com", "ns2.example.com"],
        }

        # Should not raise exception
        formatter.format_table(data, "Nested Data")

    def test_format_tree(self):
        """Test tree formatting."""
        console = Console()
        formatter = OutputFormatter(console)

        data = {
            "domain": "example.com",
            "registration": {
                "created": "2000-01-01",
                "registrant": {"name": "John Doe", "email": "john@example.com"},
            },
        }

        # Should not raise exception
        formatter.format_tree(data, "Domain Info")

    def test_build_tree_with_list(self):
        """Test tree building with list data."""
        console = Console()
        formatter = OutputFormatter(console)

        data = {"domains": ["example.com", "test.com", "demo.com"]}

        # Should not raise exception
        formatter.format_tree(data, "Domains List")

    def test_format_value_string(self):
        """Test value formatting for strings."""
        console = Console()
        formatter = OutputFormatter(console)

        result = formatter._format_value("test string")
        assert "test string" in result

    def test_format_value_number(self):
        """Test value formatting for numbers."""
        console = Console()
        formatter = OutputFormatter(console)

        result = formatter._format_value(42)
        assert "42" in result

    def test_format_value_boolean(self):
        """Test value formatting for booleans."""
        console = Console()
        formatter = OutputFormatter(console)

        result_true = formatter._format_value(True)
        result_false = formatter._format_value(False)

        assert "True" in result_true
        assert "False" in result_false

    def test_format_value_none(self):
        """Test value formatting for None."""
        console = Console()
        formatter = OutputFormatter(console)

        result = formatter._format_value(None)
        assert "N/A" in result

    def test_format_value_list(self):
        """Test value formatting for lists."""
        console = Console()
        formatter = OutputFormatter(console)

        test_list = ["item1", "item2", "item3"]
        result = formatter._format_value(test_list)

        assert "item1" in result
        assert "item2" in result
        assert "item3" in result

    def test_format_domain_profile(self):
        """Test domain profile formatting."""
        console = Console()
        formatter = OutputFormatter(console)

        profile_data = {
            "response": {
                "domain": "example.com",
                "ip_addresses": [
                    {"address": {"ip": "192.0.2.1"}},
                    {"address": {"ip": "192.0.2.2"}},
                ],
                "registrant": "Example Corp",
                "registration": {"created": "2000-01-01", "expires": "2025-01-01"},
                "name_servers": ["ns1.example.com", "ns2.example.com"],
            }
        }

        # Should not raise exception
        formatter.format_domain_profile(profile_data)

    def test_format_search_results(self):
        """Test search results formatting."""
        console = Console()
        formatter = OutputFormatter(console)

        search_data = {
            "results": [
                {"domain": "example.com", "created": "2000-01-01"},
                {"domain": "test.com", "created": "2001-02-02"},
                {"domain": "demo.com", "created": "2002-03-03"},
            ],
            "total_results": 3,
        }

        # Should not raise exception
        formatter.format_search_results(search_data, "Domain")

    def test_format_search_results_empty(self):
        """Test search results formatting with no results."""
        console = Console()
        formatter = OutputFormatter(console)

        empty_data = {"results": [], "total_results": 0}

        # Should not raise exception
        formatter.format_search_results(empty_data, "Domain")

    def test_format_reputation(self):
        """Test reputation formatting."""
        console = Console()
        formatter = OutputFormatter(console)

        reputation_data = {
            "response": {
                "domain": "suspicious.com",
                "risk_score": 85,
                "components": [
                    {"name": "malware", "risk_score": 90},
                    {"name": "phishing", "risk_score": 80},
                ],
            }
        }

        # Should not raise exception
        formatter.format_reputation(reputation_data)

    def test_format_reputation_no_components(self):
        """Test reputation formatting without components."""
        console = Console()
        formatter = OutputFormatter(console)

        reputation_data = {"response": {"domain": "clean.com", "risk_score": 15}}

        # Should not raise exception
        formatter.format_reputation(reputation_data)

    def test_show_progress(self):
        """Test progress indicator."""
        console = Console()
        formatter = OutputFormatter(console)

        # Should not raise exception
        with formatter.show_progress("Processing..."):
            pass

    def test_format_domain_profile_minimal_data(self):
        """Test domain profile formatting with minimal data."""
        console = Console()
        formatter = OutputFormatter(console)

        minimal_data = {"response": {"domain": "minimal.com"}}

        # Should handle missing fields gracefully
        formatter.format_domain_profile(minimal_data)

    def test_format_search_results_missing_fields(self):
        """Test search results formatting with missing fields."""
        console = Console()
        formatter = OutputFormatter(console)

        incomplete_data = {
            "results": [
                {"domain": "example.com"},  # missing created date
                {"created": "2001-01-01"},  # missing domain
            ]
        }

        # Should handle missing fields gracefully
        formatter.format_search_results(incomplete_data, "Domain")
