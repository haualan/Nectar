from rest_framework.settings import api_settings
from rest_framework.pagination import PageNumberPagination, DjangoPaginator
# from rest_framework.pagination import BasePagination, _positive_int, Response, OrderedDict, replace_query_param, loader, Context, _get_displayed_page_numbers, _get_page_links, remove_query_param
from django.utils.translation import ugettext_lazy as _

class SC_PageNumberPagination(PageNumberPagination):
    """
    A simple page number based style that supports page numbers as
    query parameters. For example:
    http://api.example.org/accounts/?page=4
    http://api.example.org/accounts/?page=4&page_size=100
    """
    # The default page size.
    # Defaults to `None`, meaning pagination is disabled.
    page_size = api_settings.PAGE_SIZE

    # Client can control the page using this query parameter.
    page_query_param = 'page'

    # Client can control the page size using this query parameter.
    # Default is 'None'. Set to eg 'page_size' to enable usage.
    page_size_query_param = 'page_size'

    # Set to an integer to limit the maximum page size the client may request.
    # Only relevant if 'page_size_query_param' has also been set.
    max_page_size = None

    last_page_strings = ('last',)

    template = 'rest_framework/pagination/numbers.html'

    invalid_page_message = _('Invalid page "{page_number}": {message}.')

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            # set page size to be above queryset size if not set in settings
            # return None
            # print 'not page size'
            page_size = len(queryset) + 1

        paginator = DjangoPaginator(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=six.text_type(exc)
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    # def get_paginated_response(self, data):
    #     return Response(OrderedDict([
    #         ('count', self.page.paginator.count),
    #         ('next', self.get_next_link()),
    #         ('previous', self.get_previous_link()),
    #         ('results', data)
    #     ]))

    # def get_page_size(self, request):
    #     if self.page_size_query_param:
    #         try:
    #             return _positive_int(
    #                 request.query_params[self.page_size_query_param],
    #                 strict=True,
    #                 cutoff=self.max_page_size
    #             )
    #         except (KeyError, ValueError):
    #             pass

    #     return self.page_size

    # def get_next_link(self):
    #     if not self.page.has_next():
    #         return None
    #     url = self.request.build_absolute_uri()
    #     page_number = self.page.next_page_number()
    #     return replace_query_param(url, self.page_query_param, page_number)

    # def get_previous_link(self):
    #     if not self.page.has_previous():
    #         return None
    #     url = self.request.build_absolute_uri()
    #     page_number = self.page.previous_page_number()
    #     if page_number == 1:
    #         return remove_query_param(url, self.page_query_param)
    #     return replace_query_param(url, self.page_query_param, page_number)

    # def get_html_context(self):
    #     base_url = self.request.build_absolute_uri()

    #     def page_number_to_url(page_number):
    #         if page_number == 1:
    #             return remove_query_param(base_url, self.page_query_param)
    #         else:
    #             return replace_query_param(base_url, self.page_query_param, page_number)

    #     current = self.page.number
    #     final = self.page.paginator.num_pages
    #     page_numbers = _get_displayed_page_numbers(current, final)
    #     page_links = _get_page_links(page_numbers, current, page_number_to_url)

    #     return {
    #         'previous_url': self.get_previous_link(),
    #         'next_url': self.get_next_link(),
    #         'page_links': page_links
    #     }

    # def to_html(self):
    #     template = loader.get_template(self.template)
    #     context = Context(self.get_html_context())
    #     return template.render(context)

    
