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
router.register(r'transaction/transactions', views.TransactionViewSet)
# router.register(r'transaction/stat', views.TransactionStatAPIView.as_view(), basename='transactionstat')
router.register(r'faccount/categorytype', views.FAccountCategoryTypeViewSet)
router.register(r'faccount/majorcategory', views.FAccountMajorCategoryViewSet)
router.register(r'faccount/minorcategory', views.FAccountMinorCategoryViewSet)
router.register(r'faccount/majorminorcategorylink', views.FAccountMajorMinorCategoryLinkViewSet)
router.register(r'faccount/category', views.FAccountCategoryViewSet)
router.register(r'faccount/subcategory', views.FAccountSubCategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='schema'),
    path('transaction/stat', views.TransactionStatAPIView.as_view(), name='transactionstat-detail'),
    path('transaction/upload-ledgers', views.UploadLedgerAPIView.as_view(), name='transaction-upload-ledgers'),
    path('transaction/download/<str:file_type>', views.TransactionDownloadViewSet.as_view(), name='transaction-download'),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls'))
]
