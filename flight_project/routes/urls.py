from django.urls import path
from . import views


urlpatterns = [
    path(
        "",
        views.create_root_airport,
        name="create_root_airport"
    ),

    path(
        "add-route/",
        views.add_route,
        name="add_route"
    ),
    path(
    "search-node/",
    views.find_nth_node,
    name="find_nth_node"
    ),

    path(
    "longest-route/",
    views.longest_route,
    name="longest_route"
),

path(
    "shortest-route/",
    views.shortest_route,
    name="shortest_route"
),
]