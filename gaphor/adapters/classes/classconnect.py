#!/usr/bin/env python

# Copyright (C) 2009-2017 Arjan Molenaar <gaphor@gmail.com>
#                         Artur Wroblewski <wrobell@pld-linux.org>
#                         Dan Yeaw <dan@yeaw.me>
#
# This file is part of Gaphor.
#
# Gaphor is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 2 of the License, or (at your option) any later
# version.
#
# Gaphor is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Gaphor.  If not, see <http://www.gnu.org/licenses/>.
"""
Classes related (dependency, implementation) adapter connections.
"""

from __future__ import absolute_import

import logging
from zope import component

from gaphor.UML import uml2, modelfactory
from gaphor.adapters.connectors import UnaryRelationshipConnect, RelationshipConnect
from gaphor.diagram import items

log = logging.getLogger(__name__)

class DependencyConnect(RelationshipConnect):
    """
    Connect two NamedItem elements using a Dependency
    """
    component.adapts(items.NamedItem, items.DependencyItem)

    def allow(self, handle, port):
        line = self.line
        element = self.element

        # Element should be a NamedElement
        if not element.subject or \
                not isinstance(element.subject, uml2.NamedElement):
            return False

        return super(DependencyConnect, self).allow(handle, port)

    def reconnect(self, handle, port):
        line = self.line
        dep = line.subject
        if handle is line.head:
            for s in dep.supplier:
                del dep.supplier[s]
        elif handle is line.tail:
            for c in dep.client:
                del dep.client[c]
        self.reconnect_relationship(handle, line.dependency_type.supplier, line.dependency_type.client)

    def connect_subject(self, handle):
        """
        TODO: cleck for existing relationships (use self.relation())
        """
        line = self.line

        if line.auto_dependency:
            canvas = line.canvas
            opposite = line.opposite(handle)

            if handle is line.head:
                client = self.get_connected(opposite).subject
                supplier = self.element.subject
            else:
                client = self.element.subject
                supplier = self.get_connected(opposite).subject
            line.dependency_type = modelfactory.dependency_type(client, supplier)

        relation = self.relationship_or_new(line.dependency_type,
                                            line.dependency_type.supplier,
                                            line.dependency_type.client)
        line.subject = relation


component.provideAdapter(DependencyConnect)


class GeneralizationConnect(RelationshipConnect):
    """
    Connect Classifiers with a Generalization relationship.
    """
    # FixMe: Both ends of the generalization should be of the same  type?
    component.adapts(items.ClassifierItem, items.GeneralizationItem)

    def reconnect(self, handle, port):
        self.reconnect_relationship(handle, uml2.Generalization.general, uml2.Generalization.specific)

    def connect_subject(self, handle):
        log.debug('connect_subject: %s' % handle)
        relation = self.relationship_or_new(uml2.Generalization,
                                            uml2.Generalization.general,
                                            uml2.Generalization.specific)
        log.debug('found: %s' % relation)
        self.line.subject = relation


component.provideAdapter(GeneralizationConnect)


class AssociationConnect(UnaryRelationshipConnect):
    """
    Connect association to classifier.
    """
    component.adapts(items.ClassifierItem, items.AssociationItem)

    def allow(self, handle, port):
        element = self.element

        # Element should be a Classifier
        if not isinstance(element.subject, uml2.Classifier):
            return None

        return super(AssociationConnect, self).allow(handle, port)

    def connect_subject(self, handle):
        element = self.element
        line = self.line

        c1 = self.get_connected(line.head)
        c2 = self.get_connected(line.tail)
        if c1 and c2:
            head_type = c1.subject
            tail_type = c2.subject

            # First check if we do not already contain the right subject:
            if line.subject:
                end1 = line.subject.memberEnd[0]
                end2 = line.subject.memberEnd[1]
                if (end1.type is head_type and end2.type is tail_type) \
                        or (end2.type is head_type and end1.type is tail_type):
                    return

            # Create new association
            relation = modelfactory.create_association(self.element_factory, head_type, tail_type)
            relation.package = element.canvas.diagram.namespace

            line.head_end.subject = relation.memberEnd[0]
            line.tail_end.subject = relation.memberEnd[1]

            # Do subject itself last, so event handlers can trigger
            line.subject = relation

    def reconnect(self, handle, port):
        line = self.line
        c = self.get_connected(handle)
        if handle is line.head:
            end = line.tail_end
            oend = line.head_end
        elif handle is line.tail:
            end = line.head_end
            oend = line.tail_end
        else:
            raise ValueError('Incorrect handle passed to adapter')

        nav = oend.subject.navigability

        modelfactory.set_navigability(line.subject, end.subject, None)  # clear old data

        oend.subject.type = c.subject
        modelfactory.set_navigability(line.subject, oend.subject, nav)

    def disconnect_subject(self, handle):
        """
        Disconnect model element.
        Disconnect property (memberEnd) too, in case of end of life for
        Extension
        """
        opposite = self.line.opposite(handle)
        c1 = self.get_connected(handle)
        c2 = self.get_connected(opposite)
        if c1 and c2:
            old = self.line.subject
            del self.line.subject
            del self.line.head_end.subject
            del self.line.tail_end.subject
            if old and len(old.presentation) == 0:
                for e in list(old.memberEnd):
                    e.unlink()
                old.unlink()


component.provideAdapter(AssociationConnect)


class ImplementationConnect(RelationshipConnect):
    """
    Connect Interface and a BehavioredClassifier using an Implementation.
    """
    component.adapts(items.NamedItem, items.ImplementationItem)

    def allow(self, handle, port):
        line = self.line
        element = self.element

        # Element at the head should be an Interface
        if handle is line.head and \
                not isinstance(element.subject, uml2.Interface):
            return None

        # Element at the tail should be a BehavioredClassifier
        if handle is line.tail and \
                not isinstance(element.subject, uml2.BehavioredClassifier):
            return None

        return super(ImplementationConnect, self).allow(handle, port)

    def reconnect(self, handle, port):
        line = self.line
        impl = line.subject
        if handle is line.head:
            for s in impl.contract:
                del impl.contract[s]
        elif handle is line.tail:
            for c in impl.implementatingClassifier:
                del impl.implementatingClassifier[c]
        self.reconnect_relationship(handle, uml2.Implementation.contract, uml2.Implementation.implementatingClassifier)

    def connect_subject(self, handle):
        """
        Perform implementation relationship connection.
        """
        relation = self.relationship_or_new(uml2.Implementation,
                                            uml2.Implementation.contract,
                                            uml2.Implementation.implementatingClassifier)
        self.line.subject = relation


component.provideAdapter(ImplementationConnect)

# vim:sw=4:et:ai
