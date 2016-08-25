# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import midocs.models


class Migration(migrations.Migration):

    dependencies = [
        ('midocs', '0001_initial'),
        ('mitesting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoquestion',
            name='question',
            field=models.ForeignKey(to='mitesting.Question'),
        ),
        migrations.AddField(
            model_name='videoquestion',
            name='video',
            field=models.ForeignKey(to='midocs.Video'),
        ),
        migrations.AddField(
            model_name='videoparameter',
            name='parameter',
            field=models.ForeignKey(to='midocs.VideoTypeParameter'),
        ),
        migrations.AddField(
            model_name='videoparameter',
            name='video',
            field=models.ForeignKey(to='midocs.Video'),
        ),
        migrations.AddField(
            model_name='videoauthor',
            name='author',
            field=models.ForeignKey(to='midocs.Author'),
        ),
        migrations.AddField(
            model_name='videoauthor',
            name='video',
            field=models.ForeignKey(to='midocs.Video'),
        ),
        migrations.AddField(
            model_name='video',
            name='associated_applet',
            field=models.ForeignKey(null=True, blank=True, to='midocs.Applet'),
        ),
        migrations.AddField(
            model_name='video',
            name='authors',
            field=models.ManyToManyField(to='midocs.Author', through='midocs.VideoAuthor', blank=True),
        ),
        migrations.AddField(
            model_name='video',
            name='copyright_type',
            field=models.ForeignKey(default=midocs.models.return_default_copyright_type, to='midocs.CopyrightType', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='video',
            name='in_pages',
            field=models.ManyToManyField(to='midocs.Page', related_name='embedded_videos', blank=True),
        ),
        migrations.AddField(
            model_name='video',
            name='keywords',
            field=models.ManyToManyField(to='midocs.Keyword', blank=True),
        ),
        migrations.AddField(
            model_name='video',
            name='parameters',
            field=models.ManyToManyField(to='midocs.VideoTypeParameter', through='midocs.VideoParameter', blank=True),
        ),
        migrations.AddField(
            model_name='video',
            name='questions',
            field=models.ManyToManyField(to='mitesting.Question', through='midocs.VideoQuestion', blank=True),
        ),
        migrations.AddField(
            model_name='video',
            name='slides',
            field=models.ForeignKey(null=True, blank=True, to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='video',
            name='subjects',
            field=models.ManyToManyField(to='midocs.Subject', blank=True),
        ),
        migrations.AddField(
            model_name='video',
            name='video_type',
            field=models.ForeignKey(verbose_name='type', to='midocs.VideoType'),
        ),
        migrations.AddField(
            model_name='referenceeditor',
            name='editor',
            field=models.ForeignKey(to='midocs.Author'),
        ),
        migrations.AddField(
            model_name='referenceeditor',
            name='reference',
            field=models.ForeignKey(to='midocs.Reference'),
        ),
        migrations.AddField(
            model_name='referenceauthor',
            name='author',
            field=models.ForeignKey(to='midocs.Author'),
        ),
        migrations.AddField(
            model_name='referenceauthor',
            name='reference',
            field=models.ForeignKey(to='midocs.Reference'),
        ),
        migrations.AddField(
            model_name='reference',
            name='authors',
            field=models.ManyToManyField(to='midocs.Author', related_name='references_authored', through='midocs.ReferenceAuthor', blank=True),
        ),
        migrations.AddField(
            model_name='reference',
            name='editors',
            field=models.ManyToManyField(to='midocs.Author', related_name='references_edited', through='midocs.ReferenceEditor', blank=True),
        ),
        migrations.AddField(
            model_name='reference',
            name='reference_type',
            field=models.ForeignKey(verbose_name='type', to='midocs.ReferenceType'),
        ),
        migrations.AddField(
            model_name='pagesimilar',
            name='origin',
            field=models.ForeignKey(related_name='similar', to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='pagesimilar',
            name='similar',
            field=models.ForeignKey(related_name='reverse_similar', to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='pagerelationship',
            name='origin',
            field=models.ForeignKey(related_name='relationships', to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='pagerelationship',
            name='related',
            field=models.ForeignKey(related_name='reverse_relationships', to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='pagerelationship',
            name='relationship_type',
            field=models.ForeignKey(to='midocs.RelationshipType'),
        ),
        migrations.AddField(
            model_name='pagenavigationsub',
            name='navigation',
            field=models.ForeignKey(to='midocs.PageNavigation'),
        ),
        migrations.AddField(
            model_name='pagenavigation',
            name='page',
            field=models.ForeignKey(to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='pagecitation',
            name='page',
            field=models.ForeignKey(to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='pagecitation',
            name='reference',
            field=models.ForeignKey(null=True, blank=True, to='midocs.Reference'),
        ),
        migrations.AddField(
            model_name='pageauthor',
            name='author',
            field=models.ForeignKey(to='midocs.Author'),
        ),
        migrations.AddField(
            model_name='pageauthor',
            name='page',
            field=models.ForeignKey(to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='page',
            name='authors',
            field=models.ManyToManyField(to='midocs.Author', through='midocs.PageAuthor', blank=True),
        ),
        migrations.AddField(
            model_name='page',
            name='copyright_type',
            field=models.ForeignKey(default=midocs.models.return_default_copyright_type, to='midocs.CopyrightType', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='page',
            name='keywords',
            field=models.ManyToManyField(to='midocs.Keyword', blank=True),
        ),
        migrations.AddField(
            model_name='page',
            name='notation_systems',
            field=models.ManyToManyField(to='midocs.NotationSystem', blank=True),
        ),
        migrations.AddField(
            model_name='page',
            name='objectives',
            field=models.ManyToManyField(to='midocs.Objective', blank=True),
        ),
        migrations.AddField(
            model_name='page',
            name='page_type',
            field=models.ForeignKey(to='midocs.PageType', default=midocs.models.return_default_page_type),
        ),
        migrations.AddField(
            model_name='page',
            name='related_pages',
            field=models.ManyToManyField(to='midocs.Page', related_name='pages_related_from', through='midocs.PageRelationship', blank=True),
        ),
        migrations.AddField(
            model_name='page',
            name='related_videos',
            field=models.ManyToManyField(to='midocs.Video', related_name='related_pages', blank=True),
        ),
        migrations.AddField(
            model_name='page',
            name='similar_pages',
            field=models.ManyToManyField(to='midocs.Page', related_name='pages_similar_from', through='midocs.PageSimilar', blank=True),
        ),
        migrations.AddField(
            model_name='page',
            name='subjects',
            field=models.ManyToManyField(to='midocs.Subject', blank=True),
        ),
        migrations.AddField(
            model_name='newsitem',
            name='authors',
            field=models.ManyToManyField(to='midocs.Author', through='midocs.NewsAuthor', blank=True),
        ),
        migrations.AddField(
            model_name='newsauthor',
            name='author',
            field=models.ForeignKey(to='midocs.Author'),
        ),
        migrations.AddField(
            model_name='newsauthor',
            name='newsitem',
            field=models.ForeignKey(to='midocs.NewsItem'),
        ),
        migrations.AddField(
            model_name='indexentry',
            name='index_type',
            field=models.ForeignKey(related_name='entries', default=1, to='midocs.IndexType'),
        ),
        migrations.AddField(
            model_name='indexentry',
            name='page',
            field=models.ForeignKey(to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='imagenotationsystem',
            name='image',
            field=models.ForeignKey(to='midocs.Image'),
        ),
        migrations.AddField(
            model_name='imagenotationsystem',
            name='notation_system',
            field=models.ForeignKey(to='midocs.NotationSystem'),
        ),
        migrations.AddField(
            model_name='imageauthor',
            name='author',
            field=models.ForeignKey(to='midocs.Author'),
        ),
        migrations.AddField(
            model_name='imageauthor',
            name='image',
            field=models.ForeignKey(to='midocs.Image'),
        ),
        migrations.AddField(
            model_name='image',
            name='authors',
            field=models.ManyToManyField(to='midocs.Author', through='midocs.ImageAuthor', blank=True),
        ),
        migrations.AddField(
            model_name='image',
            name='auxiliary_files',
            field=models.ManyToManyField(to='midocs.AuxiliaryFile', blank=True),
        ),
        migrations.AddField(
            model_name='image',
            name='copyright_type',
            field=models.ForeignKey(default=midocs.models.return_default_copyright_type, to='midocs.CopyrightType', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='image',
            name='in_pages',
            field=models.ManyToManyField(to='midocs.Page', related_name='embedded_images', blank=True),
        ),
        migrations.AddField(
            model_name='image',
            name='keywords',
            field=models.ManyToManyField(to='midocs.Keyword', blank=True),
        ),
        migrations.AddField(
            model_name='image',
            name='notation_systems',
            field=models.ManyToManyField(to='midocs.NotationSystem', through='midocs.ImageNotationSystem', blank=True),
        ),
        migrations.AddField(
            model_name='image',
            name='original_file_type',
            field=models.ForeignKey(null=True, blank=True, to='midocs.ImageType'),
        ),
        migrations.AddField(
            model_name='image',
            name='subjects',
            field=models.ManyToManyField(to='midocs.Subject', blank=True),
        ),
        migrations.AddField(
            model_name='externallink',
            name='in_page',
            field=models.ForeignKey(null=True, blank=True, to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='equationtag',
            name='page',
            field=models.ForeignKey(to='midocs.Page'),
        ),
        migrations.AddField(
            model_name='auxiliaryfile',
            name='file_type',
            field=models.ForeignKey(to='midocs.AuxiliaryFileType'),
        ),
        migrations.AddField(
            model_name='applettypeparameter',
            name='applet_type',
            field=models.ForeignKey(related_name='valid_parameters', to='midocs.AppletType'),
        ),
        migrations.AddField(
            model_name='applettext',
            name='applet',
            field=models.ForeignKey(to='midocs.Applet'),
        ),
        migrations.AddField(
            model_name='appletparameter',
            name='applet',
            field=models.ForeignKey(to='midocs.Applet'),
        ),
        migrations.AddField(
            model_name='appletparameter',
            name='parameter',
            field=models.ForeignKey(to='midocs.AppletTypeParameter'),
        ),
        migrations.AddField(
            model_name='appletobject',
            name='applet',
            field=models.ForeignKey(to='midocs.Applet'),
        ),
        migrations.AddField(
            model_name='appletobject',
            name='object_type',
            field=models.ForeignKey(to='midocs.AppletObjectType'),
        ),
        migrations.AddField(
            model_name='appletnotationsystem',
            name='applet',
            field=models.ForeignKey(to='midocs.Applet'),
        ),
        migrations.AddField(
            model_name='appletnotationsystem',
            name='notation_system',
            field=models.ForeignKey(to='midocs.NotationSystem'),
        ),
        migrations.AddField(
            model_name='appletchildobjectlink',
            name='applet',
            field=models.ForeignKey(to='midocs.Applet'),
        ),
        migrations.AddField(
            model_name='appletauthor',
            name='applet',
            field=models.ForeignKey(to='midocs.Applet'),
        ),
        migrations.AddField(
            model_name='appletauthor',
            name='author',
            field=models.ForeignKey(to='midocs.Author'),
        ),
        migrations.AddField(
            model_name='applet',
            name='applet_objects',
            field=models.ManyToManyField(to='midocs.AppletObjectType', through='midocs.AppletObject', blank=True),
        ),
        migrations.AddField(
            model_name='applet',
            name='applet_type',
            field=models.ForeignKey(verbose_name='type', to='midocs.AppletType'),
        ),
        migrations.AddField(
            model_name='applet',
            name='authors',
            field=models.ManyToManyField(to='midocs.Author', through='midocs.AppletAuthor', blank=True),
        ),
        migrations.AddField(
            model_name='applet',
            name='child_applet',
            field=models.ForeignKey(null=True, blank=True, to='midocs.Applet'),
        ),
        migrations.AddField(
            model_name='applet',
            name='copyright_type',
            field=models.ForeignKey(default=midocs.models.return_default_copyright_type, to='midocs.CopyrightType', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='applet',
            name='features',
            field=models.ManyToManyField(to='midocs.AppletFeature', blank=True),
        ),
        migrations.AddField(
            model_name='applet',
            name='in_pages',
            field=models.ManyToManyField(to='midocs.Page', related_name='embedded_applets', blank=True),
        ),
        migrations.AddField(
            model_name='applet',
            name='keywords',
            field=models.ManyToManyField(to='midocs.Keyword', blank=True),
        ),
        migrations.AddField(
            model_name='applet',
            name='notation_systems',
            field=models.ManyToManyField(to='midocs.NotationSystem', through='midocs.AppletNotationSystem', blank=True),
        ),
        migrations.AddField(
            model_name='applet',
            name='parameters',
            field=models.ManyToManyField(to='midocs.AppletTypeParameter', through='midocs.AppletParameter', blank=True),
        ),
        migrations.AddField(
            model_name='applet',
            name='subjects',
            field=models.ManyToManyField(to='midocs.Subject', blank=True),
        ),
        migrations.CreateModel(
            name='AppletHighlight',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('midocs.applet',),
        ),
        migrations.CreateModel(
            name='PageHighlight',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('midocs.page',),
        ),
        migrations.CreateModel(
            name='PageWithNotes',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Pages with notes',
            },
            bases=('midocs.page',),
        ),
        migrations.CreateModel(
            name='VideoHighlight',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('midocs.video',),
        ),
        migrations.AlterUniqueTogether(
            name='videotypeparameter',
            unique_together=set([('video_type', 'parameter_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='videoquestion',
            unique_together=set([('video', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='videoparameter',
            unique_together=set([('video', 'parameter')]),
        ),
        migrations.AlterUniqueTogether(
            name='videoauthor',
            unique_together=set([('video', 'author')]),
        ),
        migrations.AlterUniqueTogether(
            name='referenceeditor',
            unique_together=set([('reference', 'editor')]),
        ),
        migrations.AlterUniqueTogether(
            name='referenceauthor',
            unique_together=set([('reference', 'author')]),
        ),
        migrations.AlterUniqueTogether(
            name='pagesimilar',
            unique_together=set([('origin', 'similar')]),
        ),
        migrations.AlterUniqueTogether(
            name='pagerelationship',
            unique_together=set([('origin', 'related', 'relationship_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='pagenavigationsub',
            unique_together=set([('navigation', 'navigation_subphrase')]),
        ),
        migrations.AlterUniqueTogether(
            name='pagenavigation',
            unique_together=set([('page', 'navigation_phrase')]),
        ),
        migrations.AlterUniqueTogether(
            name='pagecitation',
            unique_together=set([('page', 'code')]),
        ),
        migrations.AlterUniqueTogether(
            name='pageauthor',
            unique_together=set([('page', 'author')]),
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together=set([('code', 'page_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='newsauthor',
            unique_together=set([('newsitem', 'author')]),
        ),
        migrations.AlterUniqueTogether(
            name='imagenotationsystem',
            unique_together=set([('image', 'notation_system')]),
        ),
        migrations.AlterUniqueTogether(
            name='imageauthor',
            unique_together=set([('image', 'author')]),
        ),
        migrations.AlterUniqueTogether(
            name='auxiliaryfile',
            unique_together=set([('code', 'file_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='applettypeparameter',
            unique_together=set([('applet_type', 'parameter_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='applettext',
            unique_together=set([('applet', 'code')]),
        ),
        migrations.AlterUniqueTogether(
            name='appletparameter',
            unique_together=set([('applet', 'parameter')]),
        ),
        migrations.AlterUniqueTogether(
            name='appletnotationsystem',
            unique_together=set([('applet', 'notation_system')]),
        ),
        migrations.AlterUniqueTogether(
            name='appletauthor',
            unique_together=set([('applet', 'author')]),
        ),
    ]
