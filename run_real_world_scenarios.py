"""
Real-World Scenario Test Runner

Executes all 10 real-world scenarios and generates comprehensive reports.

Usage:
    python run_real_world_scenarios.py

    # Run specific scenarios
    python run_real_world_scenarios.py --scenarios 1 2 3

    # Generate HTML report
    python run_real_world_scenarios.py --html-report

    # Save results to JSON
    python run_real_world_scenarios.py --json-output results.json
"""

import asyncio
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Import all scenarios
from tests.real_world_scenarios.scenario_01_bug_fix import BugFixScenario
from tests.real_world_scenarios.scenario_02_rest_api import RestAPIScenario
from tests.real_world_scenarios.scenarios_03_10 import (
    ThirdPartyAPIScenario,
    DatabaseMigrationScenario,
    PerformanceOptimizationScenario,
    SecurityVulnerabilityScenario,
    LegacyRefactoringScenario,
    CICDPipelineScenario,
    DocumentationGenerationScenario,
    MultiServiceFeatureScenario
)
from tests.real_world_scenarios.base_scenario import BaseScenario, ScenarioMetrics


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'


class ScenarioRunner:
    """
    Test runner for all real-world scenarios.

    Executes scenarios, collects metrics, and generates reports.
    """

    def __init__(self, api_base_url: str = "http://localhost:8000/api/v1"):
        self.api_base_url = api_base_url
        self.scenarios: List[BaseScenario] = [
            BugFixScenario(api_base_url),
            RestAPIScenario(api_base_url),
            ThirdPartyAPIScenario(api_base_url),
            DatabaseMigrationScenario(api_base_url),
            PerformanceOptimizationScenario(api_base_url),
            SecurityVulnerabilityScenario(api_base_url),
            LegacyRefactoringScenario(api_base_url),
            CICDPipelineScenario(api_base_url),
            DocumentationGenerationScenario(api_base_url),
            MultiServiceFeatureScenario(api_base_url)
        ]

        self.results: List[ScenarioMetrics] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.BLUE}{'=' * 80}{Colors.NC}")
        print(f"{Colors.BLUE}{text:^80}{Colors.NC}")
        print(f"{Colors.BLUE}{'=' * 80}{Colors.NC}\n")

    def print_scenario_header(self, number: int, name: str):
        """Print scenario header"""
        print(f"\n{Colors.CYAN}{'─' * 80}{Colors.NC}")
        print(f"{Colors.CYAN}Scenario {number}: {name}{Colors.NC}")
        print(f"{Colors.CYAN}{'─' * 80}{Colors.NC}")

    def print_status(self, status: str, message: str):
        """Print status message"""
        if "completed" in status.lower():
            color = Colors.GREEN
            icon = "✓"
        elif "failed" in status.lower():
            color = Colors.RED
            icon = "✗"
        elif "partial" in status.lower():
            color = Colors.YELLOW
            icon = "◐"
        else:
            color = Colors.BLUE
            icon = "◯"

        print(f"{color}{icon}{Colors.NC} {message}")

    async def run_scenario(
        self,
        scenario: BaseScenario,
        scenario_number: int
    ) -> ScenarioMetrics:
        """Run a single scenario"""
        self.print_scenario_header(scenario_number, scenario.scenario_description)

        print(f"{Colors.BLUE}→{Colors.NC} Starting scenario...")
        print(f"  Expected duration: {scenario.expected_duration_minutes} minutes")
        print(f"  Expected tools: {len(scenario.get_expected_tools())}")

        start_time = time.time()

        try:
            metrics = await scenario.execute()
            duration = time.time() - start_time

            # Print results
            self.print_status(
                metrics.status,
                f"Status: {metrics.status} ({duration:.1f}s)"
            )
            print(f"  Steps completed: {metrics.steps_completed}/{metrics.steps_total}")
            print(f"  Success criteria met: {metrics.success_criteria_met}/{metrics.success_criteria_total}")
            print(f"  Quality score: {metrics.quality_score:.1f}/100")
            print(f"  Tools used: {len(metrics.tools_used)}")
            print(f"  Tools missing: {len(metrics.tools_missing)}")

            if metrics.errors:
                print(f"\n{Colors.RED}Errors:{Colors.NC}")
                for error in metrics.errors[:3]:  # Show first 3 errors
                    print(f"  • {error}")
                if len(metrics.errors) > 3:
                    print(f"  ... and {len(metrics.errors) - 3} more")

            return metrics

        except Exception as e:
            print(f"{Colors.RED}✗ Scenario failed: {e}{Colors.NC}")
            raise

    async def run_all_scenarios(
        self,
        scenario_numbers: Optional[List[int]] = None
    ) -> List[ScenarioMetrics]:
        """Run all scenarios (or specific ones)"""
        self.start_time = datetime.utcnow()

        print(f"{Colors.MAGENTA}╔{'═' * 78}╗{Colors.NC}")
        print(f"{Colors.MAGENTA}║{' ' * 20}Real-World Scenario Test Suite{' ' * 27}║{Colors.NC}")
        print(f"{Colors.MAGENTA}╚{'═' * 78}╝{Colors.NC}")

        print(f"\n{Colors.BLUE}Configuration:{Colors.NC}")
        print(f"  API Base URL: {self.api_base_url}")
        print(f"  Total Scenarios: {len(self.scenarios)}")
        if scenario_numbers:
            print(f"  Running: Scenarios {', '.join(map(str, scenario_numbers))}")
        else:
            print(f"  Running: All scenarios")

        # Filter scenarios if specific ones requested
        scenarios_to_run = self.scenarios
        if scenario_numbers:
            scenarios_to_run = [
                self.scenarios[i-1]
                for i in scenario_numbers
                if 1 <= i <= len(self.scenarios)
            ]

        # Run scenarios
        for i, scenario in enumerate(scenarios_to_run, 1):
            try:
                actual_number = self.scenarios.index(scenario) + 1
                metrics = await self.run_scenario(scenario, actual_number)
                self.results.append(metrics)
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}⚠ Test run interrupted by user{Colors.NC}")
                break
            except Exception as e:
                print(f"\n{Colors.RED}✗ Scenario failed with exception: {e}{Colors.NC}")
                continue

        self.end_time = datetime.utcnow()
        return self.results

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report from all results"""
        if not self.results:
            return {}

        # Calculate totals
        total_scenarios = len(self.results)
        completed = sum(1 for r in self.results if r.status == "completed")
        partial = sum(1 for r in self.results if r.status == "partial")
        failed = sum(1 for r in self.results if r.status == "failed")

        avg_quality = sum(r.quality_score for r in self.results) / total_scenarios
        avg_completion = sum(r.completion_percentage for r in self.results) / total_scenarios
        total_duration = sum(r.duration_seconds for r in self.results)

        # Tool analysis
        all_tools_needed = set()
        all_tools_used = set()
        all_tools_missing = set()

        for result in self.results:
            all_tools_needed.update(result.tools_needed)
            all_tools_used.update(result.tools_used.keys())
            all_tools_missing.update(result.tools_missing)

        # Tool frequency
        tool_frequency = defaultdict(int)
        tool_missing_frequency = defaultdict(int)

        for result in self.results:
            for tool in result.tools_needed:
                tool_frequency[tool] += 1
                if tool in result.tools_missing:
                    tool_missing_frequency[tool] += 1

        # Sort by frequency
        most_needed_tools = sorted(
            tool_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        most_missing_tools = sorted(
            tool_missing_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        return {
            "test_run": {
                "started_at": self.start_time.isoformat() if self.start_time else None,
                "completed_at": self.end_time.isoformat() if self.end_time else None,
                "total_duration_seconds": total_duration,
                "scenarios_run": total_scenarios
            },
            "results_summary": {
                "completed": completed,
                "partial": partial,
                "failed": failed,
                "completion_rate": (completed / total_scenarios * 100) if total_scenarios > 0 else 0,
                "avg_quality_score": avg_quality,
                "avg_completion_percentage": avg_completion * 100
            },
            "tool_analysis": {
                "total_tools_needed": len(all_tools_needed),
                "total_tools_used": len(all_tools_used),
                "total_tools_missing": len(all_tools_missing),
                "tool_availability_rate": ((len(all_tools_needed) - len(all_tools_missing)) / len(all_tools_needed) * 100) if all_tools_needed else 0,
                "most_needed_tools": [
                    {"tool": tool, "scenarios": count}
                    for tool, count in most_needed_tools
                ],
                "most_missing_tools": [
                    {"tool": tool, "scenarios": count}
                    for tool, count in most_missing_tools
                ],
                "tools_missing_list": sorted(list(all_tools_missing))
            },
            "scenarios": [
                {
                    "number": i + 1,
                    "name": self.scenarios[i].scenario_description,
                    "status": result.status,
                    "quality_score": result.quality_score,
                    "duration_seconds": result.duration_seconds,
                    "steps_completed": result.steps_completed,
                    "steps_total": result.steps_total,
                    "tools_missing_count": len(result.tools_missing),
                    "errors": result.errors
                }
                for i, result in enumerate(self.results)
            ]
        }

    def print_summary(self, summary: Dict[str, Any]):
        """Print summary report to console"""
        self.print_header("TEST RUN SUMMARY")

        # Results
        print(f"{Colors.CYAN}Results Overview:{Colors.NC}")
        results = summary["results_summary"]
        print(f"  Completed: {Colors.GREEN}{results['completed']}{Colors.NC}")
        print(f"  Partial:   {Colors.YELLOW}{results['partial']}{Colors.NC}")
        print(f"  Failed:    {Colors.RED}{results['failed']}{Colors.NC}")
        print(f"  Completion Rate: {results['completion_rate']:.1f}%")
        print(f"  Avg Quality Score: {results['avg_quality_score']:.1f}/100")

        # Tool Analysis
        print(f"\n{Colors.CYAN}Tool Analysis:{Colors.NC}")
        tools = summary["tool_analysis"]
        print(f"  Tools Needed: {tools['total_tools_needed']}")
        print(f"  Tools Available: {tools['total_tools_used']}")
        print(f"  Tools Missing: {Colors.RED}{tools['total_tools_missing']}{Colors.NC}")
        print(f"  Availability Rate: {tools['tool_availability_rate']:.1f}%")

        # Most Missing Tools
        if tools["most_missing_tools"]:
            print(f"\n{Colors.YELLOW}Top 10 Missing Tools:{Colors.NC}")
            for item in tools["most_missing_tools"][:10]:
                print(f"  • {item['tool']:30} (needed in {item['scenarios']} scenarios)")

        # Recommendations
        self.print_header("RECOMMENDATIONS")

        print(f"{Colors.CYAN}Priority 1: Critical Tools (needed in 5+ scenarios){Colors.NC}")
        critical_tools = [
            item for item in tools["most_missing_tools"]
            if item["scenarios"] >= 5
        ]
        if critical_tools:
            for item in critical_tools:
                print(f"  • {Colors.RED}{item['tool']}{Colors.NC}")
        else:
            print(f"  {Colors.GREEN}✓ All critical tools available{Colors.NC}")

        print(f"\n{Colors.CYAN}Priority 2: Common Tools (needed in 3-4 scenarios){Colors.NC}")
        common_tools = [
            item for item in tools["most_missing_tools"]
            if 3 <= item["scenarios"] < 5
        ]
        if common_tools:
            for item in common_tools[:5]:
                print(f"  • {Colors.YELLOW}{item['tool']}{Colors.NC}")
        else:
            print(f"  {Colors.GREEN}✓ All common tools available{Colors.NC}")

    def save_json_report(self, filename: str, summary: Dict[str, Any]):
        """Save detailed report to JSON"""
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n{Colors.GREEN}✓{Colors.NC} JSON report saved to {filename}")

    def generate_html_report(self, filename: str, summary: Dict[str, Any]):
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Real-World Scenario Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #1e40af; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: #f8fafc; padding: 20px; border-radius: 6px; border-left: 4px solid #2563eb; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #1e40af; }}
        .metric-label {{ color: #64748b; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #2563eb; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; }}
        tr:hover {{ background: #f8fafc; }}
        .status-completed {{ color: #10b981; font-weight: bold; }}
        .status-partial {{ color: #f59e0b; font-weight: bold; }}
        .status-failed {{ color: #ef4444; font-weight: bold; }}
        .tool-critical {{ background: #fee2e2; }}
        .tool-common {{ background: #fef3c7; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Real-World Scenario Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Results Overview</h2>
        <div class="summary">
            <div class="metric">
                <div class="metric-value">{summary['results_summary']['completed']}/{summary['test_run']['scenarios_run']}</div>
                <div class="metric-label">Completed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['results_summary']['completion_rate']:.1f}%</div>
                <div class="metric-label">Completion Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['results_summary']['avg_quality_score']:.1f}</div>
                <div class="metric-label">Avg Quality Score</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['tool_analysis']['total_tools_missing']}</div>
                <div class="metric-label">Missing Tools</div>
            </div>
        </div>

        <h2>Scenario Results</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Scenario</th>
                    <th>Status</th>
                    <th>Quality</th>
                    <th>Steps</th>
                    <th>Duration</th>
                    <th>Missing Tools</th>
                </tr>
            </thead>
            <tbody>
"""

        for scenario in summary['scenarios']:
            status_class = f"status-{scenario['status']}"
            html += f"""
                <tr>
                    <td>{scenario['number']}</td>
                    <td>{scenario['name']}</td>
                    <td class="{status_class}">{scenario['status']}</td>
                    <td>{scenario['quality_score']:.1f}/100</td>
                    <td>{scenario['steps_completed']}/{scenario['steps_total']}</td>
                    <td>{scenario['duration_seconds']:.1f}s</td>
                    <td>{scenario['tools_missing_count']}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>

        <h2>Missing Tools Analysis</h2>
        <table>
            <thead>
                <tr>
                    <th>Tool</th>
                    <th>Needed In Scenarios</th>
                    <th>Priority</th>
                </tr>
            </thead>
            <tbody>
"""

        for item in summary['tool_analysis']['most_missing_tools']:
            scenarios = item['scenarios']
            if scenarios >= 5:
                priority = "Critical"
                row_class = "tool-critical"
            elif scenarios >= 3:
                priority = "High"
                row_class = "tool-common"
            else:
                priority = "Medium"
                row_class = ""

            html += f"""
                <tr class="{row_class}">
                    <td>{item['tool']}</td>
                    <td>{scenarios}</td>
                    <td>{priority}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        with open(filename, 'w') as f:
            f.write(html)
        print(f"\n{Colors.GREEN}✓{Colors.NC} HTML report saved to {filename}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run real-world scenario tests"
    )
    parser.add_argument(
        "--scenarios",
        type=int,
        nargs="+",
        help="Specific scenarios to run (1-10)"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/api/v1",
        help="API base URL"
    )
    parser.add_argument(
        "--json-output",
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML report"
    )

    args = parser.parse_args()

    # Create runner
    runner = ScenarioRunner(api_base_url=args.api_url)

    # Run scenarios
    await runner.run_all_scenarios(scenario_numbers=args.scenarios)

    # Generate summary
    summary = runner.generate_summary_report()

    # Print summary
    runner.print_summary(summary)

    # Save reports
    if args.json_output:
        runner.save_json_report(args.json_output, summary)

    if args.html_report:
        runner.generate_html_report("scenario_report.html", summary)

    # Exit code based on results
    if summary:
        completion_rate = summary["results_summary"]["completion_rate"]
        exit(0 if completion_rate >= 80 else 1)


if __name__ == "__main__":
    asyncio.run(main())
