"""Unit tests for _filterDQ / _applyDQEventState on sonObj."""

import io
import unittest
import types
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Minimal stub that satisfies _filterDQ without loading real sonar files
# ---------------------------------------------------------------------------
from pingmapper.class_sonObj import sonObj


def _make_stub(son_rows: list[dict]) -> sonObj:
    """Return a bare sonObj instance with sonMetaDF pre-populated."""
    obj = sonObj.__new__(sonObj)
    obj.sonMetaDF = pd.DataFrame(son_rows)
    return obj


# ---------------------------------------------------------------------------
# Helper to write a temporary CSV for dq_table
# ---------------------------------------------------------------------------
def _dq_csv(rows: list[dict]) -> str:
    """Serialise rows to a CSV string and return a path via tmp file."""
    import tempfile, os
    df = pd.DataFrame(rows)
    fd, path = tempfile.mkstemp(suffix='.csv')
    df.to_csv(path, index=False)
    os.close(fd)
    return path


# ===========================================================================
class TestDQFilterDatetimeOffset(unittest.TestCase):
    """dq_time_offset shifts sonar timestamps before matching."""

    def _run(self, son_ts_list, dq_rows, dq_time_offset, expected_kept_indices):
        stub = _make_stub([
            {'date': ts.split()[0], 'time': ts.split()[1], 'time_s': i + 1}
            for i, ts in enumerate(son_ts_list)
        ])
        stub.sonMetaDF.index = range(len(son_ts_list))

        path = _dq_csv(dq_rows)
        result = stub._filterDQ(
            stub.sonMetaDF,
            dq_table=path,
            dq_time_field='ts',
            dq_flag_field='flag',
            dq_keep_values=['Use'],
            dq_src_utc_offset=0.0,
            dq_target_utc_offset=0.0,
            dq_time_offset=dq_time_offset,
        )
        kept = list(result[result['filter_dq'] == True].index)
        self.assertEqual(kept, expected_kept_indices)

    def test_dq_filter_uses_datetime_and_offset(self):
        """Positive offset shifts sonar timestamps forward into a 'Use' block."""
        son_ts = [
            '2024-01-01 00:00:01',
            '2024-01-01 00:00:02',
            '2024-01-01 00:00:03',
        ]
        dq_rows = [
            {'ts': '2024-01-01T00:00:10+00:00', 'flag': 'Use'},
        ]
        # offset +10 → sonar times become 11, 12, 13 — all after the Use event at t=10
        self._run(son_ts, dq_rows, dq_time_offset=10.0, expected_kept_indices=[0, 1, 2])

    def test_dq_filter_uses_datetime_timezone_offsets(self):
        """UTC offset difference is applied to dq timestamps."""
        son_ts = [
            '2024-01-01 00:00:01',
            '2024-01-01 00:00:02',
            '2024-01-01 00:00:03',
        ]
        # DQ stored in UTC+1 (3600 s ahead), no sonar offset
        dq_rows = [
            {'ts': '2024-01-01T01:00:00+01:00', 'flag': 'Use'},
        ]
        # After tz conversion dq ts == 2024-01-01 00:00:00 UTC == 0 epoch offset
        # sonar pings at 1,2,3 s — all after the Use event
        from pingmapper.class_sonObj import sonObj as SO
        stub = _make_stub([
            {'date': ts.split()[0], 'time': ts.split()[1], 'time_s': i + 1}
            for i, ts in enumerate(son_ts)
        ])
        path = _dq_csv(dq_rows)
        result = stub._filterDQ(
            stub.sonMetaDF,
            dq_table=path,
            dq_time_field='ts',
            dq_flag_field='flag',
            dq_keep_values=['Use'],
            dq_src_utc_offset=1.0,   # DQ was recorded in UTC+1
            dq_target_utc_offset=0.0,
            dq_time_offset=0.0,
        )
        kept = list(result[result['filter_dq'] == True].index)
        self.assertEqual(kept, [0, 1, 2])


class TestDQFilterNumericTime(unittest.TestCase):
    """Falls back to numeric time_s when datetime parse fails."""

    def test_dq_filter_uses_numeric_time(self):
        rows = [{'time_s': float(i)} for i in range(1, 6)]
        stub = _make_stub(rows)

        dq_rows = [{'ts': 2.5, 'flag': 'Use'}]
        path = _dq_csv(dq_rows)

        result = stub._filterDQ(
            stub.sonMetaDF,
            dq_table=path,
            dq_time_field='ts',
            dq_flag_field='flag',
            dq_keep_values=['Use'],
            dq_src_utc_offset=0.0,
            dq_target_utc_offset=0.0,
            dq_time_offset=0.0,
        )
        # pings at time_s 1,2 are before the Use event at 2.5 → excluded
        # pings at time_s 3,4,5 are in the Use block
        kept = list(result[result['filter_dq'] == True].index)
        self.assertEqual(kept, [2, 3, 4])


class TestDQFilterEventStateBlocks(unittest.TestCase):
    """State-block semantics: alternating Use/NoUse transitions."""

    def test_dq_filter_uses_event_state_blocks(self):
        """
        DQ transitions:
            t=2.2  → Use    (good)
            t=4.1  → NoUse  (bad)
            t=6.4  → Use    (good)

        Sonar pings at t=1..7 (numeric).
        Expected kept: pings whose (adjusted) time falls in a Use block
            ping 0 (t=1): before first event  → excluded
            ping 1 (t=2): before first event  → excluded
            ping 2 (t=3): in [2.2, 4.1) Use  → kept
            ping 3 (t=4): in [2.2, 4.1) Use  → kept
            ping 4 (t=5): in [4.1, 6.4) NoUse → excluded
            ping 5 (t=6): in [4.1, 6.4) NoUse → excluded
            ping 6 (t=7): in [6.4, ∞) Use    → kept
        """
        rows = [{'time_s': float(t)} for t in range(1, 8)]
        stub = _make_stub(rows)

        dq_rows = [
            {'ts': 2.2, 'flag': 'Use'},
            {'ts': 4.1, 'flag': 'NoUse'},
            {'ts': 6.4, 'flag': 'Use'},
        ]
        path = _dq_csv(dq_rows)

        result = stub._filterDQ(
            stub.sonMetaDF,
            dq_table=path,
            dq_time_field='ts',
            dq_flag_field='flag',
            dq_keep_values=['Use'],
            dq_src_utc_offset=0.0,
            dq_target_utc_offset=0.0,
            dq_time_offset=0.0,
        )
        kept = list(result[result['filter_dq'] == True].index)
        self.assertEqual(kept, [2, 3, 6])


if __name__ == '__main__':
    unittest.main()
