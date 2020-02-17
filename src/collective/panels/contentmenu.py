# -*- coding: utf-8 -*-
from AccessControl import getSecurityManager
from Products.CMFCore.interfaces import ISiteRoot
from plone.app.layout.navigation.interfaces import INavigationRoot
from plone.memoize.instance import memoize
from plone.portlets.interfaces import ILocalPortletAssignable
from plone.protect.utils import addTokenToUrl
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import ComponentLookupError
from zope.interface import implementer
from zope.interface import providedBy
from zope.browsermenu.menu import BrowserMenu
from zope.browsermenu.menu import BrowserSubMenuItem
from zope.schema.interfaces import IVocabularyFactory
from zope.viewlet.interfaces import IViewlet
from zope.component import getSiteManager
from collective.panels.interfaces import IPanelManagerSubMenuItem
from collective.panels.interfaces import IPanelManagerMenu
from collective.panels.interfaces import IGlobalSettings
from collective.panels import _
from collective.panels.utils import root_interface
from collective.panels.browser.display import DisplayPanelManagerViewlet
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage
from Products.Five.browser import BrowserView as View


PMF = _  # used for dynamic messages we don't want to extract


@implementer(IPanelManagerSubMenuItem)
class PanelManagerSubMenuItem(BrowserSubMenuItem):

    MANAGE_SETTINGS_PERMISSION = 'Panels: Manage panels'

    # todo: fix translations
    title = _(u'manage_panels_link', default=u'Manage panels')
    submenuId = 'plone_contentmenu_panelmanager'
    order = 51

    def __init__(self, context, request):
        super(PanelManagerSubMenuItem, self).__init__(context, request)
        self.context = context
        self.context_state = getMultiAdapter((context, request),
                                             name='plone_context_state')

    @property
    def extra(self):
        # TODO: are the css classes correct?
        return {'id': 'plone-contentmenu-panelmanager',
                'li_class': 'plonetoolbar-panel-manager'}

    @property
    def description(self):
        if self._manageSettings():
            return _(
                u'title_change_panels',
                default=u'Change the panels of this item'
            )
        else:
            return u''

    @property
    def action(self):
        return self.context.absolute_url() + '/manage-panels'

    @memoize
    def available(self):
        secman = getSecurityManager()
        has_manage_panels_permission = secman.checkPermission(
            self.MANAGE_SETTINGS_PERMISSION,
            self.context
        )
        if not has_manage_panels_permission:
            return False
        else:
            # If context can have portlets, it can also have panels.
            return ILocalPortletAssignable.providedBy(self.context)

    def selected(self):
        return False

    @memoize
    def _manageSettings(self):
        secman = getSecurityManager()
        has_manage_panels_permission = secman.checkPermission(
            self.MANAGE_SETTINGS_PERMISSION,
            self.context
        )
        return has_manage_panels_permission


@implementer(IPanelManagerMenu)
class PanelManagerMenu(BrowserMenu):

    @property
    @memoize
    def _lookup(self):
        gsm = getSiteManager()
        return gsm.adapters.lookupAll

#    @memoize
    def available_locations(self, context, request):
        return list(self._iter_locations(context, request))

    def all_viewlet_managers(self, context):
        factory = getUtility(
            IVocabularyFactory,
            name="collective.panels.vocabularies.Managers"
        )

        return tuple(
            (term.value, term.title) for term in factory(context)
        )

    def _iter_locations(self, context, request):
        for viewlet_manager_name, viewlet_manager_title in self._iter_viewlet_managers(context, request):
            yield {
                'name': viewlet_manager_name,
                'title': viewlet_manager_title,
            }

    def _iter_viewlet_managers(self, context, request):
        # We use a generic view to lookup the viewletmanagers.
        view = View(context, request)
        spec = tuple(map(providedBy, (context, request, view)))

        storage = getUtility(IViewletSettingsStorage)
        skinname = context.getCurrentSkinName()

        for viewlet_name, viewlet_manager_iface, viewlet_manager_title in self._iter_enabled_viewlet_managers(context, request):
            for viewlet_manager_name, factory in self._lookup(spec, viewlet_manager_iface):
                hidden = storage.getHidden(viewlet_manager_name, skinname)

                if viewlet_name not in hidden:
                    yield viewlet_manager_name, viewlet_manager_title

    def _iter_enabled_viewlet_managers(self, context, request):
        # We use a generic view to lookup the viewlets.
        view = View(context, request)
        spec = tuple(map(providedBy, (context, request, view)))

        try:
            settings = getUtility(IRegistry).forInterface(IGlobalSettings)
        except (ComponentLookupError, KeyError):
            ignore_list = ()
        else:
            if not root_interface().providedBy(context):
                ignore_list = settings.site_local_managers or ()
            else:
                ignore_list = ()

        for viewlet_manager_iface, viewlet_manager_title in self.all_viewlet_managers(context):
            if viewlet_manager_iface in ignore_list:
                continue

            for viewlet_name, factory in self._lookup(spec + (viewlet_manager_iface, ), IViewlet):
                try:
                    if issubclass(factory, DisplayPanelManagerViewlet):
                        yield viewlet_name, viewlet_manager_iface, viewlet_manager_title
                except TypeError:
                    # Issue #9: "Unexpected non-class object while
                    # iterating over viewlet managers"
                    continue

    def getMenuItems(self, context, request):
        """Return menu item entries in a TAL-friendly form."""
        items = []
        sm = getSecurityManager()
        # Bail out if the user can't manage panels
        if not sm.checkPermission(
                PanelManagerSubMenuItem.MANAGE_SETTINGS_PERMISSION,
                context
        ):
            return items

        # Bail out if not installed
        try:
            settings = getUtility(IRegistry).forInterface(IGlobalSettings)
        except (ComponentLookupError, KeyError):
            # This (non-critical) error is reported elsewhere. The
            # product needs to be installed before we let users manage
            # panels.
            return items

        managers = self.available_locations(context, request)
        current_url = context.absolute_url()

        for manager in managers:
            item = {
                'title': PMF(manager['title'],
                           default=manager['title']),
                'description': manager['name'],
                'action': addTokenToUrl(
                    '{0}/@@manage-panels/{1}'.format(
                        current_url,
                        manager['name']),
                    request),
                'selected': False,
                'icon': None,
                'extra': {
                    'id': 'panel-manager-{0}'.format(manager['name']),
                    'separator': None},
                'submenu': None,
            }

            items.append(item)
        # items.sort()
        return items
