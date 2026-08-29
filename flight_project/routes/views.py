from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import AirportRouteForm,RootAirportForm,NodeSearchForm,ShortestRouteForm
from .models import Airport


def add_route(request):

    if request.method == "POST":

        form = AirportRouteForm(request.POST)

        if form.is_valid():

            parent = form.cleaned_data["parent_airport"]
            code = form.cleaned_data["airport_code"]
            position = form.cleaned_data["position"]
            duration = form.cleaned_data["duration"]

            # Create the new airport/node
            child = Airport.objects.create(
                code=code,
                parent=parent
            )

            if position == "left":

                # Check whether left position already has a node
                if parent.left is not None:
                    form.add_error(
                        "position",
                        "Left position is already occupied."
                    )
                    child.delete()

                    return render(
                        request,
                        "routes/add_route.html",
                        {"form": form}
                    )

                # Connect child to parent's left side
                parent.left = child
                parent.left_duration = duration

            else:

                # Check whether right position already has a node
                if parent.right is not None:
                    form.add_error(
                        "position",
                        "Right position is already occupied."
                    )
                    child.delete()

                    return render(
                        request,
                        "routes/add_route.html",
                        {"form": form}
                    )

                # Connect child to parent's right side
                parent.right = child
                parent.right_duration = duration

            # Save the updated parent
            parent.save()

            messages.success(
                request,
                f"Route to {code} added successfully."
            )

            return redirect("add_route")

    else:
        form = AirportRouteForm()

    return render(
        request,
        "routes/add_route.html",
        {"form": form}
    )

def create_root_airport(request):

    if request.method == "POST":

        # Create form with submitted data
        form = RootAirportForm(request.POST)

        if form.is_valid():

            # Get the validated airport code
            code = form.cleaned_data["code"]

            # Create the root airport
            Airport.objects.create(
                code=code
            )

            messages.success(
                request,
                f"Root airport {code} created successfully."
            )

            return redirect("create_root_airport")

    else:
        # Empty form for GET request
        form = RootAirportForm()

    return render(
        request,
        "routes/create_root_airport.html",
        {"form": form}
    )

def find_nth_node(request):

    result = None
    error = None

    if request.method == "POST":

        form = NodeSearchForm(request.POST)

        if form.is_valid():

            # Get the starting airport
            current = form.cleaned_data["airport"]

            # Get left or right
            direction = form.cleaned_data["direction"]

            # Get number of steps
            n = form.cleaned_data["n"]

            # Move N times
            for i in range(n):

                if direction == "left":
                    current = current.left
                else:
                    current = current.right

                # No node exists in this direction
                if current is None:
                    error = "No airport exists at this position."
                    break

            # If traversal was successful
            if error is None:
                result = current

    else:
        form = NodeSearchForm()

    return render(
        request,
        "routes/search_node.html",
        {
            "form": form,
            "result": result,
            "error": error,
        }
    )


def longest_route(request):

    # Get all airports from the database
    airports = Airport.objects.all()

    longest = None

    # Check every airport
    for airport in airports:

        # Check left route
        if airport.left is not None:

            if longest is None or airport.left_duration > longest["duration"]:

                longest = {
                    "from": airport,
                    "to": airport.left,
                    "duration": airport.left_duration,
                }

        # Check right route
        if airport.right is not None:

            if longest is None or airport.right_duration > longest["duration"]:

                longest = {
                    "from": airport,
                    "to": airport.right,
                    "duration": airport.right_duration,
                }

    return render(
        request,
        "routes/longest_route.html",
        {
            "longest": longest,
        }
    )

def shortest_path(current, target, path=None, duration=0, visited=None):

    if path is None:
        path = []

    if visited is None:
        visited = set()

    # Add current airport
    path = path + [current]
    visited.add(current)

    # Target found
    if current == target:
        return path, duration

    routes = []

    # LEFT
    if current.left and current.left not in visited:
        result = shortest_path(
            current.left,
            target,
            path,
            duration + current.left_duration,
            visited.copy()
        )

        if result:
            routes.append(result)

    # RIGHT
    if current.right and current.right not in visited:
        result = shortest_path(
            current.right,
            target,
            path,
            duration + current.right_duration,
            visited.copy()
        )

        if result:
            routes.append(result)

    # PARENT
    if current.parent and current.parent not in visited:

        if current.parent.left == current:
            parent_duration = current.parent.left_duration
        else:
            parent_duration = current.parent.right_duration

        result = shortest_path(
            current.parent,
            target,
            path,
            duration + parent_duration,
            visited.copy()
        )

        if result:
            routes.append(result)

    # No route
    if not routes:
        return None

    # Return route with smallest duration
    return min(routes, key=lambda x: x[1])

def shortest_route(request):

    result = None
    error = None

    if request.method == "POST":

        form = ShortestRouteForm(request.POST)

        if form.is_valid():

            from_airport = form.cleaned_data["from_airport"]
            to_airport = form.cleaned_data["to_airport"]

            result = shortest_path(
                from_airport,
                to_airport
            )

            if result is None:
                error = "No route found between these airports."

    else:
        form = ShortestRouteForm()

    return render(
        request,
        "routes/shortest_route.html",
        {
            "form": form,
            "result": result,
            "error": error,
        }
    )