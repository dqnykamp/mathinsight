# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(null=True, max_length=30, blank=True)),
                ('description', models.CharField(null=True, max_length=400, blank=True)),
                ('detailed_description', models.TextField(null=True, blank=True)),
                ('instructions', models.TextField(null=True, blank=True)),
                ('instructions2', models.TextField(null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('allow_solution_buttons', models.BooleanField(default=True)),
                ('fixed_order', models.BooleanField(default=False)),
                ('single_version', models.BooleanField(default=False)),
                ('resample_question_sets', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='AssessmentBackgroundPage',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('sort_order', models.FloatField(blank=True)),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='AssessmentType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('assessment_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('solution_privacy', models.SmallIntegerField(choices=[(0, 'Public'), (1, 'Logged in users'), (2, 'Instructors only')], default=2)),
                ('template_base_name', models.CharField(null=True, max_length=50, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='AttendanceDate',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('date', models.DateField()),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='ChangeLog',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('action', models.CharField(choices=[('change score', 'change score'), ('change date', 'change date'), ('change', 'change'), ('delete', 'delete'), ('create', 'create')], max_length=20)),
                ('old_value', models.TextField(null=True, blank=True)),
                ('new_value', models.TextField(null=True, blank=True)),
                ('datetime', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ContentAttempt',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('attempt_began', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('score_override', models.FloatField(null=True, blank=True)),
                ('score', models.FloatField(null=True, blank=True)),
                ('seed', models.CharField(null=True, max_length=150, blank=True)),
                ('valid', models.BooleanField(db_index=True, default=True)),
                ('version', models.CharField(default='', max_length=100)),
            ],
            options={
                'ordering': ['attempt_began'],
                'get_latest_by': 'attempt_began',
            },
        ),
        migrations.CreateModel(
            name='ContentAttemptQuestionSet',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('question_number', models.SmallIntegerField()),
                ('question_set', models.SmallIntegerField()),
                ('credit_override', models.FloatField(null=True, blank=True)),
            ],
            options={
                'ordering': ['question_number'],
            },
        ),
        migrations.CreateModel(
            name='ContentRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('complete', models.BooleanField(default=False)),
                ('skip', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('last_modified', models.DateTimeField(blank=True)),
                ('score', models.FloatField(null=True, blank=True)),
                ('score_override', models.FloatField(null=True, blank=True)),
                ('assigned_adjustment', models.DateTimeField(null=True, blank=True)),
                ('initial_due_adjustment', models.DateTimeField(null=True, blank=True)),
                ('final_due_adjustment', models.DateTimeField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('code', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=100)),
                ('short_name', models.CharField(null=True, max_length=50, blank=True)),
                ('description', models.CharField(null=True, max_length=400, blank=True)),
                ('semester', models.CharField(null=True, max_length=50, blank=True)),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('days_of_week', models.CharField(null=True, max_length=50, blank=True)),
                ('track_attendance', models.BooleanField(default=False)),
                ('adjust_due_attendance', models.BooleanField(default=False)),
                ('last_attendance_date', models.DateField(null=True, blank=True)),
                ('attendance_end_of_week', models.CharField(default='F', max_length=2)),
                ('attendance_time_zone', models.CharField(choices=[('Africa/Abidjan', 'Africa/Abidjan'), ('Africa/Accra', 'Africa/Accra'), ('Africa/Addis_Ababa', 'Africa/Addis_Ababa'), ('Africa/Algiers', 'Africa/Algiers'), ('Africa/Asmara', 'Africa/Asmara'), ('Africa/Bamako', 'Africa/Bamako'), ('Africa/Bangui', 'Africa/Bangui'), ('Africa/Banjul', 'Africa/Banjul'), ('Africa/Bissau', 'Africa/Bissau'), ('Africa/Blantyre', 'Africa/Blantyre'), ('Africa/Brazzaville', 'Africa/Brazzaville'), ('Africa/Bujumbura', 'Africa/Bujumbura'), ('Africa/Cairo', 'Africa/Cairo'), ('Africa/Casablanca', 'Africa/Casablanca'), ('Africa/Ceuta', 'Africa/Ceuta'), ('Africa/Conakry', 'Africa/Conakry'), ('Africa/Dakar', 'Africa/Dakar'), ('Africa/Dar_es_Salaam', 'Africa/Dar_es_Salaam'), ('Africa/Djibouti', 'Africa/Djibouti'), ('Africa/Douala', 'Africa/Douala'), ('Africa/El_Aaiun', 'Africa/El_Aaiun'), ('Africa/Freetown', 'Africa/Freetown'), ('Africa/Gaborone', 'Africa/Gaborone'), ('Africa/Harare', 'Africa/Harare'), ('Africa/Johannesburg', 'Africa/Johannesburg'), ('Africa/Juba', 'Africa/Juba'), ('Africa/Kampala', 'Africa/Kampala'), ('Africa/Khartoum', 'Africa/Khartoum'), ('Africa/Kigali', 'Africa/Kigali'), ('Africa/Kinshasa', 'Africa/Kinshasa'), ('Africa/Lagos', 'Africa/Lagos'), ('Africa/Libreville', 'Africa/Libreville'), ('Africa/Lome', 'Africa/Lome'), ('Africa/Luanda', 'Africa/Luanda'), ('Africa/Lubumbashi', 'Africa/Lubumbashi'), ('Africa/Lusaka', 'Africa/Lusaka'), ('Africa/Malabo', 'Africa/Malabo'), ('Africa/Maputo', 'Africa/Maputo'), ('Africa/Maseru', 'Africa/Maseru'), ('Africa/Mbabane', 'Africa/Mbabane'), ('Africa/Mogadishu', 'Africa/Mogadishu'), ('Africa/Monrovia', 'Africa/Monrovia'), ('Africa/Nairobi', 'Africa/Nairobi'), ('Africa/Ndjamena', 'Africa/Ndjamena'), ('Africa/Niamey', 'Africa/Niamey'), ('Africa/Nouakchott', 'Africa/Nouakchott'), ('Africa/Ouagadougou', 'Africa/Ouagadougou'), ('Africa/Porto-Novo', 'Africa/Porto-Novo'), ('Africa/Sao_Tome', 'Africa/Sao_Tome'), ('Africa/Tripoli', 'Africa/Tripoli'), ('Africa/Tunis', 'Africa/Tunis'), ('Africa/Windhoek', 'Africa/Windhoek'), ('America/Adak', 'America/Adak'), ('America/Anchorage', 'America/Anchorage'), ('America/Anguilla', 'America/Anguilla'), ('America/Antigua', 'America/Antigua'), ('America/Araguaina', 'America/Araguaina'), ('America/Argentina/Buenos_Aires', 'America/Argentina/Buenos_Aires'), ('America/Argentina/Catamarca', 'America/Argentina/Catamarca'), ('America/Argentina/Cordoba', 'America/Argentina/Cordoba'), ('America/Argentina/Jujuy', 'America/Argentina/Jujuy'), ('America/Argentina/La_Rioja', 'America/Argentina/La_Rioja'), ('America/Argentina/Mendoza', 'America/Argentina/Mendoza'), ('America/Argentina/Rio_Gallegos', 'America/Argentina/Rio_Gallegos'), ('America/Argentina/Salta', 'America/Argentina/Salta'), ('America/Argentina/San_Juan', 'America/Argentina/San_Juan'), ('America/Argentina/San_Luis', 'America/Argentina/San_Luis'), ('America/Argentina/Tucuman', 'America/Argentina/Tucuman'), ('America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), ('America/Aruba', 'America/Aruba'), ('America/Asuncion', 'America/Asuncion'), ('America/Atikokan', 'America/Atikokan'), ('America/Bahia', 'America/Bahia'), ('America/Bahia_Banderas', 'America/Bahia_Banderas'), ('America/Barbados', 'America/Barbados'), ('America/Belem', 'America/Belem'), ('America/Belize', 'America/Belize'), ('America/Blanc-Sablon', 'America/Blanc-Sablon'), ('America/Boa_Vista', 'America/Boa_Vista'), ('America/Bogota', 'America/Bogota'), ('America/Boise', 'America/Boise'), ('America/Cambridge_Bay', 'America/Cambridge_Bay'), ('America/Campo_Grande', 'America/Campo_Grande'), ('America/Cancun', 'America/Cancun'), ('America/Caracas', 'America/Caracas'), ('America/Cayenne', 'America/Cayenne'), ('America/Cayman', 'America/Cayman'), ('America/Chicago', 'America/Chicago'), ('America/Chihuahua', 'America/Chihuahua'), ('America/Costa_Rica', 'America/Costa_Rica'), ('America/Creston', 'America/Creston'), ('America/Cuiaba', 'America/Cuiaba'), ('America/Curacao', 'America/Curacao'), ('America/Danmarkshavn', 'America/Danmarkshavn'), ('America/Dawson', 'America/Dawson'), ('America/Dawson_Creek', 'America/Dawson_Creek'), ('America/Denver', 'America/Denver'), ('America/Detroit', 'America/Detroit'), ('America/Dominica', 'America/Dominica'), ('America/Edmonton', 'America/Edmonton'), ('America/Eirunepe', 'America/Eirunepe'), ('America/El_Salvador', 'America/El_Salvador'), ('America/Fortaleza', 'America/Fortaleza'), ('America/Glace_Bay', 'America/Glace_Bay'), ('America/Godthab', 'America/Godthab'), ('America/Goose_Bay', 'America/Goose_Bay'), ('America/Grand_Turk', 'America/Grand_Turk'), ('America/Grenada', 'America/Grenada'), ('America/Guadeloupe', 'America/Guadeloupe'), ('America/Guatemala', 'America/Guatemala'), ('America/Guayaquil', 'America/Guayaquil'), ('America/Guyana', 'America/Guyana'), ('America/Halifax', 'America/Halifax'), ('America/Havana', 'America/Havana'), ('America/Hermosillo', 'America/Hermosillo'), ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), ('America/Indiana/Knox', 'America/Indiana/Knox'), ('America/Indiana/Marengo', 'America/Indiana/Marengo'), ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), ('America/Indiana/Vevay', 'America/Indiana/Vevay'), ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), ('America/Indiana/Winamac', 'America/Indiana/Winamac'), ('America/Inuvik', 'America/Inuvik'), ('America/Iqaluit', 'America/Iqaluit'), ('America/Jamaica', 'America/Jamaica'), ('America/Juneau', 'America/Juneau'), ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), ('America/Kralendijk', 'America/Kralendijk'), ('America/La_Paz', 'America/La_Paz'), ('America/Lima', 'America/Lima'), ('America/Los_Angeles', 'America/Los_Angeles'), ('America/Lower_Princes', 'America/Lower_Princes'), ('America/Maceio', 'America/Maceio'), ('America/Managua', 'America/Managua'), ('America/Manaus', 'America/Manaus'), ('America/Marigot', 'America/Marigot'), ('America/Martinique', 'America/Martinique'), ('America/Matamoros', 'America/Matamoros'), ('America/Mazatlan', 'America/Mazatlan'), ('America/Menominee', 'America/Menominee'), ('America/Merida', 'America/Merida'), ('America/Metlakatla', 'America/Metlakatla'), ('America/Mexico_City', 'America/Mexico_City'), ('America/Miquelon', 'America/Miquelon'), ('America/Moncton', 'America/Moncton'), ('America/Monterrey', 'America/Monterrey'), ('America/Montevideo', 'America/Montevideo'), ('America/Montserrat', 'America/Montserrat'), ('America/Nassau', 'America/Nassau'), ('America/New_York', 'America/New_York'), ('America/Nipigon', 'America/Nipigon'), ('America/Nome', 'America/Nome'), ('America/Noronha', 'America/Noronha'), ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), ('America/North_Dakota/Center', 'America/North_Dakota/Center'), ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), ('America/Ojinaga', 'America/Ojinaga'), ('America/Panama', 'America/Panama'), ('America/Pangnirtung', 'America/Pangnirtung'), ('America/Paramaribo', 'America/Paramaribo'), ('America/Phoenix', 'America/Phoenix'), ('America/Port-au-Prince', 'America/Port-au-Prince'), ('America/Port_of_Spain', 'America/Port_of_Spain'), ('America/Porto_Velho', 'America/Porto_Velho'), ('America/Puerto_Rico', 'America/Puerto_Rico'), ('America/Rainy_River', 'America/Rainy_River'), ('America/Rankin_Inlet', 'America/Rankin_Inlet'), ('America/Recife', 'America/Recife'), ('America/Regina', 'America/Regina'), ('America/Resolute', 'America/Resolute'), ('America/Rio_Branco', 'America/Rio_Branco'), ('America/Santa_Isabel', 'America/Santa_Isabel'), ('America/Santarem', 'America/Santarem'), ('America/Santiago', 'America/Santiago'), ('America/Santo_Domingo', 'America/Santo_Domingo'), ('America/Sao_Paulo', 'America/Sao_Paulo'), ('America/Scoresbysund', 'America/Scoresbysund'), ('America/Sitka', 'America/Sitka'), ('America/St_Barthelemy', 'America/St_Barthelemy'), ('America/St_Johns', 'America/St_Johns'), ('America/St_Kitts', 'America/St_Kitts'), ('America/St_Lucia', 'America/St_Lucia'), ('America/St_Thomas', 'America/St_Thomas'), ('America/St_Vincent', 'America/St_Vincent'), ('America/Swift_Current', 'America/Swift_Current'), ('America/Tegucigalpa', 'America/Tegucigalpa'), ('America/Thule', 'America/Thule'), ('America/Thunder_Bay', 'America/Thunder_Bay'), ('America/Tijuana', 'America/Tijuana'), ('America/Toronto', 'America/Toronto'), ('America/Tortola', 'America/Tortola'), ('America/Vancouver', 'America/Vancouver'), ('America/Whitehorse', 'America/Whitehorse'), ('America/Winnipeg', 'America/Winnipeg'), ('America/Yakutat', 'America/Yakutat'), ('America/Yellowknife', 'America/Yellowknife'), ('Antarctica/Casey', 'Antarctica/Casey'), ('Antarctica/Davis', 'Antarctica/Davis'), ('Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), ('Antarctica/Macquarie', 'Antarctica/Macquarie'), ('Antarctica/Mawson', 'Antarctica/Mawson'), ('Antarctica/McMurdo', 'Antarctica/McMurdo'), ('Antarctica/Palmer', 'Antarctica/Palmer'), ('Antarctica/Rothera', 'Antarctica/Rothera'), ('Antarctica/Syowa', 'Antarctica/Syowa'), ('Antarctica/Troll', 'Antarctica/Troll'), ('Antarctica/Vostok', 'Antarctica/Vostok'), ('Arctic/Longyearbyen', 'Arctic/Longyearbyen'), ('Asia/Aden', 'Asia/Aden'), ('Asia/Almaty', 'Asia/Almaty'), ('Asia/Amman', 'Asia/Amman'), ('Asia/Anadyr', 'Asia/Anadyr'), ('Asia/Aqtau', 'Asia/Aqtau'), ('Asia/Aqtobe', 'Asia/Aqtobe'), ('Asia/Ashgabat', 'Asia/Ashgabat'), ('Asia/Baghdad', 'Asia/Baghdad'), ('Asia/Bahrain', 'Asia/Bahrain'), ('Asia/Baku', 'Asia/Baku'), ('Asia/Bangkok', 'Asia/Bangkok'), ('Asia/Beirut', 'Asia/Beirut'), ('Asia/Bishkek', 'Asia/Bishkek'), ('Asia/Brunei', 'Asia/Brunei'), ('Asia/Chita', 'Asia/Chita'), ('Asia/Choibalsan', 'Asia/Choibalsan'), ('Asia/Colombo', 'Asia/Colombo'), ('Asia/Damascus', 'Asia/Damascus'), ('Asia/Dhaka', 'Asia/Dhaka'), ('Asia/Dili', 'Asia/Dili'), ('Asia/Dubai', 'Asia/Dubai'), ('Asia/Dushanbe', 'Asia/Dushanbe'), ('Asia/Gaza', 'Asia/Gaza'), ('Asia/Hebron', 'Asia/Hebron'), ('Asia/Ho_Chi_Minh', 'Asia/Ho_Chi_Minh'), ('Asia/Hong_Kong', 'Asia/Hong_Kong'), ('Asia/Hovd', 'Asia/Hovd'), ('Asia/Irkutsk', 'Asia/Irkutsk'), ('Asia/Jakarta', 'Asia/Jakarta'), ('Asia/Jayapura', 'Asia/Jayapura'), ('Asia/Jerusalem', 'Asia/Jerusalem'), ('Asia/Kabul', 'Asia/Kabul'), ('Asia/Kamchatka', 'Asia/Kamchatka'), ('Asia/Karachi', 'Asia/Karachi'), ('Asia/Kathmandu', 'Asia/Kathmandu'), ('Asia/Khandyga', 'Asia/Khandyga'), ('Asia/Kolkata', 'Asia/Kolkata'), ('Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), ('Asia/Kuala_Lumpur', 'Asia/Kuala_Lumpur'), ('Asia/Kuching', 'Asia/Kuching'), ('Asia/Kuwait', 'Asia/Kuwait'), ('Asia/Macau', 'Asia/Macau'), ('Asia/Magadan', 'Asia/Magadan'), ('Asia/Makassar', 'Asia/Makassar'), ('Asia/Manila', 'Asia/Manila'), ('Asia/Muscat', 'Asia/Muscat'), ('Asia/Nicosia', 'Asia/Nicosia'), ('Asia/Novokuznetsk', 'Asia/Novokuznetsk'), ('Asia/Novosibirsk', 'Asia/Novosibirsk'), ('Asia/Omsk', 'Asia/Omsk'), ('Asia/Oral', 'Asia/Oral'), ('Asia/Phnom_Penh', 'Asia/Phnom_Penh'), ('Asia/Pontianak', 'Asia/Pontianak'), ('Asia/Pyongyang', 'Asia/Pyongyang'), ('Asia/Qatar', 'Asia/Qatar'), ('Asia/Qyzylorda', 'Asia/Qyzylorda'), ('Asia/Rangoon', 'Asia/Rangoon'), ('Asia/Riyadh', 'Asia/Riyadh'), ('Asia/Sakhalin', 'Asia/Sakhalin'), ('Asia/Samarkand', 'Asia/Samarkand'), ('Asia/Seoul', 'Asia/Seoul'), ('Asia/Shanghai', 'Asia/Shanghai'), ('Asia/Singapore', 'Asia/Singapore'), ('Asia/Srednekolymsk', 'Asia/Srednekolymsk'), ('Asia/Taipei', 'Asia/Taipei'), ('Asia/Tashkent', 'Asia/Tashkent'), ('Asia/Tbilisi', 'Asia/Tbilisi'), ('Asia/Tehran', 'Asia/Tehran'), ('Asia/Thimphu', 'Asia/Thimphu'), ('Asia/Tokyo', 'Asia/Tokyo'), ('Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), ('Asia/Urumqi', 'Asia/Urumqi'), ('Asia/Ust-Nera', 'Asia/Ust-Nera'), ('Asia/Vientiane', 'Asia/Vientiane'), ('Asia/Vladivostok', 'Asia/Vladivostok'), ('Asia/Yakutsk', 'Asia/Yakutsk'), ('Asia/Yekaterinburg', 'Asia/Yekaterinburg'), ('Asia/Yerevan', 'Asia/Yerevan'), ('Atlantic/Azores', 'Atlantic/Azores'), ('Atlantic/Bermuda', 'Atlantic/Bermuda'), ('Atlantic/Canary', 'Atlantic/Canary'), ('Atlantic/Cape_Verde', 'Atlantic/Cape_Verde'), ('Atlantic/Faroe', 'Atlantic/Faroe'), ('Atlantic/Madeira', 'Atlantic/Madeira'), ('Atlantic/Reykjavik', 'Atlantic/Reykjavik'), ('Atlantic/South_Georgia', 'Atlantic/South_Georgia'), ('Atlantic/St_Helena', 'Atlantic/St_Helena'), ('Atlantic/Stanley', 'Atlantic/Stanley'), ('Australia/Adelaide', 'Australia/Adelaide'), ('Australia/Brisbane', 'Australia/Brisbane'), ('Australia/Broken_Hill', 'Australia/Broken_Hill'), ('Australia/Currie', 'Australia/Currie'), ('Australia/Darwin', 'Australia/Darwin'), ('Australia/Eucla', 'Australia/Eucla'), ('Australia/Hobart', 'Australia/Hobart'), ('Australia/Lindeman', 'Australia/Lindeman'), ('Australia/Lord_Howe', 'Australia/Lord_Howe'), ('Australia/Melbourne', 'Australia/Melbourne'), ('Australia/Perth', 'Australia/Perth'), ('Australia/Sydney', 'Australia/Sydney'), ('Canada/Atlantic', 'Canada/Atlantic'), ('Canada/Central', 'Canada/Central'), ('Canada/Eastern', 'Canada/Eastern'), ('Canada/Mountain', 'Canada/Mountain'), ('Canada/Newfoundland', 'Canada/Newfoundland'), ('Canada/Pacific', 'Canada/Pacific'), ('Europe/Amsterdam', 'Europe/Amsterdam'), ('Europe/Andorra', 'Europe/Andorra'), ('Europe/Athens', 'Europe/Athens'), ('Europe/Belgrade', 'Europe/Belgrade'), ('Europe/Berlin', 'Europe/Berlin'), ('Europe/Bratislava', 'Europe/Bratislava'), ('Europe/Brussels', 'Europe/Brussels'), ('Europe/Bucharest', 'Europe/Bucharest'), ('Europe/Budapest', 'Europe/Budapest'), ('Europe/Busingen', 'Europe/Busingen'), ('Europe/Chisinau', 'Europe/Chisinau'), ('Europe/Copenhagen', 'Europe/Copenhagen'), ('Europe/Dublin', 'Europe/Dublin'), ('Europe/Gibraltar', 'Europe/Gibraltar'), ('Europe/Guernsey', 'Europe/Guernsey'), ('Europe/Helsinki', 'Europe/Helsinki'), ('Europe/Isle_of_Man', 'Europe/Isle_of_Man'), ('Europe/Istanbul', 'Europe/Istanbul'), ('Europe/Jersey', 'Europe/Jersey'), ('Europe/Kaliningrad', 'Europe/Kaliningrad'), ('Europe/Kiev', 'Europe/Kiev'), ('Europe/Lisbon', 'Europe/Lisbon'), ('Europe/Ljubljana', 'Europe/Ljubljana'), ('Europe/London', 'Europe/London'), ('Europe/Luxembourg', 'Europe/Luxembourg'), ('Europe/Madrid', 'Europe/Madrid'), ('Europe/Malta', 'Europe/Malta'), ('Europe/Mariehamn', 'Europe/Mariehamn'), ('Europe/Minsk', 'Europe/Minsk'), ('Europe/Monaco', 'Europe/Monaco'), ('Europe/Moscow', 'Europe/Moscow'), ('Europe/Oslo', 'Europe/Oslo'), ('Europe/Paris', 'Europe/Paris'), ('Europe/Podgorica', 'Europe/Podgorica'), ('Europe/Prague', 'Europe/Prague'), ('Europe/Riga', 'Europe/Riga'), ('Europe/Rome', 'Europe/Rome'), ('Europe/Samara', 'Europe/Samara'), ('Europe/San_Marino', 'Europe/San_Marino'), ('Europe/Sarajevo', 'Europe/Sarajevo'), ('Europe/Simferopol', 'Europe/Simferopol'), ('Europe/Skopje', 'Europe/Skopje'), ('Europe/Sofia', 'Europe/Sofia'), ('Europe/Stockholm', 'Europe/Stockholm'), ('Europe/Tallinn', 'Europe/Tallinn'), ('Europe/Tirane', 'Europe/Tirane'), ('Europe/Uzhgorod', 'Europe/Uzhgorod'), ('Europe/Vaduz', 'Europe/Vaduz'), ('Europe/Vatican', 'Europe/Vatican'), ('Europe/Vienna', 'Europe/Vienna'), ('Europe/Vilnius', 'Europe/Vilnius'), ('Europe/Volgograd', 'Europe/Volgograd'), ('Europe/Warsaw', 'Europe/Warsaw'), ('Europe/Zagreb', 'Europe/Zagreb'), ('Europe/Zaporozhye', 'Europe/Zaporozhye'), ('Europe/Zurich', 'Europe/Zurich'), ('GMT', 'GMT'), ('Indian/Antananarivo', 'Indian/Antananarivo'), ('Indian/Chagos', 'Indian/Chagos'), ('Indian/Christmas', 'Indian/Christmas'), ('Indian/Cocos', 'Indian/Cocos'), ('Indian/Comoro', 'Indian/Comoro'), ('Indian/Kerguelen', 'Indian/Kerguelen'), ('Indian/Mahe', 'Indian/Mahe'), ('Indian/Maldives', 'Indian/Maldives'), ('Indian/Mauritius', 'Indian/Mauritius'), ('Indian/Mayotte', 'Indian/Mayotte'), ('Indian/Reunion', 'Indian/Reunion'), ('Pacific/Apia', 'Pacific/Apia'), ('Pacific/Auckland', 'Pacific/Auckland'), ('Pacific/Bougainville', 'Pacific/Bougainville'), ('Pacific/Chatham', 'Pacific/Chatham'), ('Pacific/Chuuk', 'Pacific/Chuuk'), ('Pacific/Easter', 'Pacific/Easter'), ('Pacific/Efate', 'Pacific/Efate'), ('Pacific/Enderbury', 'Pacific/Enderbury'), ('Pacific/Fakaofo', 'Pacific/Fakaofo'), ('Pacific/Fiji', 'Pacific/Fiji'), ('Pacific/Funafuti', 'Pacific/Funafuti'), ('Pacific/Galapagos', 'Pacific/Galapagos'), ('Pacific/Gambier', 'Pacific/Gambier'), ('Pacific/Guadalcanal', 'Pacific/Guadalcanal'), ('Pacific/Guam', 'Pacific/Guam'), ('Pacific/Honolulu', 'Pacific/Honolulu'), ('Pacific/Johnston', 'Pacific/Johnston'), ('Pacific/Kiritimati', 'Pacific/Kiritimati'), ('Pacific/Kosrae', 'Pacific/Kosrae'), ('Pacific/Kwajalein', 'Pacific/Kwajalein'), ('Pacific/Majuro', 'Pacific/Majuro'), ('Pacific/Marquesas', 'Pacific/Marquesas'), ('Pacific/Midway', 'Pacific/Midway'), ('Pacific/Nauru', 'Pacific/Nauru'), ('Pacific/Niue', 'Pacific/Niue'), ('Pacific/Norfolk', 'Pacific/Norfolk'), ('Pacific/Noumea', 'Pacific/Noumea'), ('Pacific/Pago_Pago', 'Pacific/Pago_Pago'), ('Pacific/Palau', 'Pacific/Palau'), ('Pacific/Pitcairn', 'Pacific/Pitcairn'), ('Pacific/Pohnpei', 'Pacific/Pohnpei'), ('Pacific/Port_Moresby', 'Pacific/Port_Moresby'), ('Pacific/Rarotonga', 'Pacific/Rarotonga'), ('Pacific/Saipan', 'Pacific/Saipan'), ('Pacific/Tahiti', 'Pacific/Tahiti'), ('Pacific/Tarawa', 'Pacific/Tarawa'), ('Pacific/Tongatapu', 'Pacific/Tongatapu'), ('Pacific/Wake', 'Pacific/Wake'), ('Pacific/Wallis', 'Pacific/Wallis'), ('US/Alaska', 'US/Alaska'), ('US/Arizona', 'US/Arizona'), ('US/Central', 'US/Central'), ('US/Eastern', 'US/Eastern'), ('US/Hawaii', 'US/Hawaii'), ('US/Mountain', 'US/Mountain'), ('US/Pacific', 'US/Pacific'), ('UTC', 'UTC')], default='America/Chicago', max_length=50)),
                ('attendance_threshold_percent', models.SmallIntegerField(default=75)),
                ('numbered', models.BooleanField(default=True)),
                ('active', models.BooleanField(db_index=True, default=True)),
                ('sort_order', models.FloatField(blank=True)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='CourseEnrollment',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('section', models.CharField(null=True, max_length=20, blank=True)),
                ('group', models.CharField(null=True, max_length=20, blank=True)),
                ('date_enrolled', models.DateTimeField(blank=True)),
                ('withdrew', models.BooleanField(default=False)),
                ('role', models.CharField(choices=[('A', 'Auditor'), ('S', 'Student'), ('I', 'Instructor'), ('D', 'Designer')], default='S', max_length=1)),
            ],
            options={
                'ordering': ['student'],
            },
        ),
        migrations.CreateModel(
            name='CourseGradeCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('number_count_for_grade', models.IntegerField(null=True, blank=True)),
                ('rescale_factor', models.FloatField(default=1.0)),
                ('sort_order', models.FloatField(blank=True)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
                'verbose_name_plural': 'Course grade categories',
            },
        ),
        migrations.CreateModel(
            name='CourseSkipDate',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='CourseURL',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('sort_order', models.FloatField(blank=True)),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='CourseUser',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('userid', models.CharField(null=True, max_length=20, blank=True)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name', 'user__username'],
            },
        ),
        migrations.CreateModel(
            name='GradeCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Grade categories',
            },
        ),
        migrations.CreateModel(
            name='QuestionAssigned',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('question_set', models.SmallIntegerField(blank=True)),
            ],
            options={
                'ordering': ['question_set', 'id'],
                'verbose_name_plural': 'Questions assigned',
            },
        ),
        migrations.CreateModel(
            name='QuestionAttempt',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('seed', models.CharField(max_length=150)),
                ('random_outcomes', models.TextField(null=True)),
                ('attempt_began', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('valid', models.BooleanField(db_index=True, default=True)),
                ('solution_viewed', models.DateTimeField(null=True, blank=True)),
                ('credit', models.FloatField(null=True, blank=True)),
                ('content_attempt_question_set', models.ForeignKey(related_name='question_attempts', to='micourses.ContentAttemptQuestionSet')),
            ],
            options={
                'ordering': ['attempt_began'],
                'get_latest_by': 'attempt_began',
            },
        ),
        migrations.CreateModel(
            name='QuestionResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('response', models.TextField()),
                ('credit', models.FloatField()),
                ('response_submitted', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('valid', models.BooleanField(db_index=True, default=True)),
                ('question_attempt', models.ForeignKey(related_name='responses', to='micourses.QuestionAttempt')),
            ],
            options={
                'ordering': ['question_attempt', 'response_submitted'],
                'get_latest_by': 'response_submitted',
            },
        ),
        migrations.CreateModel(
            name='QuestionSetDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('question_set', models.SmallIntegerField(db_index=True)),
                ('weight', models.FloatField(default=1)),
                ('group', models.CharField(default='', max_length=50, blank=True)),
                ('assessment', models.ForeignKey(to='micourses.Assessment')),
            ],
        ),
        migrations.CreateModel(
            name='StudentAttendance',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('date', models.DateField()),
                ('present', models.SmallIntegerField(default=1)),
                ('enrollment', models.ForeignKey(to='micourses.CourseEnrollment')),
            ],
        ),
        migrations.CreateModel(
            name='ThreadContent',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('substitute_title', models.CharField(null=True, max_length=200, blank=True)),
                ('comment', models.CharField(default='', max_length=200, blank=True)),
                ('instructions', models.TextField(null=True, blank=True)),
                ('assigned', models.DateTimeField(null=True, blank=True)),
                ('initial_due', models.DateTimeField(null=True, blank=True)),
                ('final_due', models.DateTimeField(null=True, blank=True)),
                ('points', models.FloatField(null=True, blank=True)),
                ('attempt_aggregation', models.CharField(choices=[('Max', 'Maximum'), ('Avg', 'Average'), ('Las', 'Last')], default='Max', max_length=3)),
                ('individualize_by_student', models.BooleanField(default=True)),
                ('optional', models.BooleanField(default=False)),
                ('available_before_assigned', models.BooleanField(default=False)),
                ('record_scores', models.BooleanField(default=True)),
                ('n_of_object', models.SmallIntegerField(default=1)),
                ('sort_order', models.FloatField(blank=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('course', models.ForeignKey(related_name='thread_contents', to='micourses.Course')),
                ('grade_category', models.ForeignKey(null=True, blank=True, to='micourses.CourseGradeCategory')),
            ],
            options={
                'ordering': ['section', 'sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ThreadSection',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('sort_order', models.FloatField(blank=True)),
                ('deleted', models.BooleanField(db_index=True, default=False)),
                ('course', models.ForeignKey(null=True, related_name='thread_sections', blank=True, to='micourses.Course')),
                ('parent', models.ForeignKey(null=True, related_name='child_sections', blank=True, to='micourses.ThreadSection')),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='threadcontent',
            name='section',
            field=models.ForeignKey(related_name='thread_contents', to='micourses.ThreadSection'),
        ),
    ]
