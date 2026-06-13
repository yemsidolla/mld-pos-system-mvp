# Authz Phase 1: data-driven Role model.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_backfill_staff_profiles'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(max_length=40, unique=True)),
                ('name', models.CharField(max_length=80)),
                ('is_builtin', models.BooleanField(default=False)),
                ('is_owner', models.BooleanField(default=False)),
                ('capabilities', models.JSONField(blank=True, default=list)),
                ('rank', models.PositiveIntegerField(default=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['rank', 'name'],
            },
        ),
    ]
