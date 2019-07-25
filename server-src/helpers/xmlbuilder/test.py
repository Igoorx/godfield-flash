# -*- encoding:utf8 -*-
from __future__ import with_statement
from nose.tools import eq_, raises
from xmlbuilder import XMLBuilder

class TestXMLBuilder(object):
    def setUp(self):
        self.xml = XMLBuilder('root')
        self.xml['xml_header'] = False
        self.xml['formatted'] = False
    
    def test_very_simple(self):
        eq_(str(self.xml), "<root />")

    def test_xml_header(self):
        self.xml['xml_header'] = True
        eq_(str(self.xml), '<?xml version="1.0" encoding="utf-8" ?>\n<root />')

    def test_unicode(self):
        self.xml.t
        eq_(unicode(self.xml), u"<root><t /></root>")

    def test_simple1(self):
        self.xml.t
        eq_(str(self.xml), "<root><t /></root>")

    def test_simple2(self):
        self.xml.t("some_data")
        eq_(str(self.xml), "<root><t>some_data</t></root>")

    def test_simple3(self):
        self.xml.t(a='1')
        eq_(str(self.xml), '<root><t a="1" /></root>')

    def test_simple4(self):
        self.xml.t("some data", a='1')
        eq_(str(self.xml), '<root><t a="1">some data</t></root>')

    def test_simple5(self):
        self.xml << "some data"
        eq_(str(self.xml), '<root>some data</root>')

    def test_simple6(self):
        self.xml << "some data" << '111' << '222'
        eq_(str(self.xml), '<root>some data111222</root>')

    @raises(ValueError)
    def test_wrong_data1(self):
        self.xml << 3

    @raises(ValueError)
    def test_wrong_data2(self):
        self.xml.t(attr=3)

    @raises(ValueError)
    def test_wrong_data2(self):
        self.xml.t("some_data", attr=3)

    @raises(ValueError)
    def test_wrong_data2(self):
        self.xml.t(True, attr=3)

    @raises(ValueError)
    def test_wrong_data3(self):
        self.xml.t(3)

    test_formatter1_res = \
"""<root>
    <t1 m="1">
        <t2 />
    </t1>
    <t3>mmm</t3>
</root>"""

    def test_formatter1(self):
        self.xml['formatted'] = True
        self.xml.t1(m='1').t2
        self.xml.t3('mmm')
        
        eq_(str(self.xml), self.test_formatter1_res)

    test_formatter2_res = '<root>\n\t<t1 m="1">\n\t\t<t2 />\n\t</t1>\n\t<t3>mmm</t3>\n</root>'

    def test_formatter2(self):
        self.xml['formatted'] = True
        self.xml['tabstep'] = '\t'
        self.xml.t1(m='1').t2
        self.xml.t3('mmm')
        
        eq_(str(self.xml), self.test_formatter2_res)

    def test_attrib(self):
        self.xml.t1(m='1').t2
        self.xml.t3('mmm')
        eq_(str(self.xml), '<root><t1 m="1"><t2 /></t1><t3>mmm</t3></root>')

    def test_with1(self):
        with self.xml.tree_root:
            pass

        eq_(str(self.xml), "<root><tree_root /></root>")        

    def test_with2(self):
        with self.xml.tree_root('rr'):
            pass

        eq_(str(self.xml), "<root><tree_root>rr</tree_root></root>")        

    def test_with3(self):
        with self.xml.tree_root(a='dt'):
            pass

        eq_(str(self.xml), '<root><tree_root a="dt" /></root>')        

    def test_with4(self):
        with self.xml.tree_root('mm', a='dt'):
            pass

        eq_(str(self.xml), '<root><tree_root a="dt">mm</tree_root></root>')        

    def test_with5(self):
        with self.xml.tree_root(a='dt'):
            self.xml << '11'

        eq_(str(self.xml), '<root><tree_root a="dt">11</tree_root></root>')        

    def test_with6(self):
        with self.xml.tree_root(a='dt'):
            self.xml << '11'
            self.xml.tt

        eq_(str(self.xml), '<root><tree_root a="dt">11<tt /></tree_root></root>')        

    def test_unicode(self):
        with self.xml.tree_root(a=u'dt'):
            self.xml << u'11'
            self.xml.tt('12')

        eq_(str(self.xml), u'<root><tree_root a="dt">11<tt>12</tt></tree_root></root>')        

    def test_unicode1(self):
        with self.xml.tree_root(a=u'dt'):
            self.xml << u'11'
            self.xml.tt('12')

        eq_(unicode(self.xml),
            u'<root><tree_root a="dt">11<tt>12</tt></tree_root></root>')        

    def test_unicode2(self):
        with self.xml.tree_root(a=u'dt'):
            self.xml << u'бла-бла-бла'
            self.xml.tt('12')

        eq_(str(self.xml).decode('utf8'),
            u'<root><tree_root a="dt">бла-бла-бла<tt>12</tt></tree_root></root>')        

    def test_with_all(self):
        self.xml.top
        with self.xml.tree_root('some data', attr='12'):
            self.xml.child1
            self.xml.child2('child data', attr='11')
            with self.xml.tree_subroot(attr='13'):
                self.xml.very_child('very data')
                with self.xml.tree_subsubroot:
                    pass

        eq_(str(self.xml), '<root>' + 
                             '<top />' + 
                                '<tree_root attr="12">some data' + 
                                    '<child1 />' + 
                                    '<child2 attr="11">child data</child2>' +
                                    '<tree_subroot attr="13">' +
                                        '<very_child>very data</very_child>'
                                        '<tree_subsubroot />' +
                                    '</tree_subroot>' +
                                '</tree_root>' + 
                            '</root>')



