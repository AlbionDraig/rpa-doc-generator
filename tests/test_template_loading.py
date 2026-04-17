"""Test template loading for PDF and Word generators."""
import json
import pytest
from pathlib import Path


class TestPdfTemplateLoading:
    """Test PDF style template loading."""

    def test_pdf_style_template_file_exists(self):
        """Verify pdf_style.css template file exists."""
        template_path = Path("app/templates/pdf_style.css")
        assert template_path.exists(), "pdf_style.css template not found"

    def test_pdf_style_template_has_content(self):
        """Verify pdf_style.css has CSS content."""
        template_path = Path("app/templates/pdf_style.css")
        content = template_path.read_text(encoding="utf-8")
        assert len(content) > 100, "pdf_style.css is too small"
        assert "@page" in content, "pdf_style.css missing @page rule"
        assert "body {" in content, "pdf_style.css missing body style"

    def test_pdf_generator_load_css_function_exists(self):
        """Verify pdf_generator has _load_pdf_style function."""
        from app.generator.pdf_generator import _load_pdf_style
        assert callable(_load_pdf_style), "_load_pdf_style should be callable"

    def test_pdf_generator_loads_css_style(self):
        """Verify pdf_generator loads CSS from template."""
        from app.generator.pdf_generator import _get_css_style
        css = _get_css_style()
        assert isinstance(css, str), "CSS should be string"
        assert len(css) > 100, "CSS content should not be empty"
        assert "@page" in css, "CSS should contain @page rule"

    def test_pdf_style_template_has_color_definitions(self):
        """Verify pdf_style.css has proper color codes."""
        template_path = Path("app/templates/pdf_style.css")
        content = template_path.read_text(encoding="utf-8")
        assert "#1e293b" in content.lower(), "Should have slate 800 color"
        assert "#4f46e5" in content.lower(), "Should have indigo 600 color"
        assert "#f1f5f9" in content.lower(), "Should have slate 100 color"


class TestWordThemeLoading:
    """Test Word theme template loading."""

    def test_word_theme_template_file_exists(self):
        """Verify word_theme.json template file exists."""
        template_path = Path("app/templates/word_theme.json")
        assert template_path.exists(), "word_theme.json template not found"

    def test_word_theme_template_valid_json(self):
        """Verify word_theme.json is valid JSON."""
        template_path = Path("app/templates/word_theme.json")
        content = template_path.read_text(encoding="utf-8")
        theme = json.loads(content)
        assert isinstance(theme, dict), "word_theme.json should be a dict"

    def test_word_theme_has_required_sections(self):
        """Verify word_theme.json has required sections."""
        template_path = Path("app/templates/word_theme.json")
        theme = json.loads(template_path.read_text(encoding="utf-8"))
        assert "colors" in theme, "word_theme.json should have 'colors' section"
        assert "fonts" in theme, "word_theme.json should have 'fonts' section"
        assert "spacing" in theme, "word_theme.json should have 'spacing' section"
        assert "sizes" in theme, "word_theme.json should have 'sizes' section"

    def test_word_theme_colors_complete(self):
        """Verify word_theme.json has all required colors."""
        template_path = Path("app/templates/word_theme.json")
        theme = json.loads(template_path.read_text(encoding="utf-8"))
        colors = theme["colors"]
        required_colors = ["primary", "secondary", "accent", "dark", "table_header", "text", "muted"]
        for color_name in required_colors:
            assert color_name in colors, f"Missing color: {color_name}"
            assert "hex" in colors[color_name] or "rgb" in colors[color_name], \
                f"Color {color_name} missing hex or rgb value"

    def test_word_generator_load_theme_function_exists(self):
        """Verify word_generator has _load_word_theme function."""
        from app.generator.word_generator import _load_word_theme
        assert callable(_load_word_theme), "_load_word_theme should be callable"

    def test_word_generator_loads_theme(self):
        """Verify word_generator loads theme from JSON."""
        from app.generator.word_generator import _get_theme_colors
        colors = _get_theme_colors()
        assert isinstance(colors, dict), "Theme colors should be dict"
        assert "primary" in colors, "Colors should have primary"
        assert "accent" in colors, "Colors should have accent"

    def test_word_generator_colors_loaded_from_theme(self):
        """Verify word_generator colors are loaded from theme."""
        from app.generator.word_generator import _get_theme_colors
        from docx.shared import RGBColor
        colors = _get_theme_colors()
        primary_rgb = colors["primary"]["rgb"]
        # Verify it's a valid RGB triple
        assert len(primary_rgb) == 3, "RGB should have 3 components"
        assert all(0 <= v <= 255 for v in primary_rgb), "RGB values should be 0-255"


class TestTemplateConsistency:
    """Test that templates are consistent with generator usage."""

    def test_pdf_template_colors_match_word_theme(self):
        """Verify PDF and Word templates use same color values."""
        # Read PDF template
        pdf_path = Path("app/templates/pdf_style.css")
        pdf_content = pdf_path.read_text(encoding="utf-8")
        
        # Read Word theme
        word_path = Path("app/templates/word_theme.json")
        word_theme = json.loads(word_path.read_text(encoding="utf-8"))
        
        # Verify they use same primary color
        primary_hex = word_theme["colors"]["primary"]["hex"]
        assert f"#{primary_hex.lower()}" in pdf_content.lower(), \
            "PDF template should use word theme primary color"

    def test_templates_fallback_behavior_consistent(self):
        """Verify both templates have fallback mechanisms."""
        from app.generator.pdf_generator import _load_pdf_style, _DEFAULT_CSS_STYLE
        from app.generator.word_generator import _load_word_theme, _DEFAULT_THEME
        
        # Both should have defaults
        assert _DEFAULT_CSS_STYLE is not None, "PDF should have default CSS"
        assert _DEFAULT_THEME is not None, "Word should have default theme"
        
        # Both load functions should work
        pdf_style = _load_pdf_style()
        word_theme = _load_word_theme()
        assert pdf_style is not None, "PDF style should load"
        assert word_theme is not None, "Word theme should load"
