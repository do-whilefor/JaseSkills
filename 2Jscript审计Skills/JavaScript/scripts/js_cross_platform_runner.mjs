#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

function commandExists(command, versionArgs = ['--version']) {
  const probe = spawnSync(command, versionArgs, { stdio: 'ignore', shell: false });
  return probe.status === 0;
}

function findPython() {
  if (process.env.PYTHON) return [process.env.PYTHON];
  if (process.platform === 'win32' && commandExists('py', ['-3', '--version'])) return ['py', '-3'];
  if (commandExists('python', ['--version'])) return ['python'];
  if (commandExists('python3', ['--version'])) return ['python3'];
  console.error('No Python interpreter found. Install Python 3.10+ and make python/py available on PATH, or set PYTHON.');
  process.exit(127);
}

const py = findPython();
const commands = {
  'env:check': [...py, 'scripts/install_and_env_check.py', '--root', '.', '--out', 'reports/env-check'],
  'windows:check': [...py, 'scripts/js_windows_env_check.py', '--root', '.', '--out', 'reports/windows-check', '--simulate-windows'],
  'windows:validate': [...py, 'scripts/js_windows_validation_suite.py', '--root', '.', '--out', 'tests/windows-validation-last-run', '--clean'],
  'fixture:test': [...py, 'scripts/run_js_top_tier_fixture_tests.py', '.'],
  'self:check': [...py, 'scripts/package_self_check.py', '.'],
  'assets:check': [...py, 'scripts/verify_js_top_tier_assets.py', '.'],
  'quality': [...py, 'scripts/js_top_tier_quality_gate.py', '--report-dir', 'reports/js-top-tier'],
  'quality:strict': [...py, 'scripts/js_top_tier_quality_gate.py', '--report-dir', 'reports/js-top-tier', '--strict'],
  'dashboard': [...py, 'scripts/js_evidence_dashboard_drilldown.py', '--report-dir', 'reports/js-top-tier'],
  'semantic:sample': [...py, 'scripts/js_semantic_graph_builder.py', '--root', 'fixtures/js-top-tier-samples/app', '--out', 'tests/worldclass-last-run'],
  'detectors:sample': [...py, 'scripts/js_detector_registry_runner.py', '--graph', 'tests/worldclass-last-run/js_semantic_graph.json', '--ledger', 'tests/worldclass-last-run/js_asset_ledger.json', '--scope', 'tests/worldclass-last-run/scope.json', '--out', 'tests/worldclass-last-run'],
  'adversarial:test': [...py, 'scripts/js_adversarial_harness.py', '--out', 'tests/worldclass-last-run'],
  'self:worldclass': [...py, 'scripts/js_worldclass_selftest.py', '--root', '.'],
  'report:generate': [...py, 'scripts/js_top_tier_report_generator.py', '--report-dir', 'tests/worldclass-last-run'],
  'schema:semantic': [...py, 'scripts/js_schema_validator.py', '--schema', 'schemas/js-semantic-graph.schema.json', '--input', 'tests/worldclass-last-run/js_semantic_graph.json'],
  'schema:evidence': [...py, 'scripts/js_schema_validator.py', '--schema', 'schemas/js-evidence-manifest.schema.json', '--input', 'tests/reverse-audit-last-run/js_evidence_manifest.json'],
  'scope:check': [...py, 'scripts/js_scope_guard.py', '--scope', 'fixtures/worldclass-semantic-sample/scope.json', '--out', 'tests/worldclass-last-run'],
  'reverse:audit': [...py, 'scripts/js_reverse_claim_auditor.py', '--root', '.', '--out', 'tests/reverse-audit-last-run'],
  'unit:test': [...py, 'scripts/js_unit_tests.py', '--root', '.', '--out', 'tests/reverse-audit-last-run'],
  'validate:full': [...py, 'scripts/js_full_validation_suite.py', '--root', '.', '--out', 'tests/reverse-audit-last-run', '--clean'],
  'runtime:import': [...py, 'scripts/js_runtime_artifact_importer.py', '--evidence-root', 'fixtures/runtime-artifacts-import-sample', '--out', 'reports/js-top-tier'],
  'runtime:authorized-gate': [...py, 'scripts/js_authorized_target_import_gate.py', '--evidence-root', 'fixtures/runtime-artifacts-import-sample', '--out', 'reports/js-top-tier'],
  'roletenant:replay': [...py, 'scripts/js_role_tenant_authorization_replay.py', '--fixture-server', '--out', 'reports/js-top-tier'],
  'hiddenparam:acceptance': [...py, 'scripts/js_hidden_param_acceptance_matrix.py', '--fixture-server', '--out', 'reports/js-top-tier'],
  'runtime:bind': [...py, 'scripts/js_runtime_detector_binder.py', '--detectors', 'reports/js-top-tier/js_detector_registry_run.json', '--runtime-bundle', 'reports/js-top-tier/js_runtime_artifact_bundle.json', '--authorization', 'reports/js-top-tier/js_role_tenant_authorization_result.json', '--out', 'reports/js-top-tier'],
  'oss:replay': [...py, 'scripts/js_real_oss_replay_executor.py', '--vendor-local-oss10', '--out', 'reports/js-top-tier/real-oss-replay'],
  'p0:validate': [...py, 'scripts/js_full_validation_suite.py', '--root', '.', '--out', 'tests/p0-validation-last-run', '--clean'],
  'playwright:replay': [...py, 'scripts/js_playwright_safe_replay_executor.py', '--plan', 'reports/js-top-tier/playwright-local-plan.json', '--out', 'reports/js-top-tier/playwright-probe', '--execute'],
  'taint:interprocedural': [...py, 'scripts/js_semantic_graph_builder.py', '--root', 'fixtures/interprocedural-taint-sample', '--out', 'tests/taint-last-run'],
  'p1:validate': [...py, 'scripts/js_p1_validation_suite.py', '--root', '.', '--out', 'tests/p1-validation-last-run', '--clean']
};

const name = process.argv[2];
if (!name || name === '--help' || name === '-h') {
  console.log('Usage: node scripts/js_cross_platform_runner.mjs <command> [extra args]');
  console.log('Commands:');
  for (const key of Object.keys(commands).sort()) console.log('  ' + key);
  process.exit(name ? 0 : 2);
}
if (!commands[name]) {
  console.error(`Unknown command: ${name}`);
  console.error('Run with --help for command names.');
  process.exit(2);
}
const extra = process.argv.slice(3);
const cmd = [...commands[name], ...extra];
const exe = cmd[0];
const args = cmd.slice(1);
console.error('RUN ' + cmd.map(x => /\s/.test(x) ? JSON.stringify(x) : x).join(' '));
const result = spawnSync(exe, args, { stdio: 'inherit', shell: false, cwd: process.cwd(), env: process.env });
process.exit(result.status ?? 1);
