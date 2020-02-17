# -*- coding: utf-8 -*-
from .interfaces import IPanel
from plone.portlets.interfaces import IPortletManager
from zope.component import getUtilitiesFor
#todo: check where used:
from plone.portlets.interfaces import IPortletType
from zope.interface import implementer


def getAddablePortletTypes(interface):
    types = (p[1] for p in getUtilitiesFor(IPortletType))

    return filter(
        lambda p: any(
            i for i in p.for_ if interface.isOrExtends(i)
        ),
        types)


@implementer(IPortletManager)
class PanelPortletManager(object):
    """ Dummy IPortletManager implementation, registered as the named utility
        'panels'. For being able to reference an IPortletManager implementation
        in the portlet info, under the 'manager' key (See DisplayPanelView).
    """

    def __call__(self, context, request, view):
        raise NotImplementedError(
            "This portlet manager does not provide a renderer."
        )

    def get(self, name, default=None):
        return default

    def getAddablePortletTypes(self):
        return getAddablePortletTypes(IPanel)
