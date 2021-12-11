from django import template

register = template.Library()


@register.filter(name='get_filter_values')
def get_filter_values(value):
    """
    Cоздание списка из параметорв breakfast/lunch/dinner
    полученных в форме QueryDict из GET-запроса.
    """
    return value.getlist('filters')


@register.filter(name='get_filter_link')
def get_filter_values(request, tag):
    """Изменение строки запроса в соответствии с выбранными тегами."""
    new_request = request.GET.copy()
    # eсли тег уже есть в списке, он должен
    # выключиться при нажатии в браузере - удаляем его
    if tag.value in request.GET.getlist('filters'):
        filters = new_request.getlist('filters')
        filters.remove(tag.value)
        new_request.setlist('filters', filters)
    # если тега ещё нет, то добавляем его в список
    else:
        new_request.appendlist('filters', tag.value)
    # возвращаем новый запрос с помощью метода QueryDict,
    # который формирует строку запроса
    return new_request.urlencode()
