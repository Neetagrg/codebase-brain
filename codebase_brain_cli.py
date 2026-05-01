#!/usr/bin/env python3
"""
Codebase Brain CLI - Professional tool for managing AI-friendly codebase documentation.

This CLI tool helps teams create, maintain, and query AGENTS.md files that serve
as comprehensive guides for AI coding assistants like Claude, GitHub Copilot, and Cursor.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import print as rprint

console = Console()

# Version
__version__ = "1.0.0"


class CodebaseBrainError(Exception):
    """Base exception for Codebase Brain CLI errors."""
    pass


class RepositoryAnalyzer:
    """Analyzes repository structure and generates AGENTS.md content."""
    
    def __init__(self, repo_path: Path, verbose: bool = False):
        self.repo_path = repo_path
        self.verbose = verbose
        self.console = console if verbose else Console(quiet=True)
    
    def analyze(self) -> Dict[str, any]:
        """Analyze repository and return structured data."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Analyzing repository...", total=None)
            
            analysis = {
                "project_name": self.repo_path.name,
                "languages": self._detect_languages(),
                "structure": self._analyze_structure(),
                "dependencies": self._detect_dependencies(),
                "entry_points": self._find_entry_points(),
                "test_framework": self._detect_test_framework(),
                "build_system": self._detect_build_system(),
            }
            
            progress.update(task, completed=True)
            return analysis
    
    def _detect_languages(self) -> List[str]:
        """Detect programming languages used in the repository."""
        extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
        }
        
        found_languages = set()
        for ext, lang in extensions.items():
            if list(self.repo_path.rglob(f"*{ext}")):
                found_languages.add(lang)
        
        return sorted(found_languages)
    
    def _analyze_structure(self) -> Dict[str, List[str]]:
        """Analyze directory structure."""
        structure = {
            "source_dirs": [],
            "test_dirs": [],
            "config_files": [],
            "doc_dirs": [],
        }
        
        # Common patterns
        source_patterns = ['src', 'lib', 'app', 'core']
        test_patterns = ['test', 'tests', 'spec', '__tests__']
        doc_patterns = ['docs', 'doc', 'documentation']
        
        for item in self.repo_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                name_lower = item.name.lower()
                if any(p in name_lower for p in source_patterns):
                    structure["source_dirs"].append(item.name)
                elif any(p in name_lower for p in test_patterns):
                    structure["test_dirs"].append(item.name)
                elif any(p in name_lower for p in doc_patterns):
                    structure["doc_dirs"].append(item.name)
        
        # Config files
        config_patterns = [
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod',
            'pom.xml', 'build.gradle', 'Gemfile', 'composer.json',
            'setup.py', 'pyproject.toml', 'tsconfig.json'
        ]
        
        for pattern in config_patterns:
            if (self.repo_path / pattern).exists():
                structure["config_files"].append(pattern)
        
        return structure
    
    def _detect_dependencies(self) -> Dict[str, str]:
        """Detect dependency management files."""
        dep_files = {
            'package.json': 'npm/yarn',
            'requirements.txt': 'pip',
            'Pipfile': 'pipenv',
            'poetry.lock': 'poetry',
            'Cargo.toml': 'cargo',
            'go.mod': 'go modules',
            'pom.xml': 'maven',
            'build.gradle': 'gradle',
            'Gemfile': 'bundler',
        }
        
        found = {}
        for file, manager in dep_files.items():
            if (self.repo_path / file).exists():
                found[file] = manager
        
        return found
    
    def _find_entry_points(self) -> List[str]:
        """Find main entry points of the application."""
        entry_patterns = [
            'main.py', 'app.py', '__main__.py',
            'index.js', 'main.js', 'app.js',
            'main.go', 'main.rs', 'Main.java',
        ]
        
        entry_points = []
        for pattern in entry_patterns:
            matches = list(self.repo_path.rglob(pattern))
            entry_points.extend([str(m.relative_to(self.repo_path)) for m in matches])
        
        return entry_points
    
    def _detect_test_framework(self) -> Optional[str]:
        """Detect testing framework used."""
        frameworks = {
            'pytest': ['pytest.ini', 'conftest.py'],
            'unittest': ['test_*.py'],
            'jest': ['jest.config.js'],
            'mocha': ['.mocharc.json'],
            'junit': ['pom.xml'],
        }
        
        for framework, indicators in frameworks.items():
            for indicator in indicators:
                if list(self.repo_path.rglob(indicator)):
                    return framework
        
        return None
    
    def _detect_build_system(self) -> Optional[str]:
        """Detect build system."""
        build_files = {
            'Makefile': 'make',
            'CMakeLists.txt': 'cmake',
            'build.gradle': 'gradle',
            'pom.xml': 'maven',
            'Cargo.toml': 'cargo',
        }
        
        for file, system in build_files.items():
            if (self.repo_path / file).exists():
                return system
        
        return None


class AgentsGenerator:
    """Generates AGENTS.md content from repository analysis."""
    
    def __init__(self, analysis: Dict[str, any]):
        self.analysis = analysis
    
    def generate(self) -> str:
        """Generate complete AGENTS.md content."""
        sections = [
            self._generate_header(),
            self._generate_overview(),
            self._generate_architecture(),
            self._generate_development_guide(),
            self._generate_testing_guide(),
            self._generate_common_tasks(),
            self._generate_troubleshooting(),
        ]
        
        return "\n\n".join(sections)
    
    def _generate_header(self) -> str:
        """Generate header section."""
        return f"""# {self.analysis['project_name']} - AI Agent Guide

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version:** 1.0.0

This document serves as a comprehensive guide for AI coding assistants working with this codebase.
It provides context, patterns, and best practices to help AI agents understand and modify the code effectively."""
    
    def _generate_overview(self) -> str:
        """Generate project overview."""
        languages = ", ".join(self.analysis['languages']) if self.analysis['languages'] else "Not detected"
        
        return f"""## Project Overview

### Technology Stack
- **Languages:** {languages}
- **Build System:** {self.analysis.get('build_system', 'Not detected')}
- **Test Framework:** {self.analysis.get('test_framework', 'Not detected')}

### Repository Structure
```
{self.analysis['project_name']}/
├── {'/\n├── '.join(self.analysis['structure']['source_dirs'])} (source code)
├── {'/\n├── '.join(self.analysis['structure']['test_dirs'])} (tests)
└── {'/\n└── '.join(self.analysis['structure']['doc_dirs'])} (documentation)
```

### Entry Points
{self._format_list(self.analysis['entry_points']) if self.analysis['entry_points'] else '- To be documented'}"""
    
    def _generate_architecture(self) -> str:
        """Generate architecture section."""
        return """## Architecture

### Core Components
<!-- Document your main modules/components here -->

### Data Flow
<!-- Describe how data flows through your system -->

### Key Design Patterns
<!-- List important design patterns used -->"""
    
    def _generate_development_guide(self) -> str:
        """Generate development guide."""
        deps = self.analysis['dependencies']
        setup_cmd = self._get_setup_command(deps)
        
        return f"""## Development Guide

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd {self.analysis['project_name']}

# Install dependencies
{setup_cmd}
```

### Running the Application
```bash
# Add your run commands here
```

### Code Style
- Follow language-specific conventions
- Use meaningful variable names
- Add comments for complex logic
- Keep functions focused and small"""
    
    def _generate_testing_guide(self) -> str:
        """Generate testing guide."""
        test_cmd = self._get_test_command()
        
        return f"""## Testing Guide

### Running Tests
```bash
{test_cmd}
```

### Writing Tests
- Write tests for new features
- Maintain test coverage above 80%
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)"""
    
    def _generate_common_tasks(self) -> str:
        """Generate common tasks section."""
        return """## Common Tasks

### Adding a New Feature
1. Create a feature branch
2. Implement the feature
3. Add tests
4. Update documentation
5. Submit pull request

### Debugging
- Check logs in [log location]
- Use debugger breakpoints
- Review error messages carefully

### Performance Optimization
- Profile before optimizing
- Focus on bottlenecks
- Measure improvements"""
    
    def _generate_troubleshooting(self) -> str:
        """Generate troubleshooting section."""
        return """## Troubleshooting

### Common Issues

#### Build Failures
- Ensure all dependencies are installed
- Check for version conflicts
- Clear build cache

#### Test Failures
- Run tests individually to isolate issues
- Check for environment-specific problems
- Review recent changes

### Getting Help
- Check documentation in `/docs`
- Review existing issues
- Ask team members"""
    
    def _format_list(self, items: List[str]) -> str:
        """Format list items."""
        return "\n".join(f"- `{item}`" for item in items)
    
    def _get_setup_command(self, deps: Dict[str, str]) -> str:
        """Get appropriate setup command."""
        if 'package.json' in deps:
            return "npm install"
        elif 'requirements.txt' in deps:
            return "pip install -r requirements.txt"
        elif 'Pipfile' in deps:
            return "pipenv install"
        elif 'poetry.lock' in deps:
            return "poetry install"
        elif 'Cargo.toml' in deps:
            return "cargo build"
        elif 'go.mod' in deps:
            return "go mod download"
        else:
            return "# Add your setup command here"
    
    def _get_test_command(self) -> str:
        """Get appropriate test command."""
        framework = self.analysis.get('test_framework')
        
        commands = {
            'pytest': 'pytest',
            'unittest': 'python -m unittest discover',
            'jest': 'npm test',
            'mocha': 'npm test',
            'junit': 'mvn test',
        }
        
        return commands.get(framework, '# Add your test command here')


class Validator:
    """Validates AGENTS.md quality and completeness."""
    
    def __init__(self, agents_path: Path, verbose: bool = False):
        self.agents_path = agents_path
        self.verbose = verbose
        self.console = console if verbose else Console(quiet=True)
    
    def validate(self) -> Tuple[bool, Dict[str, any]]:
        """Validate AGENTS.md and return results."""
        if not self.agents_path.exists():
            return False, {"error": "AGENTS.md not found"}
        
        content = self.agents_path.read_text()
        
        metrics = {
            "file_size": len(content),
            "line_count": len(content.splitlines()),
            "sections": self._count_sections(content),
            "code_blocks": self._count_code_blocks(content),
            "links": self._count_links(content),
            "completeness": 0,
            "quality_score": 0,
        }
        
        # Calculate completeness
        required_sections = [
            "Project Overview", "Architecture", "Development Guide",
            "Testing", "Common Tasks"
        ]
        found_sections = sum(1 for s in required_sections if s.lower() in content.lower())
        metrics["completeness"] = (found_sections / len(required_sections)) * 100
        
        # Calculate quality score
        quality_factors = [
            metrics["line_count"] > 100,  # Substantial content
            metrics["code_blocks"] > 3,   # Has examples
            metrics["sections"] > 5,      # Well structured
            metrics["completeness"] > 80, # Complete
        ]
        metrics["quality_score"] = (sum(quality_factors) / len(quality_factors)) * 100
        
        is_valid = metrics["completeness"] >= 60 and metrics["quality_score"] >= 50
        
        return is_valid, metrics
    
    def _count_sections(self, content: str) -> int:
        """Count markdown sections."""
        return len(re.findall(r'^#{1,3}\s+', content, re.MULTILINE))
    
    def _count_code_blocks(self, content: str) -> int:
        """Count code blocks."""
        return len(re.findall(r'```', content)) // 2
    
    def _count_links(self, content: str) -> int:
        """Count markdown links."""
        return len(re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content))


class QueryEngine:
    """Search and query AGENTS.md content."""
    
    def __init__(self, agents_path: Path):
        self.agents_path = agents_path
        self.content = ""
        self.sections = {}
        
        if agents_path.exists():
            self.content = agents_path.read_text()
            self._parse_sections()
    
    def _parse_sections(self):
        """Parse content into sections."""
        lines = self.content.splitlines()
        current_section = "header"
        current_content = []
        
        for i, line in enumerate(lines):
            if line.startswith('#'):
                if current_content:
                    self.sections[current_section] = {
                        "content": "\n".join(current_content),
                        "line": i - len(current_content)
                    }
                current_section = line.strip('#').strip()
                current_content = [line]
            else:
                current_content.append(line)
        
        if current_content:
            self.sections[current_section] = {
                "content": "\n".join(current_content),
                "line": len(lines) - len(current_content)
            }
    
    def search(self, query: str) -> List[Dict[str, any]]:
        """Search for query in AGENTS.md."""
        results = []
        query_lower = query.lower()
        
        for section_name, section_data in self.sections.items():
            content = section_data["content"]
            if query_lower in content.lower():
                # Find specific lines
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        results.append({
                            "section": section_name,
                            "line": section_data["line"] + i,
                            "content": line.strip(),
                            "context": self._get_context(lines, i)
                        })
        
        return results
    
    def _get_context(self, lines: List[str], index: int, context_size: int = 2) -> str:
        """Get surrounding context for a line."""
        start = max(0, index - context_size)
        end = min(len(lines), index + context_size + 1)
        return "\n".join(lines[start:end])
    
    def suggest_commands(self, query: str) -> List[str]:
        """Suggest relevant slash commands based on query."""
        suggestions = []
        query_lower = query.lower()
        
        command_keywords = {
            "debug": ["/debug-joint", "/lua-trace"],
            "test": ["/run-tests", "/test-coverage"],
            "build": ["/build", "/compile"],
            "deploy": ["/deploy", "/release"],
            "refactor": ["/refactor", "/optimize"],
        }
        
        for keyword, commands in command_keywords.items():
            if keyword in query_lower:
                suggestions.extend(commands)
        
        return suggestions[:3]  # Return top 3


class DriftDetector:
    """Detects drift between codebase and AGENTS.md."""
    
    def __init__(self, repo_path: Path, agents_path: Path):
        self.repo_path = repo_path
        self.agents_path = agents_path
    
    def detect_drift(self) -> Dict[str, any]:
        """Detect changes in codebase that may require AGENTS.md updates."""
        drift = {
            "new_files": [],
            "deleted_files": [],
            "modified_structure": False,
            "new_dependencies": [],
            "recommendations": []
        }
        
        # This is a simplified version - in production, you'd compare
        # against a stored snapshot of the previous state
        
        analyzer = RepositoryAnalyzer(self.repo_path, verbose=False)
        current_analysis = analyzer.analyze()
        
        # Check if AGENTS.md mentions current entry points
        if self.agents_path.exists():
            content = self.agents_path.read_text()
            for entry_point in current_analysis['entry_points']:
                if entry_point not in content:
                    drift["new_files"].append(entry_point)
                    drift["recommendations"].append(
                        f"Document new entry point: {entry_point}"
                    )
        
        return drift


# CLI Commands

@click.group()
@click.version_option(version=__version__)
@click.option('--config', type=click.Path(), help='Path to config file')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """Codebase Brain - AI-friendly codebase documentation tool.
    
    Generate, maintain, and query AGENTS.md files for better AI assistance.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config


@cli.command()
@click.argument('repo_path', type=click.Path(exists=True), default='.')
@click.option('--force', is_flag=True, help='Overwrite existing AGENTS.md')
@click.pass_context
def init(ctx, repo_path, force):
    """Initialize Codebase Brain for a repository.
    
    Analyzes the repository structure and generates AGENTS.md with
    comprehensive documentation for AI coding assistants.
    
    Example:
        codebase-brain init /path/to/repo
        codebase-brain init . --force
    """
    verbose = ctx.obj['verbose']
    repo_path = Path(repo_path).resolve()
    
    try:
        console.print(Panel.fit(
            "[bold blue]Codebase Brain Initialization[/bold blue]\n"
            f"Repository: {repo_path}",
            border_style="blue"
        ))
        
        # Check if AGENTS.md already exists
        bob_dir = repo_path / "bob-copilot"
        agents_file = bob_dir / "AGENTS.md"
        
        if agents_file.exists() and not force:
            console.print("[yellow]⚠ AGENTS.md already exists. Use --force to overwrite.[/yellow]")
            raise click.Abort()
        
        # Analyze repository
        console.print("\n[cyan]Step 1:[/cyan] Analyzing repository structure...")
        analyzer = RepositoryAnalyzer(repo_path, verbose=verbose)
        analysis = analyzer.analyze()
        
        # Generate AGENTS.md
        console.print("[cyan]Step 2:[/cyan] Generating AGENTS.md...")
        generator = AgentsGenerator(analysis)
        content = generator.generate()
        
        # Create directory structure
        console.print("[cyan]Step 3:[/cyan] Creating bob-copilot/ structure...")
        bob_dir.mkdir(exist_ok=True)
        (bob_dir / "commands").mkdir(exist_ok=True)
        (bob_dir / "skills").mkdir(exist_ok=True)
        
        # Write AGENTS.md
        agents_file.write_text(content)
        
        # Create sample command
        sample_command = bob_dir / "commands" / "example.md"
        sample_command.write_text("""# Example Command

## Purpose
Describe what this command does

## Usage
```
/example <parameter>
```

## Implementation
Steps to execute this command
""")
        
        # Success message
        console.print("\n[green]✓ Initialization complete![/green]\n")
        
        # Getting started guide
        guide = f"""[bold]Next Steps:[/bold]

1. Review and customize [cyan]{agents_file.relative_to(repo_path)}[/cyan]
2. Add project-specific details to each section
3. Create custom slash commands in [cyan]bob-copilot/commands/[/cyan]
4. Add domain expertise in [cyan]bob-copilot/skills/[/cyan]

[bold]Validate your setup:[/bold]
  codebase-brain validate

[bold]Query your documentation:[/bold]
  codebase-brain query "how to run tests"

[bold]Keep it updated:[/bold]
  codebase-brain update
"""
        console.print(Panel(guide, title="Getting Started", border_style="green"))
        
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option('--ci', is_flag=True, help='CI-friendly output with exit codes')
@click.pass_context
def validate(ctx, ci):
    """Validate AGENTS.md quality and completeness.
    
    Checks for required sections, code examples, and overall quality.
    Returns exit code 0 for valid, 1 for invalid (useful in CI/CD).
    
    Example:
        codebase-brain validate
        codebase-brain validate --ci
    """
    verbose = ctx.obj['verbose']
    repo_path = Path.cwd()
    agents_file = repo_path / "bob-copilot" / "AGENTS.md"
    
    try:
        if not ci:
            console.print(Panel.fit(
                "[bold blue]Validating AGENTS.md[/bold blue]",
                border_style="blue"
            ))
        
        validator = Validator(agents_file, verbose=verbose)
        is_valid, metrics = validator.validate()
        
        if ci:
            # CI-friendly output
            print(json.dumps(metrics, indent=2))
        else:
            # Rich output
            table = Table(title="Validation Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_column("Status", style="green")
            
            table.add_row("File Size", f"{metrics.get('file_size', 0)} bytes", "✓")
            table.add_row("Line Count", str(metrics.get('line_count', 0)), "✓")
            table.add_row("Sections", str(metrics.get('sections', 0)), "✓")
            table.add_row("Code Blocks", str(metrics.get('code_blocks', 0)), "✓")
            table.add_row(
                "Completeness",
                f"{metrics.get('completeness', 0):.1f}%",
                "✓" if metrics.get('completeness', 0) >= 60 else "✗"
            )
            table.add_row(
                "Quality Score",
                f"{metrics.get('quality_score', 0):.1f}%",
                "✓" if metrics.get('quality_score', 0) >= 50 else "✗"
            )
            
            console.print(table)
            
            if is_valid:
                console.print("\n[green]✓ AGENTS.md is valid and complete![/green]")
            else:
                console.print("\n[yellow]⚠ AGENTS.md needs improvement[/yellow]")
                console.print("\nRecommendations:")
                if metrics.get('completeness', 0) < 60:
                    console.print("  • Add missing required sections")
                if metrics.get('code_blocks', 0) < 3:
                    console.print("  • Include more code examples")
                if metrics.get('line_count', 0) < 100:
                    console.print("  • Expand documentation with more details")
        
        sys.exit(0 if is_valid else 1)
        
    except Exception as e:
        if ci:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]✗ Error: {str(e)}[/red]")
            if verbose:
                console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument('question')
@click.option('--format', type=click.Choice(['text', 'json']), default='text')
@click.pass_context
def query(ctx, question, format):
    """Search AGENTS.md for relevant information.
    
    Searches through AGENTS.md and returns relevant sections with
    file:line references and suggested slash commands.
    
    Example:
        codebase-brain query "how to run tests"
        codebase-brain query "debugging" --format json
    """
    verbose = ctx.obj['verbose']
    repo_path = Path.cwd()
    agents_file = repo_path / "bob-copilot" / "AGENTS.md"
    
    try:
        if not agents_file.exists():
            console.print("[red]✗ AGENTS.md not found. Run 'codebase-brain init' first.[/red]")
            sys.exit(1)
        
        engine = QueryEngine(agents_file)
        results = engine.search(question)
        suggestions = engine.suggest_commands(question)
        
        if format == 'json':
            output = {
                "query": question,
                "results": results,
                "suggested_commands": suggestions
            }
            print(json.dumps(output, indent=2))
        else:
            console.print(Panel.fit(
                f"[bold blue]Query:[/bold blue] {question}",
                border_style="blue"
            ))
            
            if results:
                console.print(f"\n[green]Found {len(results)} result(s):[/green]\n")
                
                for i, result in enumerate(results, 1):
                    console.print(f"[bold]{i}. {result['section']}[/bold]")
                    console.print(f"   [dim]Line {result['line']}[/dim]")
                    console.print(f"   {result['content']}\n")
                    
                    if verbose:
                        console.print("[dim]Context:[/dim]")
                        console.print(Panel(result['context'], border_style="dim"))
                        console.print()
            else:
                console.print("[yellow]No results found.[/yellow]")
            
            if suggestions:
                console.print("\n[cyan]Suggested commands:[/cyan]")
                for cmd in suggestions:
                    console.print(f"  • {cmd}")
        
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option('--dry-run', is_flag=True, help='Show what would be updated without making changes')
@click.pass_context
def update(ctx, dry_run):
    """Update AGENTS.md based on codebase changes.
    
    Detects drift between the codebase and AGENTS.md, then updates
    only the changed sections while preserving manual edits.
    
    Example:
        codebase-brain update
        codebase-brain update --dry-run
    """
    verbose = ctx.obj['verbose']
    repo_path = Path.cwd()
    agents_file = repo_path / "bob-copilot" / "AGENTS.md"
    
    try:
        console.print(Panel.fit(
            "[bold blue]Detecting Codebase Drift[/bold blue]",
            border_style="blue"
        ))
        
        if not agents_file.exists():
            console.print("[red]✗ AGENTS.md not found. Run 'codebase-brain init' first.[/red]")
            sys.exit(1)
        
        # Detect drift
        detector = DriftDetector(repo_path, agents_file)
        drift = detector.detect_drift()
        
        has_drift = (
            drift['new_files'] or
            drift['deleted_files'] or
            drift['modified_structure'] or
            drift['new_dependencies']
        )
        
        if not has_drift:
            console.print("[green]✓ No drift detected. AGENTS.md is up to date![/green]")
            return
        
        # Show drift
        console.print("\n[yellow]Drift detected:[/yellow]\n")
        
        if drift['new_files']:
            console.print("[cyan]New files:[/cyan]")
            for file in drift['new_files']:
                console.print(f"  + {file}")
        
        if drift['deleted_files']:
            console.print("\n[cyan]Deleted files:[/cyan]")
            for file in drift['deleted_files']:
                console.print(f"  - {file}")
        
        if drift['recommendations']:
            console.print("\n[cyan]Recommendations:[/cyan]")
            for rec in drift['recommendations']:
                console.print(f"  • {rec}")
        
        if dry_run:
            console.print("\n[dim]Dry run - no changes made[/dim]")
        else:
            console.print("\n[yellow]⚠ Automatic updates not yet implemented[/yellow]")
            console.print("Please review the recommendations and update AGENTS.md manually.")
        
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == '__main__':
    cli(obj={})

# Made with Bob
