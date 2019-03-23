# -*- coding: utf-8 -*-
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import PLONE_RESTAPI_DX_FUNCTIONAL_TESTING
from plone.restapi.testing import RelativeSession

import unittest

try:
    from Products.CMFPlone.factory import _IMREALLYPLONE5  # noqa
except ImportError:
    PLONE5 = False
else:
    PLONE5 = True


@unittest.skipIf(not PLONE5, 'Just Plone 5 currently.')
class TestControlpanelsEndpoint(unittest.TestCase):

    layer = PLONE_RESTAPI_DX_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({'Accept': 'application/json'})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def tearDown(self):
        self.api_session.close()

    def test_schema_user_get(self):
        response = self.api_session.get('/@userschema')

        self.assertEqual(200, response.status_code)
        response = response.json()

        self.assertIn('fullname', response['fieldsets'][0]['fields'])
        self.assertIn('email', response['fieldsets'][0]['fields'])
        self.assertIn('home_page', response['fieldsets'][0]['fields'])
        self.assertIn('description', response['fieldsets'][0]['fields'])
        self.assertIn('location', response['fieldsets'][0]['fields'])
        self.assertIn('portrait', response['fieldsets'][0]['fields'])

        self.assertIn('fullname', response['properties'])
        self.assertIn('email', response['properties'])
        self.assertIn('home_page', response['properties'])
        self.assertIn('description', response['properties'])
        self.assertIn('location', response['properties'])
        self.assertIn('portrait', response['properties'])

        self.assertIn('email', response['required'])

        self.assertTrue('object', response['type'])
