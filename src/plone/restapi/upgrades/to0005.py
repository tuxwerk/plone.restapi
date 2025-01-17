# -*- coding: utf-8 -*-
from plone import api
from zope.component import queryUtility
from plone.dexterity.interfaces import IDexterityFTI

import logging

logger = logging.getLogger(__name__)

OLD_BEHAVIOR_NAME = "plone.restapi.behaviors.ITiles"
SHORT_OLD_BEHAVIOR_NAME = "plone.tiles"
NEW_BEHAVIOR_NAME = "plone.restapi.behaviors.IBlocks"


def rename_tiles_to_blocks(setup_context):
    """Rename tiles and tiles_layout fields from Tiles behavior to blocks and blocks_layout
    """
    pt = api.portal.get_tool("portal_types")

    types_with_tiles_behavior = []

    for _type in pt.objectIds():
        fti = queryUtility(IDexterityFTI, name=_type)
        if fti and OLD_BEHAVIOR_NAME in fti.behaviors:
            types_with_tiles_behavior.append(_type)
            new_fti = [
                currentbehavior
                for currentbehavior in fti.behaviors
                if currentbehavior != OLD_BEHAVIOR_NAME
            ]
            new_fti.append(NEW_BEHAVIOR_NAME)
            fti.behaviors = tuple(new_fti)
            logger.info("Migrated behavior of {} type".format(_type))

        # In case we used the short behavior name
        if fti and SHORT_OLD_BEHAVIOR_NAME in fti.behaviors:
            types_with_tiles_behavior.append(_type)
            new_fti = [
                currentbehavior
                for currentbehavior in fti.behaviors
                if currentbehavior != SHORT_OLD_BEHAVIOR_NAME
            ]
            new_fti.append(NEW_BEHAVIOR_NAME)
            fti.behaviors = tuple(new_fti)
            logger.info("Migrated behavior of {} type".format(_type))

    for brain in api.content.find(portal_type=types_with_tiles_behavior):
        obj = brain.getObject()
        obj.blocks = getattr(obj, "tiles", {})
        obj.blocks_layout = getattr(obj, "tiles_layout", {"items": []})
        logger.info("Migrated fields of content object: {}".format(obj.absolute_url()))
