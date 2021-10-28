import unittest
from datetime import datetime, timedelta

from streamz import Stream


class TestQuadlaterationStream(unittest.TestCase):

    def test_merge_rssi_streams_does_not_emit_for_insufficient_emissions(self):
        s1 = Stream()
        s2 = Stream()
        s3 = Stream()
        s4 = Stream()

        L = Stream.merge_rssi_streams(s1, s2, s3, s4).sink_to_list()

        start = datetime(2000, 1, 1, 0, 0, 0)
        interval5s = timedelta(seconds=5)

        s1.emit((start, 10))
        s2.emit((start + interval5s, 10))
        s3.emit((start + 2*interval5s, 10))
        s4.emit((start + 3*interval5s, 10))

        self.assertTrue(len(L) == 0)

    def test_merge_rssi_streams_does_emits_for_sufficient_emissions(self):
        s1 = Stream()
        s2 = Stream()
        s3 = Stream()
        s4 = Stream()

        L = Stream().merge_rssi_streams(s1, s2, s3, s4).sink_to_list()

        start = datetime(2000, 1, 1, 0, 0, 0)
        interval5s = timedelta(seconds=5)

        s1.emit((start, 10))
        s2.emit((start + interval5s, 10))
        s3.emit((start + 2*interval5s, 10))
        result_timestamp = start + 3*interval5s
        s4.emit((result_timestamp, 10))
        s1.emit((start + 4*interval5s, 20))
        s2.emit((start + 5*interval5s, 20))
        s3.emit((start + 6*interval5s, 20))

        self.assertTrue(len(L) == 1)
        result = L[0]
        values = result.values
        self.assertTrue(result.timestamp == result_timestamp)
        self.assertTrue(values[3] == 10)
        self.assertTrue(values[0] == 17.5)
        self.assertTrue(values[1] == 15)
        self.assertTrue(values[2] == 12.5)

    def test_merge_rssi_streams_emits_multiple_values(self):
        s1 = Stream()
        s2 = Stream()
        s3 = Stream()
        s4 = Stream()

        L = Stream().merge_rssi_streams(s1, s2, s3, s4).sink_to_list()

        start = datetime(2000, 1, 1, 0, 0, 0)
        interval5s = timedelta(seconds=5)

        s1.emit((start, 10))
        s2.emit((start + interval5s, 10))
        s3.emit((start + 2*interval5s, 10))
        result1_timestamp = start + 3*interval5s
        s4.emit((result1_timestamp, 10))
        result2_timestamp = start + 4*interval5s
        s1.emit((result2_timestamp, 20))
        s2.emit((start + 5*interval5s, 20))
        s3.emit((start + 6*interval5s, 20))
        s4.emit((start + 7*interval5s, 20))

        self.assertTrue(len(L) == 2)
        self.assertTrue(L[0].timestamp == result1_timestamp)
        self.assertTrue(L[1].timestamp == result2_timestamp)

    def test_merge_rssi_streams_emits_correct_values(self):

        s1 = Stream()
        s2 = Stream()
        s3 = Stream()
        s4 = Stream()

        L = Stream.merge_rssi_streams(s1, s2, s3, s4).sink_to_list()

        start = datetime(2000, 1, 1, 0, 0, 0)
        interval5s = timedelta(seconds=5)

        s1.emit((start, 10))
        s2.emit((start + interval5s, 10))
        s3.emit((start + 2*interval5s, 10))
        s4.emit((start + 3*interval5s, 10))
        s3.emit((start + 4*interval5s, 10))
        s4.emit((start + 5*interval5s, 20))
        s1.emit((start + 6*interval5s, 10))
        s2.emit((start + 7*interval5s, 10))
        s3.emit((start + 8*interval5s, 10))

        self.assertTrue(len(L) == 3)
        self.assertTrue(L[0].values[3] == 10)
        self.assertTrue(L[1].values[3] == 15)
        self.assertTrue(L[2].values[3] == 20)



if __name__ == '__main__':
    unittest.main()

