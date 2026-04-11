import type { Reporter, TestCase, TestResult, FullResult } from '@playwright/test/reporter';
import * as fs from 'fs';
import * as path from 'path';

interface EvalEntry {
  testId: string;
  domain: string;
  title: string;
  status: string;
  durationMs: number;
  classification: string;
  responsePreview: string;
  extraAnnotations: Record<string, string>;
}

class EvalSummaryReporter implements Reporter {
  private results: EvalEntry[] = [];

  onTestEnd(test: TestCase, result: TestResult) {
    const titleParts = test.titlePath();
    const domain = titleParts.length >= 2 ? titleParts[titleParts.length - 2] : 'Unknown';
    const title = titleParts[titleParts.length - 1];
    const testIdMatch = title.match(/^([A-Z]{2}-\d{3}):/);
    const testId = testIdMatch ? testIdMatch[1] : title;

    let classification = 'FALHA';
    if (result.status === 'passed') {
      classification = 'RESPOSTA COERENTE';
    } else if (result.status === 'timedOut') {
      classification = 'SEM RESPOSTA';
    } else if (result.status === 'skipped') {
      classification = 'SEM RESPOSTA';
    }

    let responsePreview = '';
    const extraAnnotations: Record<string, string> = {};
    const annotations = result.annotations || [];
    for (const ann of annotations) {
      if (ann.type === 'eval_classification' && ann.description) {
        classification = ann.description;
      } else if (ann.type === 'eval_response' && ann.description) {
        responsePreview = ann.description;
      } else if (ann.type && ann.type.startsWith('eval_') && ann.description) {
        extraAnnotations[ann.type] = ann.description;
      }
    }

    this.results.push({
      testId,
      domain,
      title,
      status: result.status,
      durationMs: result.duration,
      classification,
      responsePreview,
      extraAnnotations,
    });
  }

  onEnd(result: FullResult) {
    const reportsDir = path.join(process.cwd(), 'e2e', 'reports');
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }

    const domainSummary: Record<string, { total: number; passed: number; failed: number; classifications: Record<string, number> }> = {};
    for (const entry of this.results) {
      if (!domainSummary[entry.domain]) {
        domainSummary[entry.domain] = { total: 0, passed: 0, failed: 0, classifications: {} };
      }
      domainSummary[entry.domain].total++;
      if (entry.status === 'passed') domainSummary[entry.domain].passed++;
      else domainSummary[entry.domain].failed++;

      const cls = entry.classification;
      domainSummary[entry.domain].classifications[cls] = (domainSummary[entry.domain].classifications[cls] || 0) + 1;
    }

    const summary = {
      generatedAt: new Date().toISOString(),
      overallStatus: result.status,
      totalTests: this.results.length,
      passed: this.results.filter(r => r.status === 'passed').length,
      failed: this.results.filter(r => r.status === 'failed').length,
      timedOut: this.results.filter(r => r.status === 'timedOut').length,
      domainSummary,
      results: this.results,
    };

    const outputPath = path.join(reportsDir, 'eval-summary.json');
    fs.writeFileSync(outputPath, JSON.stringify(summary, null, 2));
  }
}

export default EvalSummaryReporter;
