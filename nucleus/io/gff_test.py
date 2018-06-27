# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for nucleus.io.gff."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from absl.testing import parameterized

from nucleus.io import gff
from nucleus.protos import gff_pb2
from nucleus.testing import test_utils
from nucleus.util import io_utils
from nucleus.util import ranges

# Names of testdata GFF files; we also reuse these basenames for output files
# in the tmp directory.
TEXT_GFF_FILES = ('test_features.gff', 'test_features.gff.gz')
TFRECORD_GFF_FILES = ('test_features.gff.tfrecord',
                      'test_features.gff.tfrecord.gz')
ALL_GFF_FILES = TEXT_GFF_FILES + TFRECORD_GFF_FILES

EXPECTED_GFF_VERSION = 'gff-version 3.2.1'


class GffReaderTests(parameterized.TestCase):

  @parameterized.parameters(*ALL_GFF_FILES)
  def test_iterate_gff_reader(self, gff_filename):
    gff_path = test_utils.genomics_core_testdata(gff_filename)
    expected = [('ctg123', 999, 9000), ('ctg123', 999, 1012)]

    with gff.GffReader(gff_path) as reader:
      records = list(reader.iterate())
    self.assertLen(records, 2)
    self.assertEqual(
        [(r.range.reference_name, r.range.start, r.range.end) for r in records],
        expected)

  @parameterized.parameters(*TEXT_GFF_FILES)
  def test_native_gff_header(self, gff_filename):
    gff_path = test_utils.genomics_core_testdata(gff_filename)
    with gff.GffReader(gff_path) as reader:
      self.assertEqual(EXPECTED_GFF_VERSION, reader.header.gff_version)
    with gff.NativeGffReader(gff_path) as native_reader:
      self.assertEqual(EXPECTED_GFF_VERSION, native_reader.header.gff_version)


class GffWriterTests(parameterized.TestCase):
  """Tests for GffWriter."""

  def setUp(self):
    tfrecord_file = test_utils.genomics_core_testdata(
        'test_features.gff.tfrecord')
    self.records = list(
        io_utils.read_tfrecords(tfrecord_file, proto=gff_pb2.GffRecord))
    self.header = gff_pb2.GffHeader(
        sequence_regions=[ranges.make_range('ctg123', 0, 1497228)])

  @parameterized.parameters(*ALL_GFF_FILES)
  def test_roundtrip_writer(self, filename):
    output_path = test_utils.test_tmpfile(filename)
    with gff.GffWriter(output_path, header=self.header) as writer:
      for record in self.records:
        writer.write(record)

    with gff.GffReader(output_path) as reader:
      v2_records = list(reader.iterate())

    self.assertEqual(self.records, v2_records)


if __name__ == '__main__':
  absltest.main()
