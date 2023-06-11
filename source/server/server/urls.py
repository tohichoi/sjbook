"""
URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from restful_server import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'bankaccount', views.BankAccountViewSet)
router.register(r'transaction', views.TransactionViewSet)
router.register(r'faccount/categorytype', views.FAccountCategoryTypeViewSet)
router.register(r'faccount/majorcategory', views.FAccountMajorCategoryViewSet)
router.register(r'faccount/minorcategory', views.FAccountMinorCategoryViewSet)
router.register(r'faccount/majorminorcategorylink', views.FAccountMajorMinorCategoryLinkViewSet)
router.register(r'faccount/category', views.FAccountCategoryViewSet)
router.register(r'faccount/subcategory', views.FAccountSubCategoryViewSet)

urlpatterns = [

    # path('unicode/', views.UnicodeListAPIView.as_view()),
    # path('unicode/<int:pk>/', views.UnicodeRetrieveAPIView.as_view(), name='unicode-detail'),
    path('', include(router.urls)),
    path('transaction/stat', views.TransactionStatAPIView.as_view(), name='transactionstat-detail'),
    path('transaction/upload-ledgers', views.UploadLedgerAPIView.as_view(), name='transaction-upload-ledgers'),

    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls'))
]
