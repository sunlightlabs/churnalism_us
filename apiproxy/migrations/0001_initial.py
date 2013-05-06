# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SearchDocument'
        db.create_table('apiproxy_searchdocument', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32, db_index=True)),
            ('hashed_url', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('url', self.gf('django.db.models.fields.TextField')(max_length=4000)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, db_index=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('title', self.gf('django.db.models.fields.TextField')(null=True)),
            ('user_agent', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
            ('times_shared', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('apiproxy', ['SearchDocument'])

        # Adding model 'IncorrectTextReport'
        db.create_table('apiproxy_incorrecttextreport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('search_document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='text_problems', to=orm['apiproxy.SearchDocument'])),
            ('problem_description', self.gf('django.db.models.fields.TextField')()),
            ('remote_addr', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('user_agent', self.gf('django.db.models.fields.TextField')()),
            ('languages', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('encodings', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('apiproxy', ['IncorrectTextReport'])

        # Adding unique constraint on 'IncorrectTextReport', fields ['search_document', 'remote_addr']
        db.create_unique('apiproxy_incorrecttextreport', ['search_document_id', 'remote_addr'])

        # Adding model 'MatchedDocument'
        db.create_table('apiproxy_matcheddocument', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('doc_type', self.gf('django.db.models.fields.IntegerField')()),
            ('doc_id', self.gf('django.db.models.fields.IntegerField')()),
            ('source_url', self.gf('django.db.models.fields.TextField')()),
            ('source_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('source_headline', self.gf('django.db.models.fields.TextField')(null=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('apiproxy', ['MatchedDocument'])

        # Adding unique constraint on 'MatchedDocument', fields ['doc_type', 'doc_id']
        db.create_unique('apiproxy_matcheddocument', ['doc_type', 'doc_id'])

        # Adding model 'Match'
        db.create_table('apiproxy_match', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('search_document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['apiproxy.SearchDocument'])),
            ('matched_document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['apiproxy.MatchedDocument'])),
            ('overlapping_characters', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('percent_churned', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2)),
            ('fragment_density', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2)),
            ('number_matches', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
            ('confirmed', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('response', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('apiproxy', ['Match'])

        # Adding unique constraint on 'Match', fields ['search_document', 'matched_document']
        db.create_unique('apiproxy_match', ['search_document_id', 'matched_document_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Match', fields ['search_document', 'matched_document']
        db.delete_unique('apiproxy_match', ['search_document_id', 'matched_document_id'])

        # Removing unique constraint on 'MatchedDocument', fields ['doc_type', 'doc_id']
        db.delete_unique('apiproxy_matcheddocument', ['doc_type', 'doc_id'])

        # Removing unique constraint on 'IncorrectTextReport', fields ['search_document', 'remote_addr']
        db.delete_unique('apiproxy_incorrecttextreport', ['search_document_id', 'remote_addr'])

        # Deleting model 'SearchDocument'
        db.delete_table('apiproxy_searchdocument')

        # Deleting model 'IncorrectTextReport'
        db.delete_table('apiproxy_incorrecttextreport')

        # Deleting model 'MatchedDocument'
        db.delete_table('apiproxy_matcheddocument')

        # Deleting model 'Match'
        db.delete_table('apiproxy_match')


    models = {
        'apiproxy.incorrecttextreport': {
            'Meta': {'unique_together': "(('search_document', 'remote_addr'),)", 'object_name': 'IncorrectTextReport'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'encodings': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'languages': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'problem_description': ('django.db.models.fields.TextField', [], {}),
            'remote_addr': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'search_document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'text_problems'", 'to': "orm['apiproxy.SearchDocument']"}),
            'user_agent': ('django.db.models.fields.TextField', [], {})
        },
        'apiproxy.match': {
            'Meta': {'unique_together': "(('search_document', 'matched_document'),)", 'object_name': 'Match'},
            'confirmed': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'fragment_density': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'matched_document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['apiproxy.MatchedDocument']"}),
            'number_matches': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'overlapping_characters': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'percent_churned': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'response': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'search_document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['apiproxy.SearchDocument']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'apiproxy.matcheddocument': {
            'Meta': {'unique_together': "(('doc_type', 'doc_id'),)", 'object_name': 'MatchedDocument'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'doc_id': ('django.db.models.fields.IntegerField', [], {}),
            'doc_type': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source_headline': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'source_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'source_url': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'apiproxy.searchdocument': {
            'Meta': {'ordering': "['-updated', '-created']", 'object_name': 'SearchDocument'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'}),
            'hashed_url': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'times_shared': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {'max_length': '4000'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'})
        }
    }

    complete_apps = ['apiproxy']