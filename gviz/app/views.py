from django.shortcuts import render


def index(request):
    """Main graph explorer view"""
    return render(request, 'app/index.html')
