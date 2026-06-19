# Contributing to Screenshot Analytics System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🎯 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected vs actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, Docker version, Python version)
- **Logs** from relevant services

**Example:**
```markdown
**Bug**: OCR analyzer fails to detect 1C applications after update

**Steps to Reproduce**:
1. Add screenshots with 1C interface
2. Wait for analysis
3. Check results - shows as "unknown"

**Expected**: Should detect as "1c" with database name
**Actual**: Classified as unknown

**Environment**: Docker 24.0, Ubuntu 22.04
**Logs**: [attach docker-compose logs output]
```

### Suggesting Enhancements

Enhancement suggestions should include:

- **Use case**: Why is this needed?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches you've thought about
- **Additional context**: Screenshots, examples, references

### Pull Requests

1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

## 💻 Development Guidelines

### Code Style

**Python (PEP 8)**:
```python
# Good
def process_screenshot(image_path: str) -> dict:
    """Process screenshot and return classification results."""
    result = analyze_image(image_path)
    return result

# Bad
def ProcessScreenshot(imagePath):
    result=analyze_image(imagePath)
    return result
```

**Documentation**:
- All functions must have docstrings
- Complex logic should have inline comments
- Update README when adding features

### Testing

Before submitting PR:

1. **Run existing tests**:
```bash
python scripts/test_1c_context.py
python scripts/test_browser_details.py
python scripts/test_bitrix_detection.py
python scripts/test_russian_business.py
```

2. **Add new tests** for your changes:
```python
def test_your_feature():
    """Test description"""
    classifier = KeywordClassifier(MockDB())
    result = classifier.detect_applications("test text")
    assert "expected_app" in result['work_apps']
```

3. **Verify no regressions**:
```bash
docker-compose up -d --build
# Monitor for errors
docker-compose logs -f
```

### Commit Messages

Use clear, descriptive commit messages:

```
✅ Good:
feat: add support for SAP application detection
fix: resolve Bitrix false positive on short words
docs: update README with Quick Start guide
test: add test cases for 1C context detection

❌ Bad:
update code
fix bug
changes
```

**Format**: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, semicolons, etc)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

## 🔧 Development Setup

### Local Environment

```bash
# Clone fork
git clone https://github.com/YOUR_USERNAME/screenshot-analytics-mvp.git
cd screenshot-analytics-mvp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r ocr-analyzer/requirements.txt
pip install -r data-collector/requirements.txt
pip install -r dashboard/requirements.txt

# Setup database
psql -U postgres -c "CREATE DATABASE screenshot_analytics;"
psql -U postgres -d screenshot_analytics -f db-init/init.sql
```

### Docker Development

```bash
# Build with no cache (fresh build)
docker-compose build --no-cache

# Run specific service in foreground for debugging
docker-compose up ocr-analyzer

# View logs with timestamps
docker-compose logs -ft ocr-analyzer
```

## 📊 Areas Needing Contribution

### High Priority

- [ ] **ML-based Classification**: Replace keyword matching with machine learning
- [ ] **Performance Optimization**: Faster OCR processing for large batches
- [ ] **Multi-language Support**: Better support for non-Russian/Cyrillic text
- [ ] **Mobile App**: Companion app for field employees

### Medium Priority

- [ ] **Real-time Notifications**: Slack/Telegram alerts for violations
- [ ] **Advanced Analytics**: Predictive productivity insights
- [ ] **API Documentation**: OpenAPI/Swagger specs
- [ ] **Unit Tests**: Increase test coverage to 80%+

### Low Priority

- [ ] **Dark Mode**: For dashboard UI
- [ ] **Export Formats**: PDF, CSV, Excel reports
- [ ] **Custom Themes**: Dashboard customization
- [ ] **Plugin System**: Extensible classification rules

## 🎓 Learning Resources

- **[Architecture Docs](ARCHITECTURE.md)**: System design overview
- **[OCR Engine Guide](EASYOCR_SETUP.md)**: Understanding OCR pipeline
- **[Keyword Classification](ocr-analyzer/keyword_classifier.py)**: How detection works
- **[Dashboard Code](dashboard/app.py)**: Streamlit implementation

## ❓ Questions?

- 💬 **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/screenshot-analytics-mvp/discussions)
- 🐛 **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/screenshot-analytics-mvp/issues)
- 📧 **Email**: your.email@example.com

---

**Thank you for contributing!** 🎉
