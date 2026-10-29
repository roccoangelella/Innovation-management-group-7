"""Synthetic, offline verification of the production translation pipeline."""

import csv
import io
import json
from argparse import Namespace
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import translate_abstracts as t


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'humanoid_patents.zip'
        self.rows = [
            ['100', '2020', 'Robotic arm', 'en', 'An arm, with two joints.\nSensor (11).', 'en', 'B25J'],
            ['101', '2021', 'Bras robotique', 'fr', 'Un bras avec deux articulations (13).', 'fr', 'B25J'],
            ['102', '2022', 'Leer', 'de', '  ', 'de', 'B25J'],
            ['103', '2023', 'Unknown', '', 'Eine Maschine (8).', '', 'B25J'],
            *[[str(200 + i), '2020', '機械', 'ja', f'構造 {i} mm。', 'ja', 'B25J'] for i in range(10)],
        ]
        self.write_source(self.rows)
        self.args = Namespace(
            input=str(self.source), output=str(self.root / 'output.csv'), state=str(self.root / 'progress.jsonl'),
            env=str(self.root / '.env'), endpoint='https://example.invalid/v1/chat/completions',
            model='gemini-cascade', stats_only=False, batch_size=8, max_batch_chars=12000,
            max_requests=None, rpm=0, retries=0, backoff=0, timeout=1,
        )

    def write_source(self, rows):
        data = io.StringIO(newline='')
        writer = csv.writer(data)
        writer.writerow(t.SOURCE_FIELDS)
        writer.writerows(rows)
        with zipfile.ZipFile(self.source, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('humanoid_patents.csv', data.getvalue())

    def read_output(self):
        with open(self.args.output, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def fake(self, calls):
        def translate(endpoint, key, model, batch, timeout):
            calls.append([(x['docdb_family_id'], x['abstract_language']) for x in batch])
            return {x['docdb_family_id']: 'English of ' + x['abstract'] for x in batch}
        return translate

    def test_stats_without_api(self):
        self.args.stats_only = True
        data = t.run(self.args, lambda *a: self.fail('Unexpected API call'))
        self.assertEqual((data['total'], data['missing'], data['non_english_or_unknown']), (14, 1, 12))
        self.assertEqual(data['languages']['ja'], 10)
        self.assertFalse(Path(self.args.state).exists())

    def test_complete_corpus_batches_and_languages(self):
        calls = []
        summary = t.run(self.args, self.fake(calls))
        self.assertEqual([len(c) for c in calls], [8, 4])
        self.assertEqual((summary['completed'], summary['translated'], summary['incomplete']), (13, 12, 0))
        self.assertEqual(summary['translated_unknown_language'], 1)
        self.assertIn(('101', 'fr'), calls[0])
        self.assertIn(('103', ''), calls[0])
        output = self.read_output()
        self.assertEqual([x['docdb_family_id'] for x in output], ['100', '101', '103'] + [str(200+i) for i in range(10)])
        self.assertEqual(output[0]['abstract_en'], output[0]['abstract'])
        self.assertEqual(output[1]['abstract'], 'Un bras avec deux articulations (13).')
        self.assertEqual(list(output[1]), t.OUTPUT_FIELDS)
        t.run(self.args, self.fake(calls))
        self.assertEqual(len(calls), 2)

    def test_budget_and_resume(self):
        self.args.max_requests = 1
        calls = []
        summary = t.run(self.args, self.fake(calls))
        self.assertEqual((summary['completed'], summary['incomplete']), (9, 4))
        self.assertEqual(summary['stop_reason'], 'request_budget')
        self.args.max_requests = None
        summary = t.run(self.args, self.fake(calls))
        self.assertEqual(summary['incomplete'], 0)
        self.assertEqual([len(c) for c in calls], [8, 4])

    def test_invalid_batch_falls_back_to_singletons(self):
        def malformed(endpoint, key, model, batch, timeout):
            if len(batch) > 1:
                raise t.ResponseError('not JSON')
            if batch[0]['docdb_family_id'] == '103':
                raise t.ResponseError('bad content')
            return {batch[0]['docdb_family_id']: 'English'}
        summary = t.run(self.args, malformed)
        self.assertEqual((summary['translated'], summary['incomplete']), (11, 1))
        self.assertEqual(summary['failed_singletons_this_run'], 1)
        self.assertNotIn('103', [x['docdb_family_id'] for x in self.read_output()])

    def test_rate_quota_stop_and_resume(self):
        def quota(endpoint, key, model, batch, timeout):
            raise t.ApiError(429, 'HTTP 429')
        first = t.run(self.args, quota)
        self.assertEqual(first['completed'], 1)
        self.assertEqual(first['api_attempts_this_run'], 1)
        self.assertIn('429', first['stop_reason'])
        second = t.run(self.args, self.fake([]))
        self.assertEqual(second['incomplete'], 0)

    def test_retry_and_attempt_budget(self):
        tries = []
        def flaky(endpoint, key, model, batch, timeout):
            tries.append(len(batch))
            if len(tries) < 2:
                raise t.ApiError(503, 'HTTP 503')
            return {r['docdb_family_id']: 'Translated' for r in batch}
        self.args.max_requests = 2
        self.args.retries = 2
        first = t.run(self.args, flaky)
        self.assertEqual(first['api_attempts_this_run'], 2)
        self.assertEqual(first['successful_api_calls_this_run'], 1)
        self.assertEqual(first['incomplete'], 4)

    def test_journal_partial_write_and_middle_corruption(self):
        p = Path(self.args.state)
        p.write_bytes(b'{"docdb_family_id":"100","abstract_en":"Original","translation_status":"original_en"}\n{"bad"')
        self.assertEqual(set(t.load_progress(p)), {'100'})
        self.assertNotIn(b'bad', p.read_bytes())
        p.write_bytes(b'{"bad"}\n')
        with self.assertRaisesRegex(ValueError, 'Malformed'):
            t.load_progress(p)

    def test_changed_zip_rejected_for_resumption(self):
        t.run(self.args, self.fake([]))
        self.write_source(self.rows[:-1])
        with self.assertRaisesRegex(ValueError, 'changed'):
            t.run(self.args, self.fake([]))

    def test_duplicate_ids_rejected(self):
        self.write_source(self.rows + [self.rows[1]])
        with self.assertRaisesRegex(ValueError, 'duplicated'):
            t.run(self.args, self.fake([]))

    def test_parse_json_contract(self):
        items = [{'docdb_family_id': '101', 'abstract_language': 'fr', 'abstract': 'bonjour'}]
        parsed = t.parse_translations('```json\n{"translations":[{"docdb_family_id":"101","abstract_en":"Hello"}]}\n```', items)
        self.assertEqual(parsed, {'101': 'Hello'})
        with self.assertRaises(t.ResponseError):
            t.parse_translations('{"translations":[{"docdb_family_id":"102","abstract_en":"Hello"}]}', items)

    def test_completely_english_without_credentials(self):
        self.write_source([self.rows[0]])
        summary = t.run(self.args, lambda *a: self.fail('No API expected'))
        self.assertEqual(summary['completed'], 1)
        self.assertEqual(summary['api_attempts_this_run'], 0)


if __name__ == '__main__':
    unittest.main()
