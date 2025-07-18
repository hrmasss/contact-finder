# Generated by Django 5.2.4 on 2025-07-14 08:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscoveredEmployee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('full_name', models.CharField(help_text='Complete name as found from source', max_length=255)),
                ('name_variations', models.JSONField(default=dict, help_text="Name components and variations for email generation. Structure: {  'first_name': 'Timothy',   'last_name': 'Johnson',   'nickname': 'Tim',   'initials': 'TJ',   'middle_name': 'Robert',   'name_variants': ['T. Johnson', 'Tim J.', 'Timothy R. Johnson'] }")),
                ('email_candidates', models.JSONField(default=list, help_text="All possible emails with confidence scores. Structure: [{  'email': 'tim.johnson@acme.com',   'confidence': 0.92,   'source': 'pattern_generated',  # pattern_generated|scraped|api_lookup|linkedin|manual  'pattern_used': 'first.last',   'domain': 'acme.com',   'verified': false,   'verification_method': 'none'  # none|smtp_check|api_verify|send_test}]")),
                ('additional_info', models.JSONField(default=dict, help_text="Additional employee information from discovery. Structure: {  'title': 'Senior Manager',   'department': 'Engineering',   'linkedin_url': 'https://linkedin.com/in/...',   'phone': '+1-555-...',   'location': 'New York, NY',   'bio': 'Senior software engineer with 10+ years...',   'skills': ['Python', 'Django', 'React'],   'education': 'MIT Computer Science' }")),
                ('search_aliases', models.JSONField(default=list, help_text="Search variations that lead to this employee. Structure: ['Tim Johnson', 'Timothy Johnson', 'T. Johnson', 'TJ'] Used for cache optimization and duplicate prevention.")),
                ('search_level', models.CharField(default='basic', help_text='Level of search that found this employee (basic/advanced)', max_length=20)),
                ('metadata', models.JSONField(default=dict, help_text="Discovery metadata and source information. Structure: {  'search_query': 'John Doe at Acme Corp',   'sources': ['linkedin', 'company_website'] }")),
                ('cache_expires_at', models.DateTimeField(blank=True, help_text='When this employee data becomes stale (default: 30 days)', null=True)),
                ('last_validated_at', models.DateTimeField(blank=True, help_text="When we last validated this employee's information", null=True)),
                ('company', models.ForeignKey(help_text='Company this employee belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='discovered_employees', to='pipeline.discoveredcompany')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['company', 'full_name'], name='pipeline_di_company_a0997a_idx'), models.Index(fields=['full_name'], name='pipeline_di_full_na_4d8088_idx'), models.Index(fields=['cache_expires_at'], name='pipeline_di_cache_e_1ccf8f_idx')],
                'unique_together': {('company', 'full_name')},
            },
        ),
    ]
