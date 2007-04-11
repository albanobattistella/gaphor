
import unittest
from zope import component
from gaphor.UML import *
from gaphor.UML.interfaces import *
import gc
import weakref, sys


# Event handlers are registered as persisting top level handlers, since no
# unsubscribe functionality is provided.
handled = False
events = []
last_event = None

@component.adapter(IServiceEvent)
def handler(event):
    global handled, events, last_event
    handled = True
    events.append(event)
    last_event = event

component.provideHandler(handler)


class ElementFactoryTestCase(unittest.TestCase):

    def setUp(self):
        self.factory = ElementFactory()

    def tearDown(self):
        del self.factory
        self.clearEvents()

    def clearEvents(self):
        global handled, events, last_event
        handled = False
        events = [ ]
        last_event = None

    def testCreate(self):
        ef = self.factory

        p = ef.create(Parameter)
        wp = weakref.ref(p)
        assert len(ef.values()) == 1

    def testFlush(self):
        ef = self.factory

        p = ef.create(Parameter)
        wp = weakref.ref(p)
        assert len(ef.values()) == 1
        ef.flush()
        del p
        self.clearEvents()

        gc.collect()

        assert wp() is None
        assert len(ef.values()) == 0

    def testUnlink(self):
        ef = self.factory
        p = ef.create(Parameter)

        assert len(ef.values()) == 1

        p.unlink()

        assert len(ef.values()) == 0

        p = ef.create(Parameter)
        l = ef.create(LiteralString)
        p.defaultValue = l

        assert len(ef.values()) == 2

        p.unlink()
        del p

        assert len(ef.values()) == 0

    def testCreateEvent(self):
        ef = self.factory
        global handled
        p = ef.create(Parameter)
        self.assertTrue(IElementCreateEvent.providedBy(last_event) )
        self.assertTrue(handled)

    def testRemoveEvent(self):
        ef = self.factory
        global handled
        p = ef.create(Parameter)
        self.assertTrue(IElementCreateEvent.providedBy(last_event) )
        self.assertTrue(handled)
        self.clearEvents()
        p.unlink()
        self.assertTrue(IElementDeleteEvent.providedBy(last_event) )

    def testModelEvent(self):
        ef = self.factory
        global handled
        ef.notify_model()
        self.assertTrue(IModelFactoryEvent.providedBy(last_event) )

    def testFlushEvent(self):
        ef = self.factory
        global handled
        ef.flush()
        self.assertTrue(IFlushFactoryEvent.providedBy(last_event) )

    def testUndo(self):
        from gaphor.services.undomanager import get_undo_manager
        get_undo_manager().begin_transaction()
        ef = self.factory
        p = ef.create(Parameter)

        assert get_undo_manager().can_undo()

        get_undo_manager().commit_transaction()
        assert get_undo_manager().can_undo()
        assert ef.size() == 1

        get_undo_manager().undo_transaction()
        assert not get_undo_manager().can_undo()
        assert get_undo_manager().can_redo()
        assert ef.size() == 0

        get_undo_manager().redo_transaction()
        assert get_undo_manager().can_undo()
        assert not get_undo_manager().can_redo()
        assert ef.size() == 1
        assert ef.lselect()[0] is p
        

# vim:sw=4:et