# -*- coding: utf-8 -*-
from Acquisition import Implicit
from OFS.Traversable import Traversable
from persistent import Persistent
from plone.app.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import ILocalPortletAssignable
from plone.portlets.interfaces import IPortletAssignment
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletType
from zope.component import getUtilitiesFor
from zope.container.contained import Contained
from zope.interface import implementer
from zope.interface import providedBy

from collective.panels.interfaces import IPanel
from collective.panels import _

PANEL_ANNOTATION_KEY = "collective.panels"


def getAddablePortletTypes(interface):
    types = (p[1] for p in getUtilitiesFor(IPortletType))

    return filter(
        lambda p: any(
            i for i in p.for_ if interface.isOrExtends(i)
        ),
        types)


def getAssignmentMapping(panel, manager):
    return panel


@implementer(IPortletAssignment, IPortletAssignmentMapping, ILocalPortletAssignable)
class PortletContainerAssignment(Implicit, Persistent, Contained, Traversable):

    __allow_access_to_unprotected_subobjects__ = 1

    # Currently, panel assignments do not carry state.
    data = None

    def __init__(self, name, *assignments):
        self.__name__ = name
        self._assignments = list(assignments)

    def __delitem__(self, name):
        for index, assignment in enumerate(self):
            if assignment.__name__ == name:
                break
        else:
            raise KeyError(name)

        self._assignments.pop(index)
        self._p_changed = True

    def __getitem__(self, name):
        for assignment in self:
            if assignment.__name__ == name:
                return assignment.__of__(self)

        raise KeyError(name)

    def __setitem__(self, name, assignment):
        # Make sure assignment name is unique, e.g. "calendar-1".
        if name in self:
            c = 1
            while True:
                suggestion = "%s-%d" % (name, c)
                if suggestion not in self:
                    break

                c += 1

            name = suggestion

        assignment.__name__ = name
        self._assignments.append(assignment)
        self._p_changed = True

    def __contains__(self, name):
        return any(name == assignment.__name__ for assignment in self)

    def __iter__(self):
        return iter(self._assignments)

    def __len__(self):
        return len(self._assignments)

    def __repr__(self):
        return '<%s name="%s" items="%d">' % (
            self.__class__.__name__, self.__name__, len(self._assignments)
        )

    def getId(self):
        return self.__name__

    @property
    def available(self):
        return any(
            assignment.available for assignment in self
        )

    def getAddablePortletTypes(self):
        interface = providedBy(self)
        return getAddablePortletTypes(interface)

    def items(self):
        return dict(zip(self.iterkeys(), self.itervalues()))

    def iterkeys(self):
        return (assignment.__name__ for assignment in self)

    def itervalues(self):
        return iter(self)

    def keys(self):
        return [assignment.__name__ for assignment in self]

    def values(self):
        return list(self)

    def updateOrder(self, keys):
        self._assignments.sort(
            key=lambda assignment: keys.index(assignment.__name__)
        )
        self._p_changed = True


@implementer(IPanel)
class Panel(PortletContainerAssignment):

    heading = u""
    css_class = u""

    def __init__(self, name, layout, css_class=None, heading=None, *assignments):
        super(Panel, self).__init__(name, *assignments)
        self.layout = layout
        self.css_class = css_class
        self.heading = heading

    @property
    def title(self):
        return _(u"Panel ${name} - ${heading}", mapping={'name': self.__name__, 'heading': self.heading})
