# Code Analyzer & Bug Fixer Skill

## Description
Analyze code files, identify bugs, suggest fixes, and run tests within the workspace.

## Workspace Paths
- Source code: `/workspace/projects/{project}/`
- Analysis reports: `/workspace/builds/{project}/analysis/`
- Test results: `/workspace/builds/{project}/tests/`

## Capabilities
- Static code analysis (ESLint, Pylint, etc.)
- Bug detection and fix suggestions
- Test execution
- Code review

## Usage Examples

### Analyze Python Code
```bash
cd /workspace/projects/myapp
python -m pylint src/ --output-format=json > /workspace/builds/myapp/analysis/pylint.json
```

### Analyze JavaScript/TypeScript
```bash
cd /workspace/projects/myapp
npx eslint src/ --format json > /workspace/builds/myapp/analysis/eslint.json
```

### Run Tests
```bash
cd /workspace/projects/myapp
npm test 2>&1 | tee /workspace/builds/myapp/tests/results.log
```

### Fix Common Issues
```python
import subprocess

def auto_fix_lint(project_path: str):
    """Auto-fix linting issues"""
    # ESLint auto-fix
    subprocess.run(
        f"cd /workspace/projects/{project_path} && npx eslint src/ --fix",
        shell=True
    )
    
    # Black (Python formatter)
    subprocess.run(
        f"cd /workspace/projects/{project_path} && python -m black .",
        shell=True
    )
    
    return "Auto-fixes applied"
```

### Generate Analysis Report
```python
def generate_report(project: str) -> str:
    report_path = f"/workspace/builds/{project}/analysis/report.md"
    
    # Read analysis results
    with open(f"/workspace/builds/{project}/analysis/eslint.json") as f:
        eslint_data = json.load(f)
    
    # Generate markdown report
    report = f"# Code Analysis Report for {project}\n\n"
    report += f"## Issues Found: {len(eslint_data)}\n\n"
    
    for issue in eslint_data[:10]:  # Top 10 issues
        report += f"- **{issue['ruleId']}**: {issue['message']}\n"
    
    with open(report_path, "w") as f:
        f.write(report)
    
    return report_path
```

## Analysis Workflow
1. Clone/update project in `/workspace/projects/`
2. Run linters and analyzers
3. Save reports to `/workspace/builds/{project}/analysis/`
4. Apply auto-fixes if safe
5. Run tests to verify
6. Commit fixes if all tests pass

## Security Note
All analysis runs inside workspace - no access to host system files.
