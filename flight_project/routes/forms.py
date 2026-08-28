from django import forms
from .models import Airport


class AirportRouteForm(forms.Form):

    # Select the existing airport that will be the parent node
    parent_airport = forms.ModelChoiceField(
        queryset=Airport.objects.all(),
        label="Parent Airport"
    )

    # Enter the code of the new airport
    airport_code = forms.CharField(
        max_length=10,
        label="Airport Code"
    )

    # Select whether the new airport is on the left or right
    position = forms.ChoiceField(
        choices=[
            ("left", "Left"),
            ("right", "Right"),
        ],
        label="Position"
    )

    # Enter the duration/distance between the parent and new airport
    duration = forms.IntegerField(
        min_value=0,
        label="Duration"
    )

    def clean_airport_code(self):
        # Get the airport code entered by the user
        code = self.cleaned_data["airport_code"].upper()

        # Prevent duplicate airport codes
        if Airport.objects.filter(code=code).exists():
            raise forms.ValidationError(
                "This airport code already exists."
            )

        return code


class RootAirportForm(forms.Form):

    # Enter the airport code for the root airport
    code = forms.CharField(
        max_length=10,
        label="Airport Code"
    )

    def clean_code(self):
        # Convert the airport code to uppercase
        code = self.cleaned_data["code"].upper()

        # Check if airport already exists
        if Airport.objects.filter(code=code).exists():
            raise forms.ValidationError(
                "This airport already exists."
            )

        return code

class NodeSearchForm(forms.Form):

    # Starting airport
    airport = forms.ModelChoiceField(
        queryset=Airport.objects.all(),
        label="Starting Airport"
    )

    # Direction to move
    direction = forms.ChoiceField(
        choices=[
            ("left", "Left"),
            ("right", "Right"),
        ],
        label="Direction"
    )

    # Number of nodes to move
    n = forms.IntegerField(
        min_value=1,
        label="N"
    )


class ShortestRouteForm(forms.Form):

    # Starting airport
    from_airport = forms.ModelChoiceField(
        queryset=Airport.objects.all(),
        label="From Airport"
    )

    # Destination airport
    to_airport = forms.ModelChoiceField(
        queryset=Airport.objects.all(),
        label="To Airport"
    )

    def clean(self):
        cleaned_data = super().clean()

        from_airport = cleaned_data.get("from_airport")
        to_airport = cleaned_data.get("to_airport")

        # Prevent selecting the same airport
        if from_airport and to_airport:
            if from_airport == to_airport:
                raise forms.ValidationError(
                    "From and To airports must be different."
                )

        return cleaned_data