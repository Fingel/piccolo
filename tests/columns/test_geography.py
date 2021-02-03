from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import Geography

from ..base import postgres_only


class MyTable(Table):
    location = Geography('POINT')


@postgres_only
class TestGeography(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_point(self):
        """Test storing a geographical point"""
        isla_vista = 'POINT(-119.8892005 34.4117751)'
        MyTable(location=isla_vista).save().run_sync()
        row = MyTable.select(MyTable.location.ST_AsText().as_alias('location_text')).first().run_sync()
        self.assertEqual(row['location_text'], isla_vista)

    def test_st_dwithin(self):
        """Find all cities within a 30 mile radius of Isla Vista
        """
        isla_vista = 'POINT(-119.8892005 34.4117751)'
        santa_barbara = 'POINT(-119.7067965 34.4243348)'
        goleta = 'POINT(-119.811087 34.437549)'
        san_luis_obsipo = 'POINT(-120.668494 35.275636)'

        iv = MyTable(location=isla_vista).save().run_sync()
        sb = MyTable(location=santa_barbara).save().run_sync()
        gl = MyTable(location=goleta).save().run_sync()
        slo = MyTable(location=san_luis_obsipo).save().run_sync()

        radius = 30 * 1609.344  # 30 miles in meters

        results = MyTable.select(MyTable.id).where(MyTable.location.ST_Dwithin(isla_vista, radius)==True).run_sync()

        # Results should include iv, sb, gl, but not slo
        self.assertEqual(len(results), 3)
        self.assertIn(iv[0], results)
        self.assertIn(sb[0], results)
        self.assertIn(gl[0], results)
        self.assertNotIn(slo[0], results)
