# -*- coding: utf-8 -*-
from collective.panels.content import Panel
from collective.panels import _
from collective.panels.interfaces import IPanel
from Acquisition import ExplicitAcquisitionWrapper
from Acquisition import Implicit
from Acquisition import aq_base
from OFS.Traversable import Traversable
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.portlets.assignable import localPortletAssignmentMappingAdapter
from plone.portlets.interfaces import ILocalPortletAssignable
from plone.portlets.interfaces import IPortletAssignmentMapping
from zExceptions import BadRequest, NotFound
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.traversing.interfaces import ITraversable
from plone.protect.interfaces import IDisableCSRFProtection
from zope.interface import alsoProvides
from collective.panels.utils import encode
from collective.panels.utils import decode
from collective.panels.interfaces import IPanelManager


@implementer(IBrowserPublisher, IPortletAssignmentMapping, ILocalPortletAssignable, IPanelManager)
class PanelManager(Implicit, Traversable):

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, context, request, location, name):
        # context is the rendering context of the panel.
        # location is the location of the panel definition.
        self.__name__ = decode(name)
        self.context = context
        self.request = request

        # We use `self` as the viewlet manager here because only the
        # name is actually needed.
        self._mapping = localPortletAssignmentMappingAdapter(location, self)

    def __delitem__(self, name):
        del self._mapping[name]
        IStatusMessage(self.request).addStatusMessage(
            _(u"Panel removed."), type="info")

    def __getitem__(self, name):
        for panel in self.getAssignments():
            if panel.__name__ == name:
                return panel.__of__(self)

        raise KeyError(name)

    def getAssignments(self):
        """Return panel assignments.

        Note that panels are specialized portlet assignments. We make
        sure that the contained assignment implement the ``IPanel``
        interface.
        """

        assignments = self._mapping.values()
        return filter(IPanel.providedBy, assignments)

    def addPanel(self, *args):
        """Add panel with the provided layout and optional css_class and heading"""

        # Find first available integer; we use this as the
        # panel name.
        n = 1
        for panel in self.getAssignments():
            i = int(panel.__name__)
            if i >= n:
                n = i + 1

        panel = Panel(str(n), *args)
        aq_base(self._mapping)[panel.__name__] = panel

        return panel

    def __iter__(self):
        return (
            assignment.__of__(self) for assignment
            in self.getAssignments()
        )

    def __len__(self):
        return len(tuple(iter(self)))

    def getId(self):
        return "++panel++%s" % encode(self.__name__)

    def publishTraverse(self, request, name):
        try:
            return self[name]
        except KeyError:
            raise NotFound(self, name, request)

    def index(self, name):
        for index, panel in enumerate(self):
            if panel.__name__ == name:
                return index

        return -1

    def keys(self):
        return self._mapping.keys()

    def updateOrder(self, keys):
        self._mapping.updateOrder(keys)


@implementer(ITraversable)
@adapter(IAttributeAnnotatable, IBrowserRequest)
class PanelTraverser(object):
    def __init__(self, context, request=None):
        self.context = context
        self.request = request

    def traverse(self, name, ignore):
        if not name:
            raise BadRequest("Must provide panel name.")

        return PanelManager(self.context, self.request, self.context, name)
