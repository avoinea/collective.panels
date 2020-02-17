from plone.app.layout.viewlets import interfaces
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from collective.panels.interfaces import IGlobalSettings
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter, getUtility

from collective.panels import _

# todo: this could be dynamic:

MANAGER_INTERFACE_TO_NAME = {
    interfaces.IBelowContentBody: 'plone.belowcontentbody',
    interfaces.IAboveContentBody: 'plone.abovecontentbody',
    interfaces.IPortalFooter: 'plone.portalfooter',
    interfaces.IPortalTop: 'plone.portaltop',
}

@implementer(IVocabularyFactory)
class ManagerVocabulary(object):

    # Order is important here; the default location will be the first
    # available (non-hidden) manager.
    all_viewlet_managers = (
        (interfaces.IBelowContentBody, _(u"Below page content")),
        (interfaces.IAboveContentBody, _(u"Above page content")),
        (interfaces.IPortalFooter, _(u"Portal footer")),
        (interfaces.IPortalTop, _(u"Portal top")),
    )

    def __call__(self, context):
        return SimpleVocabulary([
            SimpleTerm(interface, interface.__name__, title)
            for (interface, title) in self.all_viewlet_managers
        ])


managers = ManagerVocabulary()


@implementer(IVocabularyFactory)
class CssClassesVocabulary(object):
    """ Vocabulary for css classes, stored in the registry. """

    def __call__(self, context):
        result = []

        try:
            settings = getUtility(IRegistry).forInterface(IGlobalSettings)
        except:
            return SimpleVocabulary(result)

        if settings.css_classes:
            for css_class in settings.css_classes:
                value = css_class
                if '|' in css_class:
                    value, title = css_class.split('|', 1)
                else:
                    value = title = css_class
                result.append(SimpleTerm(value=value, title=title))

        return SimpleVocabulary(result)
