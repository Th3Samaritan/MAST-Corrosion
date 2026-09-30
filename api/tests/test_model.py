"""Real checkpoint parity tests. Requires LFS files and api/requirements.txt."""
import importlib.util
import io
import csv
import os
from pathlib import Path
import sys
import unittest

API = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('MODEL_ROOT', API.parent)).resolve()
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('model_worker', API / 'model-worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials = worker.catalog()
        cls.pair = {'anode': cls.materials[-1]['Material'], 'cathode': cls.materials[0]['Material'],
                    'environment': worker.ENVIRONMENTS[0], 'area_ratio': 1.0}

    def test_all_checkpoints_match_retained_inference(self):
        import inference
        lookup, _, _ = inference.load_galvanic_data()
        for run in ['1', '2', '3']:
            for ratio in [0.01, 1, 50]:
                pair = {**self.pair, 'area_ratio': ratio}
                actual = worker.predict({'run': run, 'pairs': [pair]})['results'][0]
                expected = inference.predict_single(worker.model_for(run), pair['anode'], pair['cathode'], pair['environment'], ratio, lookup)
                self.assertAlmostEqual(actual['current_proxy'], expected['current_density'], places=7)
                self.assertAlmostEqual(actual['unfavorable_score'], expected['compatibility_prob'], places=7)

    def test_quoted_csv_matches_single(self):
        pair = {**self.pair, 'anode': next(m['Material'] for m in self.materials if ',' in m['Material'])}
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['anode','cathode','environment','area_ratio'])
        writer.writeheader(); writer.writerow(pair)
        actual = worker.predict({'csv': output.getvalue()})['results']
        expected = worker.predict({'pairs': [pair]})['results']
        self.assertEqual(actual, expected)

    def test_unknown_material_and_bad_range_rejected(self):
        for change in [{'anode': 'unknown'}, {'area_ratio': float('nan')}, {'area_ratio': True}, {'area_ratio': 51}, {'environment': 'unknown'}]:
            with self.assertRaises(ValueError): worker.predict({'pairs': [{**self.pair, **change}]})

    def test_training_logs_retained(self):
        self.assertEqual([(r['run'],r['epochs']) for r in worker.training()], [('1',200),('2',200),('3',200)])

if __name__ == '__main__': unittest.main()
