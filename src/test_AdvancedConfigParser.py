import unittest

from AdvancedConfigParser import parse_string

class TestAdvancedConfigParser(unittest.TestCase):
    def test_bool(self):
        config = parse_string("""
        a = True
        b = False
        c = bool(1)
        d = bool(b)""")
        self.assertEqual(config.a, True)
        self.assertEqual(config.b, False)
        self.assertEqual(config.c, True)
        self.assertEqual(config.d, False)

    def test_int(self):
        config = parse_string("""
        a = 0
        b = 3298479328479234
        c = -34
        d = int(123)""")
        self.assertEqual(config.a, 0)
        self.assertEqual(config.b, 3298479328479234)
        self.assertEqual(config.c, -34)
        self.assertEqual(config.d, 123)
        config2 = parse_string(config.pretty_print())
        self.assertEqual(config2.a, config.a)
        self.assertEqual(config2.b, config.b)
        self.assertEqual(config2.c, config.c)
        self.assertEqual(config2.d, config.d)

    def test_float(self):
        config = parse_string("""
        a = 0.
        b = 4793284.79234
        c = -34.3
        d = float(123)""")
        self.assertEqual(config.a, 0.)
        self.assertEqual(type(config.a), float)
        self.assertEqual(config.b, 4793284.79234)
        self.assertEqual(config.c, -34.3)
        self.assertEqual(config.d, 123.)
        self.assertEqual(type(config.d), float)
        config2 = parse_string(config.dump())
        self.assertEqual(config2.a, config.a)
        self.assertEqual(type(config2.a), type(config.a))
        self.assertEqual(config2.b, config.b)
        self.assertEqual(config2.c, config.c)
        self.assertEqual(config2.d, config.d)
        self.assertEqual(type(config2.d), type(config.d))

    def test_string(self):
        config = parse_string("""
        a = "abc"
        b = 'def'
        c = a + b
        d = r'''multi
               line'''
        e = 'a"b'
        f = "a'b"
        """)
        self.assertEqual(config.a, "abc")
        self.assertEqual(config.b, "def")
        self.assertEqual(config.c, "abcdef")
        self.assertEqual(config.d, "multi\n               line")
        self.assertEqual(config.e, 'a"b')
        self.assertEqual(config.f, "a'b")
        config2 = parse_string(config.dump())
        self.assertEqual(config2.a, config.a)
        self.assertEqual(config2.b, config.b)
        self.assertEqual(config2.c, config.c)
        self.assertEqual(config2.d, config.d)
        self.assertEqual(config2.e, config.e)
        self.assertEqual(config2.f, config.f)

    def test_list(self):
        config = parse_string("""
        a = []
        b = [1, 2, 3]
        c = [1, [2, b], [4], 5,]
        d = list((1, a, 3))""")
        self.assertEqual(config.a, [])
        self.assertEqual(config.b, [1, 2, 3])
        self.assertEqual(config.c, [1, [2, [1, 2, 3]], [4], 5,])
        self.assertEqual(config.d, [1, [], 3])
        config2 = parse_string(config.dump())
        self.assertEqual(config2.a, config.a)
        self.assertEqual(config2.b, config.b)
        self.assertEqual(config2.c, config.c)
        self.assertEqual(config2.d, config.d)

    def test_tuple(self):
        config = parse_string("""
        a = ()
        b = (1, 2, 3)
        c = (1, (2, b), [4], 5,)
        d = tuple([1, 2, 3])
        e = ("a",)
        f = 3, 2, 1""")
        self.assertEqual(config.a, ())
        self.assertEqual(config.b, (1, 2, 3))
        self.assertEqual(config.c, (1, (2, (1, 2, 3)), [4], 5,))
        self.assertEqual(config.d, (1, 2, 3))
        self.assertEqual(config.e, ("a",))
        self.assertEqual(config.f, (3, 2, 1))
        config2 = parse_string(config.dump())
        self.assertEqual(config2.a, config.a)
        self.assertEqual(config2.b, config.b)
        self.assertEqual(config2.c, config.c)
        self.assertEqual(config2.d, config.d)
        self.assertEqual(config2.e, config.e)
        self.assertEqual(config2.f, config.f)

    def test_dict(self):
        config = parse_string("""
        a = {}
        b = {1: 2, 3:4, 5:6}
        c = dict(foo=1, bar=2, baz=3)
        d = dict([(1, b), (2,a), (5,6.3)])
        """)
        self.assertEqual(config.a, {})
        self.assertEqual(config.b, {1: 2, 3: 4, 5: 6})
        self.assertEqual(config.c, dict(foo=1, bar=2, baz=3))
        self.assertEqual(config.d, dict([(1, config.b), (2, config.a),
                                         (5, 6.3)]))
        config2 = parse_string(config.dump())
        self.assertEqual(config2.a, config.a)
        self.assertEqual(config2.b, config.b)
        self.assertEqual(config2.c, config.c)
        self.assertEqual(config2.d, config.d)

    def test_arithmetic(self):
        config = parse_string(u"""
        a = 3 + 5
        b = ((5 + 3) * 2) / 3.
        c = a-b
        d = 1//2.
        e = (5%2) ** 3
        f = (2 | 4, 3^1, 3 & 2)""")
        self.assertEqual(config.a, 3 + 5)
        self.assertEqual(config.b, ((5 + 3) * 2) / 3.)
        self.assertEqual(config.c, config.a - config.b)
        self.assertEqual(config.d, 1 // 2.)
        self.assertEqual(config.e, (5 % 2) ** 3)
        self.assertEqual(config.f, (2 | 4, 3^1, 3 & 2))
        config2 = parse_string(config.dump())
        self.assertEqual(config2.a, config.a)
        self.assertEqual(config2.b, config.b)
        self.assertEqual(config2.c, config.c)
        self.assertEqual(config2.d, config.d)
        self.assertEqual(config2.e, config.e)
        self.assertEqual(config2.f, config.f)

    def test_empty_line(self):
        config = parse_string("""a = 3

        b = 5
""")
        self.assertEqual(config.dump(), """a = 3

b = 5
""")

    def test_comment(self):
        config = parse_string("""# leading comment
a = 1
# some very important comment!
b = 2
  # indented ending comment; intendation will be removed
""")
        self.assertEqual(config.pretty_print(), """# leading comment
a = 1
# some very important comment!
b = 2
# indented ending comment; intendation will be removed
""")

    def test_section(self):
        config = parse_string("""
        a = 3
        [Foo]
        bar = 5
        baz = a * bar - Foo.bar
        [[Sub_Foo]]
        eggs = "yummy"
        [foo]
        bar = 7
        spam = Foo.bar - 2
        [[sub_foo]]
        x = 1
        [[[sub_sub_foo]]]
        y = 2
        [[sub_foo_2]]
        z = sub_foo.sub_sub_foo.y
        w = foo.sub_foo.x
        """)
        self.assertEqual(config.a, 3)
        self.assertEqual(config.Foo.bar, 5)
        self.assertEqual(config.foo.bar, 7)
        self.assertEqual(config.Foo.baz,
                         config.a * config.Foo.bar - config.Foo.bar)
        self.assertEqual(config.foo.spam, config.Foo.bar - 2)
        self.assertEqual(config.Foo.Sub_Foo.eggs, "yummy")
        self.assertEqual(config.foo.sub_foo.x, 1)
        self.assertEqual(config.foo.sub_foo.sub_sub_foo.y, 2)
        self.assertEqual(config.foo.sub_foo_2.z,
                         config.foo.sub_foo.sub_sub_foo.y)
        self.assertEqual(config.foo.sub_foo_2.w, config.foo.sub_foo.x)
        config2 = parse_string(config.dump())
        self.assertEqual(config2.a, config.a)
        self.assertEqual(config2.Foo.bar, config.Foo.bar)
        self.assertEqual(config2.foo.bar, config.foo.bar)
        self.assertEqual(config2.Foo.baz, config.Foo.baz)
        self.assertEqual(config2.foo.spam, config.foo.spam)
        self.assertEqual(config2.Foo.Sub_Foo.eggs, config.Foo.Sub_Foo.eggs)
        self.assertEqual(config2.foo.sub_foo.x, config.foo.sub_foo.x)
        self.assertEqual(config2.foo.sub_foo.sub_sub_foo.y,
                         config.foo.sub_foo.sub_sub_foo.y)
        self.assertEqual(config2.foo.sub_foo_2.z, config.foo.sub_foo_2.z)
        self.assertEqual(config2.foo.sub_foo_2.w, config.foo.sub_foo_2.w)
#        print config.pretty_print()

    def test_foo(self):
        config = parse_string("""
[Section_1]
pi = 3.141
[[Sub_Section_1]]
tau = 2 * pi
[Section_2]
foo = [Section_1.pi, Section_1.Sub_Section_1.tau]
bar = max(foo)
baz = foo if 2 < Section_1.pi < 2**2 < Section_1.Sub_Section_1.tau/2 or True else bar
snafu = 3.141 not in foo
""")
        self.assertEqual(config.Section_2.foo, [config.Section_1.pi, config.Section_1.Sub_Section_1.tau])
        self.assertEqual(config.Section_2.bar, max(config.Section_2.foo))
        self.assertEqual(config.Section_2.baz, (config.Section_2.foo if (2 < config.Section_1.pi < 4 < config.Section_1.Sub_Section_1.tau/2 or True)
                                                else config.Section_2.bar))
        self.assertEqual(config.Section_2.snafu, 3.141 not in config.Section_2.foo)
        config2 = parse_string(config.dump())
        self.assertEqual(config.Section_2.foo, config2.Section_2.foo)
        self.assertEqual(config.Section_2.bar, config2.Section_2.bar)
        self.assertEqual(config.Section_2.baz, config2.Section_2.baz)
        self.assertEqual(config.Section_2.snafu, config2.Section_2.snafu)

if __name__ == '__main__':
    unittest.main()
