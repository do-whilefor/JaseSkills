from django.contrib.auth.decorators import login_required
@login_required
def order_detail(request, id):
    return JsonResponse({'id': id})
