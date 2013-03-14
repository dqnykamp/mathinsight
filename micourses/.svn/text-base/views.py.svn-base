from micourses.models import CommentForCredit
from micomments.models import MiComment
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
import datetime

@login_required
def profileview(request):

    theuser=request.user

    credit_groups=[];

    for thegroup in theuser.groups.all():
        # find pages with possible comments for credit
        possible_comment_credits = CommentForCredit.objects.order_by('deadline').filter(group=thegroup)

        total_available=0
        total_attempted=0
        total_credit=0
        page_list = []
        for comment_page in possible_comment_credits:
            thepage = comment_page.page
            if datetime.datetime.now() > comment_page.opendate:
                total_available+=1
                available=True
            else:
                available=False

            # check if user posted a comment
            thecomments = MiComment.objects.filter(content_type__model='page',
                                                   object_pk=thepage.id,
                                                   user=theuser, 
                                                   credit_eligible=True,
                                                   credit_group=thegroup)
            
            attempted = False
            credit = False
            if thecomments:
                attempted = True
                total_attempted+=1

                # check if got credit for any comments
                for comment in thecomments:
                    if comment.credit:
                        credit=True
                        total_credit+=1
                        break;
                
            credit_info = {'page': thepage, 'available': available,
                           'opendate': comment_page.opendate,
                           'deadline': comment_page.deadline,
                           'attempted': attempted, 'credit': credit }
            
            page_list.append(credit_info)

        group_totals={'total_available': total_available,
                      'total_attempted': total_attempted,
                      'total_credit': total_credit,}

        group_info = {'group': thegroup, 'page_list': page_list, 
                      'group_totals': group_totals}
        credit_groups.append(group_info)
    
    return render_to_response \
        ('registration/profile.html', {'credit_groups': credit_groups,
                                       },
         context_instance=RequestContext(request))
