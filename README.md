# Survey123 Assistant

A library and chat assistant for creating Survey123 forms using object-oriented code.

## Project Structure

```
survey123-assistant/
├── src/
│   ├── xlsform_orm/           # Core library
│   │   ├── __init__.py
│   │   ├── models.py          # Data models
│   │   ├── validators.py      # Validation logic
│   │   ├── constants.py       # Shared constants
│   │   └── export.py          # Excel/YAML export
│   └── assistant/             # Chat assistant
│       ├── __init__.py
│       ├── ui.py              # Streamlit interface
│       ├── api.py             # OpenAI integration
│       └── handlers.py        # Request handlers
├── tests/                     # Test suite
│   ├── conftest.py           # Test fixtures
│   ├── test_models.py
│   ├── test_validators.py
│   └── test_export.py
├── docs/                      # Documentation
├── requirements/              # Dependencies
├── .github/                   # CI/CD workflows
├── pyproject.toml            # Project configuration
├── .pre-commit-config.yaml   # Code quality checks
└── README.md
```

## Features

### XLSForm ORM Library
- Object-oriented interface for Survey123 forms
- Strong type safety with Pydantic models
- Support for all standard XLSForm features
- Excel and YAML export/import
- Comprehensive validation

### Chat Assistant
- Natural language interface
- OpenAI-powered assistance
- Interactive form creation
- File operations support

## Installation

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/survey123-assistant.git
cd survey123-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Development

### Running Tests

Run the full test suite:
```bash
pytest
```

Run with coverage report:
```bash
pytest --cov=xlsform_orm --cov-report=html
```

### Code Quality

The project uses several tools to maintain code quality:

- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **flake8**: Linting
- **pre-commit**: Automated checks

Run all checks manually:
```bash
pre-commit run --all-files
```

### Continuous Integration

GitHub Actions workflows automatically run:
- Tests on multiple Python versions
- Code quality checks
- Package building
- Coverage reporting

## Usage

### XLSForm ORM Library

```python
from xlsform_orm import Survey, Question, QuestionGroup, Choice, QuestionTypes

# Create a simple survey
survey = Survey(
    name="my_survey",
    label="My Survey",
    items=[
        Question(
            type=QuestionTypes.text,
            name="name",
            label="What is your name?"
        ),
        Question(
            type=QuestionTypes.select_one,
            name="color",
            label="Favorite color?",
            choices=[
                Choice(value="r", label="Red"),
                Choice(value="b", label="Blue"),
                Choice(value="g", label="Green"),
            ]
        )
    ]
)

# Export to Excel
survey.save_to_excel("my_survey.xlsx")

# Export to YAML
survey.save_to_yaml("my_survey.yaml")
```

### Chat Assistant

Run the Streamlit app:
```bash
streamlit run src/assistant/ui.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

This project is licensed under the terms of the LICENSE file included in the repository.
