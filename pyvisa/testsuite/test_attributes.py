# -*- coding: utf-8 -*-
"""Test attribute descriptors.

"""
import enum

from pyvisa import constants
from pyvisa.attributes import (Attribute, BooleanAttribute, CharAttribute,
                               EnumAttribute, IntAttribute, RangeAttribute,
                               ValuesAttribute, AttrVI_ATTR_INTF_INST_NAME,
                               AttrVI_ATTR_ASRL_BAUD)

from . import BaseTestCase


class FakeResource:
    """Fake resource to test attributes.

    """

    def __init__(self, attr_id, attr_value):
        self.attr_id = attr_id
        self.attr_value = attr_value

    def get_visa_attribute(self, attr_id):
        if attr_id == self.attr_id:
            return self.attr_value
        else:
            raise ValueError()

    def set_visa_attribute(self, attr_id, value):
        if attr_id == self.attr_id:
            self.attr_value = value
        else:
            raise ValueError()


def create_resource_cls(attribute_name, attribute_type, read=True, write=True,
                        attrs={}):
    """Create a new attribute class and a resource using it.

    """
    attrs.update({"attribute_id": attribute_name, "read": read, "write": write})
    attr_cls = type("CA", (attribute_type,), attrs)

    return type("FakeR", (FakeResource,), {"attr": attr_cls()})


class TestAttributeClasses(BaseTestCase):
    """Test the descriptors used to handle VISA attributes.

    """

    def test_in_resource_method(self):
        """Test the in_resource class method.

        """
        self.assertTrue(AttrVI_ATTR_INTF_INST_NAME.in_resource(object()))
        self.assertTrue(
            AttrVI_ATTR_ASRL_BAUD.in_resource((constants.InterfaceType.asrl,
                                               "INSTR"))
        )
        self.assertFalse(AttrVI_ATTR_ASRL_BAUD.in_resource(object()))

    def test_Attribute(self):
        """Test the base class Attribute.

        """
        rc = create_resource_cls("attr_id", Attribute)
        r = rc("attr_id", 1)
        self.assertEqual(r.attr, 1)
        r.attr = 2
        self.assertEqual(r.attr, 2)

        # Check we do pass the write ID
        r.attr_id = "dummy"
        with self.assertRaises(ValueError):
            r.attr
        with self.assertRaises(ValueError):
            r.attr = 2

        # Un-readable attribute
        rc = create_resource_cls("attr_id", Attribute, read=False)
        r = rc("attr_id", 1)
        with self.assertRaises(AttributeError):
            r.attr

        # Un-writable attribute
        rc = create_resource_cls("attr_id", Attribute, write=False)
        r = rc("attr_id", 1)
        with self.assertRaises(AttributeError):
            r.attr = 1

    def test_BooleanAttribute(self):
        """Test BooleanAttribute.

        """
        rc = create_resource_cls("attr_id", BooleanAttribute)
        r = rc("attr_id", constants.VI_TRUE)
        self.assertEqual(r.attr, True)
        r.attr = False
        self.assertEqual(r.attr, False)
        self.assertEqual(r.attr_value, constants.VI_FALSE)

    def test_CharAttribute(self):
        """Test CharAttribute.

        """
        rc = create_resource_cls("attr_id", CharAttribute)
        r = rc("attr_id", ord("\n"))
        self.assertEqual(r.attr, "\n")
        r.attr = "\r"
        self.assertEqual(r.attr, "\r")
        self.assertEqual(r.attr_value, 13)

    def test_EnumAttribute(self):
        """Test EnumAttribute

        """
        @enum.unique
        class E(enum.IntEnum):
            a = 1
            b = 2

        rc = create_resource_cls("attr_id", EnumAttribute, attrs={"enum_type": E})
        r = rc("attr_id", 1)
        self.assertEqual(r.attr, E.a)
        r.attr = E.b
        self.assertEqual(r.attr, E.b)
        self.assertEqual(r.attr_value, 2)

        with self.assertRaises(ValueError):
            r.attr = 3

    def test_IntAttribute(self):
        """Test IntAttribute.

        """
        rc = create_resource_cls("attr_id", IntAttribute)
        r = rc("attr_id", "1")
        self.assertEqual(r.attr, 1)

    def test_RangeAttribute(self):
        """Test RangeAttribute

        """
        rc = create_resource_cls("attr_id", RangeAttribute,
                                 attrs={"min_value": 0,
                                        "max_value": 2})
        r = rc("attr_id", 1)
        r.attr = 0
        self.assertEqual(r.attr_value, 0)
        r.attr = 2
        self.assertEqual(r.attr_value, 2)
        r.attr = 1
        self.assertEqual(r.attr_value, 1)

        with self.assertRaises(ValueError) as cm:
            r.attr = -1

        self.assertIn("invalid value", str(cm.exception))
        self.assertNotIn(" or ", str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            r.attr = 3

        self.assertIn("invalid value", str(cm.exception))
        self.assertNotIn(" or ", str(cm.exception))

        rc = create_resource_cls("attr_id", RangeAttribute,
                                 attrs={"min_value": 0,
                                        "max_value": 2,
                                        "values": [10]})
        r = rc("attr_id", 1)
        r.attr = 10
        self.assertEqual(r.attr_value, 10)

        with self.assertRaises(ValueError) as cm:
            r.attr = 3

        self.assertIn("invalid value", str(cm.exception))
        self.assertIn(" or ", str(cm.exception))

    def test_ValuesAttribute(self):
        """Test ValuesAttribute

        """
        rc = create_resource_cls("attr_id", ValuesAttribute,
                                 attrs={"values": [10, 20]})
        r = rc("attr_id", 1)
        r.attr = 10
        self.assertEqual(r.attr_value, 10)

        with self.assertRaises(ValueError) as cm:
            r.attr = 3
        self.assertIn("invalid value", str(cm.exception))
