#!/usr/bin/env python3
"""
AGENTS.md Validation Tool

Validates that bob-copilot/AGENTS.md stays accurate by checking:
1. File coverage - all mentioned files exist
2. Line references - line numbers are still valid
3. Drift detection - staleness vs actual files
4. Quality metrics - documentation completeness

Exit codes:
  0 - All checks pass, drift < 15%
  1 - Validation failures or drift >= 15%
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional


@dataclass
class ValidationResult:
    """Results from validation checks"""
    total_files_mentioned: int
    files_exist: int
    files_missing: List[str]
    coverage_percentage: float
    
    total_line_refs: int
    valid_line_refs: int
    stale_line_refs: List[Dict[str, Any]]
    line_accuracy_percentage: float
    
    agents_md_modified: str
    newest_repo_file_modified: str
    staleness_percentage: float
    
    total_gotchas: int
    total_failure_modes: int
    quality_score: float
    
    drift_check_passed: bool
    overall_passed: bool


class AgentsValidator:
    """Validates AGENTS.md against actual codebase"""
    
    def __init__(self, workspace_dir: Path, verbose: bool = False):
        self.workspace_dir = workspace_dir
        self.agents_md_path = workspace_dir / "bob-copilot" / "AGENTS.md"
        self.verbose = verbose
        
        if not self.agents_md_path.exists():
            raise FileNotFoundError(f"AGENTS.md not found at {self.agents_md_path}")
        
        self.agents_content = self.agents_md_path.read_text()
        self.agents_lines = self.agents_content.split('\n')
    
    def log(self, message: str) -> None:
        """Print message if verbose mode enabled"""
        if self.verbose:
            print(f"[DEBUG] {message}")
    
    def extract_file_paths(self) -> Set[str]:
        """Extract all file paths mentioned in AGENTS.md"""
        file_paths = set()
        
        # Pattern 1: Markdown headers with file paths (e.g., #### `model.sdf`)
        header_pattern = r'####?\s+`([^`]+\.[a-zA-Z0-9]+)`'
        
        # Pattern 2: Inline code with file paths (e.g., `scripts/gait_controller.py`)
        inline_pattern = r'`([a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+)`'
        
        for match in re.finditer(header_pattern, self.agents_content):
            file_paths.add(match.group(1))
        
        for match in re.finditer(inline_pattern, self.agents_content):
            path = match.group(1)
            # Filter out likely file paths (has directory separator or common extensions)
            if '/' in path or path.endswith(('.py', '.sh', '.sdf', '.param', '.parm', '.config', '.md', '.DAT')):
                file_paths.add(path)
        
        self.log(f"Extracted {len(file_paths)} file paths from AGENTS.md")
        return file_paths
    
    def check_file_coverage(self) -> Tuple[int, int, List[str]]:
        """Check which mentioned files actually exist"""
        file_paths = self.extract_file_paths()
        files_exist = 0
        files_missing = []
        
        for file_path in sorted(file_paths):
            # Try multiple possible locations
            possible_paths = [
                self.workspace_dir / file_path,
                self.workspace_dir / file_path.lstrip('/'),
            ]
            
            exists = any(p.exists() for p in possible_paths)
            
            if exists:
                files_exist += 1
                self.log(f"✓ Found: {file_path}")
            else:
                files_missing.append(file_path)
                self.log(f"✗ Missing: {file_path}")
        
        return len(file_paths), files_exist, files_missing
    
    def extract_line_references(self) -> List[Dict[str, Any]]:
        """Extract all line number references from AGENTS.md"""
        line_refs = []
        
        # Pattern: "line 123", "lines 45-67", "(line 89)", etc.
        patterns = [
            r'line\s+(\d+)',
            r'lines\s+(\d+)-(\d+)',
            r'\(line\s+(\d+)\)',
            r'line\s+(\d+),\s+(\d+)',
        ]
        
        for line_num, line in enumerate(self.agents_lines, 1):
            for pattern in patterns:
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    # Extract all numbers from the match
                    numbers = [int(g) for g in match.groups() if g]
                    
                    # Try to find associated file in nearby context
                    context_start = max(0, line_num - 5)
                    context_end = min(len(self.agents_lines), line_num + 2)
                    context = '\n'.join(self.agents_lines[context_start:context_end])
                    
                    # Look for file references in context
                    file_match = re.search(r'`([a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+)`', context)
                    file_path = file_match.group(1) if file_match else None
                    
                    for num in numbers:
                        line_refs.append({
                            'agents_line': line_num,
                            'referenced_line': num,
                            'file': file_path,
                            'context': line.strip()
                        })
        
        self.log(f"Found {len(line_refs)} line references")
        return line_refs
    
    def validate_line_references(self, line_refs: List[Dict[str, Any]]) -> Tuple[int, List[Dict[str, Any]]]:
        """Validate that referenced line numbers still exist in files"""
        valid_refs = 0
        stale_refs = []
        
        for ref in line_refs:
            if not ref['file']:
                continue  # Skip if we couldn't determine the file
            
            file_path = self.workspace_dir / ref['file'].lstrip('/')
            
            if not file_path.exists():
                stale_refs.append({**ref, 'reason': 'file_not_found'})
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                if ref['referenced_line'] <= len(lines):
                    valid_refs += 1
                    self.log(f"✓ Valid line ref: {ref['file']}:{ref['referenced_line']}")
                else:
                    stale_refs.append({**ref, 'reason': 'line_out_of_range', 'actual_lines': len(lines)})
                    self.log(f"✗ Stale line ref: {ref['file']}:{ref['referenced_line']} (file has {len(lines)} lines)")
            except Exception as e:
                stale_refs.append({**ref, 'reason': f'read_error: {str(e)}'})
        
        return valid_refs, stale_refs
    
    def calculate_drift(self) -> Tuple[datetime, datetime, float]:
        """Calculate staleness percentage based on file modification times"""
        agents_mtime = datetime.fromtimestamp(self.agents_md_path.stat().st_mtime)
        
        # Find newest file in the repo (excluding AGENTS.md itself)
        newest_mtime = agents_mtime
        newest_file = None
        
        for file_path in self.workspace_dir.rglob('*'):
            if file_path.is_file() and file_path != self.agents_md_path:
                # Skip hidden files and common non-source files
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                if file_path.suffix in ['.pyc', '.log', '.tmp']:
                    continue
                
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime > newest_mtime:
                        newest_mtime = mtime
                        newest_file = file_path
                except:
                    continue
        
        # Calculate staleness as percentage of time difference
        if newest_mtime > agents_mtime:
            time_diff = (newest_mtime - agents_mtime).total_seconds()
            # Normalize to percentage (1 day = 10% staleness, capped at 100%)
            staleness = min(100.0, (time_diff / 86400) * 10)
        else:
            staleness = 0.0
        
        self.log(f"AGENTS.md modified: {agents_mtime}")
        self.log(f"Newest repo file: {newest_file} at {newest_mtime}")
        self.log(f"Staleness: {staleness:.1f}%")
        
        return agents_mtime, newest_mtime, staleness
    
    def count_quality_metrics(self) -> Tuple[int, int]:
        """Count gotchas and failure modes documented"""
        gotchas = len(re.findall(r'\*\*GOTCHA\*\*', self.agents_content, re.IGNORECASE))
        
        # Count failure modes section entries
        failure_section = re.search(
            r'## ⚠️ Known Failure Modes(.*?)(?=##|\Z)',
            self.agents_content,
            re.DOTALL
        )
        
        if failure_section:
            failure_content = failure_section.group(1)
            # Count numbered failure modes (### 1., ### 2., etc.)
            failure_modes = len(re.findall(r'###\s+\d+\.', failure_content))
        else:
            failure_modes = 0
        
        self.log(f"Found {gotchas} gotchas and {failure_modes} failure modes")
        return gotchas, failure_modes
    
    def calculate_quality_score(self, files_exist: int, total_files: int, 
                                gotchas: int, failure_modes: int) -> float:
        """Calculate overall quality score (0-100)"""
        # Weighted scoring:
        # - 40% file coverage
        # - 30% gotchas (1 point per gotcha, max 30)
        # - 30% failure modes (3 points per mode, max 30)
        
        coverage_score = (files_exist / total_files * 40) if total_files > 0 else 0
        gotcha_score = min(30, gotchas)
        failure_score = min(30, failure_modes * 3)
        
        total_score = coverage_score + gotcha_score + failure_score
        return round(total_score, 1)
    
    def validate(self, quiet: bool = False) -> ValidationResult:
        """Run all validation checks"""
        if not quiet:
            print("🔍 Validating AGENTS.md...")
            print()
        
        # 1. File Coverage Check
        if not quiet:
            print("📁 Checking file coverage...")
        total_files, files_exist, files_missing = self.check_file_coverage()
        coverage_pct = (files_exist / total_files * 100) if total_files > 0 else 0
        if not quiet:
            print(f"   Files documented: {total_files}")
            print(f"   Files exist: {files_exist}")
            print(f"   Files missing: {len(files_missing)}")
            print(f"   Coverage: {coverage_pct:.1f}%")
            print()
        
        # 2. Line Reference Validation
        if not quiet:
            print("🔢 Validating line references...")
        line_refs = self.extract_line_references()
        valid_refs, stale_refs = self.validate_line_references(line_refs)
        line_accuracy = (valid_refs / len(line_refs) * 100) if line_refs else 100
        if not quiet:
            print(f"   Total line references: {len(line_refs)}")
            print(f"   Valid references: {valid_refs}")
            print(f"   Stale references: {len(stale_refs)}")
            print(f"   Accuracy: {line_accuracy:.1f}%")
            print()
        
        # 3. Drift Detection
        if not quiet:
            print("📅 Detecting drift...")
        agents_mtime, newest_mtime, staleness = self.calculate_drift()
        drift_passed = staleness < 15.0
        if not quiet:
            print(f"   AGENTS.md last modified: {agents_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Newest repo file modified: {newest_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Staleness: {staleness:.1f}%")
            print(f"   Drift check: {'✅ PASS' if drift_passed else '❌ FAIL'} (threshold: 15%)")
            print()
        
        # 4. Quality Metrics
        if not quiet:
            print("📊 Quality metrics...")
        gotchas, failure_modes = self.count_quality_metrics()
        quality_score = self.calculate_quality_score(files_exist, total_files, gotchas, failure_modes)
        if not quiet:
            print(f"   Total gotchas: {gotchas}")
            print(f"   Total failure modes: {failure_modes}")
            print(f"   Quality score: {quality_score}/100")
            print()
        
        # Overall result
        overall_passed = (
            len(files_missing) == 0 and
            len(stale_refs) == 0 and
            drift_passed
        )
        
        return ValidationResult(
            total_files_mentioned=total_files,
            files_exist=files_exist,
            files_missing=files_missing,
            coverage_percentage=round(coverage_pct, 1),
            total_line_refs=len(line_refs),
            valid_line_refs=valid_refs,
            stale_line_refs=stale_refs,
            line_accuracy_percentage=round(line_accuracy, 1),
            agents_md_modified=agents_mtime.isoformat(),
            newest_repo_file_modified=newest_mtime.isoformat(),
            staleness_percentage=round(staleness, 1),
            total_gotchas=gotchas,
            total_failure_modes=failure_modes,
            quality_score=quality_score,
            drift_check_passed=drift_passed,
            overall_passed=overall_passed
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Validate AGENTS.md accuracy against actual codebase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run validation with summary output
  %(prog)s --json             # Output results as JSON
  %(prog)s --verbose          # Show detailed debug information
  %(prog)s --json > report.json  # Save JSON report to file

Exit Codes:
  0 - All checks pass, drift < 15%%
  1 - Validation failures or drift >= 15%%
        """
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON instead of human-readable format'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed debug information during validation'
    )
    
    parser.add_argument(
        '--workspace',
        type=Path,
        default=Path.cwd(),
        help='Workspace directory (default: current directory)'
    )
    
    args = parser.parse_args()
    
    try:
        validator = AgentsValidator(args.workspace, verbose=args.verbose)
        result = validator.validate(quiet=args.json)
        
        if args.json:
            # JSON output
            print(json.dumps(asdict(result), indent=2))
        else:
            # Human-readable summary
            print("=" * 60)
            print("VALIDATION SUMMARY")
            print("=" * 60)
            print()
            print(f"Overall Status: {'✅ PASS' if result.overall_passed else '❌ FAIL'}")
            print()
            print(f"File Coverage:      {result.coverage_percentage}% ({result.files_exist}/{result.total_files_mentioned})")
            print(f"Line Accuracy:      {result.line_accuracy_percentage}% ({result.valid_line_refs}/{result.total_line_refs})")
            print(f"Staleness:          {result.staleness_percentage}%")
            print(f"Quality Score:      {result.quality_score}/100")
            print()
            
            if result.files_missing:
                print("⚠️  Missing Files:")
                for file in result.files_missing[:10]:  # Show first 10
                    print(f"   - {file}")
                if len(result.files_missing) > 10:
                    print(f"   ... and {len(result.files_missing) - 10} more")
                print()
            
            if result.stale_line_refs:
                print("⚠️  Stale Line References:")
                for ref in result.stale_line_refs[:5]:  # Show first 5
                    print(f"   - {ref['file']}:{ref['referenced_line']} - {ref['reason']}")
                if len(result.stale_line_refs) > 5:
                    print(f"   ... and {len(result.stale_line_refs) - 5} more")
                print()
        
        # Exit with appropriate code
        sys.exit(0 if result.overall_passed else 1)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

# Made with Bob
