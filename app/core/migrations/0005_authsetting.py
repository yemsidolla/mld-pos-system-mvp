# Authz Phase 5: singleton authentication settings.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_storesetting_khr_khqr'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('local_login_enabled', models.BooleanField(default=True)),
                ('session_timeout_minutes', models.PositiveIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Authentication setting',
                'verbose_name_plural': 'Authentication settings',
            },
        ),
    ]
