from django.shortcuts import render


def lista_paineis(request):
    return render(request, 'paineis/lista_paineis.html', {'paineis': []})
