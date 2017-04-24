# -*- coding: utf-8 -*-
from plone.folder.interfaces import IExplicitOrdering
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFCore.utils import getToolByName
from zExceptions import BadRequest


class OrderingMixin(object):
    # Handles both ordering and sorting

    def handle_ordering(self, data):
        if 'ordering' in data:
            obj_id = data['ordering']['obj_id']
            delta = data['ordering']['delta']
            subset_ids = data['ordering'].get('subset_ids')

            self.reorderItems(obj_id, delta, subset_ids)

    def reorderItems(self, obj_id, delta, subset_ids=None):
        # Based on wildcard.foldercontents.viewsItemOrder
        ordering = self.getOrdering()

        # Make sure we're seeing the same order as the client is.
        if subset_ids:
            position_id = [(ordering.getObjectPosition(i), i)
                           for i in subset_ids]
            position_id.sort()
            if subset_ids != [i for position, i in position_id]:
                raise BadRequest('Client/server ordering mismatch')

        # All movement is relative to the subset of ids, if passed in.
        if delta == 'top':
            ordering.moveObjectsToTop([obj_id], subset_ids=subset_ids)
        elif delta == 'bottom':
            ordering.moveObjectsToBottom([obj_id], subset_ids=subset_ids)
        else:
            delta = int(delta)
            ordering.moveObjectsByDelta([obj_id], delta, subset_ids=subset_ids)

    def getOrdering(self):
        if IPloneSiteRoot.providedBy(self.context):
            return self.context
        else:
            ordering = self.context.getOrdering()
            if not IExplicitOrdering.providedBy(ordering):
                return None
            return ordering

    def handle_sorting(self, data):
        if 'sort' not in data:
            return
        ordering = self.getOrdering()
        catalog = getToolByName(self.context, 'portal_catalog')

        sort_order = str(data['sort'].get('order', 'ascending'))

        brains = catalog(
            path={
                'query': '/'.join(self.context.getPhysicalPath()),
                'depth': 1
            },
            sort_on=data['sort']['on'],
            sort_order=sort_order,
        )

        for idx, brain in enumerate(brains):
            ordering.moveObjectToPosition(brain.id, idx)
