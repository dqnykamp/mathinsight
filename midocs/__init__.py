try:
    from django.contrib.comments.moderation import moderator
    from micomments.moderation import ModeratorWithoutObject, ModeratorWithObject
    from midocs.models import Page, Image, Applet, Author

    if Page not in moderator._registry:
        moderator.register(Page, ModeratorWithObject)
    if Applet not in moderator._registry:
        moderator.register(Applet, ModeratorWithObject)
    if Image not in moderator._registry:
        moderator.register(Image, ModeratorWithObject)
    if Author not in moderator._registry:
        moderator.register(Author, ModeratorWithoutObject)
except:
    pass
