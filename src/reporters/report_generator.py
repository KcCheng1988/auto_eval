"""Report generator for Task 3"""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates evaluation reports in email format"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize report generator

        Args:
            config: Report configuration from config_loader
        """
        self.config = config

    def generate_email_report(
        self,
        validation_result: Any,
        evaluation_result: Any,
        extracted_data: Dict[str, Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate HTML email report

        Args:
            validation_result: Template validation result
            evaluation_result: Evaluation result
            extracted_data: Data extracted from template
            output_path: Optional path to save report

        Returns:
            HTML string for email
        """
        logger.info("Generating email report")

        # Extract key information
        use_case_info = extracted_data.get("use_case_info", {})
        model_info = extracted_data.get("model_info", {})

        # Build HTML report
        html_report = self._build_html_report(
            validation_result,
            evaluation_result,
            use_case_info,
            model_info
        )

        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_report)
            logger.info(f"Report saved to: {output_path}")

        return html_report

    def _build_html_report(
        self,
        validation_result: Any,
        evaluation_result: Any,
        use_case_info: Dict[str, Any],
        model_info: Dict[str, Any]
    ) -> str:
        """
        Build HTML report structure

        Args:
            validation_result: Validation result object
            evaluation_result: Evaluation result object
            use_case_info: Use case information
            model_info: Model information

        Returns:
            HTML string
        """
        # Get summaries
        validation_summary = validation_result.get_summary()
        evaluation_summary = evaluation_result.get_summary()

        # Build status badges
        validation_status = "PASS" if validation_summary["is_valid"] else "FAIL"
        evaluation_status = "PASS" if evaluation_summary["passed"] else "FAIL"

        validation_color = "#28a745" if validation_summary["is_valid"] else "#dc3545"
        evaluation_color = "#28a745" if evaluation_summary["passed"] else "#dc3545"

        # Build HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .status-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
            margin-left: 10px;
        }}
        .section {{
            background: #f8f9fa;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .section h2 {{
            margin-top: 0;
            color: #495057;
            font-size: 20px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 12px;
            margin: 15px 0;
        }}
        .info-label {{
            font-weight: 600;
            color: #6c757d;
        }}
        .info-value {{
            color: #212529;
        }}
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .metrics-table th {{
            background: #e9ecef;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #495057;
        }}
        .metrics-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #dee2e6;
        }}
        .metrics-table tr:last-child td {{
            border-bottom: none;
        }}
        .metric-pass {{
            color: #28a745;
            font-weight: 600;
        }}
        .metric-fail {{
            color: #dc3545;
            font-weight: 600;
        }}
        .issue-list {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .issue-list li {{
            margin: 5px 0;
            color: #dc3545;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            color: #6c757d;
            font-size: 14px;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>GenAI Model Evaluation Report</h1>
        <p>Operation Team Data Chapter - Auto Evaluation Tool</p>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <!-- Overall Status -->
    <div class="section">
        <h2>📋 Overall Status</h2>
        <div style="margin: 15px 0;">
            <span style="font-weight: 600;">Template Validation:</span>
            <span class="status-badge" style="background-color: {validation_color}; color: white;">
                {validation_status}
            </span>
        </div>
        <div style="margin: 15px 0;">
            <span style="font-weight: 600;">Model Evaluation:</span>
            <span class="status-badge" style="background-color: {evaluation_color}; color: white;">
                {evaluation_status}
            </span>
        </div>
    </div>

    <!-- Use Case Information -->
    <div class="section">
        <h2>🎯 Use Case Information</h2>
        <div class="info-grid">
            {self._build_info_rows(use_case_info)}
        </div>
    </div>

    <!-- Model Information -->
    <div class="section">
        <h2>🤖 Model Information</h2>
        <div class="info-grid">
            {self._build_info_rows(model_info)}
        </div>
    </div>

    <!-- Validation Results -->
    <div class="section">
        <h2>✅ Template Validation Results</h2>
        <div class="info-grid">
            <div class="info-label">Total Errors:</div>
            <div class="info-value">{validation_summary['error_count']}</div>
            <div class="info-label">Total Warnings:</div>
            <div class="info-value">{validation_summary['warning_count']}</div>
        </div>
        {self._build_issues_section(validation_summary)}
    </div>

    <!-- Evaluation Results -->
    <div class="section">
        <h2>📊 Evaluation Results</h2>
        {self._build_metrics_section(evaluation_summary)}
        {self._build_miit_section(evaluation_summary)}
    </div>

    <!-- Threshold Checks -->
    <div class="section">
        <h2>🎯 Threshold Compliance</h2>
        {self._build_threshold_section(evaluation_summary)}
    </div>

    <div class="footer">
        <p><strong>Operation Team Data Chapter</strong></p>
        <p>This report was automatically generated by the Auto-Evaluation Tool</p>
        <p>For questions or concerns, please contact the Operation Team Data Chapter</p>
    </div>
</body>
</html>
"""
        return html

    def _build_info_rows(self, info_dict: Dict[str, Any]) -> str:
        """Build HTML rows for information grid"""
        if not info_dict:
            return "<div>No information available</div>"

        rows = []
        for key, value in info_dict.items():
            rows.append(f'<div class="info-label">{key}:</div>')
            rows.append(f'<div class="info-value">{value}</div>')

        return "\n".join(rows)

    def _build_issues_section(self, validation_summary: Dict[str, Any]) -> str:
        """Build issues section HTML"""
        html_parts = []

        if validation_summary['errors']:
            html_parts.append('<div class="highlight">')
            html_parts.append('<strong>⚠️ Errors Found:</strong>')
            html_parts.append('<ul class="issue-list">')
            for error in validation_summary['errors']:
                html_parts.append(f'<li>{error}</li>')
            html_parts.append('</ul></div>')

        if validation_summary['warnings']:
            html_parts.append('<div style="margin-top: 15px;">')
            html_parts.append('<strong>⚡ Warnings:</strong>')
            html_parts.append('<ul class="issue-list" style="color: #856404;">')
            for warning in validation_summary['warnings']:
                html_parts.append(f'<li>{warning}</li>')
            html_parts.append('</ul></div>')

        return "\n".join(html_parts) if html_parts else "<p>No issues found</p>"

    def _build_metrics_section(self, evaluation_summary: Dict[str, Any]) -> str:
        """Build metrics section HTML"""
        metrics = evaluation_summary.get('metrics', {})

        if not metrics:
            return "<p>No metrics available</p>"

        html = '<table class="metrics-table">'
        html += '<thead><tr><th>Metric</th><th>Value</th></tr></thead>'
        html += '<tbody>'

        for metric_name, value in metrics.items():
            # Format value
            if isinstance(value, float):
                formatted_value = f"{value:.4f}"
            else:
                formatted_value = str(value)

            html += f'<tr><td>{metric_name}</td><td>{formatted_value}</td></tr>'

        html += '</tbody></table>'
        return html

    def _build_miit_section(self, evaluation_summary: Dict[str, Any]) -> str:
        """Build MIIT results section HTML"""
        miit_results = evaluation_summary.get('miit_results', {})

        if not miit_results or miit_results.get('status') == 'not_found':
            return '<div style="margin-top: 20px;"><em>MIIT evaluation not performed</em></div>'

        html = '<div style="margin-top: 25px;"><h3>MIIT Consistency Check</h3>'

        consistency_rate = miit_results.get('consistency_rate', 0)
        html += f'<p><strong>Consistency Rate:</strong> {consistency_rate:.2%}</p>'

        discrepancies = miit_results.get('discrepancies', [])
        if discrepancies:
            html += '<div class="highlight">'
            html += f'<strong>⚠️ Found {len(discrepancies)} discrepancies between Sandbox and UAT:</strong>'
            html += '<ul class="issue-list">'
            for disc in discrepancies[:5]:  # Show first 5
                html += f'<li>Query {disc["query_index"]}: "{disc["query"][:50]}..."</li>'
            if len(discrepancies) > 5:
                html += f'<li>... and {len(discrepancies) - 5} more</li>'
            html += '</ul></div>'

        html += '</div>'
        return html

    def _build_threshold_section(self, evaluation_summary: Dict[str, Any]) -> str:
        """Build threshold checks section HTML"""
        threshold_checks = evaluation_summary.get('threshold_checks', {})

        if not threshold_checks:
            return "<p>No threshold checks configured</p>"

        html = '<table class="metrics-table">'
        html += '<thead><tr><th>Metric</th><th>Threshold</th><th>Actual</th><th>Status</th></tr></thead>'
        html += '<tbody>'

        for metric_name, check in threshold_checks.items():
            threshold = check['threshold']
            actual = check['actual']
            passed = check['passed']

            status_class = 'metric-pass' if passed else 'metric-fail'
            status_text = '✓ PASS' if passed else '✗ FAIL'

            # Format values
            if isinstance(threshold, float):
                threshold_str = f"{threshold:.4f}"
                actual_str = f"{actual:.4f}"
            else:
                threshold_str = str(threshold)
                actual_str = str(actual)

            html += f'''<tr>
                <td>{metric_name}</td>
                <td>{threshold_str}</td>
                <td>{actual_str}</td>
                <td class="{status_class}">{status_text}</td>
            </tr>'''

        html += '</tbody></table>'
        return html

    def generate_summary_text(
        self,
        validation_result: Any,
        evaluation_result: Any
    ) -> str:
        """
        Generate plain text summary for quick review

        Args:
            validation_result: Validation result object
            evaluation_result: Evaluation result object

        Returns:
            Plain text summary
        """
        validation_summary = validation_result.get_summary()
        evaluation_summary = evaluation_result.get_summary()

        summary = []
        summary.append("=" * 60)
        summary.append("EVALUATION SUMMARY")
        summary.append("=" * 60)
        summary.append("")

        # Validation status
        val_status = "PASS ✓" if validation_summary['is_valid'] else "FAIL ✗"
        summary.append(f"Template Validation: {val_status}")
        summary.append(f"  - Errors: {validation_summary['error_count']}")
        summary.append(f"  - Warnings: {validation_summary['warning_count']}")
        summary.append("")

        # Evaluation status
        eval_status = "PASS ✓" if evaluation_summary['passed'] else "FAIL ✗"
        summary.append(f"Model Evaluation: {eval_status}")
        summary.append("")

        # Metrics
        summary.append("Metrics:")
        for metric_name, value in evaluation_summary.get('metrics', {}).items():
            if isinstance(value, float):
                summary.append(f"  - {metric_name}: {value:.4f}")
            else:
                summary.append(f"  - {metric_name}: {value}")

        summary.append("")
        summary.append("=" * 60)

        return "\n".join(summary)
