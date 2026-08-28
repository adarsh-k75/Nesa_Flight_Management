from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import AirportRouteForm,RootAirportForm,NodeSearchForm,ShortestRouteForm
from .models import Airport


def add_route(request):

    if request.method == "POST":

        # Create the form with the submitted data
        form = AirportRouteForm(request.POST)

        if form.is_valid():

            # Get validated values from the form
            parent = form.cleaned_data["parent_airport"]
            code = form.cleaned_data["airport_code"]
            position = form.cleaned_data["position"]
            duration = form.cleaned_data["duration"]

            # Create the new airport/node
            child = Airport.objects.create(
                code=code
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
        # Empty form for GET request
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

def find_path(current, target, path=None, total_duration=0):

    if path is None:
        path = []

    # Add current airport to the path
    path.append(current)

    # We reached the destination
    if current == target:
        return path, total_duration

    # Check the left child
    if current.left:

        result = find_path(
            current.left,
            target,
            path.copy(),
            total_duration + current.left_duration
        )

        if result:
            return result

    # Check the right child
    if current.right:

        result = find_path(
            current.right,
            target,
            path.copy(),
            total_duration + current.right_duration
        )

        if result:
            return result

    # Target not found from this branch
    return None

def shortest_route(request):

    result = None
    error = None

    if request.method == "POST":

        form = ShortestRouteForm(request.POST)

        if form.is_valid():

            from_airport = form.cleaned_data["from_airport"]
            to_airport = form.cleaned_data["to_airport"]

            # Find path between the two airports
            result = find_path(
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