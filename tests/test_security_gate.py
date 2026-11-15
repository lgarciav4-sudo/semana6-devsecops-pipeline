import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from security_gate import read_json, evaluate, normalized_severity

class GateTests(unittest.TestCase):
    def test_high_semgrep_blocks(self):
        a = read_json(ROOT/'ejemplos/semgrep-high.json')
        b = read_json(ROOT/'ejemplos/dependency-check-clean.json')
        self.assertEqual(len(evaluate(a, b, 'HIGH')[1]), 1)
    def test_high_sca_blocks(self):
        a = read_json(ROOT/'ejemplos/semgrep-low.json')
        b = read_json(ROOT/'ejemplos/dependency-check-high.json')
        self.assertEqual(len(evaluate(a, b, 'HIGH')[1]), 1)
    def test_low_finding_passes_high_gate(self):
        a = read_json(ROOT/'ejemplos/semgrep-low.json')
        b = read_json(ROOT/'ejemplos/dependency-check-clean.json')
        self.assertEqual(len(evaluate(a, b, 'HIGH')[1]), 0)
    def test_threshold_low_blocks_low(self):
        a = read_json(ROOT/'ejemplos/semgrep-low.json')
        b = read_json(ROOT/'ejemplos/dependency-check-clean.json')
        self.assertEqual(len(evaluate(a, b, 'LOW')[1]), 1)
    def test_missing_report_is_error(self):
        with self.assertRaises(ValueError): read_json('/file/not/found')
    def test_missing_dependency_array_is_error(self):
        with self.assertRaises(ValueError): evaluate({'results':[]}, {}, 'HIGH')
    def test_missing_semgrep_array_is_error(self):
        with self.assertRaises(ValueError): evaluate({}, {'dependencies':[]}, 'HIGH')
    def test_cvss_fallback(self):
        self.assertEqual(normalized_severity(None, 9.8), 'CRITICAL')
    def test_semgrep_errors_are_not_ignored(self):
        with self.assertRaises(ValueError): evaluate({'results':[], 'errors':[{'message':'failure'}]}, {'dependencies':[]}, 'HIGH')
    def test_critical_blocks_at_high(self):
        a={'results':[], 'errors':[]}
        b={'dependencies':[{'vulnerabilities':[{'severity':'CRITICAL','name':'CVE-TEST'}]}]}
        self.assertEqual(len(evaluate(a,b,'HIGH')[1]),1)
    def test_invalid_json_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'roto.json'
            path.write_text('{no es json', encoding='utf-8')
            with self.assertRaises(ValueError):
                read_json(path)
    def test_analysis_exception_is_technical_error(self):
        report = {'dependencies': [], 'scanInfo': {'analysisExceptions': [{'message': 'fallo de analizador'}]}}
        with self.assertRaises(ValueError):
            evaluate({'results': [], 'errors': []}, report, 'HIGH')
    def test_exit_code_separates_vulnerability_from_technical_error(self):
        import subprocess
        script = ROOT / 'scripts' / 'security_gate.py'
        blocked = subprocess.run(
            [sys.executable, str(script), '--semgrep', str(ROOT / 'ejemplos/semgrep-high.json'),
             '--dependency-check', str(ROOT / 'ejemplos/dependency-check-clean.json'), '--fail-on', 'HIGH'],
            capture_output=True, text=True)
        self.assertEqual(blocked.returncode, 1)
        self.assertIn('BUILD BLOQUEADO', blocked.stdout)
        self.assertNotIn('BUILD APROBADO', blocked.stdout)
        missing = subprocess.run(
            [sys.executable, str(script), '--semgrep', str(ROOT / 'no-existe.json'),
             '--dependency-check', str(ROOT / 'ejemplos/dependency-check-clean.json'), '--fail-on', 'HIGH'],
            capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        self.assertIn('ERROR:', missing.stderr)
        self.assertNotIn('BUILD APROBADO', missing.stdout)

if __name__ == '__main__': unittest.main()
