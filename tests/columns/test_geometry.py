from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import Geometry
from asyncpg.exceptions import InvalidParameterValueError

from ..base import postgres_only


class MyTable(Table):
    point = Geometry('POINT', null=True)
    line = Geometry('LINESTRING', null=True)
    point_srid = Geometry('POINT', srid=4035, null=True)


@postgres_only
class TestGeometry(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_point(self):
        """Test storing a point
        """
        MyTable(point='POINT(1 1)').save().run_sync()
        row = MyTable.select(MyTable.point.ST_AsText().as_alias('point_text')).first().run_sync()
        self.assertEqual(row['point_text'], 'POINT(1 1)')

    def test_line(self):
        """test storing a linestring
        """
        MyTable(line='LINESTRING(1 1,2 2,3 3)').save().run_sync()
        row = MyTable.select(MyTable.line.ST_AsText().as_alias('line_text')).first().run_sync()
        self.assertEqual(row['line_text'], 'LINESTRING(1 1,2 2,3 3)')

    def test_point_with_srid(self):
        """test supplying a SRID to geometry
        """
        MyTable(point_srid='SRID=4035;POINT(1 1)').save().run_sync()
        row = MyTable.select(MyTable.point_srid.ST_AsText().as_alias('point_text')).first().run_sync()
        self.assertEqual(row['point_text'], 'POINT(1 1)')

    def test_wrong_shape(self):
        """test supplying the wrong shape for a column
        """
        with self.assertRaises(InvalidParameterValueError):
            MyTable(line='POINT(1 1)').save().run_sync()

    def test_st_dwithin(self):
        """Test the ST_Dwithin function by searching for rows
        that are within a radius of some other geometry
        """
        inside = MyTable(point='POINT(1 1)').save().run_sync()
        outside = MyTable(point='POINT(5 5)').save().run_sync()
        center = 'POINT(2 2)'
        radius = 2

        # Search for rows within `radius` of `center`
        # outside should be excluded
        results = MyTable.select(MyTable.id).where(MyTable.point.ST_Dwithin(center, radius)==True).run_sync()
        self.assertEqual(len(results), 1)
        self.assertEqual(results, inside)

        # Search for rows not within `radius` of `center`
        # inside should be excluded
        results = MyTable.select(MyTable.id).where(MyTable.point.ST_Dwithin(center, radius)==False).run_sync()
        self.assertEqual(len(results), 1)
        self.assertEqual(results, outside)

    def test_st_intersects(self):
        """Test the ST_Intersects function by searching for rows
        with points that lie on a line.
        """
        intersects = MyTable(point='POINT(2 2)').save().run_sync()
        disjoint = MyTable(point='POINT(1 2)').save().run_sync()
        line = 'LINESTRING(1 1,2 2,3 3)'

        # Search for rows that instersect with `line`
        results = MyTable.select(MyTable.id).where(MyTable.point.ST_Intersects(line)==True).run_sync()
        self.assertEqual(len(results), 1)
        self.assertEqual(results, intersects)

        # Search for rows that do not intersect with `line`
        results = MyTable.select(MyTable.id).where(MyTable.point.ST_Intersects(line)==False).run_sync()
        self.assertEqual(len(results), 1)
        self.assertEqual(results, disjoint)
