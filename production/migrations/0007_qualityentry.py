from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0006_rollinspection'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RollInspection',
        ),
        migrations.CreateModel(
            name='QualityEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_no', models.CharField(max_length=50, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('weight', models.FloatField()),
                ('fault_type', models.CharField(blank=True, choices=[('Press Hole', 'Press Hole'), ('Double Kunda', 'Double Kunda'), ('Needle Break', 'Needle Break')], max_length=50, null=True)),
                ('press_hole', models.IntegerField(default=0)),
                ('double_kunda', models.IntegerField(default=0)),
                ('needle_break', models.IntegerField(default=0)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Pass', 'Pass'), ('Hold', 'Hold'), ('Reject', 'Reject')], default='Pass', max_length=20)),
                ('roll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quality_entries', to='production.productionroll')),
            ],
        ),
    ]
