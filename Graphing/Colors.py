CATEGORY_COLORS = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
                   '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
COLOR_DISCRETE_MAP = {
    "Passenger Cars": '#636EFA',
    "Light Commercial Vehicles": '#FFA15A',
    "Heavy Duty Trucks": '#EF553B',
    "Buses": '#FF97FF',
    "L-Category": '#00CC96',
    "Off Road": '#8C564B'
}

# Colors for the segmentation labels not included in CHART_CONFIG (ex: a new segment), assigned in order
FALLBACK_SEGMENTATION_COLORS = ['rgb(166,206,227)', 'rgb(178,223,138)', 'rgb(251,154,153)', 'rgb(253,191,111)',
                                'rgb(202,178,214)', 'rgb(255,255,153)', 'rgb(177,89,40)', 'rgb(128,128,128)']

# Stock per manufacturing year charts: for each Category, the segmentation labels (Fuel + Segment) in the order they
# are shown in the chart, with the color of each one.
CHART_CONFIG = {
    "Passenger Cars": [
        ('Battery electric', 'rgb(0,68,27)'),
        ('PHEV', 'rgb(35,139,69)'),
        ('Hybrid', 'rgb(199,233,192)'),
        ('Diesel Large-SUV-Executive', 'rgb(8,48,107)'),
        ('Diesel Medium', 'rgb(33,113,181)'),
        ('Diesel Small', 'rgb(107,174,214)'),
        ('Diesel Mini', 'rgb(198,219,239)'),
        ('Petrol Large-SUV-Executive', 'rgb(127,39,4)'),
        ('Petrol Medium', 'rgb(217,72,1)'),
        ('Petrol Small', 'rgb(253,141,60)'),
        ('Petrol Mini', 'rgb(253,208,162)'),
        ('LPG Bi-fuel Small', 'rgb(171,171,171)'),
    ],
    "Light Commercial Vehicles": [
        ('Battery electric', 'rgb(0,68,27)'),
        ('Diesel N1-I', 'rgb(8,48,107)'),
        ('Diesel N1-II', 'rgb(33,113,181)'),
        ('Diesel N1-III', 'rgb(107,174,214)'),
        ('Petrol N1-I', 'rgb(127,39,4)'),
        ('Petrol N1-II', 'rgb(217,72,1)'),
        ('Petrol N1-III', 'rgb(253,141,60)'),
        ('LPG Bi-fuel N1-I', 'rgb(171,171,171)'),
        ('LPG Bi-fuel N1-II', 'rgb(135,135,135)'),
        ('LPG Bi-fuel N1-III', 'rgb(99,99,99)'),
        ('PHEV', 'rgb(35,139,69)'),
        ('Hybrid', 'rgb(199,233,192)'),
    ],
    "Heavy Duty Trucks": [
        ('Diesel Rigid <=7,5 t', 'rgb(8,48,107)'),
        ('Diesel Rigid 7,5 - 12 t', 'rgb(8,81,156)'),
        ('Diesel Rigid 12 - 14 t', 'rgb(33,113,181)'),
        ('Diesel Rigid 14 - 20 t', 'rgb(66,146,198)'),
        ('Diesel Rigid 20 - 26 t', 'rgb(107,174,214)'),
        ('Diesel Rigid 26 - 28 t', 'rgb(158,202,225)'),
        ('Diesel Rigid 28 - 32 t', 'rgb(198,219,239)'),
        ('Diesel Rigid >32 t', 'rgb(222,235,247)'),
        ('Petrol Rigid <=7,5 t', 'rgb(127,39,4)'),
        ('Petrol Rigid 7,5 - 12 t', 'rgb(217,72,1)'),
        ('LPG Bi-fuel Rigid <=7,5 t', 'rgb(171,171,171)'),
        ('Hybrid', 'rgb(199,233,192)'),
    ],
    "Buses": [
        ('Diesel Urban Buses Midi <=15 t', 'rgb(8,48,107)'),
        ('Diesel Urban Buses Standard 15 - 18 t', 'rgb(33,113,181)'),
        ('Diesel Urban Buses Articulated >18 t', 'rgb(107,174,214)'),
        ('Hybrid', 'rgb(199,233,192)'),
    ],
    "L-Category": [
        ('Battery electric', 'rgb(0,68,27)'),
        ('Petrol Mopeds 2-stroke <50 cm³', 'rgb(127,39,4)'),
        ('Petrol Motorcycles 4-stroke <250 cm³', 'rgb(217,72,1)'),
        ('Petrol Motorcycles 4-stroke 250 - 750 cm³', 'rgb(253,141,60)'),
        ('Petrol Motorcycles 4-stroke >750 cm³', 'rgb(253,208,162)'),
        ('Diesel Motorcycles 4-stroke >750 cm³', 'rgb(107,174,214)'),
    ],
}

# Label used for vehicles with no Segment or no Euro Standard
NO_SEGMENT_LABEL = 'Sin segmento'
NO_EURO_LABEL = 'Sin Euro'
