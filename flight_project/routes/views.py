from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import AirportRouteForm, RootAirportForm, NodeSearchForm, ShortestRouteForm
from .models import Airport


def add_route(request):

    if request.method == "POST":

        form = AirportRouteForm(request.POST)

        if form.is_valid():

            parent = form.cleaned_data["parent_airport"]
            code = form.cleaned_data["airport_code"]
            position = form.cleaned_data["position"]
            duration = form.cleaned_data["duration"]

            # Create child airport
            child = Airport.objects.create(
                code=code,
                parent=parent
            )

            # Connect child to parent
            if position == "left":
                parent.left = child
                parent.left_duration = duration
            else:
                parent.right = child
                parent.right_duration = duration

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

def build_airport_graph():
    """
    Helper function to load all airports and build a graph (adjacency list).
    This graph allows us to travel forwards (parent to child), backwards (child to parent),
    and sideways, satisfying the route requirements.
    
    Returns:
        airports: List of all Airport objects
        airport_map: Dictionary mapping airport ID to Airport object
        adj: Adjacency list where adj[airport_id] = [(neighbor_id, flight_duration), ...]
    """
    # Fetch all airports at once to be efficient (prevents N+1 query issue)
    airports = list(Airport.objects.all())
    airport_map = {a.id: a for a in airports}
    
    # Initialize an empty list of neighbors for each airport
    adj = {a.id: [] for a in airports}
    
    for a in airports:
        # If the airport has a left child, add a connection in BOTH directions
        if a.left_id and a.left_id in airport_map:
            adj[a.id].append((a.left_id, a.left_duration))
            adj[a.left_id].append((a.id, a.left_duration))
            
        # If the airport has a right child, add a connection in BOTH directions
        if a.right_id and a.right_id in airport_map:
            adj[a.id].append((a.right_id, a.right_duration))
            adj[a.right_id].append((a.id, a.right_duration))
            
    return airports, airport_map, adj


def find_longest_path_from(node_id, adj, visited):
    """
    Recursively finds the longest path starting from a specific airport.
    """
    visited.add(node_id)
    longest_path = [node_id]
    longest_duration = 0

    # Check all connected neighbors
    for neighbor_id, duration in adj[node_id]:
        if neighbor_id not in visited:
            # Continue searching from the neighbor
            path, dist = find_longest_path_from(neighbor_id, adj, visited.copy())
            
            # If this path is longer than what we have found so far, update it
            if dist + duration > longest_duration:
                longest_duration = dist + duration
                longest_path = [node_id] + path

    return longest_path, longest_duration


def longest_route(request):
    """
    View to find and display the longest route in the entire airport network.
    """
    airports, airport_map, adj = build_airport_graph()
    
    if not airports:
        return render(request, "routes/longest_route.html", {"longest": None})

    longest_path_ids = []
    longest_duration = -1

    # Try starting the longest path from every possible airport
    for a in airports:
        path, dist = find_longest_path_from(a.id, adj, set())
        
        # Keep track of the absolute longest path found across all starting points
        if dist > longest_duration:
            longest_duration = dist
            longest_path_ids = path

    # Convert airport IDs back to Airport objects for the HTML template
    path_nodes = [airport_map[nid] for nid in longest_path_ids]
    longest = (path_nodes, longest_duration) if longest_duration > 0 else None

    return render(
        request,
        "routes/longest_route.html",
        {"longest": longest}
    )


def find_shortest_path(start, target):
    """
    Finds the shortest path between a start and target airport using Dijkstra's algorithm.
    This guarantees we find the path with the shortest total flight duration.
    """
    # If we are already at the target, the distance is 0
    if start.id == target.id:
        return [start], 0

    airports, airport_map, adj = build_airport_graph()

    import heapq
    # The priority queue stores: (current_total_duration, current_airport_id, path_taken_so_far)
    queue = [(0, start.id, [start.id])]
    visited = set()

    while queue:
        # Get the path with the SMALLEST total duration from the queue
        dist, node_id, path = heapq.heappop(queue)

        # Skip if we already visited this airport to avoid cycles
        if node_id in visited:
            continue
        visited.add(node_id)

        # If we reached our target, we are done! We found the shortest path.
        if node_id == target.id:
            # Convert airport IDs back to Airport objects
            path_nodes = [airport_map[nid] for nid in path]
            return path_nodes, dist

        # Add all connected neighbors to the queue to explore them
        for neighbor_id, duration in adj[node_id]:
            if neighbor_id not in visited:
                new_distance = dist + duration
                new_path = path + [neighbor_id]
                heapq.heappush(queue, (new_distance, neighbor_id, new_path))

    # Return None if no path exists at all
    return None


def shortest_route(request):
    result = None
    error = None

    if request.method == "POST":
        form = ShortestRouteForm(request.POST)

        if form.is_valid():
            from_airport = form.cleaned_data["from_airport"]
            to_airport = form.cleaned_data["to_airport"]

            result = find_shortest_path(from_airport, to_airport)

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