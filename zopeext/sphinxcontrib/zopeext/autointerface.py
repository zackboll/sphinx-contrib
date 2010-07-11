"""
=============
autointerface
=============

Sphinx extension that adds an :dir:`autointerface` directive, which can be
used like autoclass to document zope interfaces.  Interfaces are
intended to be very different beasts than regular python classes, and
as a result require customized access to documentation, signatures
etc.

`autointerface` directive
-----------------------
The :dir:`autointerface` directive has the same form and option as the
:dir:`autoclass` directive::

    .. autointerface:: IClass
       ...

.. seealso:: :mod:`sphinx.ext.autodoc`

.. note:: This extension also serves as a simple example of using the
   new sphinx version 6.0 version :mod:`autodoc` refactoring.  Mostly
   this was straight forward, but I stumbled across a "gotcha":

   The `objtype` attribute of the documenters needs to be unique.
   Thus, for example, :attr:`InterfaceMethodDocumenter.objtype`
   cannot be `'method'` because this would overwrite the entry in
   :attr:`AutoDirective._registry` used to choose the correct
   documenter.
"""
import sphinx.ext.autodoc
import sphinx.directives

import zope.interface.interface

def interface_getattr(*v):
    """Behaves like `getattr` but for zope Interface objects which
    hide the attributes.


    .. note::  Originally I simply tried to override
      :meth:`InterfaceDocumenter.special_attrgetter` to deal with the
      special access needs of :class:`Interface` objects, but found
      that this is not intended to be overwritten.  Instead one should
      register the special accessor  using
      :func:`app.add_autodoc_attrgetter`.
    """
    obj, name = v[:2]
    if "__dict__" == name:
        # Interface objects do not list their members through
        # __dict__.
        return dict((n,obj.get(n)) for n in obj.names())
    try:
        return getattr(obj, name)
    except AttributeError:
        if name in obj.names():
            return obj.get(name)
        elif 2 < len(v):
            return v[2]
        else:
            raise

def interface_format_args(obj):
    r"""Return the signature of an interface method or of an
    interface."""
    sig = "()"
    if isinstance(obj, zope.interface.interface.InterfaceClass):
        if '__init__' in obj:
            sig = interface_format_args(obj.get('__init__'))
    else:
        sig = obj.getSignatureString()
        if sig.startswith('(self, '):
            sig = "(" + sig[7:]
        elif sig.startswith('(cls, '):
            sig = "(" + sig[6:]
        elif sig in ("(self)", "(cls)"):
            sig = "()"
    return sig

class InterfaceDocumenter(sphinx.ext.autodoc.ClassDocumenter):
    """A Documenter for :class:`zope.interface.Interface` interfaces.
    """
    objtype = 'interface'               # Called 'autointerface'

    priority = 10       # needs a higher priority than ClassDocumenter

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, zope.interface.interface.InterfaceClass)

    def format_args(self):
        return interface_format_args(self.object)

    def get_object_members(self, want_all):
        """
        Return `(members_check_module, members)` where `members` is a
        list of `(membername, member)` pairs of the members of *self.object*.

        If *want_all* is True, return all members.  Else, only return those
        members given by *self.options.members* (which may also be none).
        """
        obj = self.object
        names = obj.names(want_all)
        return False, [(_name, obj.get(_name)) for _name in names]

class InterfaceAttributeDocumenter(sphinx.ext.autodoc.AttributeDocumenter):
    """A Documenter for :class:`zope.interface.interface.Attribute`
    interface attributes.
    """
    objtype = 'interfaceattribute'   # Called 'autointerfaceattribute'
    directivetype = 'attribute'      # Formats as a 'class' for now

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, zope.interface.interface.Attribute)

class InterfaceMethodDocumenter(sphinx.ext.autodoc.MethodDocumenter):
    """
    A Documenter for :class:`zope.interface.interface.Attribute`
    interface attributes.
    """
    objtype = 'interfacemethod'   # Called 'autointerfacemethod'
    directivetype = 'method'      # Formats as a 'class' for now

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, zope.interface.interface.Method)

    def format_args(self):
        return interface_format_args(self.object)

class InterfaceDirective(sphinx.directives.DescDirective):
    """An 'interface' directive."""
    def get_index_text(self, modname, name_cls):
        if self.desctype == 'interface':
            if not modname:
                return '%s (built-in interface)' % name_cls[0]
            return '%s (interface in %s)' % (name_cls[0], modname)
        else:
            return ''

def setup(app):
    app.add_autodoc_attrgetter(zope.interface.interface.InterfaceClass,
                               interface_getattr)
    app.add_autodocumenter(InterfaceDocumenter)
    app.add_autodocumenter(InterfaceAttributeDocumenter)
    app.add_autodocumenter(InterfaceMethodDocumenter)
    app.add_directive('interface', InterfaceDirective)