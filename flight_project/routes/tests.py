from django.test import TestCase
from django.core.exceptions import ValidationError
from routes.models import Airport
from routes.forms import AirportRouteForm
from routes.views import find_shortest_path

# routes/tests.py

class FlightManagementSystemTests(TestCase):

    def setUp(self):
        # Create standard layout:
        #       A
        #      / \
        #     B   C
        #    /
        #   D
        self.a = Airport.objects.create(code="A")
        self.b = Airport.objects.create(code="B", parent=self.a)
        self.c = Airport.objects.create(code="C", parent=self.a)
        self.d = Airport.objects.create(code="D", parent=self.b)

        # Connect parent children with durations
        self.a.left = self.b
        self.a.left_duration = 300
        self.a.right = self.c
        self.a.right_duration = 200
        self.a.save()

        self.b.left = self.d
        self.b.left_duration = 200
        self.b.save()

    def test_shortest_path_simple(self):
        # Simple downward: A -> B
        path, dist = find_shortest_path(self.a, self.b)
        self.assertEqual([n.code for n in path], ["A", "B"])
        self.assertEqual(dist, 300)

    def test_shortest_path_backward(self):
        # Backward: B -> A
        path, dist = find_shortest_path(self.b, self.a)
        self.assertEqual([n.code for n in path], ["B", "A"])
        self.assertEqual(dist, 300)

    def test_shortest_path_sideways(self):
        # Sideways: B -> A -> C
        path, dist = find_shortest_path(self.b, self.c)
        self.assertEqual([n.code for n in path], ["B", "A", "C"])
        self.assertEqual(dist, 500)

    def test_shortest_path_multi_step(self):
        # Multi-step: D -> B -> A -> C
        path, dist = find_shortest_path(self.d, self.c)
        self.assertEqual([n.code for n in path], ["D", "B", "A", "C"])
        self.assertEqual(dist, 700)

    def test_shortest_path_alternative_shorter_duration(self):
        # Let's add an alternative path from D -> C directly (simulating tree bypass/shortcut in layout if exists)
        # In a strict tree it might not exist, but let's check Dijkstra with multiple path options
        # We can create another connection if we link them (e.g. D.right = C with small duration)
        self.d.right = self.c
        self.d.right_duration = 50
        self.d.save()

        # Path D -> C is now directly available with duration 50, whereas D -> B -> A -> C is 700
        path, dist = find_shortest_path(self.d, self.c)
        self.assertEqual([n.code for n in path], ["D", "C"])
        self.assertEqual(dist, 50)

    def test_longest_route_multi_step(self):
        # Longest path from setUp is D -> B -> A -> C with duration 700
        # Let's call the longest_route logic programmatically (similar to longest_route view)
        from routes.views import find_longest_path_from
        airports = list(Airport.objects.all())
        airport_map = {a.id: a for a in airports}
        adj = {a.id: [] for a in airports}
        for a in airports:
            if a.left_id and a.left_id in airport_map:
                adj[a.id].append((a.left_id, a.left_duration))
                adj[a.left_id].append((a.id, a.left_duration))
            if a.right_id and a.right_id in airport_map:
                adj[a.id].append((a.right_id, a.right_duration))
                adj[a.right_id].append((a.id, a.right_duration))

        longest_path_ids = []
        longest_duration = -1
        for a in airports:
            path, dist = find_longest_path_from(a.id, adj, set())
            if dist > longest_duration:
                longest_duration = dist
                longest_path_ids = path

        path_codes = [airport_map[nid].code for nid in longest_path_ids]
        self.assertEqual(path_codes, ["D", "B", "A", "C"])
        self.assertEqual(longest_duration, 700)

    def test_airport_route_form_validation(self):
        # Form tries to add a new child 'E' to 'A' at 'left' position.
        # But 'left' position of 'A' is already occupied by 'B'.
        form_data = {
            "parent_airport": self.a.id,
            "airport_code": "E",
            "position": "left",
            "duration": 100
        }
        form = AirportRouteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("position", form.errors)
        self.assertEqual(form.errors["position"][0], "Left position is already occupied.")

    def test_cycle_validation_self_loops(self):
        # Test self loop (pointing left to self)
        with self.assertRaises(ValidationError):
            self.a.left = self.a
            self.a.save()

    def test_cycle_validation_pointing_to_parent_as_child(self):
        # Test child pointing back to its parent as left child
        with self.assertRaises(ValidationError):
            self.b.left = self.a
            self.b.save()

    def test_cycle_validation_ancestor_cycles(self):
        # Test cycle in parent hierarchy (D -> B -> A, making A's parent D)
        with self.assertRaises(ValidationError):
            self.a.parent = self.d
            self.a.save()
