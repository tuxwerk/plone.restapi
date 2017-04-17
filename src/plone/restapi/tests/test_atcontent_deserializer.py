# -*- coding: utf-8 -*-
from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes.interfaces import IObjectEditedEvent
from Products.Archetypes.interfaces import IObjectInitializedEvent
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.restapi.deserializer.atcontent import ValidationRequest
from plone.restapi.interfaces import IDeserializeFromJson
from plone.restapi.testing import PLONE_RESTAPI_AT_INTEGRATION_TESTING
from zExceptions import BadRequest
from zope.component import getMultiAdapter
from zope.component import provideHandler
from zope.component import provideSubscriptionAdapter
from zope.component import adapter
from zope.interface import implementer
from Products.Archetypes.interfaces import IObjectPostValidation
from Products.Archetypes.interfaces import IObjectPreValidation


import unittest


class TestATContentDeserializer(unittest.TestCase):

    layer = PLONE_RESTAPI_AT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])

        self.doc1 = self.portal[self.portal.invokeFactory(
            'ATTestDocument', id='doc1', title='Test Document')]

    def deserialize(self, body='{}', validate_all=False):
        self.request['BODY'] = body
        deserializer = getMultiAdapter((self.doc1, self.request),
                                       IDeserializeFromJson)
        return deserializer(validate_all=validate_all)

    def test_deserializer_ignores_readonly_fields(self):
        self.doc1.getField('testReadonlyField').set(self.doc1, 'Readonly')
        self.deserialize(body='{"testReadonlyField": "Changed"}')
        self.assertEquals('Readonly', self.doc1.getTestReadonlyField())

    def test_deserializer_updates_field_value(self):
        self.deserialize(body='{"testStringField": "Updated"}')
        self.assertEquals('Updated', self.doc1.getTestStringField())

    def test_deserializer_validates_content(self):
        with self.assertRaises(BadRequest) as cm:
            self.deserialize(body='{"testURLField": "Not an URL"}')
        self.assertEquals(
            u"Validation failed(isURL): 'Not an URL' is not a valid url.",
            cm.exception.message[0]['message'])

    def test_deserializer_clears_creation_flag(self):
        self.doc1.markCreationFlag()
        self.deserialize(body='{"testStringField": "Updated"}')
        self.assertFalse(self.doc1.checkCreationFlag(),
                         'Creation flag not cleared')

    def test_deserializer_notifies_object_initialized(self):
        def handler(obj, event):
            obj._handler_called = True
        provideHandler(handler, (IBaseObject, IObjectInitializedEvent,))
        self.doc1.markCreationFlag()
        self.deserialize(body='{"testStringField": "Updated"}')
        self.assertTrue(getattr(self.doc1, '_handler_called', False),
                        'IObjectInitializedEvent not notified')

    def test_deserializer_notifies_object_edited(self):
        def handler(obj, event):
            obj._handler_called = True
        provideHandler(handler, (IBaseObject, IObjectEditedEvent,))
        self.doc1.unmarkCreationFlag()
        self.deserialize(body='{"testStringField": "Updated"}')
        self.assertTrue(getattr(self.doc1, '_handler_called', False),
                        'IObjectEditedEvent not notified')

    def test_deserializer_raises_if_required_value_is_missing(self):
        with self.assertRaises(BadRequest) as cm:
            self.deserialize(body='{"testStringField": "My Value"}',
                             validate_all=True)
        self.assertEquals(u'TestRequiredField is required, please correct.',
                          cm.exception.message[0]['message'])

    def test_deserializer_succeeds_if_required_value_is_provided(self):
        self.deserialize(body='{"testRequiredField": "My Value"}',
                         validate_all=True)
        self.assertEquals(u'My Value', self.portal.doc1.getTestRequiredField())

    def test_post_validation(self):

        @implementer(IObjectPostValidation)
        @adapter(IBaseObject)
        class PostValidator(object):

            def __init__(self, context):
                self.context = context

            def __call__(self, request):
                return {'post': 'post_validation_error'}

        provideSubscriptionAdapter(PostValidator)

        with self.assertRaises(BadRequest) as cm:
            self.deserialize(body='{"testRequiredField": "My Value"}',
                             validate_all=True)

        self.assertEquals(
            'post_validation_error', cm.exception.message[0]['message'])

    def test_pre_validation(self):

        @implementer(IObjectPreValidation)
        @adapter(IBaseObject)
        class PreValidator(object):

            def __init__(self, context):
                self.context = context

            def __call__(self, request):
                return {'pre': 'pre_validation_error'}

        provideSubscriptionAdapter(PreValidator)

        with self.assertRaises(BadRequest) as cm:
            self.deserialize(body='{"testRequiredField": "My Value"}',
                             validate_all=True)

        self.assertEquals(
            'pre_validation_error', cm.exception.message[0]['message'])

    def test_set_layout(self):
        current_layout = self.doc1.getLayout()
        self.assertNotEquals(current_layout, "my_new_layout")
        self.deserialize(body='{"layout": "my_new_layout"}')
        self.assertEquals('my_new_layout', self.doc1.getLayout())


class TestValidationRequest(unittest.TestCase):

    layer = PLONE_RESTAPI_AT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        self.doc1 = self.portal[self.portal.invokeFactory(
            'ATTestDocument', id='doc1', title='Test Document')]
        self.request = ValidationRequest(self.layer['request'], self.doc1)

    def test_value_from_validation_request_using_key_access(self):
        self.assertEquals('Test Document', self.request['title'])

    def test_value_from_validation_request_using_get(self):
        self.assertEquals('Test Document', self.request.get('title'))

    def test_value_from_validation_request_form_using_key_access(self):
        self.assertEquals('Test Document', self.request.form['title'])

    def test_value_from_validation_request_form_using_get(self):
        self.assertEquals('Test Document', self.request.form.get('title'))

    def test_validation_request_contains_key(self):
        self.assertIn('title', self.request)

    def test_validation_request_form_contains_key(self):
        self.assertIn('title', self.request.form)

    def test_validation_request_key_access_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.request['foo']

    def test_validation_request_get_returns_default_value(self):
        self.assertEquals(None, self.request.get('foo'))
        marker = object()
        self.assertEquals(marker, self.request.get('foo', marker))

    def test_validation_request_form_key_access_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.request.form['foo']

    def test_validation_request_form_get_returns_default_value(self):
        self.assertEquals(None, self.request.form.get('foo'))
        marker = object()
        self.assertEquals(marker, self.request.form.get('foo', marker))

    def test_value_from_real_request_using_key_access(self):
        self.assertEquals('GET', self.request['REQUEST_METHOD'])

    def test_value_form_real_request_using_get(self):
        self.assertEquals('GET', self.request.get('REQUEST_METHOD'))
