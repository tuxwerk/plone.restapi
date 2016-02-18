# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.testing import PLONE_RESTAPI_AT_INTEGRATION_TESTING
from zope.component import getMultiAdapter

import json
import unittest


class TestATContentSerializer(unittest.TestCase):

    layer = PLONE_RESTAPI_AT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])

        self.doc1 = self.portal[self.portal.invokeFactory(
            'ATTestDocument', id='doc1', title='Test Document')]

        self.doc1.setCreationDate(DateTime('2016-01-21T01:14:48+00:00'))
        self.doc1.setModificationDate(DateTime('2016-01-21T01:24:11+00:00'))
        self.doc1._setUID('76644b6611ab44c6881efd9cb17db12e')

    def serialize(self, obj):
        serializer = getMultiAdapter((obj, self.request),
                                     ISerializeToJson)
        return serializer()

    def test_serializer_returns_json_serializeable_object(self):
        obj = self.serialize(self.doc1)
        self.assertTrue(isinstance(json.dumps(obj), str),
                        'Not JSON serializable')

    def test_serializer_includes_context(self):
        obj = self.serialize(self.doc1)
        self.assertIn(u'@context', obj)
        self.assertEqual(u'http://www.w3.org/ns/hydra/context.jsonld',
                         obj[u'@context'])

    def test_serializer_includes_id(self):
        obj = self.serialize(self.doc1)
        self.assertIn(u'@id', obj)
        self.assertEqual(self.doc1.absolute_url(), obj[u'@id'])

    def test_serializer_includes_type(self):
        obj = self.serialize(self.doc1)
        self.assertIn(u'@type', obj)
        self.assertEqual(self.doc1.portal_type, obj[u'@type'])

    def test_serializer_includes_uid(self):
        obj = self.serialize(self.doc1)
        self.assertIn(u'UID', obj)
        self.assertEqual(u'76644b6611ab44c6881efd9cb17db12e', obj[u'UID'])

    def test_serializer_includes_creation_date(self):
        obj = self.serialize(self.doc1)
        self.assertIn(u'creation_date', obj)
        self.assertEqual(u'2016-01-21T01:14:48+00:00', obj[u'creation_date'])

    def test_serializer_includes_modification_date(self):
        obj = self.serialize(self.doc1)
        self.assertIn(u'modification_date', obj)
        self.assertEqual(u'2016-01-21T01:24:11+00:00',
                         obj[u'modification_date'])

    def test_serializer_ignores_field_without_read_permission(self):
        self.doc1.setTestReadPermissionField(u'Secret Stuff')
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        self.assertNotIn(u'testReadPermissionField',
                         self.serialize(self.doc1))

    def test_serializer_ignores_writeonly_field(self):
        self.doc1.setTestWriteonlyField(u'Secret Stuff')
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        self.assertNotIn(u'testWriteonlyField',
                         self.serialize(self.doc1))

    def test_serializer_includes_folder_items(self):
        folder = self.portal[self.portal.invokeFactory(
            'ATTestFolder', id='folder', title='Test Folder')]
        folder.invokeFactory('ATTestFolder', id='subfolder', title='Subfolder')
        folder.invokeFactory('ATTestDocument', id='doc', title='A Document')
        obj = self.serialize(folder)
        self.assertIn('member', obj)
        self.assertDictEqual({
            '@id': 'http://nohost/plone/folder/subfolder',
            'description': '',
            'title': u'Subfolder'},
            obj['member'][0])
        self.assertDictEqual({
            '@id': 'http://nohost/plone/folder/doc',
            'description': '',
            'title': u'A Document'},
            obj['member'][1])