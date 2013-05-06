# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Match', fields ['fragment_density']
        db.create_index('apiproxy_match', ['fragment_density'])

        # Adding index on 'Match', fields ['percent_churned']
        db.create_index('apiproxy_match', ['percent_churned'])

        # Adding index on 'Match', fields ['overlapping_characters']
        db.create_index('apiproxy_match', ['overlapping_characters'])


    def backwards(self, orm):
        # Removing index on 'Match', fields ['overlapping_characters']
        db.delete_index('apiproxy_match', ['overlapping_characters'])

        # Removing index on 'Match', fields ['percent_churned']
        db.delete_index('apiproxy_match', ['percent_churned'])

        # Removing index on 'Match', fields ['fragment_density']
        db.delete_index('apiproxy_match', ['fragment_density'])


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
            'fragment_density': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'matched_document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['apiproxy.MatchedDocument']"}),
            'number_matches': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'overlapping_characters': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'percent_churned': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'db_index': 'True'}),
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