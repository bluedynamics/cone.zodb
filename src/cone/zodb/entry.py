from plumber import (
    plumber,
    default,
    extend,
)
from node.parts import (
    AsAttrAccess,
    NodeChildValidate,
    Nodespaces,
    Attributes,
    DefaultInit,
    Nodify,
    Lifecycle,
    Storage,
)
from node.locking import locktree
from node.ext.zodb import (
    IZODBNode,
    OOBTNode,
)
from zope.interface import implements
from pyramid.threadlocal import get_current_request
from cone.app.model import AppNode
from cone.zodb.interfaces import (
    IZODBEntry,
    IZODBEntryNode,
)


def zodb_entry_for(node):
    while node:
        if IZODBEntryNode.providedBy(node):
            return node._v_parent
        if node.parent is None or not IZODBNode.providedBy(node):
            return None
        node = node.parent


class ZODBEntryNode(OOBTNode):
    implements(IZODBEntryNode)

    @property
    def __parent__(self):
        return self._v_parent.parent

    @property
    def metadata(self):
        return self.parent.metadata

    @property
    def properties(self):
        return self.parent.properties


class ZODBEntryStorage(Storage):
    implements(IZODBEntry)
    
    node_factory = default(ZODBEntryNode)

    @default
    @property
    def db_name(self):
        return self.name
    
    @default
    @property
    def db_root(self):
        # XXX: should be configurable somehow
        conn = get_current_request().environ['repoze.zodbconn.connection']
        return conn.root()
    
    @default
    @property
    def storage(self):
        entry = self.db_root.get(self.db_name)
        if not entry:
            entry = self.node_factory(name=self.name)
            self.db_root[self.db_name] = entry
        entry.__parent__ = self
        return entry
    
    @extend
    @locktree
    def __setitem__(self, key, val):
        self.storage[key] = val

    @extend
    @locktree
    def __delitem__(self, key):
        del self.storage[key]

    @default
    @locktree
    def __call__(self):
        self.storage()


class ZODBEntry(object):
    __metaclass__ = plumber
    __plumbing__ = (
        AppNode,
        AsAttrAccess,
        NodeChildValidate,
        Nodespaces,
        Attributes,
        DefaultInit,
        Nodify,
        Lifecycle,
        ZODBEntryStorage,
    )