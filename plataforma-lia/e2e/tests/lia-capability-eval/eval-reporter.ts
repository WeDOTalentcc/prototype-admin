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

interface DomainSummary {
  total: number;
  passed: number;
  failed: number;
  classifications: Record<string, number>;
  avgDurationMs: number;
  p95DurationMs: number;
}

interface V1Summary {
  generatedAt: string;
  totalTests: number;
  passed: number;
  failed: number;
  domainSummary: Record<string, { total: number; passed: number; failed: number; classifications: Record<string, number> }>;
}

class EvalSummaryReporter implements Reporter {
  private results: EvalEntry[] = [];

  onTestEnd(test: TestCase, result: TestResult) {
    const titleParts = test.titlePath();
    const domain = titleParts.length >= 2 ? titleParts[titleParts.length - 2] : 'Unknown';
    const title = titleParts[titleParts.length - 1];
    const testIdMatch = title.match(/^([A-Z]{2,3}-\d{3}):/);
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

    const domainSummary: Record<string, DomainSummary> = {};
    for (const entry of this.results) {
      if (!domainSummary[entry.domain]) {
        domainSummary[entry.domain] = { total: 0, passed: 0, failed: 0, classifications: {}, avgDurationMs: 0, p95DurationMs: 0 };
      }
      domainSummary[entry.domain].total++;
      if (entry.status === 'passed') domainSummary[entry.domain].passed++;
      else domainSummary[entry.domain].failed++;

      const cls = entry.classification;
      domainSummary[entry.domain].classifications[cls] = (domainSummary[entry.domain].classifications[cls] || 0) + 1;
    }

    for (const domain of Object.keys(domainSummary)) {
      const durations = this.results
        .filter(r => r.domain === domain)
        .map(r => r.durationMs)
        .sort((a, b) => a - b);
      const count = durations.length;
      if (count > 0) {
        domainSummary[domain].avgDurationMs = Math.round(durations.reduce((a, b) => a + b, 0) / count);
        domainSummary[domain].p95DurationMs = durations[Math.min(Math.floor(count * 0.95), count - 1)];
      }
    }

    const classificationTotals: Record<string, number> = {};
    for (const entry of this.results) {
      classificationTotals[entry.classification] = (classificationTotals[entry.classification] || 0) + 1;
    }

    const v1Comparison = this.generateV1Comparison(domainSummary, classificationTotals);

    const summary = {
      generatedAt: new Date().toISOString(),
      version: 'V2',
      overallStatus: result.status,
      totalTests: this.results.length,
      passed: this.results.filter(r => r.status === 'passed').length,
      failed: this.results.filter(r => r.status === 'failed').length,
      timedOut: this.results.filter(r => r.status === 'timedOut').length,
      classificationTotals,
      domainSummary,
      v1Comparison,
      executiveSummary: this.generateExecutiveSummary(domainSummary, classificationTotals, v1Comparison),
      results: this.results,
    };

    const outputPath = path.join(reportsDir, 'eval-summary.json');
    fs.writeFileSync(outputPath, JSON.stringify(summary, null, 2));
  }

  private generateV1Comparison(
    v2DomainSummary: Record<string, DomainSummary>,
    v2ClassificationTotals: Record<string, number>,
  ): Record<string, unknown> {
    const v1SummaryPath = path.join(process.cwd(), 'e2e', 'reports', 'eval-summary-v1.json');
    let v1Data: V1Summary | null = null;

    if (fs.existsSync(v1SummaryPath)) {
      try {
        v1Data = JSON.parse(fs.readFileSync(v1SummaryPath, 'utf-8'));
      } catch {
        v1Data = null;
      }
    }

    const v1Available = !!v1Data;
    const v1Totals = v1Data ? { total: v1Data.totalTests, passed: v1Data.passed, failed: v1Data.failed } : { total: 41, passed: 0, failed: 0 };
    const v2Total = Object.values(v2DomainSummary).reduce((s, d) => s + d.total, 0);
    const v2Passed = Object.values(v2DomainSummary).reduce((s, d) => s + d.passed, 0);

    const v1Domains = v1Data ? Object.keys(v1Data.domainSummary) : [
      'Domain 1: Job Management',
      'Domain 2: Sourcing & Search',
      'Domain 3: Pipeline & Candidate Management',
      'Domain 4: Communication',
      'Domain 5: Interviews & Scheduling',
      'Domain 6: Automation & Productivity',
      'Domain 7: Analytics & Insights',
      'Resilience & Edge Cases',
    ];

    const newDomainsInV2 = Object.keys(v2DomainSummary).filter(d => !v1Domains.includes(d));

    return {
      v1Available,
      v1DataSource: v1Available ? 'eval-summary-v1.json' : 'estimated (file not found)',
      v1Date: v1Data?.generatedAt || '2026-04-04 (estimated)',
      v2Date: new Date().toISOString(),
      totalTestsDelta: v2Total - v1Totals.total,
      v1TotalTests: v1Totals.total,
      v2TotalTests: v2Total,
      v1Domains: v1Domains.length,
      v2Domains: Object.keys(v2DomainSummary).length,
      newDomains: newDomainsInV2,
      newClassificationsInV2: ['CLARIFICAÇÃO ADEQUADA', 'RECUSA ÉTICA', 'AÇÃO PARCIAL'],
      passRateDelta: v1Available && v1Totals.total > 0
        ? ((v2Passed / v2Total) - (v1Totals.passed / v1Totals.total)) * 100
        : null,
    };
  }

  private generateExecutiveSummary(
    domainSummary: Record<string, DomainSummary>,
    classificationTotals: Record<string, number>,
    v1Comparison: Record<string, unknown>,
  ): string {
    const totalTests = Object.values(domainSummary).reduce((s, d) => s + d.total, 0);
    const totalPassed = Object.values(domainSummary).reduce((s, d) => s + d.passed, 0);
    const passRate = totalTests > 0 ? ((totalPassed / totalTests) * 100).toFixed(1) : '0';
    const totalDomains = Object.keys(domainSummary).length;
    const newDomains = (v1Comparison.newDomains as string[])?.length || 0;
    const delta = v1Comparison.totalTestsDelta as number;

    const lines: string[] = [
      `Production Readiness Eval V2 — ${totalTests} cenários em ${totalDomains} domínios (${newDomains} novos).`,
      `Pass rate: ${passRate}% | Delta vs V1: +${delta} cenários.`,
      `Classificações: ${Object.entries(classificationTotals).map(([k, v]) => `${k}: ${v}`).join(', ')}.`,
    ];

    const weakDomains = Object.entries(domainSummary)
      .filter(([, d]) => d.total > 0 && (d.passed / d.total) < 0.7)
      .map(([name]) => name);

    if (weakDomains.length > 0) {
      lines.push(`Domínios abaixo de 70% pass rate: ${weakDomains.join(', ')}.`);
    }

    return lines.join(' ');
  }
}

export default EvalSummaryReporter;
