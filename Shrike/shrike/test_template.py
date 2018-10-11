import os
import unittest

from tempfile import NamedTemporaryFile

import shrike
from shrike import template


class TestTemplate(unittest.TestCase):

    def setUp(self):
        self.template_contents = [
                '<?php',
                '#X-SHRIKE TEMPLATE-VERSION 2',
                '# Store shellcode on the heap',
                '$buf_shellcode = demo_create_buffer(128);',
                '##########',
                '#X-SHRIKE HEAP-MANIP 64 ',
                '#X-SHRIKE RECORD-ALLOC 0 1',
                '$buf_shellcode = demo_create_buffer(128);',
                '#X-SHRIKE HEAP-MANIP 64 256 128',
                '#X-SHRIKE RECORD-ALLOC 0 2',
                '$buf_shellcode = demo_create_buffer(128);',
                '#X-SHRIKE REQUIRE-DISTANCE 1 2 128',
                '?>']

        self.template_file = NamedTemporaryFile('w', delete=False)
        self.template_file.write('\n'.join(self.template_contents))
        self.template_file.close()

    def tearDown(self):
        os.remove(self.template_file.name)

    def testComponentsLen(self):
        t = template.Template(self.template_file.name)
        components = t.components()
        self.assertIsInstance(components[1], shrike.template.TemplateVersion)
        self.assertEqual(len(components), 13)

    def testTemplateVersion(self):
        t = template.Template(self.template_file.name)
        components = t.components()
        self.assertIsInstance(components[1], shrike.template.TemplateVersion)
        self.assertEqual(components[1].version, 2)

    def testCode(self):
        t = template.Template(self.template_file.name)
        components = t.components()
        self.assertIsInstance(components[0], shrike.template.Code)
        expected = (
                self.template_contents[0] + '\n' +
                self.template_contents[1] + '\n')
        self.assertEqual(components[0].code, expected)

        expected = (
                self.template_contents[7] + '\n' +
                self.template_contents[8] + '\n')
        self.assertEqual(components[6].code, expected)

    def testHeapManip(self):
        t = template.Template(self.template_file.name)
        components = t.components()

        self.assertIsInstance(components[3], shrike.template.HeapManip)
        self.assertIsInstance(components[7], shrike.template.HeapManip)

        self.assertEqual(components[3].sizes, [64])
        self.assertEqual(components[7].sizes, [64, 256, 128])

    def testRecordAlloc(self):
        t = template.Template(self.template_file.name)
        components = t.components()

        self.assertIsInstance(components[5], shrike.template.RecordAlloc)
        self.assertIsInstance(components[9], shrike.template.RecordAlloc)

        self.assertEqual(components[5].index, 0)
        self.assertEqual(components[5].identifier, 1)
        self.assertEqual(components[9].index, 0)
        self.assertEqual(components[9].identifier, 2)

    def testRequireDistance(self):
        t = template.Template(self.template_file.name)
        components = t.components()

        self.assertIsInstance(components[11], shrike.template.RequireDistance)
        self.assertEqual(components[11].id0, 1)
        self.assertEqual(components[11].id1, 2)
        self.assertEqual(components[11].distance, 128)

    def testIteration(self):
        t = template.Template(self.template_file.name)
        components = [x for x in t]
        self.assertEqual(len(components), 13)

        self.assertIsInstance(components[5], shrike.template.RecordAlloc)
        self.assertIsInstance(components[9], shrike.template.RecordAlloc)
        self.assertIsInstance(components[11], shrike.template.RequireDistance)


if __name__ == '__main__':
    unittest.main()
