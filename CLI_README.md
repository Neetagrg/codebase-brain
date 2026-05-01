# Codebase Brain CLI

A professional command-line tool for generating and maintaining AI-friendly codebase documentation. Works with **any** codebase to create comprehensive `AGENTS.md` files that help AI coding assistants understand your project.

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install codebase-brain

# Or install from source
git clone https://github.com/yourusername/codebase-brain.git
cd codebase-brain
pip install -e .
```

### Basic Usage

```bash
# Initialize in any repository
cd /path/to/your/project
codebase-brain init

# Validate your documentation
codebase-brain validate

# Query your documentation
codebase-brain query "how to run tests"

# Keep it updated
codebase-brain update
```

## 📋 Commands

### `init` - Initialize Codebase Brain

Generate `AGENTS.md` for any repository with automatic analysis and structure creation.

```bash
codebase-brain init [REPO_PATH]

Options:
  --force    Overwrite existing AGENTS.md
  --verbose  Show detailed progress
  --help     Show help message
```

**What it does:**
1. Analyzes repository structure and detects languages
2. Identifies entry points, dependencies, and build systems
3. Generates comprehensive `AGENTS.md` with best practices
4. Creates `bob-copilot/` folder structure
5. Provides getting started guide with next steps

**Example:**
```bash
# Initialize current directory
codebase-brain init

# Initialize specific repository
codebase-brain init /path/to/repo --verbose

# Force overwrite existing documentation
codebase-brain init . --force
```

### `validate` - Validate Documentation Quality

Run validation framework with quality metrics and CI-friendly exit codes.

```bash
codebase-brain validate

Options:
  --ci       CI-friendly JSON output with exit codes
  --verbose  Show detailed validation info
  --help     Show help message
```

**Quality Metrics:**
- File size and line count
- Section completeness (required sections present)
- Code block count (examples included)
- Overall quality score

**Exit Codes:**
- `0` - Valid and complete
- `1` - Needs improvement

**Example:**
```bash
# Interactive validation
codebase-brain validate

# CI/CD pipeline usage
codebase-brain validate --ci
if [ $? -eq 0 ]; then
  echo "Documentation is valid!"
fi
```

### `query` - Search Documentation

Search `AGENTS.md` from command line with file:line references and command suggestions.

```bash
codebase-brain query <QUESTION>

Options:
  --format [text|json]  Output format (default: text)
  --verbose            Show context around matches
  --help               Show help message
```

**Features:**
- Full-text search across all sections
- Line number references for quick navigation
- Context display for better understanding
- Suggested slash commands based on query

**Example:**
```bash
# Search for testing information
codebase-brain query "how to run tests"

# Get JSON output for scripting
codebase-brain query "debugging" --format json

# Show full context
codebase-brain query "architecture" --verbose
```

### `update` - Detect and Fix Drift

Detect drift between codebase and documentation, update only changed sections.

```bash
codebase-brain update

Options:
  --dry-run  Show what would be updated without making changes
  --verbose  Show detailed drift analysis
  --help     Show help message
```

**Drift Detection:**
- New files and entry points
- Deleted or moved files
- Modified project structure
- New dependencies added
- Configuration changes

**Smart Updates:**
- Only updates changed sections
- Preserves manual edits
- Shows recommendations before applying

**Example:**
```bash
# Check for drift
codebase-brain update --dry-run

# Apply updates
codebase-brain update

# Verbose drift analysis
codebase-brain update --verbose
```

## 🎯 Use Cases

### For New Projects

```bash
# Start with great documentation from day one
cd my-new-project
codebase-brain init
git add bob-copilot/
git commit -m "Add AI-friendly documentation"
```

### For Existing Projects

```bash
# Retrofit existing codebases
cd legacy-project
codebase-brain init --force
codebase-brain validate
# Review and customize AGENTS.md
git add bob-copilot/
git commit -m "Add Codebase Brain documentation"
```

### In CI/CD Pipelines

```yaml
# .github/workflows/validate-docs.yml
name: Validate Documentation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install codebase-brain
      - run: codebase-brain validate --ci
```

### For Team Onboarding

```bash
# New team member setup
git clone <repo-url>
cd <repo>
codebase-brain query "getting started"
codebase-brain query "how to run locally"
```

## 🛠️ Configuration

Create `.codebase-brain.json` in your repository root:

```json
{
  "version": "1.0.0",
  "exclude_patterns": [
    "node_modules/**",
    "*.pyc",
    "__pycache__/**"
  ],
  "custom_sections": [
    "Security Guidelines",
    "Deployment Process"
  ],
  "auto_update": true,
  "quality_threshold": 80
}
```

Use with `--config` flag:
```bash
codebase-brain init --config .codebase-brain.json
```

## 📊 Output Structure

After running `init`, your repository will have:

```
your-project/
├── bob-copilot/
│   ├── AGENTS.md          # Main documentation
│   ├── commands/          # Custom slash commands
│   │   └── example.md
│   └── skills/            # Domain expertise
└── .codebase-brain.json   # Optional config
```

## 🔧 Advanced Usage

### Custom Analysis

```python
from codebase_brain_cli import RepositoryAnalyzer

analyzer = RepositoryAnalyzer(Path("/path/to/repo"))
analysis = analyzer.analyze()
print(analysis['languages'])
print(analysis['entry_points'])
```

### Programmatic Validation

```python
from codebase_brain_cli import Validator

validator = Validator(Path("bob-copilot/AGENTS.md"))
is_valid, metrics = validator.validate()
print(f"Quality Score: {metrics['quality_score']:.1f}%")
```

### Custom Queries

```python
from codebase_brain_cli import QueryEngine

engine = QueryEngine(Path("bob-copilot/AGENTS.md"))
results = engine.search("testing")
suggestions = engine.suggest_commands("debug")
```

## 🤝 Integration with AI Tools

### Claude Desktop / Cursor

The generated `AGENTS.md` is automatically recognized by:
- **Claude Desktop** - Add to project context
- **Cursor** - Indexed for AI assistance
- **GitHub Copilot** - Enhanced code suggestions

### Custom AI Workflows

```bash
# Generate context for AI prompts
codebase-brain query "architecture" --format json | jq '.results[0].content'

# Validate before AI-assisted refactoring
codebase-brain validate --ci && ai-refactor.sh
```

## 📈 Best Practices

1. **Run `init` early** - Start with documentation from day one
2. **Validate regularly** - Add to CI/CD pipeline
3. **Update frequently** - Run `update` after major changes
4. **Customize sections** - Add project-specific details
5. **Use queries** - Help team members find information quickly

## 🐛 Troubleshooting

### Command not found

```bash
# Ensure installation completed
pip install --upgrade codebase-brain

# Check installation
which codebase-brain
codebase-brain --version
```

### Import errors

```bash
# Install dependencies
pip install -r requirements.txt

# Or reinstall
pip install --force-reinstall codebase-brain
```

### Permission errors

```bash
# Use user installation
pip install --user codebase-brain

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install codebase-brain
```

## 📚 Documentation

- [Full Documentation](https://github.com/yourusername/codebase-brain#readme)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [API Reference](docs/API.md)

## 🎓 Examples

See the [examples/](examples/) directory for:
- Python project setup
- JavaScript/TypeScript project
- Multi-language monorepo
- CI/CD integration examples

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 🔗 Links

- **GitHub**: https://github.com/yourusername/codebase-brain
- **PyPI**: https://pypi.org/project/codebase-brain/
- **Issues**: https://github.com/yourusername/codebase-brain/issues
- **Discussions**: https://github.com/yourusername/codebase-brain/discussions

---

Made with ❤️ for better AI-assisted development