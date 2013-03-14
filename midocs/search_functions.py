from haystack.query import SearchQuerySet, SQ 

class midocsSearchQuerySet(SearchQuerySet):
    """
    Modify SearchQuerySet to replace auto_query
    with explicitly searching for title and description 

    """

    def auto_query(self, query_string):

        """
        Performs a best guess constructing the search query.
        
        This method is somewhat naive but works well enough for the simple,
        common cases.
        """
        clone = self._clone()
        
        # Pull out anything wrapped in quotes and do an exact match on it.
        open_quote_position = None
        non_exact_query = query_string
        
        # cleaned_filter_strings=[]
        # cleaned_exclude_strings=[]

        for offset, char in enumerate(query_string):
            if char == '"':
                if open_quote_position != None:
                    current_match = query_string[open_quote_position + 1:offset]

                    if current_match:
                        cleaned_string = clone.query.clean(current_match)
                        clone = clone.filter(content=cleaned_string).filter(title=cleaned_string).filter(description=cleaned_string)
                        #cleaned_filter_strings.append(clone.query.clean(current_match))

                    non_exact_query = non_exact_query.replace('"%s"' % current_match, '', 1)
                    open_quote_position = None
                else:
                    open_quote_position = offset
            # print offset, char
            # print open_quote_position
            # print non_exact_query
        
        # Pseudo-tokenize the rest of the query.
        keywords = non_exact_query.split()
        
        # Loop through keywords and add filters to the query.
        # first skip excludes
        for keyword in keywords:
            if keyword.startswith('-') and len(keyword) > 1:
                continue
            
            cleaned_keyword = clone.query.clean(keyword)

            #print "cleaned_keyword = %s" % cleaned_keyword
            clone = clone.filter(content=cleaned_keyword).filter(title=cleaned_keyword).filter(description=cleaned_keyword)


        # now loop through and get the excludes
        for keyword in keywords:
            if not (keyword.startswith('-') and len(keyword) > 1):
                continue
            keyword = keyword[1:]
            
            cleaned_keyword = clone.query.clean(keyword)

            #print "cleaned_keyword (excluded) = %s" % cleaned_keyword

            clone = clone.exclude(content=cleaned_keyword,title=cleaned_keyword,description=cleaned_keyword)


        # if(cleaned_filter_strings or cleaned_exclude_strings):
        #     content_filter_statement =""
        #     title_filter_statement = ""
        #     description_filter_statement = ""
        #     exclude_statement =""
        #     if(cleaned_filter_strings):
        #         content_filter_statement += "("
        #         title_filter_statement += "("
        #         description_filter_statement += "("
        #         for (num, keyword) in enumerate(cleaned_filter_strings):
        #             content_filter_statement += "SQ(content='%s')" % keyword
        #             title_filter_statement += "SQ(title='%s')" % keyword
        #             description_filter_statement += "SQ(description='%s')" % keyword
        #             if(num < len(cleaned_filter_strings)-1):
        #                 content_filter_statement += "|"
        #                 title_filter_statement += "|"
        #                 description_filter_statement += "|"
        #         content_filter_statement += ")"
        #         title_filter_statement += ")"
        #         description_filter_statement += ")"
        #         filter_statement = "(%s|%s|%s)" % (content_filter_statement, title_filter_statement, description_filter_statement)
                    
        #     if(cleaned_exclude_strings):
        #         exclude_statement += "~("
            
        #         for (num, keyword) in enumerate(cleaned_exclude_strings):
        #             exclude_statement += "SQ(content='%s')|SQ(title='%s')|SQ(description='%s')" % (keyword, keyword, keyword)

        #             #exclude_statement += "(~SQ(content='%s'))" % keyword

        #             if(num < len(cleaned_exclude_strings)-1):
        #                 exclude_statement += "|"
        #         exclude_statement += ")"
            
        #     if(cleaned_filter_strings):
        #         if(cleaned_exclude_strings):
        #             total_statement = "%s&%s" % (filter_statement,exclude_statement)
        #         else:
        #             total_statement=filter_statement
        #     else:
        #         total_statement=exclude_statement

        #     filter_string = "clone = clone.filter(%s)" % total_statement

        #     print cleaned_filter_strings
        #     print cleaned_exclude_strings
        #     print filter_string
            
        #     exec(filter_string)

        return clone
    
