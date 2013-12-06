# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MatchCurveHistogram'
        db.create_table('sidebyside_matchcurvehistogram', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('mass_axis_label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('bin_axis_label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('doc_type', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('norm_coeff', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=20, decimal_places=0)),
        ))
        db.send_create_signal('sidebyside', ['MatchCurveHistogram'])

        # Adding model 'MatchCurveHistogramBin'
        db.create_table('sidebyside_matchcurvehistogrambin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ordinal_position', self.gf('django.db.models.fields.IntegerField')()),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('mass', self.gf('django.db.models.fields.DecimalField')(max_digits=20, decimal_places=0)),
            ('histogram', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bins', to=orm['sidebyside.MatchCurveHistogram'])),
        ))
        db.send_create_signal('sidebyside', ['MatchCurveHistogramBin'])

        # Adding unique constraint on 'MatchCurveHistogramBin', fields ['histogram', 'label']
        db.create_unique('sidebyside_matchcurvehistogrambin', ['histogram_id', 'label'])


    def backwards(self, orm):
        # Removing unique constraint on 'MatchCurveHistogramBin', fields ['histogram', 'label']
        db.delete_unique('sidebyside_matchcurvehistogrambin', ['histogram_id', 'label'])

        # Deleting model 'MatchCurveHistogram'
        db.delete_table('sidebyside_matchcurvehistogram')

        # Deleting model 'MatchCurveHistogramBin'
        db.delete_table('sidebyside_matchcurvehistogrambin')


    models = {
        'sidebyside.matchcurvehistogram': {
            'Meta': {'object_name': 'MatchCurveHistogram'},
            'bin_axis_label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'doc_type': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mass_axis_label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'norm_coeff': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '20', 'decimal_places': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'sidebyside.matchcurvehistogrambin': {
            'Meta': {'ordering': "['ordinal_position']", 'unique_together': "(('histogram', 'label'),)", 'object_name': 'MatchCurveHistogramBin'},
            'histogram': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bins'", 'to': "orm['sidebyside.MatchCurveHistogram']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'mass': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '0'}),
            'ordinal_position': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['sidebyside']