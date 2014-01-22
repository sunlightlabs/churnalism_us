# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MatchCharsHistogram'
        db.create_table('sidebyside_matchcharshistogram', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('mass_axis_label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('bin_axis_label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('norm_coeff', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=20, decimal_places=0)),
        ))
        db.send_create_signal('sidebyside', ['MatchCharsHistogram'])

        # Adding model 'MatchCharsHistogramBin'
        db.create_table('sidebyside_matchcharshistogrambin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ordinal_position', self.gf('django.db.models.fields.IntegerField')()),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('mass', self.gf('django.db.models.fields.DecimalField')(max_digits=20, decimal_places=0)),
            ('histogram', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bins', to=orm['sidebyside.MatchCharsHistogram'])),
        ))
        db.send_create_signal('sidebyside', ['MatchCharsHistogramBin'])

        # Adding unique constraint on 'MatchCharsHistogramBin', fields ['histogram', 'label']
        db.create_unique('sidebyside_matchcharshistogrambin', ['histogram_id', 'label'])

        # Adding model 'MatchPercentHistogram'
        db.create_table('sidebyside_matchpercenthistogram', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('mass_axis_label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('bin_axis_label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('norm_coeff', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=20, decimal_places=0)),
        ))
        db.send_create_signal('sidebyside', ['MatchPercentHistogram'])

        # Adding model 'MatchPercentHistogramBin'
        db.create_table('sidebyside_matchpercenthistogrambin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ordinal_position', self.gf('django.db.models.fields.IntegerField')()),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('mass', self.gf('django.db.models.fields.DecimalField')(max_digits=20, decimal_places=0)),
            ('histogram', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bins', to=orm['sidebyside.MatchPercentHistogram'])),
        ))
        db.send_create_signal('sidebyside', ['MatchPercentHistogramBin'])

        # Adding unique constraint on 'MatchPercentHistogramBin', fields ['histogram', 'label']
        db.create_unique('sidebyside_matchpercenthistogrambin', ['histogram_id', 'label'])


    def backwards(self, orm):
        # Removing unique constraint on 'MatchPercentHistogramBin', fields ['histogram', 'label']
        db.delete_unique('sidebyside_matchpercenthistogrambin', ['histogram_id', 'label'])

        # Removing unique constraint on 'MatchCharsHistogramBin', fields ['histogram', 'label']
        db.delete_unique('sidebyside_matchcharshistogrambin', ['histogram_id', 'label'])

        # Deleting model 'MatchCharsHistogram'
        db.delete_table('sidebyside_matchcharshistogram')

        # Deleting model 'MatchCharsHistogramBin'
        db.delete_table('sidebyside_matchcharshistogrambin')

        # Deleting model 'MatchPercentHistogram'
        db.delete_table('sidebyside_matchpercenthistogram')

        # Deleting model 'MatchPercentHistogramBin'
        db.delete_table('sidebyside_matchpercenthistogrambin')


    models = {
        'sidebyside.matchcharshistogram': {
            'Meta': {'object_name': 'MatchCharsHistogram'},
            'bin_axis_label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mass_axis_label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'norm_coeff': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '20', 'decimal_places': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'sidebyside.matchcharshistogrambin': {
            'Meta': {'ordering': "['ordinal_position']", 'unique_together': "(('histogram', 'label'),)", 'object_name': 'MatchCharsHistogramBin'},
            'histogram': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bins'", 'to': "orm['sidebyside.MatchCharsHistogram']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'mass': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '0'}),
            'ordinal_position': ('django.db.models.fields.IntegerField', [], {})
        },
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
        },
        'sidebyside.matchpercenthistogram': {
            'Meta': {'object_name': 'MatchPercentHistogram'},
            'bin_axis_label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mass_axis_label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'norm_coeff': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '20', 'decimal_places': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'sidebyside.matchpercenthistogrambin': {
            'Meta': {'ordering': "['ordinal_position']", 'unique_together': "(('histogram', 'label'),)", 'object_name': 'MatchPercentHistogramBin'},
            'histogram': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bins'", 'to': "orm['sidebyside.MatchPercentHistogram']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'mass': ('django.db.models.fields.DecimalField', [], {'max_digits': '20', 'decimal_places': '0'}),
            'ordinal_position': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['sidebyside']